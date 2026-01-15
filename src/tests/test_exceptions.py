from rclone_api.exceptions import RcloneProcessException


def test_rclone_process_exception_str():
    exc = RcloneProcessException(error="boom", input={"op": True}, status=5, path="/tmp/rclone")

    assert str(exc) == ("RcloneProcessException(status=5, path='/tmp/rclone', error='boom', input={'op': True})")
