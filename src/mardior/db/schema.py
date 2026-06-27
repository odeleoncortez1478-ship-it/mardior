from __future__ import annotations

from sqlalchemy import (
    Column, Integer, Text, Float, Boolean, DateTime,
    ForeignKey, create_engine, Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    shopify_id = Column(Text, primary_key=True)
    order_number = Column(Integer, nullable=False)
    customer_email = Column(Text)
    customer_name = Column(Text)
    total_price = Column(Float)
    currency = Column(Text, default="USD")
    financial_status = Column(Text)
    fulfillment_status = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    raw_json = Column(Text)
    last_synced_at = Column(DateTime, server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    fulfillments = relationship("Fulfillment", back_populates="order", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="linked_order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Text, ForeignKey("orders.shopify_id"))
    product_title = Column(Text)
    variant_title = Column(Text)
    quantity = Column(Integer)
    price = Column(Float)
    sku = Column(Text)

    order = relationship("Order", back_populates="items")


class Fulfillment(Base):
    __tablename__ = "fulfillments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Text, ForeignKey("orders.shopify_id"))
    tracking_number = Column(Text)
    carrier = Column(Text)
    status = Column(Text, default="unknown")
    last_checked_at = Column(DateTime)
    raw_json = Column(Text)

    order = relationship("Order", back_populates="fulfillments")
    tracking_history = relationship("TrackingHistory", back_populates="fulfillment", cascade="all, delete-orphan")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gmail_message_id = Column(Text, unique=True, nullable=False)
    thread_id = Column(Text)
    from_name = Column(Text)
    from_address = Column(Text, nullable=False)
    to_address = Column(Text)
    subject = Column(Text)
    body_text = Column(Text)
    received_at = Column(DateTime)

    classification = Column(Text)
    confidence = Column(Float)

    linked_order_id = Column(Text, ForeignKey("orders.shopify_id"), nullable=True)
    linking_method = Column(Text)

    tracking_fetched = Column(Boolean, default=False)
    tracking_status = Column(Text)

    response_sent = Column(Boolean, default=False)
    response_body = Column(Text)
    response_status = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)

    linked_order = relationship("Order", back_populates="emails")
    classification_logs = relationship("ClassificationLog", back_populates="email", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="email", cascade="all, delete-orphan")


class ClassificationLog(Base):
    __tablename__ = "classification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    model_used = Column(Text)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost = Column(Float)
    raw_prompt = Column(Text)
    raw_response = Column(Text)

    email = relationship("Email", back_populates="classification_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    channel = Column(Text)
    message = Column(Text)
    sent_at = Column(DateTime)
    success = Column(Boolean, default=False)

    email = relationship("Email", back_populates="notifications")


class TrackingHistory(Base):
    __tablename__ = "tracking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fulfillment_id = Column(Integer, ForeignKey("fulfillments.id"))
    carrier = Column(Text)
    tracking_number = Column(Text)
    status = Column(Text)
    location = Column(Text)
    timestamp = Column(DateTime)
    raw_response = Column(Text)
    checked_at = Column(DateTime, server_default=func.now())

    fulfillment = relationship("Fulfillment", back_populates="tracking_history")


class SyncLog(Base):
    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    orders_processed = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text)


class ShippingProfile(Base):
    __tablename__ = "shipping_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shopify_profile_id = Column(Text, unique=True)
    name = Column(Text)
    raw_json = Column(Text)
    last_synced_at = Column(DateTime, server_default=func.now())

    rates = relationship("ShippingRate", back_populates="profile", cascade="all, delete-orphan")


class ShippingRate(Base):
    __tablename__ = "shipping_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("shipping_profiles.id"))
    zone = Column(Text)
    carrier = Column(Text)
    method_name = Column(Text)
    shopify_price = Column(Float)
    real_price = Column(Float, nullable=True)
    currency = Column(Text, default="USD")
    conditions = Column(Text)

    profile = relationship("ShippingProfile", back_populates="rates")


Index("idx_orders_email", Order.customer_email)
Index("idx_emails_from", Email.from_address)
Index("idx_emails_class", Email.classification)
Index("idx_fulfillments_tn", Fulfillment.tracking_number)
Index("idx_tracking_history_fn", TrackingHistory.fulfillment_id)
