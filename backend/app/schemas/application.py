from pydantic import BaseModel, Field, field_validator


ALLOWED_BUSINESS_LINES = {'ST', 'LT', 'AA', 'CFM', 'LOP'}
ALLOWED_CLASSES = {'premium', 'standard'}


class VehicleItemCreate(BaseModel):
    business_line: str
    car_make: str = Field(min_length=1)
    car_model: str = Field(min_length=1)
    rent_amount: float = Field(ge=0)
    deposit_amount: float = Field(ge=0)
    vehicle_value: float = Field(ge=0)
    initial_fee: float = Field(ge=0)
    car_group: str = Field(min_length=1)
    car_class: str
    rental_period_months: int = Field(gt=0)

    @field_validator('business_line')
    @classmethod
    def validate_business_line(cls, value: str) -> str:
        upper = value.upper()
        if upper not in ALLOWED_BUSINESS_LINES:
            raise ValueError('Nieprawidłowa linia biznesowa')
        return upper

    @field_validator('car_class')
    @classmethod
    def validate_class(cls, value: str) -> str:
        lower = value.lower()
        if lower not in ALLOWED_CLASSES:
            raise ValueError('Nieprawidłowa klasa samochodu')
        return lower


class CompanyFormCreate(BaseModel):
    company_name: str = Field(min_length=1)
    nip: str = Field(min_length=10, max_length=20)
    krs: str = Field(min_length=5, max_length=20)
    vehicles: list[VehicleItemCreate] = Field(min_length=1)


class IndividualFormCreate(BaseModel):
    customer_name: str = Field(min_length=1)
    pesel: str = Field(min_length=11, max_length=11)
    nip: str = Field(min_length=10, max_length=20)
    document_number: str = Field(min_length=3, max_length=50)
    vehicles: list[VehicleItemCreate] = Field(min_length=1)
