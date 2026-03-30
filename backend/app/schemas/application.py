from pydantic import BaseModel, Field, field_validator


ALLOWED_BUSINESS_LINES = {'ST', 'LT', 'AA', 'CFM', 'LOP'}
ALLOWED_SEGMENTS = {'premium', 'standard'}


class BaseForm(BaseModel):
    nip: str = Field(min_length=10, max_length=20)
    business_line: str
    car_model: str = Field(min_length=1)
    rent_amount: float = Field(gt=0)
    deposit_amount: float = Field(ge=0)
    vehicle_value: float = Field(gt=0)
    initial_fee: float = Field(ge=0)
    car_group: str = Field(min_length=1)
    car_segment: str
    rental_period_months: int = Field(gt=0)

    @field_validator('business_line')
    @classmethod
    def validate_business_line(cls, value: str) -> str:
        upper = value.upper()
        if upper not in ALLOWED_BUSINESS_LINES:
            raise ValueError('Nieprawidłowa linia biznesowa')
        return upper

    @field_validator('car_segment')
    @classmethod
    def validate_segment(cls, value: str) -> str:
        lower = value.lower()
        if lower not in ALLOWED_SEGMENTS:
            raise ValueError('Nieprawidłowy segment samochodu')
        return lower


class CompanyFormCreate(BaseForm):
    company_name: str = Field(min_length=1)
    krs: str = Field(min_length=5, max_length=20)


class IndividualFormCreate(BaseForm):
    customer_name: str = Field(min_length=1)
    pesel: str = Field(min_length=11, max_length=11)
    document_number: str = Field(min_length=3, max_length=50)


class ApplicationOut(BaseModel):
    id: int
    applicant_type: str

    class Config:
        from_attributes = True
