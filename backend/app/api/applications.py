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
    ApplicationCollectionSnapshot,
    CollectionDecision,
    ApplicationStatus,
    ApplicationVehicleItem,
)
from app.schemas.application import CompanyFormCreate, IndividualFormCreate
from app.services.auth import bearer_scheme, validate_entra_token
from app.services.car_groups import CarGroupsService
from app.services.collection import CollectionService
from app.services.notifications import NotificationService
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


def _is_collection(payload: dict) -> bool:
    if not settings.windykacja_group_id:
        return False
    return settings.windykacja_group_id in payload.get('groups', [])


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
        'collection_decision': app.collection_decision.value if app.collection_decision else None,
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
    NotificationService().notify_new_application(
        application_id=application.id,
        applicant_label=application.company_name or '-',
        submitted_by=application.submitted_by,
    )

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
    NotificationService().notify_new_application(
        application_id=application.id,
        applicant_label=application.customer_name or '-',
        submitted_by=application.submitted_by,
    )

    return {'id': application.id, 'sharepoint_folder': folder, 'status': application.status.value, **totals}


@router.get('/me')
def me(credentials=Depends(bearer_scheme)):
    payload = validate_entra_token(credentials)
    return {'user': _user_id(payload), 'is_reviewer': _is_reviewer(payload), 'is_collection': _is_collection(payload)}


@router.get('/my')
def my_applications(credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    user = _user_id(payload)
    records = db.query(Application).filter(Application.submitted_by == user).order_by(desc(Application.created_at)).all()
    return {'items': [_serialize_application(r) for r in records]}


@router.get('/all')
def all_applications(credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    if not _is_reviewer(payload) and not _is_collection(payload):
        raise HTTPException(status_code=403, detail='Brak uprawnień do listy wszystkich wniosków')

    records = db.query(Application).order_by(desc(Application.created_at)).all()
    return {'items': [_serialize_application(r) for r in records]}


@router.get('/car-groups')
def list_car_groups(credentials=Depends(bearer_scheme)):
    validate_entra_token(credentials)
    groups = CarGroupsService().list_groups()
    return {'items': groups}




@router.get('/car-brands')
def list_car_brands(q: str = '', credentials=Depends(bearer_scheme)):
    validate_entra_token(credentials)
    items = CarGroupsService().list_brands(q)
    return {'items': items}


@router.get('/car-models')
def list_car_models(q: str = '', brand: str = '', credentials=Depends(bearer_scheme)):
    validate_entra_token(credentials)
    items = CarGroupsService().list_models(q, brand)
    return {'items': items}


@router.get('/car-brand-for-model')
def car_brand_for_model(model: str, credentials=Depends(bearer_scheme)):
    validate_entra_token(credentials)
    brand = CarGroupsService().resolve_brand_for_model(model)
    return {'brand': brand}

@router.get('/{application_id}')
def application_details(application_id: int, credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    user = _user_id(payload)
    reviewer = _is_reviewer(payload)
    collection = _is_collection(payload)

    record = db.query(Application).filter(Application.id == application_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='Wniosek nie istnieje')

    if not reviewer and not collection and record.submitted_by != user:
        raise HTTPException(status_code=403, detail='Brak dostępu do szczegółów tego wniosku')

    vehicle_rows = db.query(ApplicationVehicleItem).filter(ApplicationVehicleItem.application_id == record.id).all()
    last_snapshot = (
        db.query(ApplicationCollectionSnapshot)
        .filter(ApplicationCollectionSnapshot.application_id == record.id)
        .order_by(desc(ApplicationCollectionSnapshot.created_at))
        .first()
    )

    details = _serialize_application(record)
    details['collection_comment'] = record.collection_comment
    details['collection_snapshot'] = (
        {
            'avg_days_past_due': last_snapshot.avg_days_past_due,
            'deposits_aa_cfm_rac': last_snapshot.deposits_aa_cfm_rac,
            'deposits_orders': last_snapshot.deposits_orders,
            'source_position': last_snapshot.source_position,
            'created_at': last_snapshot.created_at.isoformat(),
        }
        if last_snapshot
        else None
    )
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


@router.get('/{application_id}/collection-preview')
def application_collection_preview(application_id: int, credentials=Depends(bearer_scheme), db: Session = Depends(get_db)):
    payload = validate_entra_token(credentials)
    if not _is_collection(payload):
        raise HTTPException(status_code=403, detail='Brak uprawnień windykacji')
    record = db.query(Application).filter(Application.id == application_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='Wniosek nie istnieje')
    return CollectionService().compute(record.nip)


@router.post('/{application_id}/collection-decision')
def save_collection_decision(
    application_id: int,
    decision: str = Form(...),
    comment: str = Form(default=''),
    avg_days_past_due: float | None = Form(default=None),
    deposits_aa_cfm_rac: float | None = Form(default=None),
    deposits_orders: float | None = Form(default=None),
    source_position: str | None = Form(default=None),
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    payload = validate_entra_token(credentials)
    if not _is_collection(payload):
        raise HTTPException(status_code=403, detail='Brak uprawnień windykacji')
    record = db.query(Application).filter(Application.id == application_id).first()
    if not record:
        raise HTTPException(status_code=404, detail='Wniosek nie istnieje')
    if decision not in {CollectionDecision.positive.value, CollectionDecision.negative.value}:
        raise HTTPException(status_code=422, detail='Nieprawidłowa decyzja windykacji')

    snapshot = ApplicationCollectionSnapshot(
        application_id=record.id,
        avg_days_past_due=avg_days_past_due,
        deposits_aa_cfm_rac=deposits_aa_cfm_rac,
        deposits_orders=deposits_orders,
        source_position=source_position,
    )
    db.add(snapshot)
    record.collection_decision = CollectionDecision(decision)
    record.collection_comment = comment or None
    record.status = ApplicationStatus.after_collection
    db.commit()
    return {'ok': True, 'status': record.status.value, 'collection_decision': record.collection_decision.value}


@router.get('/health-auth')
def auth_health(credentials=Depends(bearer_scheme)):
    payload = validate_entra_token(credentials)
    return {'ok': True, 'user': _user_id(payload), 'is_reviewer': _is_reviewer(payload)}
