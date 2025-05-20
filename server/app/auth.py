from typing import override
import jwt
import requests

from app.common.models import VisaJWTPayload, OIDCConfig, UserInfo, TokenInfo, TokenJWTPayload
from app.workflow_definition import WorkflowDefinitionMetadata


class Visa:
    def __init__(self, token: str):
        self.token = token
        self.type: str = ""
        self.value: str = ""
        self.expires: int | None = None
        self.asserted: int | None = None
        self.source: str = ""
        self.issued_by: str = ""
        self._parse_visa()

    def _parse_visa(self) -> None:
        decoded_jwt = jwt.decode(
            self.token, options={"verify_signature": False}
        )
        visa_jwt = VisaJWTPayload.model_validate(decoded_jwt)
        visa_payload = visa_jwt.ga4gh_visa_v1

        self.type = visa_payload.type
        self.value = visa_payload.value
        self.asserted = int(visa_payload.asserted) if visa_payload.asserted else None
        self.source = visa_payload.source
        self.issued_by = visa_payload.by

    @override
    def __repr__(self):
        return f"Visa(type={self.type}, value={self.value}, expires={self.expires}, asserted={self.asserted}, source={self.source}, issued_by={self.issued_by})"


class AuthClient:
    def __init__(self, oidc_url: str, client_id: str, client_secret: str):
        self.oidc_config_url = oidc_url + "/.well-known/openid-configuration"
        self.client_id = client_id
        self.client_secret = client_secret
        self.basic_auth = (client_id, client_secret)

        self.jwks_url: str = ""
        self.introspection_url: str = ""
        self.userinfo_url: str = ""
        self._get_urls()

    def _get_urls(self) -> None:
        try:
            response = requests.get(self.oidc_config_url)
            oidc_config = OIDCConfig.model_validate(response.json())
            self.jwks_url = oidc_config.jwks_uri
            self.introspection_url = oidc_config.introspection_endpoint
            self.userinfo_url = oidc_config.userinfo_endpoint
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

        self._user_info: UserInfo | None = None

    @property
    def userinfo(self) -> UserInfo:
        if self._user_info is None:
            self._user_info = self.get_userinfo()

        return self._user_info

    def is_expired(self, time_offset: int = 0) -> bool:
        token_jwt = self.get_data()

        if not token_jwt:
            return True

        if token_jwt.exp - time_offset < 0:
            return True

        return False

    def is_valid(self) -> bool:
        body = {"token": self.value}

        response = requests.post(
            self.auth_client.introspection_url, body, auth=self.auth_client.basic_auth
        )

        if response.status_code != 200:
            raise Exception("Failed to validate the access token: " + response.text)

        token_info = TokenInfo.model_validate(response.json())

        if token_info.active:
            return True

        return False

    def get_userinfo(self) -> UserInfo:
        response = requests.get(
            self.auth_client.userinfo_url,
            headers={"Authorization": f"Bearer {self.value}"},
        )

        if response.status_code != 200:
            raise Exception("Failed to get user info: " + response.text)

        data = UserInfo.model_validate(response.json())

        return data

    def get_data(self) -> TokenJWTPayload | None:
        jwks_client = jwt.PyJWKClient(self.auth_client.jwks_url)
        header = jwt.get_unverified_header(self.value)

        key = jwks_client.get_signing_key(header["kid"]).key

        try:
            decoded_jwt = jwt.decode(
                self.value, key, [header["alg"]], options={"verify_aud": False}
            )

            token_jwt = TokenJWTPayload.model_validate(decoded_jwt)
        except jwt.ExpiredSignatureError:
            return None

        return token_jwt

    def get_visas(self) -> list[Visa]:
        user_info = self.get_userinfo()

        visas: list[Visa] = []
        for visa in user_info.ga4gh_passport_v1:
            v = Visa(token=visa)
            visas.append(v)

        return visas

    def get_entitlements(self) -> list[str]:
        user_info = self.get_userinfo()

        return user_info.eduperson_entitlement

    def has_visa(self, type: str, value: str) -> bool:
        visas = self.get_visas()

        for visa in visas:
            if visa.type == type and visa.value == value:
                return True

        return False

    def has_entitlement(self, entitlement: str) -> bool:
        entitlements = self.get_entitlements()

        for entitlement in entitlements:
            if entitlement == entitlement:
                return True

        return False

    def is_authorized_for_workflow(
        self, workflow_definition: WorkflowDefinitionMetadata
    ) -> bool:
        if self.has_visa("ControlledAccessGrants", str(workflow_definition.id)):
            return True

        if workflow_definition.is_entitlement_satisfied(self.get_entitlements()):
            return True

        return False
