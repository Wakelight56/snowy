from astrbot.api import AstrBotConfig
from dataclasses import dataclass, field
from typing import cast

@dataclass
class SekaiRanking:
    base_url: str = "https://sekairanking.exmeaning.com"
    cache_duration: int = 1800
    page_size: tuple | list = (1080,1080)
    timeout: int = 60
    all_ranks: list = field(
        default_factory=lambda: [
            50, 100, 200, 300, 400, 500,
            1000, 2000, 3000, 4000, 5000,
            10000,
        ],
    )
    allow_regions: list = field(default_factory=lambda: ["cn"])

@dataclass
class SekaiProfile:
    base_url: str = "https://sekaiprofile.exmeaning.com/profile/{user_id}?token={token}"
    token: str = ""
    bind_limit: dict = field(default_factory=dict)

@dataclass
class WebDriver:
    remote_url: str = ""
    browser_type: str = "chromium"


class Config(AstrBotConfig):
    data_path: str = "data/plugin_data/moesekai"
    file_db_save_interval: int = 5
    regions: list = ['cn', 'jp']
    sekairanking: SekaiRanking
    sekaiprofile: SekaiProfile
    webdriver: WebDriver


global_config: Config | None = None


def set_global_config(config: AstrBotConfig) -> None:
    global global_config
    # 确保 sekairanking 是 SekaiRanking 实例
    if hasattr(config, 'sekairanking') and isinstance(config.sekairanking, dict):
        config.sekairanking = SekaiRanking(**config.sekairanking)
    # 确保 sekaiprofile 是 SekaiProfile 实例
    if hasattr(config, 'sekaiprofile') and isinstance(config.sekaiprofile, dict):
        config.sekaiprofile = SekaiProfile(**config.sekaiprofile)
    # 确保 webdriver 是 WebDriver 实例
    if hasattr(config, 'webdriver') and isinstance(config.webdriver, dict):
        config.webdriver = WebDriver(**config.webdriver)
    global_config = cast(Config, config)


def get_global_config() -> Config:
    if global_config is None:
        raise RuntimeError("Global config is not initialized yet.")
    return global_config
