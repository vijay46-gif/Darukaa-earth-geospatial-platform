from typing import Optional

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


def log_activity(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    details: Optional[str] = None,
):
    try:
        activity = ActivityLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            details=details,
        )
        db.add(activity)
        db.commit()
    except Exception:
        db.rollback()
        # Logging failure should not crash main transaction
        pass
