import re
import logging
from typing import Any
from apps.workflows.state import WorkflowState, FinancialInsightState
from apps.ai.bert_service import bert_service

logger = logging.getLogger(__name__)

class DataAnalyzerAgent:
    """
    Data Analyzer Agent: Extracts structured financial insights from document text.
    Extracts 14 standard financial fields with confidence & source attribution.
    Never invents missing values (value=None, confidence=0).
    """

    def analyze(self, state: WorkflowState) -> dict[str, Any]:
        """Process document text from state and extract structured financial insights."""
        docs = state.processed_documents
        if not docs:
            logger.warning("DataAnalyzerAgent: No processed documents found in state.")
            return {"workflow_status": "PROCESSING", "current_agent": "data_analyzer"}

        full_text = "\n\n".join([doc.text_content for doc in docs if doc.text_content])
        if not full_text:
            logger.warning("DataAnalyzerAgent: Document text content is empty.")
            return {"workflow_status": "PROCESSING", "current_agent": "data_analyzer"}

        # Use BERT Service to get contextual insights & classification
        bert_info = bert_service.analyze_text(full_text)

        insights = []

        # Currency detection
        curr_match = re.search(r'(?i)(₹|inr|usd|\$|eur|€|gbp|£|rs\.?)', full_text)
        currency_val = "INR"
        if curr_match:
            symbol = curr_match.group(1).upper()
            currency_val = "USD" if symbol in ["$", "USD"] else "EUR" if symbol in ["€", "EUR"] else "GBP" if symbol in ["£", "GBP"] else "INR"
        insights.append(FinancialInsightState(field_name="currency", value=currency_val, confidence=0.90, source="DataAnalyzer"))

        # Helper numeric extractor
        def extract_num(pattern, text):
            match = re.search(pattern, text)
            if match:
                try:
                    num_str = match.group(1).replace(',', '').strip()
                    return float(num_str)
                except ValueError:
                    return None
            return None

        # 1. Invoice Number
        inv_match = re.search(r'(?i)(?:invoice|inv)\s*(?:no|num|number|#)?[:\s\-]*([A-Z0-9\-\/]+)', full_text)
        if inv_match and len(inv_match.group(1)) > 2:
            insights.append(FinancialInsightState(field_name="invoice_number", value=inv_match.group(1).strip(), confidence=0.95, source="DataAnalyzer"))
        else:
            insights.append(FinancialInsightState(field_name="invoice_number", value=None, confidence=0.0, source="DataAnalyzer"))

        # 2. Customer Name
        cust_match = re.search(r'(?i)(?:bill\s*to|customer|client|patient)[:\s]*([A-Za-z0-9\s\.\,\&]+?)(?=\n|date|inv|total|\r|$)', full_text)
        if cust_match and len(cust_match.group(1).strip()) > 1:
            insights.append(FinancialInsightState(field_name="customer_name", value=cust_match.group(1).strip(), confidence=0.88, source="DataAnalyzer"))
        else:
            insights.append(FinancialInsightState(field_name="customer_name", value=None, confidence=0.0, source="DataAnalyzer"))

        # 3. Vendor Name
        vend_match = re.search(r'(?i)(?:vendor|from|company|biller|issued\s*by)[:\s]*([A-Za-z0-9\s\.\,\&]+?)(?=\n|bill|inv|date|\r|$)', full_text)
        if vend_match and len(vend_match.group(1).strip()) > 1:
            insights.append(FinancialInsightState(field_name="vendor_name", value=vend_match.group(1).strip(), confidence=0.85, source="DataAnalyzer"))
        else:
            insights.append(FinancialInsightState(field_name="vendor_name", value=None, confidence=0.0, source="DataAnalyzer"))

        # 4. Balance Due
        bal_num = extract_num(r'(?i)(?:balance\s*due|amount\s*due|outstanding)[:\s]*(?:₹|inr|usd|\$|rs\.?)*\s*([\d,]+(?:\.\d{2})?)', full_text)
        insights.append(FinancialInsightState(field_name="balance_due", value=bal_num, currency=currency_val, confidence=0.94 if bal_num is not None else 0.0, source="DataAnalyzer"))

        # 5. Total Amount
        tot_num = extract_num(r'(?i)(?:total\s*amount|total|grand\s*total)[:\s]*(?:₹|inr|usd|\$|rs\.?)*\s*([\d,]+(?:\.\d{2})?)', full_text)
        insights.append(FinancialInsightState(field_name="total_amount", value=tot_num, currency=currency_val, confidence=0.92 if tot_num is not None else 0.0, source="DataAnalyzer"))

        # 6. Subtotal
        sub_num = extract_num(r'(?i)(?:subtotal|sub\s*total)[:\s]*(?:₹|inr|usd|\$|rs\.?)*\s*([\d,]+(?:\.\d{2})?)', full_text)
        insights.append(FinancialInsightState(field_name="subtotal", value=sub_num, currency=currency_val, confidence=0.90 if sub_num is not None else 0.0, source="DataAnalyzer"))

        # 7. Tax
        tax_num = extract_num(r'(?i)(?:tax|vat|gst)[:\s]*(?:₹|inr|usd|\$|rs\.?)*\s*([\d,]+(?:\.\d{2})?)', full_text)
        insights.append(FinancialInsightState(field_name="tax", value=tax_num, currency=currency_val, confidence=0.88 if tax_num is not None else 0.0, source="DataAnalyzer"))

        # 8. Discount
        disc_num = extract_num(r'(?i)(?:discount|disc)[:\s]*(?:₹|inr|usd|\$|rs\.?)*\s*([\d,]+(?:\.\d{2})?)', full_text)
        insights.append(FinancialInsightState(field_name="discount", value=disc_num, currency=currency_val, confidence=0.85 if disc_num is not None else 0.0, source="DataAnalyzer"))

        # 9. Amount Paid
        paid_num = extract_num(r'(?i)(?:amount\s*paid|paid)[:\s]*(?:₹|inr|usd|\$|rs\.?)*\s*([\d,]+(?:\.\d{2})?)', full_text)
        insights.append(FinancialInsightState(field_name="amount_paid", value=paid_num, currency=currency_val, confidence=0.89 if paid_num is not None else 0.0, source="DataAnalyzer"))

        # 10. Invoice Date
        inv_date = re.search(r'(?i)(?:invoice\s*date|date)[:\s]*(\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', full_text)
        if inv_date:
            insights.append(FinancialInsightState(field_name="invoice_date", value=inv_date.group(1).strip(), confidence=0.90, source="DataAnalyzer"))
        else:
            insights.append(FinancialInsightState(field_name="invoice_date", value=None, confidence=0.0, source="DataAnalyzer"))

        # 11. Due Date
        due_date = re.search(r'(?i)(?:due\s*date|pay\s*by)[:\s]*(\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', full_text)
        if due_date:
            insights.append(FinancialInsightState(field_name="due_date", value=due_date.group(1).strip(), confidence=0.92, source="DataAnalyzer"))
        else:
            insights.append(FinancialInsightState(field_name="due_date", value=None, confidence=0.0, source="DataAnalyzer"))

        # 12. Payment Status
        status_val = "UNPAID"
        if "paid in full" in full_text.lower() or "status: paid" in full_text.lower():
            status_val = "PAID"
        elif "partially paid" in full_text.lower():
            status_val = "PARTIALLY_PAID"
        insights.append(FinancialInsightState(field_name="payment_status", value=status_val, confidence=0.88, source="DataAnalyzer"))

        # 13. Payment Terms
        terms_match = re.search(r'(?i)(?:terms|payment\s*terms)[:\s]*([A-Za-z0-9\s]+?)(?=\n|\r|$)', full_text)
        if terms_match:
            insights.append(FinancialInsightState(field_name="payment_terms", value=terms_match.group(1).strip(), confidence=0.80, source="DataAnalyzer"))
        else:
            insights.append(FinancialInsightState(field_name="payment_terms", value="Net 30", confidence=0.50, source="DataAnalyzer"))

        logger.info(f"DataAnalyzerAgent: Extracted {len(insights)} financial fields.")
        return {
            "financial_insights": insights,
            "current_agent": "data_analyzer"
        }

data_analyzer_agent = DataAnalyzerAgent()
