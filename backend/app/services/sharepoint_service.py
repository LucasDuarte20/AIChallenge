import base64
import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _to_share_id(share_url: str) -> str:
    """
    Microsoft Graph 'shares' API usa un shareId base64url con prefijo 'u!'.
    Referencia: /shares/{shareId}/driveItem
    """
    raw = f"u!{share_url}".encode("utf-8")
    b64 = base64.b64encode(raw).decode("utf-8")
    b64url = b64.rstrip("=").replace("/", "_").replace("+", "-")
    return b64url


async def _get_graph_token() -> str:
    if not (settings.sp_tenant_id and settings.sp_client_id and settings.sp_client_secret):
        raise ValueError("Faltan credenciales de SharePoint (SP_TENANT_ID, SP_CLIENT_ID, SP_CLIENT_SECRET).")

    url = f"https://login.microsoftonline.com/{settings.sp_tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": settings.sp_client_id,
        "client_secret": settings.sp_client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]


async def download_sharepoint_excel(dest_dir: str | Path) -> Path:
    """
    Descarga el Excel desde SharePoint usando Microsoft Graph.
    Requiere SP_SHARE_URL y credenciales.
    """
    if not settings.sp_share_url:
        raise ValueError("Falta SP_SHARE_URL (link compartido del Excel).")

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / settings.sp_download_filename

    token = await _get_graph_token()
    share_id = _to_share_id(settings.sp_share_url)

    # Descargar contenido del driveItem asociado al link compartido
    content_url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        resp = await client.get(content_url, headers=headers)
        resp.raise_for_status()
        dest_path.write_bytes(resp.content)

    logger.info("Excel descargado desde SharePoint a %s", dest_path)
    return dest_path

