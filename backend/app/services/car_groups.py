import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CarGroupsService:
    def __init__(self) -> None:
        self.enabled = bool(settings.mssql_car_groups_url)
        self.engine = create_engine(settings.mssql_car_groups_url) if self.enabled else None

    def _run_query(self, query, params: dict | None = None) -> list:
        if not self.enabled or self.engine is None:
            return []
        try:
            with self.engine.connect() as conn:
                return conn.execute(query, params or {}).all()
        except SQLAlchemyError as exc:
            logger.exception('MSSQL dictionary lookup failed; returning empty data. Error: %s', exc)
            return []

    def list_groups(self) -> list[str]:
        query = text(
            """
            SELECT OPIS
            FROM [Eurorent].[dbo].[Rodzaje]
            WHERE FKIDTYPUSLOWNIKA = '10' AND Archiwalny = '0'
            ORDER BY OPIS
            """
        )
        rows = self._run_query(query)
        return [row[0] for row in rows if row[0]]

    def list_brands(self, phrase: str = '') -> list[str]:
        query = text(
            """
            SELECT DISTINCT NAZWAMARKI
            FROM [Eurorent].[dbo].[MARKA]
            WHERE LOWER(NAZWAMARKI) LIKE :pattern
            ORDER BY NAZWAMARKI
            """
        )
        rows = self._run_query(query, {'pattern': f"%{phrase.lower()}%"})
        return [row[0] for row in rows if row[0]]

    def list_models(self, phrase: str = '', brand: str = '') -> list[str]:
        query = text(
            """
            SELECT DISTINCT NAZWAMODELU
            FROM [Eurorent].[dbo].[MODEL]
            WHERE LOWER(NAZWAMODELU) LIKE :pattern
              AND (:brand = '' OR LOWER(NAZWAMARKI) = LOWER(:brand))
            ORDER BY NAZWAMODELU
            """
        )
        rows = self._run_query(query, {'pattern': f"%{phrase.lower()}%", 'brand': brand})
        return [row[0] for row in rows if row[0]]

    def resolve_brand_for_model(self, model_name: str) -> str | None:
        query = text(
            """
            SELECT TOP 1 NAZWAMARKI
            FROM [Eurorent].[dbo].[MODEL]
            WHERE LOWER(NAZWAMODELU) = LOWER(:model_name)
            ORDER BY NAZWAMARKI
            """
        )
        rows = self._run_query(query, {'model_name': model_name})
        return rows[0][0] if rows else None
