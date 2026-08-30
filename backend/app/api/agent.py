from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.db_models import AgentEventDB
from app.schemas.pydantic_schemas import AgentEventResponse

router = APIRouter(prefix="/agent", tags=["Agent Trace"])

@router.get("/activity", response_model=List[AgentEventResponse])
def get_agent_activity_feed(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    events = db.query(AgentEventDB).order_by(AgentEventDB.timestamp.desc()).limit(limit).all()
    res = []
    for e in events:
        res.append(AgentEventResponse(
            event_id=e.event_id,
            payment_id=e.payment_id,
            timestamp=e.timestamp,
            stage=e.stage,
            status=e.status,
            message=e.message,
            metadata_json=e.metadata_json or {}
        ))
    return res
