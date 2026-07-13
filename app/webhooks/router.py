import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from app.core.config import Settings, get_settings
from app.webhooks.parser import parse_pull_request_event
from app.webhooks.security import verify_signature

logger = logging.getLogger(__name__)

router = APIRouter()

HANDLED_PULL_REQUEST_ACTIONS = {"opened", "synchronize", "reopened"}


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    x_github_event: str = Header(...),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str | int]:
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if x_github_event == "ping":
        return {"status": "ignored", "reason": "ping"}

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"unhandled event: {x_github_event}"}

    payload = json.loads(body)
    action = payload.get("action", "")

    if action not in HANDLED_PULL_REQUEST_ACTIONS:
        return {"status": "ignored", "reason": f"unhandled action: {action}"}

    pull_request = parse_pull_request_event(payload)
    logger.info(
        "Received pull_request event: %s#%d (%s)",
        pull_request.repository.full_name,
        pull_request.number,
        action,
    )

    response.status_code = 202
    return {"status": "accepted", "pull_request": pull_request.number, "action": action}
