import sys
import io
import time
import json
import builtins
from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor

# Force UTF-8 encoding for stdout/stderr on Windows to support emojis and Vietnamese characters
if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8-sig', errors='replace', write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8-sig', errors='replace', write_through=True)
    except Exception:
        pass


# Global override for input to prevent blocking/errors in non-interactive environments
_original_input = builtins.input

def safe_input(prompt=""):
    if not sys.stdin.isatty():
        # Clean print when prompt ends with whitespace
        print(f"{prompt.rstrip()} [Non-interactive: returning empty]")
        return ""
    try:
        return _original_input(prompt)
    except (EOFError, OSError):
        print(f"{prompt.rstrip()} [EOF/OSError: returning empty]")
        return ""

builtins.input = safe_input


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Facebook Post Monitor with AI Analysis")
    parser.add_argument("--login", type=str, choices=["1", "2"], default=None, help="Login method: 1 = Cookies, 2 = Credentials")
    parser.add_argument("--campaign", type=str, choices=["3d_printing", "meccha_chameleon"], default=None, help="Campaign: 3d_printing, meccha_chameleon")
    parser.add_argument("--action", type=str, choices=["1", "2", "3", "4", "5", "6"], default=None, help="Action: 1-6")
    parser.add_argument("--scrolls", type=int, default=None, help="Number of scrolls")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum relevance score")
    args = parser.parse_args()

    print("="*60)
    print("=== FACEBOOK POST MONITOR WITH AI ANALYSIS ===")
    print("="*60)
    
    # 1. Login choice
    if args.login:
        login_choice = args.login
    else:
        print("\n=== LỰA CHỌN PHƯƠNG THỨC ĐĂNG NHẬP ===")
        print("1. Sử dụng Cookies đã lưu (Nhanh nhất, bỏ qua 2FA nếu đã đăng nhập thành công)")
        print("2. Đăng nhập lại từ đầu bằng Email/Password (Bắt buộc phải nhập lại mã 2FA)")
        login_choice = input("Chọn phương thức (1-2, mặc định là 1): ").strip()
        if not login_choice:
            login_choice = "1"
            
    force_login = (login_choice == "2")
    
    # Initialize auth
    auth = FacebookAuth()
    
    try:
        # Authenticate
        success, driver = auth.authenticate(force_login=force_login)
        
        if not success:
            print("❌ Failed to authenticate session.")
            return
        
        # 2. Campaign choice
        if args.campaign:
            if args.campaign == "meccha_chameleon":
                camp_choice = "2"
            else:
                camp_choice = "1"
        else:
            camp_choice = input("Chọn chiến dịch (1-2, mặc định là 1): ").strip()
            if not camp_choice:
                camp_choice = "1"
        
        if camp_choice == "2" or camp_choice == "meccha_chameleon":
            campaign = "meccha_chameleon"
            print("🦎 Đã chọn: Chiến dịch bán mô hình Meccha Chameleon")
        else:
            campaign = "3d_printing"
            print("🖨️ Đã chọn: Chiến dịch quảng cáo Dịch vụ In 3D")
            
        # Create monitor
        monitor = FacebookMonitor(driver, campaign=campaign)
        monitor.load_keywords('keywords.json')
        
        # Determine if we run in interactive menu or run single action
        is_interactive = sys.stdin.isatty() and (args.action is None)
        
        if not is_interactive:
            # Non-interactive mode: run the specified action or default to action "3" (Full Pipeline)
            choice = args.action if args.action else "3"
            print(f"\n🤖 Running non-interactive action: {choice}")
            
            if choice == "1":
                max_scroll = args.scrolls if args.scrolls is not None else 3
                posts = monitor.search(max_scroll)
                if posts:
                    monitor.analyze_posts()
            elif choice == "2":
                min_score = args.min_score if args.min_score is not None else 0.6
                # Search first if not done
                if not monitor.analyzed_posts:
                    max_scroll = args.scrolls if args.scrolls is not None else 3
                    posts = monitor.search(max_scroll)
                    if posts:
                        monitor.analyze_posts()
                monitor.notify_posts(min_score=min_score)
            elif choice == "3":
                max_scroll = args.scrolls if args.scrolls is not None else 3
                min_score = args.min_score if args.min_score is not None else 0.6
                results = monitor.run(max_scroll, min_score)
                with open('monitor_results.json', 'w', encoding='utf-8-sig') as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)
                print("✅ Results saved to monitor_results.json")
            elif choice == "4":
                min_score = args.min_score if args.min_score is not None else 0.6
                # Search and analyze first if not done
                if not monitor.analyzed_posts:
                    max_scroll = args.scrolls if args.scrolls is not None else 3
                    posts = monitor.search(max_scroll)
                    if posts:
                        monitor.analyze_posts()
                posts_to_comment = [p for p in monitor.analyzed_posts if p.get('relevance_score', 0) >= min_score]
                if posts_to_comment:
                    monitor.comment_on_posts(posts_to_comment)
            elif choice == "5":
                print("\n📊 RESULTS SUMMARY (Non-interactive):")
                print(f"  Total posts found: {len(monitor.found_posts)}")
            return
            
        # Show menu (Interactive mode)
        while True:
            print("\n" + "="*60)
            print("🛠️  SELECT ACTION")
            print("="*60)
            print("1. 🔍 Search & Analyze Posts")
            print("2. 📨 Notify Found Posts")
            print("3. 🤖 Full Pipeline (Search+Analyze+Notify+Comment)")
            print("4. 💬 Comment on Found/Analyzed Posts")
            print("5. 📊 Show Results")
            print("6. 📰 Lướt Bảng Tin (News Feed) & Auto Comment")
            print("7. 🚪 Exit")
            print("="*60)
            
            choice = input("Enter choice (1-7): ").strip()
            
            if choice == "1":
                max_scroll = int(input("Number of scrolls (default 3): ") or "3")
                posts = monitor.search(max_scroll)
                if posts:
                    monitor.analyze_posts()
                else:
                    print("❌ No posts found")
                    
            elif choice == "2":
                if not monitor.analyzed_posts:
                    print("❌ No analyzed posts. Please run search first.")
                else:
                    min_score = float(input("Minimum score (default 0.6): ") or "0.6")
                    monitor.notify_posts(min_score=min_score)
                    
            elif choice == "3":
                max_scroll = int(input("Number of scrolls (default 3): ") or "3")
                min_score = float(input("Minimum score (default 0.6): ") or "0.6")
                results = monitor.run(max_scroll, min_score)
                
                # Save results
                with open('monitor_results.json', 'w', encoding='utf-8-sig') as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)
                print("✅ Results saved to monitor_results.json")
                
            elif choice == "4":
                # Comment on found/analyzed posts
                posts_to_comment = []
                if monitor.analyzed_posts:
                    min_score = float(input("Minimum AI relevance score to comment (default 0.6, enter 0 for all): ") or "0.6")
                    posts_to_comment = [p for p in monitor.analyzed_posts if p.get('relevance_score', 0) >= min_score]
                elif monitor.found_posts:
                    print("⚠️ Posts have not been analyzed by AI. Commenting on all matching posts.")
                    posts_to_comment = monitor.found_posts
                else:
                    print("❌ No posts found. Please run search first.")
                    continue
                
                if posts_to_comment:
                    monitor.comment_on_posts(posts_to_comment)
                else:
                    print("❌ No posts matched the score threshold.")
                    
            elif choice == "5":
                print("\n📊 RESULTS SUMMARY:")
                print(f"  Total posts found: {len(monitor.found_posts)}")
                print(f"  Analyzed posts: {len(monitor.analyzed_posts)}")
                
                if monitor.analyzed_posts:
                    high_relevance = [p for p in monitor.analyzed_posts if p.get('relevance_score', 0) >= 0.6]
                    print(f"  High relevance posts: {len(high_relevance)}")
                    
                    print("\n  📝 Posts with high relevance:")
                    for post in high_relevance[:5]:
                        print(f"  - {post.get('author', 'Unknown')}: {post.get('text', '')[:50]}... (Score: {post.get('relevance_score', 0):.2f})")
                    
            elif choice == "6":
                max_scroll = int(input("Number of scrolls on News Feed (default 10): ") or "10")
                min_score = float(input("Minimum score to comment (default 0.6): ") or "0.6")
                posts = monitor.monitor_news_feed(max_scroll=max_scroll, min_score=min_score)
                if not posts:
                    print("❌ No matching posts found on News Feed")

            elif choice == "7":
                print("\n👋 Exiting...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-7")
                
    except Exception as e:
        print(f"❌ Main Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        auth.close()
        print("✅ Browser closed.")


if __name__ == "__main__":
    main()
