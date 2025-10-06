# session_store.py
import abc, time, secrets, asyncio
from typing import Optional, Dict, Any

class SessionStore(abc.ABC):
    @abc.abstractmethod
    async def create(self, data: Dict[str, Any], ttl_sec: int) -> str: ...
    @abc.abstractmethod
    async def get(self, sid: str) -> Optional[Dict[str, Any]]: ...
    @abc.abstractmethod
    async def touch(self, sid: str, ttl_sec: int) -> None: ...
    @abc.abstractmethod
    async def delete(self, sid: str) -> None: ...

class InMemorySessionStore(SessionStore):
    """단일 프로세스용. 프로덕션에선 Redis로 교체 권장."""
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._exp: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def create(self, data: Dict[str, Any], ttl_sec: int) -> str:
        sid = secrets.token_hex(16)
        async with self._lock:
            self._sessions[sid] = data
            self._exp[sid] = time.time() + ttl_sec
        return sid

    async def get(self, sid: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        async with self._lock:
            exp = self._exp.get(sid)
            if not exp or exp < now:
                self._sessions.pop(sid, None)
                self._exp.pop(sid, None)
                return None
            return dict(self._sessions[sid])  # shallow copy

    async def touch(self, sid: str, ttl_sec: int) -> None:
        now = time.time()
        async with self._lock:
            if sid in self._exp and self._exp[sid] > now:
                self._exp[sid] = now + ttl_sec

    async def delete(self, sid: str) -> None:
        async with self._lock:
            self._sessions.pop(sid, None)
            self._exp.pop(sid, None)

# 미래 교체용 스켈레톤 (나중에 구현만 채우면 됨)
class RedisSessionStore(SessionStore):
    def __init__(self, redis_client):
        self.r = redis_client
    async def create(self, data: Dict[str, Any], ttl_sec: int) -> str: ...
    async def get(self, sid: str) -> Optional[Dict[str, Any]]: ...
    async def touch(self, sid: str, ttl_sec: int) -> None: ...
    async def delete(self, sid: str) -> None: ...
