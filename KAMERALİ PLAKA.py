import cv2
import pytesseract
import re

# Tesseract OCR yolu
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\simay\Tesseract-OCR\tesseract.exe"

# Plaka formatı (TR)
TR_PLATE_REGEX = re.compile(r'^(0[1-9]|[1-7][0-9]|8[0-1])[ ]?([A-Z]{1,3})[ ]?(\d{2,4})$')

# TXT dosyasından geçerli plakaları oku
with open("plakalar.txt", "r", encoding="utf-8") as f:
    kayitli_plakalar = [satir.strip().upper() for satir in f if satir.strip()]

# Kamera başlat
kamera = cv2.VideoCapture(0)
if not kamera.isOpened():
    print("Kamera açılamadı!")
    raise SystemExit

print("Kamera açık. 'Q' ile çıkış yapabilirsin.")
frame_count = 0
ocr_interval = 10
plaka_mesaji = "Plaka bekleniyor..."

while True:
    ret, kare = kamera.read()
    if not ret:
        print("Kare alınamadı.")
        break

    frame_count += 1

    if frame_count % ocr_interval == 0:
        gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gri = clahe.apply(gri)
        _, binimg = cv2.threshold(gri, 110, 255, cv2.THRESH_BINARY)

        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        raw = pytesseract.image_to_string(binimg, lang='eng', config=config)

        # Temizle
        txt = re.sub(r'[^A-Z0-9 ]', '', raw.upper())
        txt = txt.replace('Ö', 'O').replace('O', '0') if False else txt
        txt_compact = txt.replace(" ", "")

        # TR formatı kontrol
        m = re.match(r'(\d{2})([A-Z]{1,3})(\d{2,4})', txt_compact)
        if m:
            plaka_okunan = f"{m.group(1)} {m.group(2)} {m.group(3)}"
            if TR_PLATE_REGEX.match(plaka_okunan):
                if plaka_okunan in kayitli_plakalar:
                    plaka_mesaji = f"Girişe izin verildi: {plaka_okunan}"
                    print(plaka_mesaji)
                    break
                else:
                    plaka_mesaji = f"Bu plaka kayıtlı değil: {plaka_okunan}"
            else:
                plaka_mesaji = "Plaka formatı geçersiz"
        else:
            plaka_mesaji = "Plaka tanınamadı"

    # Ekrana yaz
    cv2.putText(kare, plaka_mesaji, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0) if "izin" in plaka_mesaji else (0, 0, 255), 2)
    cv2.imshow("Kamera", kare)

    # Çıkış tuşu
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Kullanıcı tarafından çıkıldı.")
        break

kamera.release()
cv2.destroyAllWindows()
