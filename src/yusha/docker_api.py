from __future__ import annotations

from typing import Any

import aiodocker
from aiodocker.exceptions import DockerError as AioDockerError


class DockerError(RuntimeError):
    """Bota gösterilebilir Docker hatası."""


class DockerApi:
    def __init__(self, url: str) -> None:
        self._url = url
        self._docker: aiodocker.Docker | None = None

    @property
    def _client(self) -> aiodocker.Docker:
        if self._docker is None:
            self._docker = aiodocker.Docker(url=self._url)
        return self._docker

    async def close(self) -> None:
        if self._docker is not None:
            await self._docker.close()
            self._docker = None

    async def list_containers(self) -> list[dict[str, str]]:
        try:
            raw = await self._client.containers.list(all=True)
        except AioDockerError as exc:  # pragma: no cover - ağ hatası
            raise DockerError(f"Docker API'ye ulaşılamadı: {exc}") from exc

        out: list[dict[str, str]] = []
        for container in raw:
            summary: dict[str, Any] = getattr(container, "_container", {}) or {}
            names = summary.get("Names") or []
            name = names[0].lstrip("/") if names else str(summary.get("Id", ""))[:12]
            out.append(
                {
                    "name": name,
                    "state": str(summary.get("State", "unknown")),
                    "status": str(summary.get("Status", "")),
                    "image": str(summary.get("Image", "")),
                }
            )
        out.sort(key=lambda d: d["name"])
        return out

    async def _get(self, name: str) -> aiodocker.containers.DockerContainer:
        try:
            return await self._client.containers.get(name)
        except AioDockerError as exc:
            raise DockerError(f"'{name}' bulunamadı") from exc

    async def inspect(self, name: str) -> dict[str, Any]:
        container = await self._get(name)
        data = await container.show()
        state: dict[str, Any] = data.get("State", {})
        health = state.get("Health") or {}
        return {
            "state": state.get("Status"),
            "exit_code": state.get("ExitCode"),
            "error": state.get("Error") or "",
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "restart_count": data.get("RestartCount", 0),
            "health": health.get("Status"),
            "image": (data.get("Config") or {}).get("Image", ""),
        }

    async def logs(self, name: str, tail: int) -> str:
        container = await self._get(name)
        lines = await container.log(stdout=True, stderr=True, tail=tail)
        if isinstance(lines, list):
            return "".join(lines)
        return str(lines)

    async def restart(self, name: str, timeout: int = 10) -> None:
        await (await self._get(name)).restart(timeout=timeout)

    async def start(self, name: str) -> None:
        await (await self._get(name)).start()

    async def stop(self, name: str, timeout: int = 10) -> None:
        await (await self._get(name)).stop(timeout=timeout)

    async def exec(self, name: str, argv: list[str], timeout: int = 30) -> tuple[int, str]:
        container = await self._get(name)
        try:
            execute = await container.exec(argv, stdout=True, stderr=True)
            buf = bytearray()
            async with execute.start(detach=False, timeout=timeout) as stream:
                while True:
                    msg = await stream.read_out()
                    if msg is None:
                        break
                    buf += msg.data
            info = await execute.inspect()
        except AioDockerError as exc:
            raise DockerError(f"exec başarısız ({name}): {exc}") from exc
        return int(info.get("ExitCode") or 0), buf.decode("utf-8", "replace")
