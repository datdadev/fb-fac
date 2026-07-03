import os

# Helper to load a local .env file if it exists, avoiding third-party packages
def _load_env_file(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

_load_env_file()

# Telegram Settings (Leave empty if not using)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Discord Settings (Leave empty if not using)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Keywords to match in posts
KEYWORDS = [
    "in 3D",
    "in 3d",
    "thiết kế 3D",
    "thiết kế 3d",
    "3d print",
    "mẫu 3D",
    "mẫu 3d"
]

# Time to wait between checks (in seconds)
CHECK_INTERVAL = 60

# Commenting Configuration
COMMENT_MODE = os.environ.get("COMMENT_MODE", "interactive")  # 'interactive' or 'auto'
DEFAULT_COMMENT = os.environ.get("DEFAULT_COMMENT", "Chào bạn, bên mình chuyên nhận thiết kế và in 3D chất lượng cao tại HCM và HN. Bạn check tin nhắn chờ/inbox mình trao đổi chi tiết nhé!")
COMMENT_DELAY_MIN = int(os.environ.get("COMMENT_DELAY_MIN", "15"))
COMMENT_DELAY_MAX = int(os.environ.get("COMMENT_DELAY_MAX", "45"))

