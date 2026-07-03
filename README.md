# 3D Printing Service Lead Notifier

An automated monitoring and alert system that checks matching posts for specific keywords (e.g., "in 3D", "thiết kế 3D") and notifies you via Telegram or Discord, letting you review leads and respond via direct links.

## Project Structure

- `config.py`: Configuration for target keywords, Telegram Bot credentials, and Discord Webhooks.
- `notifier.py`: Code for formatting and sending rich message alerts.
- `monitor.py`: The check loop that retrieves content, filters matches, handles deduplication, and records state to `seen_posts.json`.

## Quick Start

### 1. Configuration

Open `config.py` and populate the fields for your alert channels:

- **Discord**:
  1. Edit Channel -> Integrations -> Webhooks -> Create Webhook.
  2. Copy Webhook URL and paste into `DISCORD_WEBHOOK_URL`.

- **Telegram**:
  1. Chat with `@BotFather` to create a bot and get a token. Paste into `TELEGRAM_TOKEN`.
  2. Chat with `@userinfobot` to retrieve your Chat ID. Paste into `TELEGRAM_CHAT_ID`.

### 2. Execution

To run the notifier loop:

```powershell
# Set UTF-8 encoding (required on Windows to print Vietnamese characters without errors)
$env:PYTHONIOENCODING="utf-8"

# Start the monitoring service
python monitor.py
```

---

## Technical Note: Handling Session Authentication

To integrate browser automated checks without repeatedly entering login credentials:

1. **Persistent Browser Profiles**:
   Instead of using automated script steps to submit username/password fields, automation frameworks are typically configured to point to a local browser profile directory (e.g., Chrome's `--user-data-dir`).
   
2. **Session Preservation**:
   By logging in manually once inside that profile, the session cookies are saved locally. Subsequent runs of the script use that same directory, allowing the browser to load pages in an authenticated state automatically.
