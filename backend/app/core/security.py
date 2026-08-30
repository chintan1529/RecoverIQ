import re
from typing import Optional
from fastapi import Header, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings

# API Key Header schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_operator_keys() -> set:
    keys = {k.strip() for k in settings.OPERATOR_API_KEYS.split(",") if k.strip()}
    return keys

def get_admin_keys() -> set:
    keys = {k.strip() for k in settings.ADMIN_API_KEYS.split(",") if k.strip()}
    return keys

def require_operator_auth(x_api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Enforces Operator or Admin level authentication for financial execution and approvals.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide valid 'X-API-Key' header."
        )
    op_keys = get_operator_keys()
    adm_keys = get_admin_keys()
    if x_api_key not in op_keys and x_api_key not in adm_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Valid operator API key required."
        )
    return x_api_key

def require_admin_auth(x_api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Enforces Admin level authentication for destructive lifecycle actions (e.g. database reseed).
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Provide valid 'X-API-Key' header."
        )
    adm_keys = get_admin_keys()
    if x_api_key not in adm_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required. Admin API key required."
        )
    return x_api_key


# PII Masking Utilities (DPDP Act & GDPR compliance)

def mask_email(email: Optional[str]) -> str:
    if not email or "@" not in email:
        return "u***@domain.com"
    parts = email.split("@")
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"

def mask_phone(phone: Optional[str]) -> str:
    if not phone:
        return "+91 98*** ***10"
    clean = re.sub(r"[^\d+]", "", str(phone))
    if len(clean) >= 10:
        return clean[:5] + "*** ***" + clean[-2:]
    return clean[:2] + "****"

def mask_name(name: Optional[str]) -> str:
    if not name:
        return "C**** M*****"
    tokens = name.split()
    masked_tokens = []
    for t in tokens:
        if len(t) <= 2:
            masked_tokens.append(t[0] + "*")
        else:
            masked_tokens.append(t[0] + "*" * (len(t) - 1))
    return " ".join(masked_tokens)
