from rclone_bin_client.client import RcloneClient

if __name__ == "__main__":
    rc = RcloneClient()
    rc.start()

    print(rc.version())

    rc.stop()
