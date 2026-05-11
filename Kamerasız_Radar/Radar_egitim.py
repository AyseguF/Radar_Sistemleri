import cv2
from ultralytics import YOLO

# Kendi eğittiğin modelin tam yolunu buraya yaz (Örn: 'best.pt')
model = YOLO('best.pt') 

# Serial Monitörden aldığın IP adresini buraya yaz
stream_url = "http://192.168.238.242:81/stream" 

# Pencereyi özelleştirilebilir ve büyük yap
cv2.namedWindow("Radar Takip Sistemi", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Radar Takip Sistemi", 1280, 720)

print("Bağlantı kuruluyor...")
cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Görüntü alınamadı, yeniden bağlanılıyor...")
        cap.release()
        cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
        continue
    
    # YOLOv8 ile tespit yap
    results = model(frame)
    
    # Tespitleri ekrana çiz
    annotated_frame = results[0].plot()
    
    # Radar verisi simülasyonu (Ekrana yazı ekleme)
    cv2.putText(annotated_frame, "DURUM: AKTIF TARAMA", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    
    cv2.imshow("Radar Takip Sistemi", annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()