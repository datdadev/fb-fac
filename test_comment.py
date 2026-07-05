import sys
import io
from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor

# Hỗ trợ hiển thị tiếng Việt trên Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)
    except Exception:
        pass

def test_comment():
    print("="*60)
    print("🧪 CÔNG CỤ TEST COMMENT TRỰC TIẾP")
    print("="*60)
    
    url = input("Nhập URL bài viết Facebook cần test: ").strip()
    if not url:
        print("Không có URL. Thoát.")
        return

    text = input("Nhập nội dung bình luận (để trống sẽ dùng mặc định): ").strip()
    if not text:
        text = "Chào bạn, bên mình chuyên nhận thiết kế và in 3D chất lượng cao. Bạn check tin nhắn chờ nhé!"

    print("\n[Đang khởi động trình duyệt và đăng nhập bằng cookies...]")
    auth = FacebookAuth()
    success, driver = auth.authenticate()
    
    if not success:
        print("❌ Lỗi đăng nhập!")
        return
        
    try:
        # Chọn campaign 3d_printing để không bắt buộc đính kèm ảnh như chameleon
        monitor = FacebookMonitor(driver, campaign="3d_printing")
        
        print("\n⏳ Đang tiến hành bình luận...")
        result = monitor._comment_on_single_post(url, text)
        
        if result:
            print("\n✅ COMMENT THÀNH CÔNG!")
        else:
            print("\n❌ COMMENT THẤT BẠI! Hãy kiểm tra file comment_failed.png")
            
    finally:
        print("="*60)
        input("Nhấn Enter để đóng trình duyệt và kết thúc...")
        auth.close()

if __name__ == "__main__":
    test_comment()
