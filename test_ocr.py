import pytesseract
from PIL import Image
from pathlib import Path
import pyttsx3

# Đường dẫn ảnh output.jpg
image_path = Path(__file__).parent / "output.jpg"

if not image_path.exists():
    print(f"❌ Không tìm thấy file ảnh: {image_path}")
    exit()

print(f"🖼️ Đang OCR ảnh: {image_path}")

try:
    # OCR với tiếng Anh (đổi "eng" -> "vie" nếu cần đọc tiếng Việt)
    text = pytesseract.image_to_string(Image.open(image_path), lang="eng").strip()

    if text:
        print("📖 Kết quả OCR:\n", text)

        # Khởi tạo TTS
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)   # tốc độ đọc
        engine.setProperty("volume", 1.0) # âm lượng

        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)

        print("🔊 Đang đọc văn bản...")
        engine.say(text)
        engine.runAndWait()
        print("✅ Đọc xong.")
    else:
        print("⚠️ OCR không tìm thấy văn bản.")
        engine = pyttsx3.init()
        engine.say("Không tìm thấy văn bản trong ảnh.")
        engine.runAndWait()

except Exception as e:
    print("❌ Lỗi khi OCR hoặc TTS:", e)
