import sys
from pathlib import Path

bin_dir = Path(__file__).parent / "bin"
bin_name = "rclone.exe" if sys.platform == "win32" else "rclone"
rclone = bin_dir / bin_name

assert rclone.is_file(), "rclone binary missing!"


BINARY_PATH = rclone.absolute()
