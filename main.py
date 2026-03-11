"""
Telegram Channel → WhatsApp Group News Bot
Stack : Replit (Flask) + Fonnte + Make.com
Format: Ringkas | Filter: Anti-Duplikat
"""

from flask import Flask, request, jsonify
import requests
import hashlib
import os
from datetime import datetime

app = Flask(__name__)

# ── Konfigurasi dari Replit Secrets ──
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
FONNTE_TOKEN   = os.environ.get("FONNTE_TOKEN", "")
WA_TARGET      = os.environ.get("WA_TARGET", "")
MAKE_SECRET    = os.environ.get("MAKE_SECRET", "")

_sent_hashes = []
HASH_LIMIT   = 200


def is_duplicate(text):
    h = hashlib.md5(text.strip().encode()).hexdigest()
    if h in _sent_hashes:
        return True
    _sent_hashes.append(h)
    if len(_sent_hashes) > HASH_LIMIT:
        _sent_hashes.pop(0)
    return False


def extract_url(text, entities):
    for e in entities:
        if e.get("type") == "text_link":
            return e.get("url", "")
        if e.get("type") == "url":
            return text[e["offset"]: e["offset"] + e["length"]]
    for word in text.split():
        if word.startswith("http"):
            return word
    return ""


def format_message(title, desc, url, source):
    now  = datetime.now().strftime("%d %b %Y %H:%M")
    desc = (desc[:120] + "…") if len(desc) > 120 else desc
    lines = [f"📰 *{title}*"]
    if desc:
        lines.append(desc)
    if url:
        lines.append(f"🔗 {url}")
    lines.append(f"_📡 {source} • {now}_")
    return "\n".join(lines)


def parse_post(post):
    text     = post.get("text") or post.get("caption") or ""
    entities = post.get("entities") or post.get("caption_entities") or []
    source   = post.get("chat", {}).get("title") or "Telegram"
    if not text:
        return None
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    title = lines[0] if lines else "Update"
    desc  = " ".join(
        l for l in lines[1:]
        if not l.startswith("http") and not l.startswith("@")
    )
    url = extract_url(text, entities)
    return {"title": title, "desc": desc, "url": url, "source": source, "raw": text}


def send_whatsapp(message, target=None):
    try:
        resp = requests.post(
            "https://api.fonnte.com/send",
            headers={"Authorization": FONNTE_TOKEN},
            data={"target": target or WA_TARGET, "message": message, "countryCode": "62"},
            timeout=15,
        )
        return resp.json()
    except Exception as exc:
        return {"status": False, "error": str(exc)}


def handle_post(post):
    parsed = parse_post(post)
    if not parsed:
        return {"status": "skip", "reason": "empty_text"}
    if is_duplicate(parsed["raw"]):
        return {"status": "skip", "reason": "duplicate"}
    msg    = format_message(parsed["title"], parsed["desc"], parsed["url"], parsed["source"])
    result = send_whatsapp(msg)
    return {"status": "sent", "fonnte": result}


# ── Endpoints ──

@app.route("/", methods=["GET"])
def index():
    return jsonify({"bot": "TG→WA News Bot", "status": "running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "hashes_stored": len(_sent_hashes),
        "wa_target_set": bool(WA_TARGET),
        "fonnte_set": bool(FONNTE_TOKEN),
    })

@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False}), 400
    post = (
        data.get("channel_post")
        or data.get("edited_channel_post")
        or data.get("message")
    )
    if not post:
        return jsonify({"ok": True, "note": "no post"})
    result = handle_post(post)
    print(f"[TG] {result}")
    return jsonify({"ok": True, "result": result})

@app.route("/webhook/make", methods=["POST"])
def make_webhook():
    secret = request.headers.get("X-Secret") or request.args.get("secret", "")
    if MAKE_SECRET and secret != MAKE_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "no payload"}), 400
    if "message" in data:
        result = handle_post(data["message"])
    else:
        raw = data.get("title", "") + data.get("desc", "")
        if is_duplicate(raw):
            return jsonify({"ok": True, "result": {"status": "skip", "reason": "duplicate"}})
        msg    = format_message(
            data.get("title", "Update"),
            data.get("desc", data.get("body", "")),
            data.get("url", ""),
            data.get("source", "Make.com"),
        )
        result = {"status": "sent", "fonnte": send_whatsapp(msg, data.get("target"))}
    print(f"[Make] {result}")
    return jsonify({"ok": True, "result": result})

@app.route("/test", methods=["POST"])
def test_send():
    data   = request.get_json(silent=True) or {}
    msg    = data.get("message", "✅ *Test berhasil!*\n_Bot TG→WA aktif._")
    result = send_whatsapp(msg, data.get("target"))
    return jsonify({"ok": True, "result": result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
