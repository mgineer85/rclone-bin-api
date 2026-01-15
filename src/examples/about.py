from rclone_api.api import RcloneApi

if __name__ == "__main__":
    rc = RcloneApi()
    rc.start()

    print(rc.version())

    rc.stop()
