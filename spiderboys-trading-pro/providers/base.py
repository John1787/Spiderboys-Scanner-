from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class MarketDataProvider(ABC):
    """Contract for demo and future live market-data providers."""

    @abstractmethod
    def market(self) -> pd.DataFrame:
        """Return normalized intraday market data."""

    @abstractmethod
    def news(self) -> pd.DataFrame:
        """Return normalized catalyst/news data."""

    @abstractmethod
    def indices(self) -> pd.DataFrame:
        """Return normalized market-index data."""
