import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.application import ApplicantType, Application
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


@router.post('/company')
async def create_company_application(
    payload: str = Form(..., description='JSON CompanyFormCreate'),
    files: list[UploadFile] = File(...),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user = validate_entra_token(credentials)
    data = _parse_form_payload(CompanyFormCreate, payload)
    application = Application(
        applicant_type=ApplicantType.company,
        company_name=data.company_name,
        nip=data.nip,
        krs=data.krs,
        business_line=data.business_line,
        car_model=data.car_model,
        rent_amount=data.rent_amount,
        deposit_amount=data.deposit_amount,
        vehicle_value=data.vehicle_value,
        initial_fee=data.initial_fee,
        car_group=data.car_group,
        car_segment=data.car_segment,
        rental_period_months=data.rental_period_months,
        submitted_by=user.get('preferred_username', user.get('sub', 'unknown')),
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    folder = await SharePointService().upload_files(application.id, files)
    application.sharepoint_folder = folder
    db.commit()
    return {'id': application.id, 'sharepoint_folder': folder}


@router.post('/individual')
async def create_individual_application(
    payload: str = Form(..., description='JSON IndividualFormCreate'),
    files: list[UploadFile] = File(...),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    user = validate_entra_token(credentials)
    data = _parse_form_payload(IndividualFormCreate, payload)
    application = Application(
        applicant_type=ApplicantType.individual,
        customer_name=data.customer_name,
        pesel=data.pesel,
        nip=data.nip,
        document_number=data.document_number,
        business_line=data.business_line,
        car_model=data.car_model,
        rent_amount=data.rent_amount,
        deposit_amount=data.deposit_amount,
        vehicle_value=data.vehicle_value,
        initial_fee=data.initial_fee,
        car_group=data.car_group,
        car_segment=data.car_segment,
        rental_period_months=data.rental_period_months,
        submitted_by=user.get('preferred_username', user.get('sub', 'unknown')),
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    folder = await SharePointService().upload_files(application.id, files)
    application.sharepoint_folder = folder
    db.commit()
    return {'id': application.id, 'sharepoint_folder': folder}


@router.get('/health-auth')
def auth_health(credentials=Depends(bearer_scheme)):
    payload = validate_entra_token(credentials)
    if settings.reception_group_id:
        groups = payload.get('groups', [])
        if settings.reception_group_id not in groups:
            raise HTTPException(status_code=403, detail='Brak uprawnień do składania wniosków')
    return {'ok': True, 'user': payload.get('preferred_username')}
