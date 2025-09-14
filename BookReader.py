#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BookReader: Kiểm thử pipeline Camera -> OCR -> TTS trên Raspberry Pi 4
- Có preview camera bằng OpenCV
- Điều khiển bằng phím: Enter = chụp & đọc, 'q' + Enter = thoát
"""
import sys
import signal
import tempfile
import logging
import time
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
    import pytesseract
    import pyttsx3
    import cv2
except Exception as e:
    print("Thiếu thư viện Python. Hãy tạo venv và cài: pip install pytesseract pillow pyttsx3 opencv-python")
    raise

# =========================
# Cấu hình kỹ thuật
# =========================
CONFIG = {
    "OCR_LANG": "vie+eng",    # "vie", "eng" hoặc "vie+eng"
    "TESSERACT_PSM": "3",     # 3 = fully automatic, 6 = single column
    "TESSERACT_OEM": "3",
    "OCR_DPI": 300,
    "TTS_RATE": 165,
    "TTS_VOLUME": 1.0,
    "CAM_INDEX": 0,           # /dev/video0
    "CAM_WIDTH": 1280,
    "CAM_HEIGHT": 720,
}

# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("BookReader")

# =========================
# TTS
# =========================
def init_tts():
    engine = pyttsx3.init()
    engine.setProperty("rate", CONFIG["TTS_RATE"])
    engine.setProperty("volume", CONFIG["TTS_VOLUME"])
    # Thử chọn giọng tiếng Việt nếu có
    try:
        for v in engine.getProperty("voices"):
            name = (v.name or "").lower()
            langs = [str(x).lower() for x in (v.languages or [])]
            if "vietnam" in name or "vie" in name or "vi_" in name or "vi" in langs:
                engine.setProperty("voice", v.id)
                break
    except Exception:
        pass
    return engine

def speak(engine, text: str):
    if not text:
        text = "Không có nội dung để đọc."
    engine.say(text)
    engine.runAndWait()

# =========================
# Camera capture with preview
# =========================
def capture_image_with_preview(tmpdir: Path) -> Path:
    """
    Mở preview bằng OpenCV, nhấn Enter để chụp, ESC để hủy.
    Ảnh được lưu vào file tạm và trả về đường dẫn.
    """
    cap = cv2.VideoCapture(CONFIG["CAM_INDEX"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG["CAM_WIDTH"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["CAM_HEIGHT"])

    if not cap.isOpened():
        raise RuntimeError("Không mở được camera")

    cv2.namedWindow("Camera Preview", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Preview", CONFIG["CAM_WIDTH"], CONFIG["CAM_HEIGHT"])

    img_path = tmpdir / f"capture_{int(time.time()*1000)}.jpg"
    captured = False
    frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow("Camera Preview", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 13:  # Enter
            captured = True
            break
        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

    if captured and frame is not None:
        cv2.imwrite(str(img_path), frame)
        log.info("Đã chụp ảnh: %s", img_path)
        return img_path
    else:
        raise RuntimeError("Chưa chụp ảnh nào")

# =========================
# OCR
# =========================
def ocr_image(img_path: Path) -> str:
    img = Image.open(img_path)
    img = img.convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img = ImageEnhance.Sharpness(img).enhance(1.2)

    custom = f'--oem {CONFIG["TESSERACT_OEM"]} --psm {CONFIG["TESSERACT_PSM"]} -l {CONFIG["OCR_LANG"]} --dpi {CONFIG["OCR_DPI"]}'
    text = pytesseract.image_to_string(img, config=custom)
    return text.strip()

# =========================
# Thoát gọn
# =========================
def graceful_exit(engine=None, tmpdir: Path = None):
    try:
        if engine:
            engine.stop()
    except Exception:
        pass
    try:
        if tmpdir and tmpdir.exists():
            for f in tmpdir.glob("capture_*.jpg"):
                f.unlink(missing_ok=True)
            tmpdir.rmdir()
    except Exception:
        pass
    log.info("Thoát chương trình an toàn.")
    sys.exit(0)

def signal_handler(sig, frame):
    log.info("Nhận tín hiệu dừng (%s).", sig)
    graceful_exit()

# =========================
# Main
# =========================
def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    engine = init_tts()
    tmpdir = Path(tempfile.mkdtemp(prefix="bookreader_"))

    intro = (
        "Xin chào. Hệ thống đọc sách đã sẵn sàng. "
        "Một cửa sổ preview sẽ mở ra. "
        "Nhấn Enter để chụp, Esc để hủy, gõ q rồi Enter để thoát."
    )
    print(intro)
    speak(engine, intro)

    while True:
        try:
            user = input("> ")
        except (EOFError, KeyboardInterrupt):
            graceful_exit(engine, tmpdir)

        if user.lower().strip() == "q":
            speak(engine, "Tạm biệt.")
            graceful_exit(engine, tmpdir)

        speak(engine, "Mở camera preview.")
        try:
            img_path = capture_image_with_preview(tmpdir)
        except Exception as e:
            log.error("Lỗi chụp ảnh: %s", e)
            speak(engine, "Không thể chụp ảnh. Kiểm tra camera.")
            continue

        speak(engine, "Đang nhận dạng văn bản.")
        try:
            text = ocr_image(img_path)
        except Exception as e:
            log.error("Lỗi OCR: %s", e)
            speak(engine, "Lỗi nhận dạng văn bản.")
            continue

        if not text:
            speak(engine, "Không tìm thấy văn bản rõ ràng. Hãy căn chỉnh trang hoặc tăng ánh sáng.")
            continue

        log.info("Nội dung OCR (rút gọn 300 ký tự): %s", text[:300].replace("\n", " "))
        speak(engine, "Bắt đầu đọc.")
        speak(engine, text)
        speak(engine, "Đã đọc xong. Nhấn Enter để đọc lần nữa, hoặc gõ q để thoát.")

if __name__ == "__main__":
    main()
