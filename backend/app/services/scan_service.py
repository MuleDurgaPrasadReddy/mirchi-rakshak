from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.schemas.scan import ScanCreate


class ScanService:
    def create_scan(self, db: Session, user_id: str, scan_data: ScanCreate) -> Scan:
        """
        Placeholder method to store scan metadata record in PostgreSQL.
        """
        db_scan = Scan(
            user_id=user_id,
            **scan_data.model_dump(exclude_unset=True)
        )
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)
        return db_scan

    def list_user_scans(self, db: Session, user_id: str, limit: int = 50) -> List[Scan]:
        """
        Placeholder method to retrieve scan records for a user.
        """
        return db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.created_at.desc()).limit(limit).all()


scan_service = ScanService()
