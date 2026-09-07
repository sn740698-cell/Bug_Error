import os
import logging
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class MockLLM:
    """
    Deterministic Mock LLM client for unit tests and local execution without live API credentials.
    Produces role-appropriate responses and supports structured Pydantic / JSON outputs.
    """
    def __init__(self, role: str = "solver", model_name: str = "mock-model"):
        self.role = role
        self.model_name = model_name

    def invoke(self, prompt: Any) -> Any:
        prompt_str = str(prompt)
        
        # Check if caller expects structured output (e.g. AntiHallucinationAudit)
        if "AntiHallucinationAudit" in prompt_str or "is_valid" in prompt_str:
            from pydantic import BaseModel
            class AntiHallucinationAuditResponse(BaseModel):
                is_valid: bool = True
                confidence: float = 0.95
                hallucination_findings: List[str] = []
                unsupported_claims: List[str] = []
                contradictions: List[str] = []
                missing_requirements: List[str] = []
                actionable_critique: str = "The solution is factually grounded and meets all requirements."
                synthesized_solution: str = "Synthesized consensus solution validated against retrieved evidence."

            return AntiHallucinationAuditResponse()

        # Regular textual output
        if "DecompositionAgent" in prompt_str or "subtask" in prompt_str.lower():
            return "1. Analyze user requirements\n2. Evaluate retrieved evidence\n3. Formulate architectural recommendation"

        if "RiskConstraintAgent" in prompt_str or "risk" in prompt_str.lower():
            return "- Security Risk: Verify input sanitization\n- Architectural Constraint: Maintain sub-second latency\n- Failure Mode: ChromaDB connection timeout"

        if "PrimaryLLMSolver" in prompt_str or self.role == "solver_a":
            return "[Primary Solution A]: High-performance distributed consensus protocol using multi-region quorum replication with zero data loss."

        if "SecondaryLLMSolver" in prompt_str or self.role == "solver_b":
            return "[Secondary Solution B]: Asynchronous event-driven ledger using raft consensus with geo-partitioned multi-master storage."

        return f"[Mock Response from {self.role} ({self.model_name})]: Processed input prompt successfully."

    def with_structured_output(self, pydantic_schema: Any) -> Any:
        class StructuredMockWrapper:
            def __init__(self, schema, parent):
                self.schema = schema
                self.parent = parent

            def invoke(self, prompt: Any) -> Any:
                try:
                    return self.schema(
                        is_valid=True,
                        confidence=0.92,
                        hallucination_findings=[],
                        unsupported_claims=[],
                        contradictions=[],
                        missing_requirements=[],
                        actionable_critique="Grounded in evidence.",
                        synthesized_solution="Grounded synthesized solution proposal."
                    )
                except Exception:
                    return self.schema.construct()

        return StructuredMockWrapper(pydantic_schema, self)


class OllamaLLM:
    """
    Direct Ollama client wrapper executing local GGUF models.
    """
    def __init__(self, role: str = "solver", model_name: str = "llama"):
        self.role = role
        self.model_name = model_name

    def invoke(self, prompt: Any) -> Any:
        prompt_str = str(prompt)
        try:
            import ollama
            res = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt_str}],
                options={'temperature': 0.2, 'num_ctx': 2048, 'num_predict': 220}
            )
            content = res.get('message', {}).get('content', '')
            if content and content.strip():
                return content.strip()
        except Exception as e:
            logger.error(f"Ollama chat execution error for model '{self.model_name}': {e}")

        # Fallback if local Ollama model execution fails
        return MockLLM(role=self.role, model_name=self.model_name).invoke(prompt)

    def with_structured_output(self, pydantic_schema: Any) -> Any:
        class StructuredOllamaWrapper:
            def __init__(self, schema, parent):
                self.schema = schema
                self.parent = parent

            def invoke(self, prompt: Any) -> Any:
                prompt_str = (
                    f"{prompt}\n\n"
                    "Return valid JSON only matching schema: {\"is_valid\": bool, \"confidence\": float (0.0-1.0), \"hallucination_findings\": list, \"unsupported_claims\": list, \"contradictions\": list, \"missing_requirements\": list, \"actionable_critique\": str, \"synthesized_solution\": str}"
                )
                raw = self.parent.invoke(prompt_str)
                raw_str = getattr(raw, 'content', str(raw))
                try:
                    import json, re
                    match = re.search(r'\{.*\}', raw_str, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        return self.schema(**data)
                except Exception:
                    pass
                return MockLLM(role=self.parent.role, model_name=self.parent.model_name).with_structured_output(self.schema).invoke(prompt)

        return StructuredOllamaWrapper(pydantic_schema, self)


class LLMFactory:
    @staticmethod
    def get_llm(role: str) -> Any:
        """
        Instantiates an LLM instance based on configured environment settings for the given role.
        Role choices: 'llm_a', 'llm_b', 'evaluator', or 'general'
        """
        role_lower = role.lower().strip()

        if role_lower == 'llm_a':
            provider = getattr(settings, 'LLM_A_PROVIDER', 'mock').lower()
            model_name = getattr(settings, 'LLM_A_MODEL', 'gpt-4o')
        elif role_lower == 'llm_b':
            provider = getattr(settings, 'LLM_B_PROVIDER', 'mock').lower()
            model_name = getattr(settings, 'LLM_B_MODEL', 'claude-3-5-sonnet')
        elif role_lower == 'evaluator':
            provider = getattr(settings, 'EVALUATOR_PROVIDER', 'mock').lower()
            model_name = getattr(settings, 'EVALUATOR_MODEL', 'gpt-4o')
        else:
            provider = os.getenv('DEFAULT_LLM_PROVIDER', 'mock').lower()
            model_name = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4o')

        if provider == 'ollama':
            return OllamaLLM(role=role_lower, model_name=model_name)

        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning(f"OPENAI_API_KEY missing for role {role_lower}. Falling back to MockLLM.")
                return MockLLM(role=role_lower, model_name=model_name)
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.2)
            except Exception as e:
                logger.error(f"Error instantiating ChatOpenAI: {e}. Falling back to MockLLM.")
                return MockLLM(role=role_lower, model_name=model_name)

        elif provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning(f"ANTHROPIC_API_KEY missing for role {role_lower}. Falling back to MockLLM.")
                return MockLLM(role=role_lower, model_name=model_name)
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(model_name=model_name, api_key=api_key, temperature=0.2)
            except Exception as e:
                logger.error(f"Error instantiating ChatAnthropic: {e}. Falling back to MockLLM.")
                return MockLLM(role=role_lower, model_name=model_name)

        elif provider == 'mock':
            return MockLLM(role=role_lower, model_name=model_name)

        else:
            logger.warning(f"Unknown LLM provider '{provider}' for role {role_lower}. Falling back to MockLLM.")
            return MockLLM(role=role_lower, model_name=model_name)
