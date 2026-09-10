from __future__ import annotations

import shlex
from dataclasses import dataclass

from .config import CommandCfg, Settings
from .docker_api import DockerApi, DockerError


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    output: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class CommandRunner:
    """config.yaml'da isimle tanımlı komutları çalıştırır. Serbest shell yoktur:
    çağıran taraf bir CommandCfg verir, komut metnini kullanıcı giremez."""

    def __init__(self, settings: Settings, docker: DockerApi) -> None:
        self._s = settings
        self._docker = docker

    async def run(self, cmd: CommandCfg) -> RunResult:
        if cmd.target == "host":
            return await self._run_host(cmd.argv)
        if cmd.target.startswith("container:"):
            return await self._run_container(cmd.target.split(":", 1)[1], cmd.argv)
        return RunResult(1, f"Bilinmeyen target: {cmd.target!r}")

    async def _run_container(self, name: str, argv: list[str]) -> RunResult:
        try:
            code, out = await self._docker.exec(name, argv, timeout=self._s.command_timeout)
        except DockerError as exc:
            return RunResult(1, str(exc))
        return RunResult(code, out)

    async def _run_host(self, argv: list[str]) -> RunResult:
        if not self._s.ssh_enabled:
            return RunResult(
                1,
                "Host komutları için SSH yapılandırılmamış "
                "(YUSHA_SSH_HOST / YUSHA_SSH_USER / YUSHA_SSH_KEY_PATH).",
            )

        import asyncssh

        known_hosts = str(self._s.ssh_known_hosts) if self._s.ssh_known_hosts else None
        command = " ".join(shlex.quote(a) for a in argv)
        try:
            async with asyncssh.connect(
                self._s.ssh_host,
                username=self._s.ssh_user,
                client_keys=[str(self._s.ssh_key_path)],
                known_hosts=known_hosts,
            ) as conn:
                result = await conn.run(
                    command, check=False, timeout=self._s.command_timeout
                )
        except (OSError, asyncssh.Error) as exc:
            return RunResult(1, f"SSH hatası: {exc}")

        output = (result.stdout or "") + (result.stderr or "")
        code = result.exit_status if result.exit_status is not None else 0
        return RunResult(int(code), str(output))
