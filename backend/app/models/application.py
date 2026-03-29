import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.session import Base


class ApplicantType(str, enum.Enum):
    company = 'company'
    individual = 'individual'


class Application(Base):
    __tablename__ = 'wnioski'
    __table_args__ = {'schema': settings.db_schema}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    applicant_type: Mapped[ApplicantType] = mapped_column(Enum(ApplicantType), nullable=False)

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    nip: Mapped[str] = mapped_column(String(20), nullable=False)
    krs: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pesel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    business_line: Mapped[str] = mapped_column(String(10), nullable=False)
    car_model: Mapped[str] = mapped_column(String(255), nullable=False)

    rent_amount: Mapped[float] = mapped_column(Float, nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_value: Mapped[float] = mapped_column(Float, nullable=False)
    initial_fee: Mapped[float] = mapped_column(Float, nullable=False)

    car_group: Mapped[str] = mapped_column(String(100), nullable=False)
    car_segment: Mapped[str] = mapped_column(String(20), nullable=False)
    rental_period_months: Mapped[int] = mapped_column(Integer, nullable=False)

    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    sharepoint_folder: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
