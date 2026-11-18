import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.context import ApplicationContext, get_context

basic_auth = HTTPBasic()


def require_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(basic_auth)],
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> str:
    """Compare both credential fields without leaking which field mismatched."""
    supplied_username = credentials.username.encode("utf-8")
    configured_username = context.settings.basic_auth_username.encode("utf-8")
    supplied_password = credentials.password.encode("utf-8")
    configured_password = (
        context.settings.basic_auth_password.get_secret_value().encode("utf-8")
    )

    username_matches = secrets.compare_digest(
        supplied_username,
        configured_username,
    )
    password_matches = secrets.compare_digest(
        supplied_password,
        configured_password,
    )
    if not (username_matches and password_matches):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
