import uuid
import requests

from app import app

tes_auth = requests.auth.HTTPBasicAuth(
    app.config["TES_BASIC_AUTH_USER"], app.config["TES_BASIC_AUTH_PASSWORD"]
)


def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test
