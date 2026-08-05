import logging
import sys

from rclone_api.api import RcloneApi

if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.WARNING,
        format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    )

    rc = RcloneApi()
    rc.start()

    print(rc.version())

    rc.stop()
