import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.application import ApplicantType, Application, ApplicationVehicleItem
from app.schemas.application import CompanyFormCreate, IndividualFormCreate
from app.services.auth import bearer_scheme, validate_entra_token
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


@router.post('/company')
async def create_company_application(
    payload: str = Form(..., description='JSON CompanyFormCreate'),
    files: list[UploadFile] = File(...),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user = validate_entra_token(credentials)
    data = _parse_form_payload(CompanyFormCreate, payload)
    totals = _calculate_totals(data.vehicles)

    application = Application(
        applicant_type=ApplicantType.company,
        company_name=data.company_name,
        nip=data.nip,
        krs=data.krs,
        submitted_by=user.get('preferred_username', user.get('sub', 'unknown')),
        **totals,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    db.add_all(_build_vehicle_items(application.id, data.vehicles))
    folder = await SharePointService().upload_files(application.id, files)
    application.sharepoint_folder = folder
    db.commit()

    return {'id': application.id, 'sharepoint_folder': folder, **totals}


@router.post('/individual')
async def create_individual_application(
    payload: str = Form(..., description='JSON IndividualFormCreate'),
    files: list[UploadFile] = File(...),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user = validate_entra_token(credentials)
    data = _parse_form_payload(IndividualFormCreate, payload)
    totals = _calculate_totals(data.vehicles)

    application = Application(
        applicant_type=ApplicantType.individual,
        customer_name=data.customer_name,
        pesel=data.pesel,
        nip=data.nip,
        document_number=data.document_number,
        submitted_by=user.get('preferred_username', user.get('sub', 'unknown')),
        **totals,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    db.add_all(_build_vehicle_items(application.id, data.vehicles))
    folder = await SharePointService().upload_files(application.id, files)
    application.sharepoint_folder = folder
    db.commit()

    return {'id': application.id, 'sharepoint_folder': folder, **totals}


@router.get('/health-auth')
def auth_health(credentials=Depends(bearer_scheme)):
    payload = validate_entra_token(credentials)
    if settings.reception_group_id:
        groups = payload.get('groups', [])
        if settings.reception_group_id not in groups:
            raise HTTPException(status_code=403, detail='Brak uprawnień do składania wniosków')
    return {'ok': True, 'user': payload.get('preferred_username')}
