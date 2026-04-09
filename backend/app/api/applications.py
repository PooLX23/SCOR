import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.application import (
    ApplicantType,
    Application,
    ApplicationStatus,
    ApplicationVehicleItem,
)
from app.schemas.application import CompanyFormCreate, IndividualFormCreate
from app.services.auth import bearer_scheme, validate_entra_token
from app.services.car_groups import CarGroupsService
from app.services.sharepoint import SharePointService

router = APIRouter(prefix='/applications', tags=['applications'])


def _parse_form_payload(model_cls: type[CompanyFormCreate | IndividualFormCreate], payload: str):
    try:
        return model_cls(**json.loads(payload))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f'Niepoprawny JSON payload: {exc.msg}') from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _build_vehicle_items(application_id: int, vehicles: list) -> list[ApplicationVehicleItem]:
    return [
        ApplicationVehicleItem(
            application_id=application_id,
            business_line=item.business_line,
            car_make=item.car_make,
            car_model=item.car_model,
            rent_amount=item.rent_amount,
            deposit_amount=item.deposit_amount,
            vehicle_value=item.vehicle_value,
            initial_fee=item.initial_fee,
            car_group=item.car_group,
            car_class=item.car_class,
            rental_period_months=item.rental_period_months,
        )
        for item in vehicles
    ]


def _calculate_totals(vehicles: list) -> dict[str, float | int]:
    return {
        'total_rent_amount': sum(v.rent_amount for v in vehicles),
        'total_deposit_amount': sum(v.deposit_amount for v in vehicles),
        'total_vehicle_value': sum(v.vehicle_value for v in vehicles),
        'total_initial_fee': sum(v.initial_fee for v in vehicles),
        'total_vehicle_count': len(vehicles),
    }


def _is_reviewer(payload: dict) -> bool:
    if not settings.reception_group_id:
        return False
    return settings.reception_group_id in payload.get('groups', [])


def _user_id(payload: dict) -> str:
    return payload.get('preferred_username') or payload.get('upn') or payload.get('sub', 'unknown')


def _serialize_application(app: Application) -> dict:
    return {
        'id': app.id,
        'status': app.status.value,
        'applicant_type': app.applicant_type.value,
        'company_name': app.company_name,
        'customer_name': app.customer_name,
        'submitted_by': app.submitted_by,
        'created_at': app.created_at.isoformat(),
        'total_rent_amount': app.total_rent_amount,
        'total_deposit_amount': app.total_deposit_amount,
        'total_vehicle_value': app.total_vehicle_value,
        'total_initial_fee': app.total_initial_fee,
        'total_vehicle_count': app.total_vehicle_count,
    }


@router.post('/company')
async def create_company_application(
    payload: str = Form(..., description='JSON CompanyFormCreate'),
    files: list[UploadFile] = File(...),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user_payload = validate_entra_token(credentials)
    data = _parse_form_payload(CompanyFormCreate, payload)
    totals = _calculate_totals(data.vehicles)

    application = Application(
        applicant_type=ApplicantType.company,
        status=ApplicationStatus.new,
        company_name=data.company_name,
        nip=data.nip,
        krs=data.krs,
        submitted_by=_user_id(user_payload),
        **totals,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    db.add_all(_build_vehicle_items(application.id, data.vehicles))
    folder = await SharePointService().upload_files(application.id, files)
    application.sharepoint_folder = folder
    db.commit()

    return {'id': application.id, 'sharepoint_folder': folder, 'status': application.status.value, **totals}


@router.post('/individual')
async def create_individual_application(
    payload: str = Form(..., description='JSON IndividualFormCreate'),
    files: list[UploadFile] = File(...),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user_payload = validate_entra_token(credentials)
    data = _parse_form_payload(IndividualFormCreate, payload)
    totals = _calculate_totals(data.vehicles)

    application = Application(
        applicant_type=ApplicantType.individual,
        status=ApplicationStatus.new,
        customer_name=data.customer_name,
        pesel=data.pesel,
        nip=data.nip,
        document_number=data.document_number,
        submitted_by=_user_id(user_payload),
        **totals,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    db.add_all(_build_vehicle_items(application.id, data.vehicles))
    folder = await SharePointService().upload_files(application.id, files)
    application.sharepoint_folder = folder
    db.commit()

    return {'id': application.id, 'sharepoint_folder': folder, 'status': application.status.value, **totals}


@router.get('/me')
def me(credentials=Depends(bearer_scheme)):
    payload = validate_entra_token(credentials)
    return {'user': _user_id(payload), 'is_reviewer': _is_reviewer(payload)}


@router.get('/my')
def my_applications(credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    user = _user_id(payload)
    records = db.query(Application).filter(Application.submitted_by == user).order_by(desc(Application.created_at)).all()
    return {'items': [_serialize_application(r) for r in records]}


@router.get('/all')
def all_applications(credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    if not _is_reviewer(payload):
        raise HTTPException(status_code=403, detail='Brak uprawnień do listy wszystkich wniosków')

    records = db.query(Application).order_by(desc(Application.created_at)).all()
    return {'items': [_serialize_application(r) for r in records]}


@router.get('/car-groups')
def list_car_groups(credentials=Depends(bearer_scheme)):
    validate_entra_token(credentials)
    groups = CarGroupsService().list_groups()
    return {'items': groups}


@router.get('/{application_id}')
def application_details(application_id: int, credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    user = _user_id(payload)
    reviewer = _is_reviewer(payload)

    record = db.query(Application).filter(Application.id == application_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='Wniosek nie istnieje')

    if not reviewer and record.submitted_by != user:
        raise HTTPException(status_code=403, detail='Brak dostępu do szczegółów tego wniosku')

    vehicle_rows = db.query(ApplicationVehicleItem).filter(ApplicationVehicleItem.application_id == record.id).all()

    details = _serialize_application(record)
    details['vehicles'] = [
        {
            'id': item.id,
            'business_line': item.business_line,
            'car_make': item.car_make,
            'car_model': item.car_model,
            'rent_amount': item.rent_amount,
            'deposit_amount': item.deposit_amount,
            'vehicle_value': item.vehicle_value,
            'initial_fee': item.initial_fee,
            'car_group': item.car_group,
            'car_class': item.car_class,
            'rental_period_months': item.rental_period_months,
        }
        for item in vehicle_rows
    ]
    return details


@router.get('/health-auth')
def auth_health(credentials=Depends(bearer_scheme)):
    payload = validate_entra_token(credentials)
    return {'ok': True, 'user': _user_id(payload), 'is_reviewer': _is_reviewer(payload)}
