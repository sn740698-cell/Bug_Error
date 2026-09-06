from rest_framework import serializers
from .models import Workflow, FinancialInsight, RoutingDecision, GeneratedDraft
from apps.documents.serializers import DocumentSerializer

class FinancialInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialInsight
        fields = ['id', 'field_name', 'field_value', 'confidence', 'source', 'created_at']

class RoutingDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingDecision
        fields = ['id', 'supervisor', 'selected_target', 'reason', 'created_at']

class GeneratedDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDraft
        fields = ['id', 'draft_text', 'llm_model', 'generation_attempt', 'validation_status', 'validation_notes', 'created_at']

class WorkflowSerializer(serializers.ModelSerializer):
    document = DocumentSerializer(read_only=True)
    insights = FinancialInsightSerializer(many=True, read_only=True)
    routing_decisions = RoutingDecisionSerializer(many=True, read_only=True)
    drafts = GeneratedDraftSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'user', 'document', 'status', 'current_agent', 'current_supervisor',
            'selected_llm', 'document_sections', 'simplified_summary', 'fallback_used', 'failure_reason', 'started_at', 'completed_at',
            'progress', 'insights', 'routing_decisions', 'drafts'
        ]

    def get_progress(self, obj) -> int:
        if obj.status == 'COMPLETED':
            return 100
        if obj.status == 'FAILED':
            return 0
        if obj.current_supervisor in ['communication_orchestrator', 'communication_supervisor']:
            return 80
        if obj.current_agent in ['vector_retrieval_agent', 'retrieval_agent']:
            return 50
        return 25
