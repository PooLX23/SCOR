from sqlalchemy import create_engine, text

from app.core.config import settings


class CarGroupsService:
    def __init__(self) -> None:
        self.enabled = bool(settings.mssql_car_groups_url)
        self.engine = create_engine(settings.mssql_car_groups_url) if self.enabled else None

    def list_groups(self) -> list[str]:
        if not self.enabled or self.engine is None:
            return []

        query = text(
            """
            SELECT OPIS
            FROM [Eurorent].[dbo].[Rodzaje]
            WHERE FKIDTYPUSLOWNIKA = '10' AND Archiwalny = '0'
            ORDER BY OPIS
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query).all()

        return [row[0] for row in rows if row[0]]
