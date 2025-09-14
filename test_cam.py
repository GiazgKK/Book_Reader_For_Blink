import cv2
from pathlib import Path

# Khởi tạo camera
cap = cv2.VideoCapture(0)  # 0 = camera mặc định

if not cap.isOpened():
    print("❌ Không mở được camera")
    exit()

print("✅ Camera sẵn sàng. Nhấn ENTER để chụp, ESC để thoát.")

# Đường dẫn file output
output_path = Path(__file__).parent / "output.jpg"

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Không lấy được khung hình")
        break

    cv2.imshow("Camera Preview", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 13:  # ENTER
        cv2.imwrite(str(output_path), frame)
        print(f"📸 Đã chụp và lưu ảnh: {output_path}")

    elif key == 27:  # ESC
        print("🛑 Thoát.")
        break

cap.release()
cv2.destroyAllWindows()
