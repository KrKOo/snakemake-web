from fastapi import HTTPException, Request
from pymongo import MongoClient

from .auth import AccessToken, AuthClient
from .config import config
from .repository import WorkflowRepository, JobRepository
from .db import MongoDatabase

async def get_authenticated_user(request: Request) -> str:
    username = request.headers.get("X-Forwarded-Preferred-Username")
    if not username:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return username

async def get_valid_access_token(request: Request) -> AccessToken:
    authorization_header = request.headers.get("Authorization", None)
    forwarded_token_header = request.headers.get("X-Forwarded-Access-Token", None)

    if authorization_header:
        if not authorization_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid access token")
        token_value = authorization_header.split(" ")[1]
    elif forwarded_token_header:
        token_value = forwarded_token_header
    else:
        raise HTTPException(status_code=401, detail="No access token provided")
    auth_client = AuthClient(
		config.app.oidc_url,
        config.app.oidc_client_id,
        config.app.oidc_client_secret
    )
    token = AccessToken(token_value, auth_client)
    if token.is_expired() or not token.is_valid():
        raise HTTPException(status_code=401, detail="Invalid access token")
    return token

def get_workflow_repository():
    mongo_client = MongoClient(config.mongo.mongodb_uri, uuidRepresentation="standard")
    mongo_db = MongoDatabase(mongo_client[config.mongo.db_name])
    job_repository = JobRepository(config.snakemake.tes_url)
    return WorkflowRepository(mongo_db, job_repository)
