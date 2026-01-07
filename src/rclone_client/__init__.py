import os
import platform
from pathlib import Path

bin_name = "rclone.exe" if platform.system() == "Windows" else "rclone"
bin_dir = Path(__file__).parent / "bin"
rclone = bin_dir / ("rclone.exe" if os.name == "nt" else "rclone")

if not rclone.is_file():
    raise RuntimeError("rclone binary missing in non-editable install")


BINARY_PATH = rclone.absolute()
