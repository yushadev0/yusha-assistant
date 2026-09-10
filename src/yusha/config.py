from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Action = Literal["logs", "inspect", "restart", "start", "stop"]


class ServiceCfg(BaseModel):
    name: str
    container: str
    actions: list[Action] = Field(default_factory=lambda: ["logs", "inspect"])


class CommandCfg(BaseModel):
    name: str
    description: str = ""
    target: str = "host"  # "host" | "container:<ad>"
    argv: list[str]
    confirm: bool = False

    @field_validator("argv")
    @classmethod
    def _argv_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("argv boş olamaz")
        return v


class AppConfig(BaseModel):
    services: list[ServiceCfg] = Field(default_factory=list)
    commands: list[CommandCfg] = Field(default_factory=list)

    def service(self, name: str) -> ServiceCfg | None:
        return next((s for s in self.services if s.name == name), None)

    def service_by_container(self, container: str) -> ServiceCfg | None:
        return next((s for s in self.services if s.container == container), None)

    def command(self, name: str) -> CommandCfg | None:
        return next((c for c in self.commands if c.name == name), None)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="YUSHA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    # NoDecode: "111,222" gibi düz string'i JSON olarak ayrıştırmayı kapat;
    # ayırma işi aşağıdaki validator'da.
    admin_ids: Annotated[list[int], NoDecode]
    docker_host: str = "tcp://docker-socket-proxy:2375"
    config_path: Path = Path("config.yaml")

    host_proc: str = "/proc"
    host_root: str = "/"

    ssh_host: str | None = None
    ssh_user: str | None = None
    ssh_key_path: Path | None = None
    ssh_known_hosts: Path | None = None

    command_timeout: int = 30
    log_tail_default: int = 80
    log_tail_max: int = 400

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _split_ids(cls, v: object) -> object:
        if isinstance(v, str):
            return [p for p in (x.strip() for x in v.split(",")) if p]
        return v

    @property
    def ssh_enabled(self) -> bool:
        return bool(self.ssh_host and self.ssh_user and self.ssh_key_path)

    def load_app_config(self) -> AppConfig:
        if not self.config_path.exists():
            return AppConfig()
        data = yaml.safe_load(self.config_path.read_text("utf-8")) or {}
        return AppConfig.model_validate(data)
