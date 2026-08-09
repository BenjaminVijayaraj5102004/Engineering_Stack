from uuid import UUID

from sqlalchemy.orm import Session

from ..memory.session_memory import SessionMemory


class SessionRepository:
    """Repository for storing and retrieving agent session memory."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        session_id: UUID,
        thread_id: str,
        user_message: str,
        ai_message: str,
    ) -> SessionMemory:
        memory = SessionMemory(
            session_id=session_id,
            thread_id=thread_id,
            user_message=user_message,
            ai_message=ai_message,
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return memory

    def get_by_session(
        self,
        session_id: UUID,
    ) -> list[SessionMemory]:
        return (
            self.db.query(SessionMemory)
            .filter(SessionMemory.session_id == session_id)
            .order_by(SessionMemory.created_at.asc())
            .all()
        )

    def get_by_thread(
        self,
        thread_id: str,
    ) -> list[SessionMemory]:
        return (
            self.db.query(SessionMemory)
            .filter(SessionMemory.thread_id == thread_id)
            .order_by(SessionMemory.created_at.asc())
            .all()
        )

    def get_latest(
        self,
        session_id: UUID,
    ) -> SessionMemory | None:
        return (
            self.db.query(SessionMemory)
            .filter(SessionMemory.session_id == session_id)
            .order_by(SessionMemory.created_at.desc())
            .first()
        )

    def delete_session(
        self,
        session_id: UUID,
    ) -> int:
        deleted = (
            self.db.query(SessionMemory)
            .filter(SessionMemory.session_id == session_id)
            .delete()
        )

        self.db.commit()

        return deleted