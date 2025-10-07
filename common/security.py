from fastapi import HTTPException, Cookie, Depends
from session_store import session_store

def try_get_current_user(session_id: str | None = Cookie(None)) -> dict | None:
    """Tries to get the current user from the session cookie, but does not raise an error if not found."""
    if session_id is None:
        return None
    return session_store.get(session_id)

def get_current_user(user: dict | None = Depends(try_get_current_user)) -> dict:
    """Gets the current user from the session cookie. Raises a 401 error if not authenticated."""
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

