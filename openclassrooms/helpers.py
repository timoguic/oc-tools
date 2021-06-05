import os


def get_username_password():
    username = os.environ.get("OC_USERNAME")
    password = os.environ.get("OC_PASSWORD")

    if not (username and password):
        raise RuntimeError("No credentials provided!")

    return username, password
