from __future__ import annotations

import os
import time
from dataclasses import dataclass

import psutil


@dataclass(frozen=True)
class HostMetrics:
    cpu_percent: float
    load1: float
    load5: float
    load15: float
    mem_total: int
    mem_used: int
    mem_percent: float
    swap_total: int
    swap_used: int
    disk_total: int
    disk_used: int
    disk_percent: float
    uptime_seconds: float


def collect(host_proc: str = "/proc", host_root: str = "/") -> HostMetrics:
    """Host metriklerini topla. `host_proc` verilirse psutil onu procfs olarak kullanır
    (bot bir container içindeyken host'un /proc'unu mount edip buraya vermek gerekir)."""
    if host_proc and os.path.isdir(host_proc):
        psutil.PROCFS_PATH = host_proc

    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    root = host_root if os.path.isdir(host_root) else "/"
    disk = psutil.disk_usage(root)

    try:
        load1, load5, load15 = os.getloadavg()
    except (OSError, AttributeError):
        load1 = load5 = load15 = 0.0

    return HostMetrics(
        cpu_percent=psutil.cpu_percent(interval=0.4),
        load1=load1,
        load5=load5,
        load15=load15,
        mem_total=vm.total,
        mem_used=vm.total - vm.available,
        mem_percent=vm.percent,
        swap_total=swap.total,
        swap_used=swap.used,
        disk_total=disk.total,
        disk_used=disk.used,
        disk_percent=disk.percent,
        uptime_seconds=time.time() - psutil.boot_time(),
    )
