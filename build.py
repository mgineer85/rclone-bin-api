import hashlib
import io
import os
import pathlib
import platform
import shutil
import tempfile
import zipfile

import requests
from hatchling.builders.hooks.plugin.interface import BuildHookInterface  # type: ignore

SYS_SET = {"windows", "linux", "osx"}
ARCH_SET = {"amd64", "arm64"}

ARCH_MAP = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
}

SYS_MAP = {
    "windows": "windows",
    "linux": "linux",
    "darwin": "osx",
}


def _norm_arch(arch: str) -> str:
    key = arch.lower()
    try:
        return ARCH_MAP[key]
    except KeyError:
        raise OSError(f"{arch} is not supported.") from None


def _norm_sys(sys: str) -> str:
    key = sys.lower()
    try:
        return SYS_MAP[key]
    except KeyError:
        raise OSError(f"{sys} is not supported.") from None


def rclone_download(system: str, arch: str, rclone_version: str, out_dir: str) -> pathlib.Path:
    dest = pathlib.Path(out_dir) / "src" / "rclone_client" / "bin"

    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    base_url = f"https://downloads.rclone.org/v{rclone_version}"
    filename = f"rclone-v{rclone_version}-{system}-{arch}.zip"
    url = f"{base_url}/{filename}"
    sums_url = f"{base_url}/SHA256SUMS"

    print(f"Downloading rclone from {url}")
    # with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
    #     shutil.copyfileobj(r, f)

    req_session = requests.Session()
    resp = req_session.get(url)
    resp.raise_for_status()
    assert resp.content
    zip_bytes = resp.content

    try:
        hash_valid = None
        resp = req_session.get(sums_url)
        resp.raise_for_status()
        assert resp.text
        sums_text = resp.text

        for line in sums_text.splitlines():
            parts = line.strip().split()
            if len(parts) == 2 and parts[1] == filename:
                hash_valid = parts[0]
                break

        if not hash_valid:
            raise RuntimeError(f"{filename} not found in SHA256SUMS")

        hash = hashlib.sha256(zip_bytes).hexdigest()
        if hash != hash_valid.lower():
            raise RuntimeError(f"rclone checksum mismatch: expected {hash_valid}, got {hash}")

    except Exception as e:
        raise RuntimeError(f"Failed to verify rclone checksum: {e}") from e
    else:
        print("download verified successfully")

    bin_name = "rclone.exe" if system == "windows" else "rclone"
    bin_path = dest / bin_name

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf, tempfile.TemporaryDirectory() as temp_dir:
        print(f"unpacking downloaded zipfile to {temp_dir}")
        for member in zf.filelist:
            if pathlib.Path(member.filename).name == bin_name:
                unpacked_rclone_bin_path = pathlib.Path(zf.extract(member, temp_dir))
                unpacked_rclone_bin_path.move(bin_path)

    assert bin_path.is_file()

    print(f"unpacked rclone to {bin_path}")

    if system != "windows":
        bin_path.chmod(0o755)

    print("unpacking done")

    return bin_path


class RcloneclientBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        rclone_version = os.environ.get("BUILD_RCLONE_VERSION", "1.72.1")
        system = os.environ.get("BUILD_SYSTEM", _norm_sys(platform.system()))
        arch = os.environ.get("BUILD_ARCH", _norm_arch(platform.machine()))

        if system not in SYS_SET:
            raise RuntimeError(f"Invalid system: {system}")

        if arch not in ARCH_SET:
            raise RuntimeError(f"Invalid arch: {arch}")

        print(f"Downloading binary for {system}_{arch}")
        rclone_download(system, arch, rclone_version, self.root)

        # Override wheel tag
        build_data["tag"] = f"py3-none-{system}_{arch}"
