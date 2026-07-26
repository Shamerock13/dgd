from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import HTTPException

UPDATER_URL = os.getenv("UPDATER_URL", "http://DGD-Updater:8090").rstrip("/")
UPDATER_TOKEN = os.getenv("UPDATER_TOKEN", "")


def _headers() -> dict[str, str]:
    return {"X-DGD-Updater-Token": UPDATER_TOKEN} if UPDATER_TOKEN else {}


async def updater_request(
    method: str,
    path: str,
    *,
    timeout: float = 20.0,
    json_data: dict[str, Any] | None = None,
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                f"{UPDATER_URL}{path}",
                headers=_headers(),
                json=json_data,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Der DGD-Updater ist nicht erreichbar. Prüfe den Container DGD-Updater.",
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text or f"Updater-Fehler {response.status_code}"}

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=payload.get("detail", f"Updater-Fehler {response.status_code}"),
        )
    return payload
