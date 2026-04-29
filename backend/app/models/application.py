import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.session import Base


class ApplicantType(str, enum.Enum):
    company = 'company'
    individual = 'individual'


class ApplicationStatus(str, enum.Enum):
    new = 'nowy'
    processing = 'procesowany'
    negative = 'negatywny'
    positive = 'pozytywny'
    manual_verification = 'weryfikacja manualna'
    after_collection = 'po windykacji'


class CollectionDecision(str, enum.Enum):
    positive = 'pozytywna'
    negative = 'negatywna'


class Application(Base):
    __tablename__ = 'wnioski'
    __table_args__ = {'schema': settings.db_schema}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    applicant_type: Mapped[ApplicantType] = mapped_column(Enum(ApplicantType), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            name='application_status',
        ),
        nullable=False,
        default=ApplicationStatus.new,
    )

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nip: Mapped[str] = mapped_column(String(20), nullable=False)
    krs: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pesel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    total_rent_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_deposit_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_vehicle_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_initial_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    sharepoint_folder: Mapped[str | None] = mapped_column(Text, nullable=True)
    collection_decision: Mapped[CollectionDecision | None] = mapped_column(
        Enum(
            CollectionDecision,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            name='collection_decision',
        ),
        nullable=True,
    )
    collection_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    vehicle_items: Mapped[list['ApplicationVehicleItem']] = relationship(
        back_populates='application', cascade='all, delete-orphan'
    )
    collection_snapshots: Mapped[list['ApplicationCollectionSnapshot']] = relationship(
        back_populates='application', cascade='all, delete-orphan'
    )


class ApplicationVehicleItem(Base):
    __tablename__ = 'wnioski_pozycje'
    __table_args__ = {'schema': settings.db_schema}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey(f'{settings.db_schema}.wnioski.id', ondelete='CASCADE'), nullable=False, index=True
    )

    business_line: Mapped[str] = mapped_column(String(10), nullable=False)
    car_make: Mapped[str] = mapped_column(String(100), nullable=False)
    car_model: Mapped[str] = mapped_column(String(100), nullable=False)
    rent_amount: Mapped[float] = mapped_column(Float, nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Float, nullable=False)
    vehicle_value: Mapped[float] = mapped_column(Float, nullable=False)
    initial_fee: Mapped[float] = mapped_column(Float, nullable=False)
    car_group: Mapped[str] = mapped_column(String(100), nullable=False)
    car_class: Mapped[str] = mapped_column(String(50), nullable=False)
    rental_period_months: Mapped[int] = mapped_column(Integer, nullable=False)

    application: Mapped[Application] = relationship(back_populates='vehicle_items')


class ApplicationCollectionSnapshot(Base):
    __tablename__ = 'wnioski_windykacja_snapshot'
    __table_args__ = {'schema': settings.db_schema}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey(f'{settings.db_schema}.wnioski.id', ondelete='CASCADE'), nullable=False, index=True
    )
    avg_days_past_due: Mapped[float | None] = mapped_column(Float, nullable=True)
    deposits_aa_cfm_rac: Mapped[float | None] = mapped_column(Float, nullable=True)
    deposits_orders: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    application: Mapped[Application] = relationship(back_populates='collection_snapshots')
