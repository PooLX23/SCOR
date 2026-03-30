from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.applications import router as applications_router
from app.core.config import settings
from app.db.session import Base, engine, ensure_schema

app = FastAPI(title='SCOR API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup() -> None:
    ensure_schema()
    Base.metadata.create_all(bind=engine)


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


app.include_router(applications_router)
