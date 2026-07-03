import json
import urllib.request
import urllib.parse
import config

def send_discord_alert(title, description, url):
    """
    Sends a rich embed message to a Discord Webhook.
    """
    if not config.DISCORD_WEBHOOK_URL:
        print("[Notifier] Discord webhook URL not configured. Skipping Discord alert.")
        return False

    payload = {
        "embeds": [
            {
                "title": f"🔔 New Lead Found: {title}",
                "description": description,
                "url": url,
                "color": 3447003,  # Blue color
                "fields": [
                    {
                        "name": "Action Required",
                        "value": f"[Click here to open and review the post]({url})"
                    }
                ],
                "footer": {
                    "text": "3D Printing Service Lead Notifier"
                }
            }
        ]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            config.DISCORD_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 204]:
                print("[Notifier] Discord alert sent successfully.")
                return True
            else:
                print(f"[Notifier] Discord alert returned status code: {response.status}")
                return False
    except Exception as e:
        print(f"[Notifier] Error sending Discord alert: {e}")
        return False

def send_telegram_alert(title, description, url):
    """
    Sends a message to a Telegram chat/channel using a bot token.
    """
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[Notifier] Telegram Token or Chat ID not configured. Skipping Telegram alert.")
        return False

    # Format message in Markdown
    text = (
        f"🔔 *New Lead Found*\n\n"
        f"*Topic:* {title}\n"
        f"*Content:* {description}\n\n"
        f"🔗 [Link to post]({url})"
    )

    # Use inline keyboard for a cleaner interface
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "💬 Open Post", "url": url}
            ]
        ]
    }

    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }

    telegram_url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            telegram_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("ok"):
                print("[Notifier] Telegram alert sent successfully.")
                return True
            else:
                print(f"[Notifier] Telegram API error: {result.get('description')}")
                return False
    except Exception as e:
        print(f"[Notifier] Error sending Telegram alert: {e}")
        return False

def send_alert(title, description, url):
    """
    Convenience function to send alerts to all configured channels.
    """
    discord_success = send_discord_alert(title, description, url)
    telegram_success = send_telegram_alert(title, description, url)
    return discord_success or telegram_success
