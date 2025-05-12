import backoff

# 2 seconds
MAX_WAIT_TIME = 2


@backoff.on_exception(backoff.expo, Exception, max_time=MAX_WAIT_TIME)
def wait_for_internet_connection():
    if is_internet_connected():
        return

    # raise a generic py exception to trigger a retry
    raise Exception("no internet connection")


def is_internet_connected():
    import socket

    try:
        with socket.socket(socket.AF_INET) as s:
            s.connect(("google.com", 80))
            return True
    except socket.error:
        return False
