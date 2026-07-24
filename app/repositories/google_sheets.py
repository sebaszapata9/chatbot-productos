from __future__ import annotations

import random
import time
from typing import Any

READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


def normalize_header(value: str) -> str:
    return "_".join(str(value).strip().lower().split())


class GoogleSheetsCatalogSource:
    def __init__(
        self,
        spreadsheet_id: str,
        sheet_range: str,
        credentials_file: str,
        max_attempts: int = 4,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.sheet_range = sheet_range
        self.credentials_file = credentials_file
        self.max_attempts = max_attempts

    def _service(self) -> Any:
        # Imports diferidos: permiten probar el dominio sin instalar ni invocar Google.
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        credentials = Credentials.from_service_account_file(
            self.credentials_file,
            scopes=[READONLY_SCOPE],
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def fetch_rows(self) -> list[dict[str, str]]:
        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID no está configurado")

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = (
                    self._service()
                    .spreadsheets()
                    .values()
                    .get(
                        spreadsheetId=self.spreadsheet_id,
                        range=self.sheet_range,
                        majorDimension="ROWS",
                    )
                    .execute()
                )
                values = response.get("values", [])
                if not values:
                    return []

                headers = [normalize_header(header) for header in values[0]]
                rows: list[dict[str, str]] = []
                for raw_row in values[1:]:
                    padded = list(raw_row) + [""] * (len(headers) - len(raw_row))
                    rows.append(dict(zip(headers, padded[: len(headers)])))
                return rows
            except Exception as exc:
                status = getattr(getattr(exc, "resp", None), "status", None)
                retryable = status in {429, 500, 502, 503, 504}
                if not retryable or attempt == self.max_attempts:
                    raise
                time.sleep(min(2 ** (attempt - 1) + random.random(), 8))

        return []
