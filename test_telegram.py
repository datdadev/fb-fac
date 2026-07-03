import sys
import config
import notifier

def main():
    print("--- Telegram Integration Test ---")
    print(f"Loaded Token: {config.TELEGRAM_TOKEN[:10]}... (Total length: {len(config.TELEGRAM_TOKEN)})" if config.TELEGRAM_TOKEN else "Loaded Token: None")
    print(f"Loaded Chat ID: {config.TELEGRAM_CHAT_ID}" if config.TELEGRAM_CHAT_ID else "Loaded Chat ID: None")
    
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("\n[Error] Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID in your .env file.")
        print("Please configure them in the '.env' file first.")
        sys.exit(1)
        
    print("\nSending test alert...")
    success = notifier.send_telegram_alert(
        title="[Test] 3D Print Lead",
        description="Testing the Telegram notification bot channel. If you see this, your setup is working!",
        url="https://facebook.com"
    )
    
    if success:
        print("\n[Success] Test message sent successfully! Check your Telegram chat.")
    else:
        print("\n[Failed] Could not send test message. Check the logs above for details.")

if __name__ == "__main__":
    main()
