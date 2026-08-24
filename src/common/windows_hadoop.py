"""Windows Hadoop configuration for local PySpark/Delta execution."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HADOOP_HOME_DIR = PROJECT_ROOT / ".tools" / "hadoop"
HADOOP_BIN_BASE_URLS = (
    "https://raw.githubusercontent.com/steveloughran/winutils/master/hadoop-3.0.0/bin",
    "https://raw.githubusercontent.com/steveloughran/winutils/master/hadoop-3.2.0/bin",
)
REQUIRED_HADOOP_BINARIES = ("winutils.exe", "hadoop.dll")


def _download_hadoop_binary(filename: str, destination: Path) -> None:
    last_error: Exception | None = None
    for base_url in HADOOP_BIN_BASE_URLS:
        url = f"{base_url}/{filename}"
        try:
            urllib.request.urlretrieve(url, destination)
            if destination.exists() and destination.stat().st_size > 0:
                return
        except urllib.error.URLError as exc:
            last_error = exc

    raise RuntimeError(
        f"Failed to download {filename} for local Spark on Windows. "
        f"Expected location: {destination}"
    ) from last_error


def _ensure_hadoop_binaries(bin_dir: Path) -> None:
    for filename in REQUIRED_HADOOP_BINARIES:
        target_path = bin_dir / filename
        if not target_path.exists() or target_path.stat().st_size == 0:
            _download_hadoop_binary(filename, target_path)


def _prepend_to_path(path_entry: str) -> None:
    normalized = os.path.normcase(os.path.normpath(path_entry))
    existing_entries = os.environ.get("PATH", "").split(os.pathsep)
    if not any(os.path.normcase(os.path.normpath(entry)) == normalized for entry in existing_entries):
        os.environ["PATH"] = normalized + os.pathsep + os.environ.get("PATH", "")


def configure_windows_hadoop() -> Path | None:
    """Ensure a local HADOOP_HOME exists for Spark on Windows.

    Downloads winutils.exe and hadoop.dll into a gitignored project folder on
    first use. Both binaries are required for Hadoop NativeIO on Windows.
    """
    if sys.platform != "win32":
        return None

    bin_dir = HADOOP_HOME_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    _ensure_hadoop_binaries(bin_dir)

    missing = [name for name in REQUIRED_HADOOP_BINARIES if not (bin_dir / name).exists()]
    if missing:
        raise RuntimeError(
            "Windows Hadoop native runtime is incomplete. Missing binaries in "
            f"{bin_dir}: {', '.join(missing)}"
        )

    hadoop_home = str(HADOOP_HOME_DIR.resolve())
    bin_path = str(bin_dir.resolve())
    os.environ["HADOOP_HOME"] = hadoop_home
    os.environ["hadoop.home.dir"] = hadoop_home
    _prepend_to_path(bin_path)
    return HADOOP_HOME_DIR
