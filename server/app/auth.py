import jwt
import requests


class Visa:
    def __init__(self, token: str):
        self.token = token
        self.type: str = None
        self.value: str = None
        self.expires: int = None
        self.asserted: str = None
        self.source: str = None
        self.issued_by: str = None
        self._parse_visa()

    def _parse_visa(self):
        decoded = jwt.decode(self.token, options={"verify_signature": False})
        data = decoded["ga4gh_visa_v1"]

        # TODO: Check if the visa is expired
        self.type = data.get("type")
        self.value = data.get("value")
        self.asserted = int(data.get("asserted")) if data.get("asserted") else None
        self.source = data.get("source")
        self.issued_by = data.get("by")

    def __repr__(self):
        return f"Visa(type={self.type}, value={self.value}, expires={self.expires}, asserted={self.asserted}, source={self.source}, issued_by={self.issued_by})"


class AuthClient:
    def __init__(self, oidc_url: str, client_id: str, client_secret: str):
        self.oidc_config_url = oidc_url + "/.well-known/openid-configuration"
        self.client_id = client_id
        self.client_secret = client_secret
        self.basic_auth = (client_id, client_secret)

        self.jwks_url: str = None
        self.introspection_url: str = None
        self.userinfo_url: str = None
        self._get_urls()

    def _get_urls(self):
        try:
            response = requests.get(self.oidc_config_url)
            data = response.json()
            self.jwks_url = data["jwks_uri"]
            self.introspection_url = data["introspection_endpoint"]
            self.userinfo_url = data["userinfo_endpoint"]
        except KeyError:
            raise Exception("Failed to get JWKS URL from the token info endpoint")


class AccessToken:
    def __init__(
        self,
        value: str,
        auth_client: AuthClient,
    ):
        self.value = value
        self.auth_client = auth_client

    def is_expired(self, time_offset: int = 0) -> bool:
        data = self.get_data()

        if not data:
            return True

        if data["exp"] - time_offset < 0:
            return True

        return False

    def is_valid(self) -> bool:
        body = {"token": self.value}

        response = requests.post(
            self.auth_client.introspection_url, body, auth=self.auth_client.basic_auth
        )

        if response.status_code != 200:
            raise Exception("Failed to validate the access token: " + response.text)

        token_info = response.json()

        if token_info["active"]:
            return True

        return False

    def get_data(self):
        jwks_client = jwt.PyJWKClient(self.auth_client.jwks_url)
        header = jwt.get_unverified_header(self.value)
        key = jwks_client.get_signing_key(header["kid"]).key

        try:
            data = jwt.decode(
                self.value, key, [header["alg"]], options={"verify_aud": False}
            )
        except jwt.ExpiredSignatureError:
            return None

        return data

    def get_visas(self) -> list[Visa]:
        response = requests.get(
            self.auth_client.userinfo_url,
            headers={"Authorization": f"Bearer {self.value}"},
        )

        if response.status_code != 200:
            raise Exception("Failed to get user info: " + response.text)

        user_info = response.json()

        if "ga4gh_passport_v1" not in user_info:
            return []

        visas = []
        for visa in user_info["ga4gh_passport_v1"]:
            v = Visa(token=visa)
            visas.append(v)

        return visas

    def has_visa(self, type: str, value: str) -> bool:
        visas = self.get_visas()
        print(visas)

        for visa in visas:
            if visa.type == type and visa.value == value:
                return True

        return False
