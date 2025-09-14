import os

def main():
    text = "Xin chào, tôi là máy đọc sách chạy trên Raspberry Pi."
    print("🔊 Đang đọc thử qua espeak-ng...")
    os.system(f'espeak-ng "{text}"')
    print("✅ Đọc xong.")

if __name__ == "__main__":
    main()
