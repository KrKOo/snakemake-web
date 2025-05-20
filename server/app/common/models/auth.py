from typing import Optional
from pydantic import BaseModel

class VisaPayload(BaseModel):
    type: str
    value: str
    asserted: int
    source: str
    by: str


class VisaJWTPayload(BaseModel):
    iss: str
    sub: str
    exp: int
    iat: int
    jti: Optional[str] = None
    ga4gh_visa_v1: VisaPayload

class OIDCConfig(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    introspection_endpoint: str

class UserInfo(BaseModel):
    sub: str
    ga4gh_passport_v1: list[str] = []
    eduperson_entitlement: list[str] = []


class TokenInfo(BaseModel):
    active: bool


class TokenJWTPayload(BaseModel):
    sub: str
    iss: str
    aud: str | list[str]
    exp: int
    iat: int
    jti: str
    acr: str
    scope: str
    auth_time: int
    client_id: str