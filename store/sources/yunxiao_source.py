from typing import List

from store.sources.base import DataSource
from models.types import YunxiaoItem


class YunxiaoSource(DataSource[List[YunxiaoItem]]):

    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 300.0)

    async def fetch(self) -> List[YunxiaoItem]:
        return []

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
