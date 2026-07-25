"""Market-data provider interfaces for Spiderboys Trading Pro."""
from .base import MarketDataProvider
from .demo import DemoMarketDataProvider

__all__ = ["MarketDataProvider", "DemoMarketDataProvider"]
