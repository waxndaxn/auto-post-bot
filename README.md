# 📰 Telegram → WhatsApp News Bot

Bot otomatis yang memforward berita dari **channel Telegram publik** ke **grup WhatsApp** dengan format ringkas dan anti-duplikat.

## Stack
- **Replit** — hosting server Flask (auto-deploy dari GitHub)
- **Make.com** — monitor channel Telegram publik (no-code)
- **Fonnte** — pengirim pesan WhatsApp via API

## Arsitektur
```
Telegram Channel (publik)
        ↓
   Make.com (Watch Posts / RSS)
        ↓
   Replit Flask Server  ← /webhook/make
        ↓
   Fonnte API
        ↓
   WhatsApp Group
```

## Format Pesan WA
```
📰 *Judul Berita*
Deskripsi singkat satu baris di sini…
🔗 https://link-berita.com
_📡 Nama Channel • 11 Mar 2025 14:32_
```

## Setup

### 1. Replit Secrets (Environment Variables)
| Key | Keterangan |
|---|---|
| `TELEGRAM_TOKEN` | Token dari BotFather |
| `FONNTE_TOKEN` | API Token dari Fonnte |
| `WA_TARGET` | Group ID WA (dari perintah `/groupid` di Fonnte) |
| `MAKE_SECRET` | Password bebas untuk autentikasi Make.com |

### 2. Hubungkan GitHub → Replit
1. Di Replit: **Version Control** → **Connect to GitHub**
2. Pilih repo ini
3. Aktifkan **Auto-deploy on push** ✅

### 3. Make.com Scenario
- Modul 1: **Telegram Bot → Watch Channel Posts** (atau RSS Feed)
- Modul 2: **HTTP → Make a Request** ke `https://[replit-url]/webhook/make`
  - Header: `X-Secret: [MAKE_SECRET]`
  - Body JSON:
    ```json
    {
      "title": "{{1.text | truncate: 100}}",
      "desc": "{{1.text | truncate: 160}}",
      "url": "{{1.entities[].url}}",
      "source": "{{1.chat.title}}"
    }
    ```

### 4. RSS Feed (alternatif Make.com)
Gunakan modul **RSS → Watch RSS Feed** dengan URL:
```
https://rsshub.app/telegram/channel/@username_channel
```

## Endpoints
| Endpoint | Method | Fungsi |
|---|---|---|
| `/` | GET | Status bot |
| `/health` | GET | Health check (untuk UptimeRobot) |
| `/webhook/telegram` | POST | Webhook langsung dari Telegram |
| `/webhook/make` | POST | Webhook dari Make.com |
| `/test` | POST | Kirim pesan test ke WA |

## Keep Alive (Replit Gratis)
Daftarkan URL `/health` ke [UptimeRobot](https://uptimerobot.com) dengan interval **5 menit** agar Replit tidak sleep.
