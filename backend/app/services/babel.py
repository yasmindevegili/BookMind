import re

import httpx

from ..core.config import get_settings


class BabelClient:
    """
    Cliente autenticado para o Calibre-Web (Babel).

    Mantém uma sessão httpx com cookies persistentes.
    Faz login automático (e re-login quando a sessão expira).
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._logged_in = False

    def _settings(self):
        return get_settings()

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15, follow_redirects=True)
        return self._client

    async def _login(self) -> bool:
        s = self._settings()
        client = await self._ensure_client()
        try:
            resp = await client.get(f"{s.BABEL_URL}/login")
            match = re.search(r'csrf_token"\s+value="([^"]+)"', resp.text)
            if not match:
                return False
            csrf = match.group(1)
            resp = await client.post(
                f"{s.BABEL_URL}/login",
                data={
                    "username": s.BABEL_USER,
                    "password": s.BABAL_PASS,
                    "next": "/",
                    "csrf_token": csrf,
                },
            )
            self._logged_in = resp.status_code in (200, 302)
            return self._logged_in
        except Exception:
            return False

    async def get_cover(self, babel_id: int) -> bytes | None:
        if not self._logged_in:
            if not await self._login():
                return None

        client = await self._ensure_client()
        s = self._settings()
        try:
            resp = await client.get(f"{s.BABEL_URL}/cover/{babel_id}")
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                return resp.content

            # Sessão expirou — tenta re-login uma vez
            self._logged_in = False
            if not await self._login():
                return None
            resp = await client.get(f"{s.BABEL_URL}/cover/{babel_id}")
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        return None

    async def list_books(self, limit: int = 6000) -> list[dict]:
        if not self._logged_in:
            if not await self._login():
                return []

        client = await self._ensure_client()
        s = self._settings()
        try:
            resp = await client.get(
                f"{s.BABEL_URL}/ajax/listbooks",
                params={"limit": limit, "offset": 0},
            )
            if resp.status_code == 200:
                return resp.json().get("rows", [])
        except Exception:
            pass
        return []


babel_client = BabelClient()
