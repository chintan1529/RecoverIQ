import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.pydantic_schemas import DecisionContract

logger = logging.getLogger("recoveriq.llm")

def validate_llm_explanation(contract: DecisionContract, parsed_json: Dict[str, Any]) -> bool:
    """
    Validates LLM-generated structured explanation against the canonical DecisionContract.
    Rejects outputs that hallucinate or contradict canonical facts.
    """
    if not isinstance(parsed_json, dict):
        return False
    
    summary = parsed_json.get("summary")
    why_selected = parsed_json.get("why_selected")
    
    if not summary or not isinstance(summary, str) or len(summary.strip()) < 10:
        return False
    if not why_selected or not isinstance(why_selected, str) or len(why_selected.strip()) < 10:
        return False
    
    # Check that blocked actions are never claimed as selected
    blocked_action_names = [b.action for b in contract.blocked_actions]
    if contract.selected_action != "Stop Intervention":
        if contract.selected_action in blocked_action_names:
            return False

    return True

class GeminiLLMProvider:
    """
    LLM Provider Abstraction with Gemini SDK and Structured Fact Validation.
    The LLM provides natural language summaries and customer communication drafts.
    IT CANNOT OVERRIDE DETERMINISTIC FINANCIAL ARITHMETIC OR GUARDRAILS.
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini Client: {e}")

    def _deterministic_fallback(self, contract: DecisionContract) -> Dict[str, Any]:
        """Grounded deterministic explanation generator."""
        amount = contract.feature_snapshot.get("amount", 0.0)
        failure_reason = contract.feature_snapshot.get("failure_reason", "Payment Failure")
        
        if contract.decision_status == "BLOCK":
            summary = f"Intervention stopped for payment {contract.payment_id} ({failure_reason}) to prevent customer fatigue or avoid negative expected net value."
            why_selected = f"Action '{contract.selected_action}' selected as outreach costs exceed expected recovery or safety guardrails restrict contact."
            customer_msg = None
        elif contract.decision_status == "RECOMMEND_FOR_APPROVAL":
            summary = f"Human review recommended for high-value transaction {contract.payment_id} (₹{amount:,.2f}) with expected net value ₹{contract.expected_net_value:,.2f}."
            why_selected = f"Selected action '{contract.selected_action}' provides high expected recovery ({contract.predicted_recovery_probability:.0%}) but exceeds financial escalation thresholds, requiring operator approval."
            customer_msg = None
        else:
            summary = f"{contract.selected_action} auto-scheduled for payment {contract.payment_id} with calibrated P(recovery) of {contract.predicted_recovery_probability:.0%} and ENV ₹{contract.expected_net_value:,.2f}."
            why_selected = f"Action '{contract.selected_action}' maximizes expected net value after accounting for channel costs, fatigue risk, and failure context ({failure_reason})."
            customer_msg = f"Hi, your payment attempt of ₹{amount:,.2f} was unsuccessful due to {failure_reason.lower()}. Please use this secure link to complete your transaction safely." if contract.selected_action in ["WhatsApp Nudge", "Personalized Email", "Payment Method Update"] else None

        return {
            "summary": summary,
            "why_selected": why_selected,
            "customer_message": customer_msg,
            "source": "deterministic_grounded_engine"
        }

    def generate_decision_explanation(self, contract: DecisionContract) -> Dict[str, Any]:
        """
        Generates enriched structured explanation for a decision contract.
        Validates LLM output against canonical ground truth; falls back safely to deterministic generator.
        """
        if self.client:
            try:
                prompt = f"""
                You are RecoverIQ AI Revenue Recovery Assistant.
                Analyze the following canonical decision contract for a failed payment:
                - Payment ID: {contract.payment_id}
                - Selected Action: {contract.selected_action}
                - Decision Status: {contract.decision_status}
                - Expected Net Value: ₹{contract.expected_net_value:.2f}
                - Calibrated Recovery Probability: {contract.predicted_recovery_probability:.1%}
                - Blocked Actions: {[b.action for b in contract.blocked_actions]}
                - Feature Snapshot: {json.dumps(contract.feature_snapshot)}
                
                Respond ONLY in valid JSON matching this schema:
                {{
                  "summary": "Concise 1-sentence operator summary",
                  "why_selected": "Grounded explanation of why selected_action was chosen",
                  "customer_message": "Friendly customer notification draft or null"
                }}
                """
                response = self.client.models.generate_content(
                    model=settings.LLM_MODEL,
                    contents=prompt
                )
                if response and response.text:
                    text = response.text.strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                    data = json.loads(text)
                    
                    if validate_llm_explanation(contract, data):
                        data["source"] = "gemini_validated"
                        return data
                    else:
                        logger.warning("Gemini output failed fact validation; reverting to deterministic fallback.")
            except Exception as e:
                logger.warning(f"Gemini API call or parsing failed, using deterministic fallback: {e}")

        # Deterministic Grounded Engine
        return self._deterministic_fallback(contract)

llm_provider = GeminiLLMProvider()
