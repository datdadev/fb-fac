"""
Main Application with AI Analysis
"""

import time
import json
from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor

def main():
    print("="*60)
    print("=== FACEBOOK POST MONITOR WITH AI ANALYSIS ===")
    print("="*60)
    
    # Select Authentication Method
    print("\n" + "="*60)
    print("🔑 PHƯƠNG THỨC ĐĂNG NHẬP (LOGIN METHOD)")
    print("="*60)
    print("1. 🍪 Sử dụng Cookies sẵn có (facebook_cookies.pkl)")
    print("2. 👤 Đăng nhập bằng tài khoản .env / Đăng nhập thủ công")
    print("="*60)
    login_choice = input("Chọn phương thức (1-2, mặc định là 1): ").strip()
    
    force_login = (login_choice == "2")
    
    # Initialize auth
    auth = FacebookAuth()
    
    try:
        # Authenticate
        success, driver = auth.authenticate(force_login=force_login)
        
        if not success:
            print("❌ Failed to authenticate session.")
            return
        
        # Select Campaign
        print("\n" + "="*60)
        print("🎯 LỰA CHỌN CHIẾN DỊCH (SELECT CAMPAIGN)")
        print("="*60)
        print("1. 🖨️ Dịch vụ In 3D (3D Printing Service)")
        print("2. 🦎 Mô hình Meccha Chameleon (Meccha Chameleon Figures)")
        print("="*60)
        camp_choice = input("Chọn chiến dịch (1-2, mặc định là 1): ").strip()
        
        if camp_choice == "2":
            campaign = "meccha_chameleon"
            print("🦎 Đã chọn: Chiến dịch bán mô hình Meccha Chameleon")
        else:
            campaign = "3d_printing"
            print("🖨️ Đã chọn: Chiến dịch quảng cáo Dịch vụ In 3D")
            
        # Create monitor
        monitor = FacebookMonitor(driver, campaign=campaign)
        monitor.load_keywords('keywords.json')
        
        # Show menu
        while True:
            print("\n" + "="*60)
            print("🛠️  SELECT ACTION")
            print("="*60)
            print("1. 🔍 Search & Analyze Posts")
            print("2. 📨 Notify Found Posts")
            print("3. 🤖 Full Pipeline (Search+Analyze+Notify+Comment)")
            print("4. 💬 Comment on Found/Analyzed Posts")
            print("5. 📊 Show Results")
            print("6. 🚪 Exit")
            print("="*60)
            
            choice = input("Enter choice (1-6): ").strip()
            
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
                with open('monitor_results.json', 'w', encoding='utf-8') as f:
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
                print("\n👋 Exiting...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-6")
                
    except Exception as e:
        print(f"❌ Main Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        auth.close()
        print("✅ Browser closed.")

if __name__ == "__main__":
    main()