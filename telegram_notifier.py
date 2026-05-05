import json
import threading
import urllib.request
import urllib.parse
from config import Contact

_USER_AGENT = "eve-gate-logger/1.1"
_API = "https://api.telegram.org/bot{token}/sendMessage"


def notify(bot_token: str, chat_ids: list[str], contact: Contact, timestamp: str) -> None:
    if not bot_token or not chat_ids:
        return
    t = threading.Thread(target=_send, args=(bot_token, chat_ids, contact, timestamp), daemon=True)
    t.start()


def _send(bot_token: str, chat_ids: list[str], contact: Contact, timestamp: str) -> None:
    time_str = timestamp[11:16]  # "HH:MM"

    # Build ship type part
    if contact.ship_type_id:
        ship_part = f'<a href="https://zkillboard.com/ship/{contact.ship_type_id}/">{_esc(contact.ship_type)}</a>'
    else:
        ship_part = _esc(contact.ship_type)

    # Build tag parts (corp links resolved inline — reuse discord_notifier cache)
    from discord_notifier import _resolve_corp
    tag_parts: list[str] = []
    for tag in contact.tags:
        url = _resolve_corp(tag)
        if url:
            tag_parts.append(f'<a href="{url}">[{_esc(tag)}]</a>')
        else:
            tag_parts.append(f"[{_esc(tag)}]")

    parts = [_esc(contact.pilot_name)]
    if ship_part:
        parts.append(ship_part)
    parts.extend(tag_parts)

    text = f"<code>{time_str}</code> {' '.join(parts)}"
    payload = json.dumps({"chat_id": None, "text": text, "parse_mode": "HTML"})

    url = _API.format(token=bot_token)
    for chat_id in chat_ids:
        body = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"[telegram] Failed (chat {chat_id}): {e}")


def _esc(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
