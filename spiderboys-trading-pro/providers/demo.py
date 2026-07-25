from __future__ import annotations

from pathlib import Path
import pandas as pd

from core.data import load_indices, load_market, load_news
from providers.base import MarketDataProvider


class DemoMarketDataProvider(MarketDataProvider):
    """Loads the repository's bundled training data."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def market(self) -> pd.DataFrame:
        return load_market(self.base_dir)

    def news(self) -> pd.DataFrame:
        return load_news(self.base_dir)

    def indices(self) -> pd.DataFrame:
        return load_indices(self.base_dir)
