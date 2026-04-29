import logging
import re

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _normalize_nip(raw: str | None) -> str:
    if not raw:
        return ''
    digits = re.sub(r'[^0-9]', '', raw)
    if digits.startswith('00') and len(digits) > 10:
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits


class CollectionService:
    def __init__(self) -> None:
        self.symfonia_engine = create_engine(settings.mssql_symfonia_url) if settings.mssql_symfonia_url else None
        self.eurorent_engine = create_engine(settings.mssql_car_groups_url) if settings.mssql_car_groups_url else None

    def _query_one(self, engine, query, params: dict) -> dict | None:
        if engine is None:
            return None
        if settings.log_external_sql:
            logger.info('External SQL [collection]: %s | params=%s', str(query), params)
        try:
            with engine.connect() as conn:
                row = conn.execute(query, params).mappings().first()
                return dict(row) if row else None
        except SQLAlchemyError as exc:
            logger.exception('Collection query failed: %s', exc)
            return None

    def compute(self, nip: str) -> dict:
        normalized = _normalize_nip(nip)
        if not normalized:
            return {'avg_days_past_due': None, 'deposits_aa_cfm_rac': None, 'deposits_orders': None, 'position': None}

        contractor = self._query_one(
            self.symfonia_engine,
            text(
                """
                SELECT TOP 1 pozycja, nip
                FROM [FK_EURORENT].[FK].[fk_kontrahenci_tmp]
                WHERE RIGHT(REPLACE(REPLACE(REPLACE(UPPER(nip), 'PL', ''), '-', ''), ' ', ''), 10) = :nip
                """
            ),
            {'nip': normalized},
        )
        if not contractor:
            return {'avg_days_past_due': None, 'deposits_aa_cfm_rac': None, 'deposits_orders': None, 'position': None}

        position = contractor.get('pozycja')
        id_kh = position
        avg_row = self._query_one(
            self.symfonia_engine,
            text(
                """
                SELECT AVG(CAST(DniPoTerminie AS FLOAT)) AS avg_days
                FROM [FK_EURORENT].[dbo].[MAPRaportDPD]
                WHERE IdFK_Kontrahenta = :position
                  AND Zakres = 'Okres - 3 lata od dziś'
                """
            ),
            {'position': position},
        )
        dep_row = self._query_one(
            self.eurorent_engine,
            text(
                """
                SELECT SUM(CAST(DoRozliczeniaPLN AS FLOAT)) AS deposits
                FROM [Eurorent].[dbo].[vSymfoniaZestawienieRozrachunkowKaucje]
                WHERE NrKontrahntaFK = :position
                  AND Stan = 'Depozyt wpłacony'
                """
            ),
            {'position': position},
        )
        orders_row = self._query_one(
            self.eurorent_engine,
            text(
                """
                SELECT SUM(CAST(KwotaKontraktu AS FLOAT)) AS deposits_orders
                FROM [Eurorent].[dbo].[vSDS_Orders]
                WHERE IdKhSymfonia = :id_kh
                  AND status = 2
                """
            ),
            {'id_kh': id_kh},
        )
        return {
            'avg_days_past_due': avg_row.get('avg_days') if avg_row else None,
            'deposits_aa_cfm_rac': dep_row.get('deposits') if dep_row else None,
            'deposits_orders': orders_row.get('deposits_orders') if orders_row else None,
            'position': str(position) if position is not None else None,
        }
