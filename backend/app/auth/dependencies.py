from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.auth.service import CurrentSession
from app.context import ApplicationContext, get_context


async def require_session(
    request: Request,
    context: Annotated[ApplicationContext, Depends(get_context)],
) -> CurrentSession:
    token = request.cookies.get(context.settings.session_cookie_name)
    session = None if token is None else await context.auth.resolve(token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return session
