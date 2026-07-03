# Facebook Find And Comment (FB-FAC)

An automated tool designed to **Find And Comment (FAC)** on Facebook posts matching specific campaign keywords. It crawls search results, de-scrambles obfuscated timestamps, extracts target post details, analyzes relevancy, and automatically posts language-specific comments with uploader attachments.

## Key Features

- **Multi-Campaign Architecture**: Configure and run multiple marketing campaigns (e.g. `3d_printing`, `meccha_chameleon`) dynamically from `keywords.json` and `comment_templates.json`.
- **Intelligent Commenting & Localization**: Automatically detects the language of a post (supports Vietnamese, English, Thai, and default fallbacks) and selects the corresponding comment template.
- **Auto Image Uploader**: Locates the file uploader in comment sections and attaches campaign-specific images (e.g., `pic1.png`) before submitting.
- **Computed-Style Timestamp De-scrambler**: Bypasses Facebook's anti-scraping scrambling spans (screen-reader decoy text $\le$ 1px) using window computed styles to extract clean, visual timestamps (e.g., `9h`, `2 ngày`).
- **Post ID & Hash Resolving**: Extracts post IDs from permalinks, group set/photo parameters (`set=pcb.`, `fbid=`), or falls back to hashing the cryptographic `__cft__` token parameter to prevent duplicate comments.
- **Rich Alerts**: Integrates Discord webhooks and Telegram alerts to notify you about matching leads.

---

## Project Structure

- `main.py`: Interactive CLI tool entry point to manage login methods, select campaigns, and trigger the pipelines.
- `facebook_monitor.py`: Core monitor class handling scrolling, "See more" expansion, post card visual screenshot cropping, and automated commenting.
- `fb_auth.py`: Session management module handling cookies (`facebook_cookies.pkl`), credentials, and interactive manual login helper windows.
- `ai_analyzer.py`: Optional Gemini AI relevance classifier and custom query scorer.
- `comment_templates.json`: Customizable language-specific templates mapped by campaign profile.
- `keywords.json`: Keyword files categorized by campaign profile.

---

## Setup & Configuration

1. **Install Dependencies**:
   Ensure you have Python 3.8+ and Selenium Chrome WebDriver installed.
   ```bash
   pip install selenium python-dotenv
   ```
2. **Environment Variables (`.env`)**:
   Create a `.env` file based on `.env.example`:
   ```env
   FACEBOOK_EMAIL=your_email@example.com
   FACEBOOK_PASSWORD=your_password
   COMMENT_MODE=auto       # 'auto' or 'interactive'
   COMMENT_DELAY_MIN=15
   COMMENT_DELAY_MAX=45
   TELEGRAM_TOKEN=
   TELEGRAM_CHAT_ID=
   DISCORD_WEBHOOK_URL=
   ```

---

## How to Run

1. **Start the Application**:
   ```bash
   python main.py
   ```
2. **Choose Authentication Method**:
   - `1`: Use saved cookies (`facebook_cookies.pkl`) for silent login.
   - `2`: Refresh session / manual login. If the saved cookies have expired, this option opens Chrome, lets you log in manually, and saves fresh cookies to file.
3. **Select Campaign & Trigger Pipeline**:
   Choose the campaign (e.g., Choice 2 for *Meccha Chameleon*), select choice `3` for **Full Pipeline**, and let the script find, crop, analyze, and post comments automatically!
