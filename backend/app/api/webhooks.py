import time
import uuid
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import PaymentDB, CustomerDB, DecisionContractDB, AgentEventDB, CustomerFatigueDB
from app.schemas.pydantic_schemas import PreDecisionFeatures, DecisionContract
from app.api.payments import global_optimizer, global_ml_model, _contract_to_db, _db_dec_to_contract


router = APIRouter(prefix="/webhooks", tags=["Razorpay Webhooks"])

SAMPLE_WEBHOOKS = {
    "payment.failed.insufficient_funds": {
        "entity": "event",
        "account_id": "acc_RecoverIQ_Prod",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_insuff_001",
                    "amount": 350000,  # 3500 INR in paise
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "description": "Enterprise SaaS Pro Plan",
                    "card": {
                        "name": "Arjun Sharma",
                        "network": "Visa",
                        "type": "debit",
                        "issuer": "HDFC"
                    },
                    "email": "arjun.sharma@techcorp.in",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed due to insufficient funds in customer bank account",
                    "error_source": "customer",
                    "error_step": "payment_authentication",
                    "error_reason": "payment_failed_insufficient_funds",
                    "created_at": 1724991200
                }
            }
        },
        "created_at": 1724991201
    },
    "payment.failed.expired_card": {
        "entity": "event",
        "account_id": "acc_RecoverIQ_Prod",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_expired_002",
                    "amount": 1250000,  # 12,500 INR in paise
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "description": "Cloud Hosting Quarterly Subscription",
                    "card": {
                        "name": "Priya Nair",
                        "network": "MasterCard",
                        "type": "credit",
                        "issuer": "ICICI"
                    },
                    "email": "priya.nair@innovate.co",
                    "contact": "+919812345678",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Card has expired. Please use a valid card or alternate payment method",
                    "error_source": "issuer",
                    "error_step": "payment_authorization",
                    "error_reason": "card_expired",
                    "created_at": 1724991250
                }
            }
        },
        "created_at": 1724991251
    },
    "payment.failed.high_value_auth": {
        "entity": "event",
        "account_id": "acc_RecoverIQ_Prod",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_highval_003",
                    "amount": 8500000,  # 85,000 INR in paise
                    "currency": "INR",
                    "status": "failed",
                    "method": "netbanking",
                    "bank": "SBIN",
                    "description": "Annual Enterprise B2B License",
                    "email": "vikram.malhotra@enterpriseglobal.com",
                    "contact": "+919988776655",
                    "error_code": "GATEWAY_ERROR",
                    "error_description": "Bank network timeout during 2FA OTP verification step",
                    "error_source": "gateway",
                    "error_step": "payment_2fa",
                    "error_reason": "payment_timed_out",
                    "created_at": 1724991300
                }
            }
        },
        "created_at": 1724991301
    },
    "payment.failed.dnc_customer": {
        "entity": "event",
        "account_id": "acc_RecoverIQ_Prod",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_dnc_004",
                    "amount": 180000,  # 1,800 INR in paise
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "vpa": "rohit@okhdfcbank",
                    "description": "E-Commerce Checkout",
                    "email": "rohit.verma@optout.org",
                    "contact": "+919112233445",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "UPI PSP server declined mandate request",
                    "error_source": "psp",
                    "error_step": "payment_initiation",
                    "error_reason": "psp_declined",
                    "notes": {
                        "dnc_status": "true"
                    },
                    "created_at": 1724991350
                }
            }
        },
        "created_at": 1724991351
    },
    "subscription.halted.recurring_card": {
        "entity": "event",
        "account_id": "acc_RecoverIQ_Prod",
        "event": "subscription.halted",
        "contains": ["subscription", "payment"],
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_rzp_recurr_005",
                    "plan_id": "plan_enterprise_monthly",
                    "status": "halted",
                    "current_cycle": 6
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_rzp_sub_005",
                    "amount": 499900,  # 4,999 INR in paise
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "description": "Monthly Recurring Dunning Mandate",
                    "email": "finance@growthventures.in",
                    "contact": "+919776655443",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Recurring AutoPay mandate authentication failed",
                    "error_source": "issuer",
                    "error_step": "recurring_debit",
                    "error_reason": "recurring_mandate_failed",
                    "created_at": 1724991400
                }
            }
        },
        "created_at": 1724991401
    }
}


def _map_razorpay_error_to_domain(error_reason: str, error_desc: str) -> str:
    """Maps Razorpay raw error reason string to standardized RecoverIQ Failure Reason."""
    err_lower = (error_reason + " " + error_desc).lower()
    if "insufficient" in err_lower or "balance" in err_lower:
        return "Insufficient Funds"
    elif "expired" in err_lower:
        return "Expired Card"
    elif "timeout" in err_lower or "timed_out" in err_lower or "gateway" in err_lower:
        return "Network Timeout"
    elif "downtime" in err_lower or "bank" in err_lower or "declined" in err_lower:
        return "Bank Downtime"
    elif "auth" in err_lower or "2fa" in err_lower or "otp" in err_lower or "mandate" in err_lower:
        return "Authentication Failed"
    return "Network Timeout"


@router.get("/samples")
def get_sample_razorpay_webhooks() -> Dict[str, Any]:
    """Returns catalog of realistic Razorpay webhook payloads for instant 1-click testing."""
    return SAMPLE_WEBHOOKS


@router.post("/razorpay")
async def ingest_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Autonomous Razorpay Webhook Ingestion Gateway:
    Ingests payment.failed or subscription.halted events, extracts financial metadata,
    executes sub-10ms Calibrated Expected Net Value (ENV) policy optimization,
    commits immutable audit trail, and generates autonomous recovery dispatch payload.
    """
    t_start = time.perf_counter()
    raw_body = await request.body()

    # Cryptographic HMAC-SHA256 signature verification (if secret is configured)
    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature:
        expected_sig = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_razorpay_signature):
            raise HTTPException(status_code=401, detail="Invalid Razorpay webhook signature")

    import json
    try:
        body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_type = body.get("event", "payment.failed")
    payload = body.get("payload", {})
    payment_entity = payload.get("payment", {}).get("entity", {})

    if not payment_entity:
        raise HTTPException(status_code=400, detail="Invalid Razorpay webhook payload: missing payment.entity")

    raw_id = payment_entity.get("id", f"pay_rzp_{uuid.uuid4().hex[:8]}")

    # Pre-Flight Idempotency Check: Prevent duplicate processing or artificial fatigue inflation on replay
    existing_pay = db.query(PaymentDB).filter(PaymentDB.payment_id == raw_id).first()
    if existing_pay:
        existing_dec = (
            db.query(DecisionContractDB)
            .filter(DecisionContractDB.payment_id == raw_id)
            .order_by(DecisionContractDB.timestamp.desc())
            .first()
        )
        if existing_dec:

            contract_res = _db_dec_to_contract(existing_dec)
            t_latency = round((time.perf_counter() - t_start) * 1000, 2)
            return {
                "status": "success",
                "is_idempotent_replay": True,
                "webhook_event": event_type,
                "payment_id": raw_id,
                "customer_id": existing_pay.customer_id,
                "customer_name": existing_pay.customer.name if existing_pay.customer else "Customer",
                "amount_inr": existing_pay.amount,
                "failure_reason": existing_pay.failure_reason,
                "selected_action": contract_res.selected_action,
                "predicted_recovery_probability": contract_res.predicted_recovery_probability,
                "expected_net_value": contract_res.expected_net_value,
                "decision_status": contract_res.decision_status,
                "approval_required": contract_res.approval_required,
                "dispatch_channel": "Razorpay Hosted Method Update Portal" if contract_res.selected_action == "Payment Method Update" else "Automated Recovery Orchestrator",
                "razorpay_payment_link": f"https://rzp.io/i/rec_{raw_id[-8:]}" if contract_res.selected_action == "Payment Method Update" else None,
                "execution_latency_ms": t_latency,
                "explanation": contract_res.explanation.summary if contract_res.explanation else "Existing decision returned via idempotent deduplication.",
                "timestamp": datetime.utcnow().isoformat()
            }

    amount_inr = float(payment_entity.get("amount", 10000)) / 100.0  # Convert paise to INR
    currency = payment_entity.get("currency", "INR")
    method_raw = payment_entity.get("method", "card")
    method_map = {"card": "CreditCard", "netbanking": "NetBanking", "upi": "UPI", "wallet": "Wallet"}
    payment_method = method_map.get(method_raw.lower(), "CreditCard")

    error_code = payment_entity.get("error_code", "PAYMENT_FAILED")
    error_desc = payment_entity.get("error_description", "Payment transaction failed")
    error_reason_raw = payment_entity.get("error_reason", "unknown")
    failure_reason = _map_razorpay_error_to_domain(error_reason_raw, error_desc)

    cust_email = payment_entity.get("email", "customer@example.com")
    cust_phone = payment_entity.get("contact", "+919876543210")
    cust_name = payment_entity.get("card", {}).get("name") or "Razorpay Merchant Customer"

    notes = payment_entity.get("notes", {})
    is_dnc = str(notes.get("dnc_status", "false")).lower() in ["true", "1", "yes"]

    # 1. Ingest or locate Customer in DB
    cust_id = f"CUST-RZP-{abs(hash(cust_email)) % 1000000:06d}"
    cust = db.query(CustomerDB).filter(CustomerDB.customer_id == cust_id).first()
    if not cust:
        cust = CustomerDB(
            customer_id=cust_id,
            name=cust_name,
            email=cust_email,
            segment="Enterprise" if amount_inr >= 50000 else "MidMarket",
            do_not_contact=is_dnc,
            created_at=datetime.utcnow()
        )
        db.add(cust)
        db.commit()

    # 2. Check or create Customer Fatigue
    fatigue = db.query(CustomerFatigueDB).filter(CustomerFatigueDB.customer_id == cust_id).first()
    if not fatigue:
        fatigue = CustomerFatigueDB(
            customer_id=cust_id,
            contacts_24h=0,
            contacts_7d=0,
            consecutive_failures=1
        )
        db.add(fatigue)
        db.commit()
    else:
        fatigue.consecutive_failures += 1
        db.commit()

    # 3. Create or update Payment Record
    pay = db.query(PaymentDB).filter(PaymentDB.payment_id == raw_id).first()
    if not pay:
        pay = PaymentDB(
            payment_id=raw_id,
            customer_id=cust_id,
            amount=amount_inr,
            currency=currency,
            payment_method=payment_method,
            failure_reason=failure_reason,
            failure_code=error_code,
            status="FAILED",
            created_at=datetime.utcnow()
        )
        db.add(pay)
        db.commit()

    # 4. Construct Pre-Decision Features
    features = PreDecisionFeatures(
        payment_id=raw_id,
        customer_id=cust_id,
        amount=amount_inr,
        payment_method=payment_method,
        failure_reason=failure_reason,
        failure_code=error_code,
        customer_segment=cust.segment or "MidMarket",
        historical_recovery_rate=0.45,
        engagement_score=0.75 if cust.segment == "Enterprise" else 0.60,
        contacts_24h=fatigue.contacts_24h,
        contacts_7d=fatigue.contacts_7d,
        consecutive_failures=fatigue.consecutive_failures,
        do_not_contact=cust.do_not_contact
    )


    # 5. Execute Autonomous Calibrated ENV Optimizer
    contract = global_optimizer.optimize_and_decide(features)
    contract.payment_id = raw_id
    contract.decision_id = f"dec_{raw_id}"

    # Commit Decision Contract
    db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == raw_id).delete()
    db_dec = _contract_to_db(contract)
    db.add(db_dec)
    db.commit()

    # 6. Generate Razorpay-Native Dispatch URL & Action Payload
    razorpay_link = f"https://rzp.io/i/rec_{raw_id[-8:]}" if "Method Update" in contract.selected_action or "WhatsApp" in contract.selected_action else None
    dispatch_channel_map = {
        "Smart WhatsApp Nudge": "Razorpay WhatsApp Flow Connector",
        "Payment Method Update": "Razorpay Hosted Payment Link (WhatsApp + SMS)",
        "Delayed Smart Retry": "Razorpay Smart Routing Queue (T+18h)",
        "Retry Immediately": "Razorpay Direct Gateway Retry",
        "Incentivized Recovery Offer": "Razorpay Dynamic Promo Link (2% Cashback)",
        "Human Escalation": "Razorpay Merchant Ops Escalation Desk",
        "Stop Intervention": "Autonomous Block (Zero Spend)"
    }
    dispatch_channel = dispatch_channel_map.get(contract.selected_action, "Razorpay Recovery Engine")

    t_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

    # 7. Record Immutable Agent Audit Event with Masked PII
    from app.core.security import mask_name
    masked_cust_name = mask_name(cust.name)

    audit_evt = AgentEventDB(
        event_id=f"evt_webhook_{uuid.uuid4().hex[:8]}",
        payment_id=raw_id,
        stage="ACT",
        status="EXECUTED" if contract.decision_status == "AUTO_EXECUTE" else "PENDING_APPROVAL",
        message=f"Ingested {event_type} for customer {masked_cust_name} -> Dispatched {contract.selected_action} ({dispatch_channel}) in {t_latency_ms}ms",
        metadata_json={
            "webhook_event": event_type,
            "decision_id": contract.decision_id,
            "raw_payment_id": raw_id,
            "amount_inr": amount_inr,
            "failure_reason": failure_reason,
            "selected_action": contract.selected_action,
            "predicted_probability": contract.predicted_recovery_probability,
            "expected_net_value": contract.expected_net_value,
            "decision_status": contract.decision_status,
            "latency_ms": t_latency_ms,
            "razorpay_link": razorpay_link
        },
        timestamp=datetime.utcnow()
    )
    db.add(audit_evt)
    db.commit()

    return {
        "status": "success",
        "webhook_event": event_type,
        "payment_id": raw_id,
        "customer_id": cust_id,
        "customer_name": masked_cust_name,
        "amount_inr": amount_inr,
        "failure_reason": failure_reason,
        "selected_action": contract.selected_action,
        "predicted_recovery_probability": contract.predicted_recovery_probability,
        "expected_net_value": contract.expected_net_value,
        "decision_status": contract.decision_status,
        "approval_required": contract.approval_required,
        "dispatch_channel": dispatch_channel,
        "razorpay_payment_link": razorpay_link,
        "execution_latency_ms": t_latency_ms,
        "explanation": contract.explanation.summary if contract.explanation else "Optimized via Expected Net Value policy under deterministic guardrails.",
        "timestamp": datetime.utcnow().isoformat()
    }
