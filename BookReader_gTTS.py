#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BookReader: Camera Preview -> OCR -> gTTS + pygame
- Preview camera bằng OpenCV
- Enter = chụp ảnh, ESC = thoát
- OCR + phát hiện ngôn ngữ (Anh/Việt) -> đọc bằng gTTS
"""

import cv2
import pytesseract
import logging
import os
import sys
from datetime import datetime
from gtts import gTTS
from langdetect import detect, DetectorFactory
import pygame

# Đảm bảo langdetect luôn ổn định
DetectorFactory.seed = 0

# ================= Logging Setup =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ================= TTS với pygame =================
def speak(text):
    if not text.strip():
        text = "Không có văn bản để đọc."

    # Phát hiện ngôn ngữ
    try:
        lang = detect(text)
    except Exception:
        lang = "vi"

    if lang not in ["en", "vi"]:
        lang = "vi"

    logging.info(f"🌐 Phát hiện ngôn ngữ: {lang}")
    logging.info("🔊 Văn bản OCR:\n%s", text)

    # Tạo file mp3 tạm
    tmp_file = "tts_output.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(tmp_file)

    # Phát bằng pygame
    pygame.mixer.init()
    pygame.mixer.music.load(tmp_file)
    pygame.mixer.music.play()

    # Chờ phát xong
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.quit()
    os.remove(tmp_file)
    logging.info("✅ Đọc xong.")

# ================= OCR =================
def ocr_image(image_path):
    if not os.path.exists(image_path):
        logging.error(f"❌ Không tìm thấy file {image_path}")
        return ""
    text = pytesseract.image_to_string(image_path, lang="eng+vie")
    return text.strip()

# ================= Camera Capture =================
def capture_image():
    """
    Mở camera preview, Enter = chụp ảnh, ESC = thoát.
    Trả về đường dẫn ảnh đã chụp hoặc None nếu thoát.
    """
    logging.info("📷 Mở camera preview. Nhấn Enter để chụp, ESC để thoát.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("❌ Không thể mở camera.")
        return None

    cv2.namedWindow("Camera Preview", cv2.WINDOW_NORMAL)

    captured_path = None
    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning("⚠️ Không đọc được khung hình từ camera.")
            continue

        cv2.imshow("Camera Preview", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            captured_path = f"capture_{timestamp}.jpg"
            cv2.imwrite(captured_path, frame)
            logging.info(f"📸 Đã chụp ảnh: {captured_path}")
            break
        elif key == 27:  # ESC
            logging.info("🚪 Thoát camera preview.")
            break

    cap.release()
    cv2.destroyWindow("Camera Preview")
    return captured_path

# ================= Main Loop =================
def main():
    logging.info("🚀 Hệ thống đọc sách đã sẵn sàng.")

    while True:
        image_path = capture_image()
        if not image_path:
            break  # ESC hoặc lỗi camera thì thoát

        # Hiển thị ảnh đã chụp
        img = cv2.imread(image_path)
        if img is not None:
            cv2.imshow("Ảnh đã chụp", img)
            cv2.waitKey(1)

        # OCR + đọc ra loa
        text = ocr_image(image_path)
        speak(text)

        logging.info("👉 Nhấn Enter để chụp lại, hoặc ESC để thoát.")
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == 13:  # Enter
                cv2.destroyWindow("Ảnh đã chụp")
                break
            elif key == 27:  # ESC
                cv2.destroyAllWindows()
                logging.info("👋 Kết thúc chương trình.")
                return

if __name__ == "__main__":
    main()
