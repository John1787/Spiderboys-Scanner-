from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "Spiderboys Trading Pro"
    app_version: str = "6.2.0"
    data_mode: str = "demo"
    market_data_provider: str = "demo"
    webhook_token: str = ""

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            data_mode=os.getenv("SPIDERBOYS_DATA_MODE", "demo").strip().lower(),
            market_data_provider=os.getenv("SPIDERBOYS_MARKET_PROVIDER", "demo").strip().lower(),
            webhook_token=os.getenv("SPIDERBOYS_WEBHOOK_TOKEN", ""),
        )
