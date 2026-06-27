from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker, joinedload

from mardior.config.settings import settings
from mardior.db.schema import Base, Order, OrderItem, Fulfillment, Email, ClassificationLog
from mardior.db.schema import Notification, TrackingHistory, SyncLog, ShippingRate, AuditLog


class Storage:
    def __init__(self):
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{settings.db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.Session()

    # ─── Orders ───

    def upsert_order(self, order_data: dict) -> Order:
        with self.get_session() as session:
            existing = session.query(Order).filter(
                Order.readycloud_id == order_data["readycloud_id"]
            ).first()
            if existing:
                for k, v in order_data.items():
                    setattr(existing, k, v)
                existing.last_synced_at = datetime.utcnow()
                obj = existing
            else:
                order_data["last_synced_at"] = datetime.utcnow()
                obj = Order(**order_data)
                session.add(obj)
            session.commit()
            return obj

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        with self.get_session() as session:
            return session.get(Order, order_id)

    def get_order_by_readycloud_id(self, rc_id: str) -> Optional[Order]:
        with self.get_session() as session:
            return session.query(Order).filter(Order.readycloud_id == rc_id).first()

    def get_order_by_email(self, email: str) -> Optional[Order]:
        with self.get_session() as session:
            return session.query(Order).options(
                joinedload(Order.items), joinedload(Order.fulfillments)
            ).filter(Order.customer_email == email).first()

    def get_order_by_number(self, number: int) -> Optional[Order]:
        with self.get_session() as session:
            return session.query(Order).options(
                joinedload(Order.items), joinedload(Order.fulfillments)
            ).filter(Order.order_number == number).first()

    def get_all_orders(self, limit: int = 100, offset: int = 0, status: str = None):
        with self.get_session() as session:
            q = session.query(Order).options(
                joinedload(Order.items), joinedload(Order.fulfillments)
            )
            if status:
                q = q.filter(Order.fulfillment_status == status)
            return q.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()

    def count_orders(self, status: str = None) -> int:
        with self.get_session() as session:
            q = session.query(func.count(Order.id))
            if status:
                q = q.filter(Order.fulfillment_status == status)
            return q.scalar()

    # ─── Emails ───

    def insert_email(self, email_data: dict) -> Email:
        with self.get_session() as session:
            email_data["created_at"] = datetime.utcnow()
            obj = Email(**email_data)
            session.add(obj)
            session.commit()
            return obj

    def update_email(self, email_id: int, updates: dict):
        with self.get_session() as session:
            session.query(Email).filter(Email.id == email_id).update(updates)
            session.commit()

    def get_email_by_gmail_id(self, gmail_id: str) -> Optional[Email]:
        with self.get_session() as session:
            return session.query(Email).filter(Email.gmail_message_id == gmail_id).first()

    def get_emails(self, limit: int = 50, offset: int = 0, classification: str = None, filter: str = None):
        with self.get_session() as session:
            q = session.query(Email)
            if classification:
                q = q.filter(Email.classification == classification)
            if filter == "attention":
                q = q.filter(Email.needs_attention == True)
            elif filter == "responded":
                q = q.filter(Email.response_sent == True)
            elif filter == "pending":
                q = q.filter(Email.response_sent == False, Email.needs_attention == False)
            elif filter == "ads":
                q = q.filter(Email.classification == "ads")
            return q.order_by(Email.received_at.desc()).limit(limit).offset(offset).all()

    def get_unprocessed_emails(self):
        with self.get_session() as session:
            return session.query(Email).filter(Email.processed_at.is_(None)).all()

    def count_emails(self, classification: str = None) -> int:
        with self.get_session() as session:
            q = session.query(func.count(Email.id))
            if classification in ("tracking", "complaint", "refund", "distributor", "partnership", "influencer", "ads", "other"):
                q = q.filter(Email.classification == classification)
            elif classification == "attention":
                q = q.filter(Email.needs_attention == True)
            elif classification == "responded":
                q = q.filter(Email.response_sent == True)
            elif classification == "pending":
                q = q.filter(Email.response_sent == False, Email.needs_attention == False)
            return q.scalar()

    def count_emails_by_filter(self, filter: str = None) -> int:
        with self.get_session() as session:
            q = session.query(func.count(Email.id))
            if filter == "attention":
                q = q.filter(Email.needs_attention == True)
            elif filter == "responded":
                q = q.filter(Email.response_sent == True)
            elif filter == "pending":
                q = q.filter(Email.response_sent == False, Email.needs_attention == False)
            elif filter == "ads":
                q = q.filter(Email.classification == "ads")
            elif filter == "influencer":
                q = q.filter(Email.classification == "influencer")
            return q.scalar()

    def get_email_counts(self) -> dict:
        return {
            "attention": self.count_emails_by_filter("attention"),
            "responded": self.count_emails_by_filter("responded"),
            "pending": self.count_emails_by_filter("pending"),
            "influencers": self.count_emails_by_filter("influencer"),
            "ads": self.count_emails_by_filter("ads"),
            "total": self.count_emails(),
        }

    def count_emails_today(self) -> int:
        with self.get_session() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            return session.query(func.count(Email.id)).filter(Email.received_at >= today).scalar()

    # ─── Tracking number lookup ───

    def find_fulfillment_by_tracking(self, tracking_number: str) -> Optional[Fulfillment]:
        with self.get_session() as session:
            return session.query(Fulfillment).filter(
                Fulfillment.tracking_number == tracking_number
            ).first()

    # ─── Stats ───

    def get_dashboard_stats(self) -> dict:
        with self.get_session() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            emails_today = session.query(func.count(Email.id)).filter(
                Email.received_at >= today
            ).scalar()
            pending = session.query(func.count(Email.id)).filter(
                Email.processed_at.is_(None)
            ).scalar()
            total_orders = session.query(func.count(Order.id)).scalar()
            unfulfilled = session.query(func.count(Order.id)).filter(
                Order.fulfillment_status == "unfulfilled"
            ).scalar()
            total_cost = session.query(func.sum(ClassificationLog.cost)).scalar() or 0
            counts = self.get_email_counts()
            return {
                "emails_today": emails_today,
                "pending": counts["pending"],
                "attention": counts["attention"],
                "total_orders": total_orders,
                "unfulfilled_orders": unfulfilled,
                "llm_cost": round(total_cost, 4),
                "tracking": session.query(func.count(Email.id)).filter(
                    Email.classification == "tracking"
                ).scalar(),
                "influencers": counts["influencers"],
                "ads": counts["ads"],
            }

    # ─── Sync log ───

    def log_sync(self, sync_type: str, orders_processed: int, success: bool, error: str = None):
        with self.get_session() as session:
            session.add(SyncLog(
                sync_type=sync_type,
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                orders_processed=orders_processed,
                success=success,
                error_message=error
            ))
            session.commit()

    # ─── Audit log ───

    def log_audit(self, action: str, ip_address: str = "", details: str = ""):
        with self.get_session() as session:
            session.add(AuditLog(
                action=action,
                ip_address=ip_address,
                details=details,
            ))
            session.commit()
