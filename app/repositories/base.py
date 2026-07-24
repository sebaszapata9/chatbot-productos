from typing import Protocol


class CatalogSource(Protocol):
    def fetch_rows(self) -> list[dict[str, str]]:
        """Return spreadsheet rows using normalized column names."""
