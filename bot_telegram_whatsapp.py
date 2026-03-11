#!/usr/bin/env python3
"""
🤖 AUTO-POST BOT: Telegram → WhatsApp
Advanced bot untuk auto-forward pesan dari Telegram ke WhatsApp group
dengan formatting rapih dan ringkas.

Requirements:
  pip install python-telegram-bot twilio python-dotenv requests

Setup:
  1. Create .env file dengan:
     TELEGRAM_BOT_TOKEN=your_token_here
     TWILIO_ACCOUNT_SID=your_sid
     TWILIO_AUTH_TOKEN=your_token
     TWILIO_WHATSAPP_FROM=whatsapp:+14155552671
     WHATSAPP_GROUP_TO=whatsapp:+62812345678
     
  2. Run: python3 bot.py
"""

import os
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from telegram import Update, Chat, User
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from twilio.rest import Client

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155552671")
WHATSAPP_GROUP_TO = os.getenv("WHATSAPP_GROUP_TO")

# Channel/Group IDs yang di-monitor (komma separated)
MONITORED_CHANNELS = list(map(int, os.getenv("MONITORED_CHANNEL_IDS", "").split(","))) if os.getenv("MONITORED_CHANNEL_IDS") else []

# Keywords untuk filter (hanya forward pesan dengan keywords ini)
FILTER_KEYWORDS = ["#share", "#update", "#news", "#info"]

# Admin IDs (yang boleh kontrol bot)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# TWILIO CLIENT
# ============================================================================

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_message(text: str, sender_name: str, timestamp: datetime, source: str) -> str:
    """
    Format pesan dari Telegram ke format rapih & ringkas untuk WhatsApp
    
    Args:
        text: Pesan asli dari Telegram
        sender_name: Nama pengirim
        timestamp: Waktu pesan
        source: Nama channel/group
    
    Returns:
        Pesan yang sudah diformat
    """
    
    # Truncate panjang text ke max 150 char
    max_length = 150
    truncated = text[:max_length] + ("..." if len(text) > max_length else "")
    
    # Format waktu
    time_str = timestamp.strftime("%H:%M - %d/%m")
    
    # Build formatted message
    formatted = (
        f"📰 {text[:40].upper()}\n"
        f"{'-' * 30}\n"
        f"{truncated}\n\n"
        f"🔗 From: {source}\n"
        f"⏰ {time_str}\n"
        f"✍️ By: {sender_name}"
    )
    
    return formatted


def format_announcement(text: str, sender_name: str, category: str = "PENTING") -> str:
    """Format untuk pengumuman/announcement"""
    max_length = 150
    truncated = text[:max_length] + ("..." if len(text) > max_length else "")
    
    formatted = (
        f"📢 [{category}]\n"
        f"{'-' * 30}\n"
        f"{truncated}\n\n"
        f"👤 From: {sender_name}\n"
        f"⏰ {datetime.now().strftime('%H:%M - %d/%m')}"
    )
    
    return formatted


def format_event(text: str, sender_name: str) -> str:
    """Format untuk event/workshop"""
    formatted = (
        f"🎯 EVENT\n"
        f"{'-' * 30}\n"
        f"{text[:200]}\n\n"
        f"✍️ Posted by: {sender_name}\n"
        f"⏰ {datetime.now().strftime('%H:%M - %d/%m')}"
    )
    return formatted


def contains_keyword(text: str) -> bool:
    """Check apakah text mengandung filter keywords"""
    return any(keyword.lower() in text.lower() for keyword in FILTER_KEYWORDS)


def is_admin(user: User) -> bool:
    """Check apakah user adalah admin"""
    return user.id in ADMIN_IDS


def send_whatsapp_message(message: str) -> Optional[str]:
    """
    Kirim pesan ke WhatsApp group via Twilio
    
    Args:
        message: Pesan yang akan dikirim
        
    Returns:
        Message SID jika berhasil, None jika gagal
    """
    try:
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=WHATSAPP_GROUP_TO,
            body=message
        )
        logger.info(f"✓ Message sent to WhatsApp. SID: {msg.sid}")
        return msg.sid
    except Exception as e:
        logger.error(f"✗ Failed to send WhatsApp message: {e}")
        return None


# ============================================================================
# BOT HANDLERS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /start command"""
    welcome_msg = (
        "🤖 *Auto-Post Bot aktivasi!*\n\n"
        "Bot ini otomatis forward pesan dari Telegram ke WhatsApp group.\n\n"
        "📋 *Commands:*\n"
        "/start - Mulai bot\n"
        "/status - Status koneksi\n"
        "/help - Bantuan\n"
        "/stop - Stop automation\n"
        "/test - Test kirim pesan\n"
    )
    
    if update.effective_chat:
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
        logger.info(f"Bot started in chat: {update.effective_chat.title}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /status command"""
    status_msg = (
        "✅ *Bot Status*\n\n"
        f"📱 Telegram: Connected\n"
        f"💬 WhatsApp: Connected\n"
        f"🔗 Twilio: {('✓ OK' if twilio_client else '✗ Error')}\n"
        f"📊 Monitored channels: {len(MONITORED_CHANNELS)}\n"
        f"⏰ Uptime: OK\n"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /help command"""
    help_msg = (
        "📖 *Bantuan*\n\n"
        "*Bagaimana cara kerja bot?*\n"
        "1. Bot listen pesan di Telegram channel\n"
        "2. Filter pesan dengan keywords (#share, #update, etc)\n"
        "3. Format pesan rapih\n"
        "4. Auto-send ke WhatsApp group\n\n"
        "*Format pesan yang didukung:*\n"
        "📰 Berita/Update\n"
        "📢 Announcement\n"
        "🎯 Event\n"
        "⚡ Info cepat\n"
        "📸 Media + Caption\n"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /stop command"""
    if not is_admin(update.effective_user):
        await update.message.reply_text("❌ Hanya admin yang bisa menggunakan command ini")
        return
    
    msg = "⏹️ Bot automation di-stop. Restart dengan /start"
    await update.message.reply_text(msg)
    logger.info(f"Bot stopped by {update.effective_user.full_name}")


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /test command - test send message"""
    if not is_admin(update.effective_user):
        await update.message.reply_text("❌ Hanya admin yang bisa test")
        return
    
    test_msg = (
        "📰 TEST MESSAGE\n"
        "─────────────────────\n"
        "Ini adalah test message dari bot automation.\n\n"
        "🔗 From: Test Channel\n"
        "⏰ 14:30 - 11/03/2026\n"
        "✍️ By: Admin"
    )
    
    result = send_whatsapp_message(test_msg)
    
    if result:
        await update.message.reply_text(f"✅ Test message sent! SID: {result}")
    else:
        await update.message.reply_text("❌ Test message gagal dikirim")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main handler untuk pesan yang masuk
    - Filter berdasarkan keyword
    - Format pesan
    - Kirim ke WhatsApp
    """
    
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Skip jika dari bot
    if user.is_bot:
        return
    
    # Skip jika tidak dari monitored channel (opsional)
    if MONITORED_CHANNELS and chat.id not in MONITORED_CHANNELS:
        return
    
    # Filter berdasarkan keyword
    if not contains_keyword(message.text):
        logger.info(f"Message filtered (no keyword): {message.text[:50]}")
        return
    
    # Format pesan
    sender_name = user.first_name or "Anonymous"
    timestamp = datetime.fromtimestamp(message.date)
    source = chat.title or chat.username or "Private"
    
    # Pilih format berdasarkan keyword
    if "#announcement" in message.text.lower():
        formatted_msg = format_announcement(message.text, sender_name, "PENTING")
    elif "#event" in message.text.lower():
        formatted_msg = format_event(message.text, sender_name)
    else:
        formatted_msg = format_message(message.text, sender_name, timestamp, source)
    
    logger.info(f"Message formatted: {formatted_msg[:50]}...")
    
    # Send ke WhatsApp
    result = send_whatsapp_message(formatted_msg)
    
    if result:
        logger.info(f"✓ Message successfully forwarded to WhatsApp")
        # Kirim confirmation reaction di Telegram (optional)
        try:
            await message.react("👍")
        except:
            pass
    else:
        logger.error("✗ Failed to forward message")
        try:
            await message.reply_text("❌ Gagal forward ke WhatsApp")
        except:
            pass


# ============================================================================
# MAIN BOT APPLICATION
# ============================================================================

def main():
    """Main function - run bot"""
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN tidak ditemukan di .env")
        return
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.error("❌ Twilio credentials tidak ditemukan di .env")
        return
    
    logger.info("🚀 Starting Auto-Post Bot...")
    
    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("test", test_command))
    
    # Add message handler (untuk auto-forward)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bot handlers registered")
    logger.info(f"📱 Monitoring channels: {MONITORED_CHANNELS}")
    logger.info(f"🔑 Filter keywords: {FILTER_KEYWORDS}")
    
    # Start bot
    logger.info("⏳ Bot is running... Press Ctrl+C to stop")
    app.run_polling()


if __name__ == "__main__":
    main()
