import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
ACCESS_KEY = os.environ["BRIDGE_ACCESS_KEY"]
SESSION_STRING = os.environ["TELEGRAM_SESSION_STRING"]

TARGET_BOT = os.getenv("TARGET_BOT", "holitechaibot")

app = FastAPI(title="Telegram MTProto Bridge")

client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

class SendMessageRequest(BaseModel):
    message: str

def check_key(x_bridge_key: str):
    if x_bridge_key != ACCESS_KEY:
        raise HTTPException(status_code=401, detail="Invalid bridge key")

@app.on_event("startup")
async def startup():
    await client.connect()

    if not await client.is_user_authorized():
        raise RuntimeError("Telegram session is not authorized")

@app.get("/health")
async def health(x_bridge_key: str = Header(default="")):
    check_key(x_bridge_key)
    me = await client.get_me()

    return {
        "ok": True,
        "telegram_connected": True,
        "username": getattr(me, "username", None),
        "user_id": me.id
    }

@app.post("/send-message")
async def send_message(
    data: SendMessageRequest,
    x_bridge_key: str = Header(default="")
):
    check_key(x_bridge_key)

    message = await client.send_message(
        TARGET_BOT,
        data.message
    )

    return {
        "ok": True,
        "message_id": message.id
    }

@app.get("/messages")
async def get_messages(
    limit: int = 10,
    x_bridge_key: str = Header(default="")
):
    check_key(x_bridge_key)

    messages = await client.get_messages(
        TARGET_BOT,
        limit=limit
    )

    result = []

    for m in messages:
        result.append({
            "id": m.id,
            "text": m.text or "",
            "date": m.date.isoformat() if m.date else None,
            "has_media": bool(m.media)
        })

    return {
        "ok": True,
        "messages": result
    }
