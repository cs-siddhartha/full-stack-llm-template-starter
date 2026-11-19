from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.auth.dependencies import require_session
from app.auth.models import LoginRequest, SessionRead, SignupRead, SignupRequest
from app.auth.service import (
    CurrentSession,
    DuplicateRegistrationError,
    EmailDeliveryError,
    EmailNotVerifiedError,
)
from app.context import ApplicationContext, get_context
from app.http import ApiError
from app.rate_limit import rate_limited

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(
    response: Response,
    context: ApplicationContext,
    session: CurrentSession,
) -> None:
    response.set_cookie(
        key=context.settings.session_cookie_name,
        value=session.token,
        max_age=context.settings.session_ttl_seconds,
        httponly=True,
        secure=context.settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post(
    "/signup",
    response_model=SignupRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ApiError,
            "description": "Email already registered",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiError,
            "description": "Verification email delivery unavailable",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiError,
            "description": "Sign-up rate limit exceeded",
        },
    },
)
@rate_limited("signup", key="ip")
async def signup(
    payload: SignupRequest,
    http_request: Request,
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> SignupRead:
    try:
        await context.auth.signup(payload.email, payload.password)
    except DuplicateRegistrationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email",
        ) from error
    except EmailDeliveryError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification email could not be sent",
        ) from error
    return SignupRead(message="Check your email to confirm your account")


@router.get("/verify-email", include_in_schema=True)
async def verify_email(
    token: str,
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> RedirectResponse:
    verified = await context.auth.verify_email(token)
    result = "verified" if verified else "invalid"
    target = f"{context.settings.frontend_url.rstrip('/')}/login?verification={result}"
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    "/login",
    response_model=SessionRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiError,
            "description": "Invalid credentials",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ApiError,
            "description": "Email confirmation required",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiError,
            "description": "Login rate limit exceeded",
        },
    },
)
@rate_limited("login", key="ip")
async def login(
    payload: LoginRequest,
    response: Response,
    http_request: Request,
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> SessionRead:
    try:
        session = await context.auth.login(payload.username, payload.password)
    except EmailNotVerifiedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirm your email before signing in",
        ) from error
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    _set_session_cookie(response, context, session)
    return session.user


@router.post(
    "/demo",
    response_model=SessionRead,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ApiError,
            "description": "Demo login disabled",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiError,
            "description": "Login rate limit exceeded",
        },
    },
)
@rate_limited("login", key="ip")
async def login_demo(
    response: Response,
    http_request: Request,
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> SessionRead:
    session = await context.auth.login_demo()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo login is disabled",
        )
    _set_session_cookie(response, context, session)
    return session.user


@router.get(
    "/session",
    response_model=SessionRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiError,
            "description": "Authentication required",
        }
    },
)
async def read_session(
    session: Annotated[CurrentSession, Depends(require_session)],
) -> SessionRead:
    return session.user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiError,
            "description": "Authentication required",
        }
    },
)
async def logout(
    response: Response,
    context: Annotated[ApplicationContext, Depends(get_context)],
    session: Annotated[CurrentSession, Depends(require_session)],
) -> None:
    await context.auth.logout(session.token)
    response.delete_cookie(
        key=context.settings.session_cookie_name,
        secure=context.settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
        path="/",
    )
