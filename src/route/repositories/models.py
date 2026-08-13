from sqlalchemy.orm import relationship, Mapped, mapped_column,  DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey,func,UniqueConstraint
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class Base(DeclarativeBase):
    pass

class ServiceType(str, Enum):
    VKONTAKTE = "vkontakte"
    ODNOKLASSNIKI = "odnoklassniki"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    VIBER = "viber"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    SIGNAL = "signal"
    DISCORD = "discord"
    SKYPE = "skype"


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    country_code: Mapped[str] = mapped_column(String(5))
    is_valid: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    registrations: Mapped[List["ServiceRegistration"]] = relationship(
        "ServiceRegistration",
        back_populates="phone_number",
        cascade="all, delete-orphan"
    )

class ServiceRegistration(Base):
    __tablename__ = "service_registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_number_id: Mapped[int] = mapped_column(ForeignKey("phone_numbers.id"))
    service: Mapped[str] = mapped_column(String(50))  # Имя сервиса
    is_registered: Mapped[bool] = mapped_column(default=False)
    check_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Дополнительная информация
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    profile_url: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))

    phone_number: Mapped["PhoneNumber"] = relationship(back_populates="registrations")

    __table_args__ = (
        UniqueConstraint('phone_number_id', 'service', name='uq_phone_service'),
    )


    user: Mapped[Optional["User"]] = relationship("User", back_populates="phone_numbers")

class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="emails")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    phone_numbers: Mapped[List[PhoneNumber]] = relationship("PhoneNumber", back_populates="user")
    emails: Mapped[List[Email]] = relationship("Email", back_populates="user")
