import cv2
import serial
import time
import math
import socket
import stepic
from PIL import Image
from ultralytics import YOLO
import numpy as np
import os

# FFmpeg ve OpenCV log seviyesini sadece kritik hataları gösterecek şekilde ayarla (Değer string olmalı)
os.environ["OPENCV_LOG_LEVEL"] = "FATAL" 
os.environ["FFMPEG_LOG_LEVEL"] = "QUIET"
# --- AYARLAR ---
ESP32_URL = "http://192.168.167.242:81/stream"
UDP_SEND_PORT = 5005   # Processing'e veri gönderme portu
UDP_LISTEN_PORT = 5006 # Processing'den tetikleme alma portu

# 📐 Donanım Geometrisi Ayarları
# Kamera yan yatırıldığı için orijinal çözünürlükteki Yükseklik (480), döndürülmüş resmin yeni genişliği olur.
# Model girişimiz (480, 360) olduğundan, yeni genişlik W_yeni = 480'dir.
W_yeni = 480  
FOVh = 65


print("⚡⚡⚡ YOLO Modeli yükleniyor...")
model = YOLO('best_s.pt')
print(" 🤖 Model yüklendi.\n 🛠️ UDP soketleri hazırlanıyor...")

# Sadece Processing'den tetik dinleyecek UDP soketi
sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_listen.bind(("127.0.0.1", UDP_LISTEN_PORT))
sock_listen.setblocking(False) # Kodun kilitlenmemesi için non-blocking yapıyoruz
print(" ✅ UDP soketleri hazır.")
print(" ⚙️ Sistem değişkenleri ayarlanıyor...")

# Paylaşılan küme koordinatları
b1,d1,t1 = None, None, None
b2, d2, t2 = None, None, None
mevcut_kam_acisi = 90
kamera_acik_mi = False
nesne_tesbiti_aktif = False
takip_modu = False
hiz=0.0
son_baglanti_denemesi = 0
etiket = "Belirsiz" # Olası Scope hatalarını önlemek için başlangıç değeri verildi
son_gorulme = None # 🌟 YENİ: Son görülen kareyi globalde tutuyoruz

# YOLO Zamanlayıcı Değişkenleri
yolo_aktif = False  
servo_hareket_zamani = 0.0
BEKLEME_SURESI = 2.0 # ⏳ Kamera hedefe varana kadar beklenecek süre (Saniye cinsinden)
helikopter_takip_suresi = 0.0 # 🚁 Helikopter takibi sırasında hedef gözden kaybolursa bekleme süresi
helikopter_takip_zamani = 0.0  # 🌟 YENİ: Kilitlenme zamanını globalde tutuyoruz

kayit_durumu = False
tesbit_uyari_basildi = False

print("📚 Sistem değişkenleri hazırlandı.")
print("  ==== 🚀 Sistem Hazır!  ====\n ⏰ Processing'den tetiklenme bekleniyor...")

# --- FONKSİYONLAR ---
def komut_gonder(komut_str):
    """Güvenli komut gönderme: Parametre olarak sadece string alır."""
    try:
        sock_send.sendto(f"CMD:{komut_str}".encode(), ("127.0.0.1", UDP_SEND_PORT))
    except Exception as e:
        print(f" ❌ UDP Gönderim Hatası: {e}")

def veriyi_resime_gizle_ve_mesajı_kaydet(resim_matrisi, mesaj,current_etiket):
    global hiz
    dosya_adi = f"TEHDIT_{current_etiket}_{int(time.time())}.png"
    cv2.imwrite(dosya_adi, resim_matrisi)
    try:
        img = Image.open(dosya_adi)

        # Mesajı byte formatına çevirerek gizliyoruz
        img_steg = stepic.encode(img, mesaj.encode('utf-8'))

        img_steg.save(dosya_adi, "PNG") 
        print(f"--- 🗃️ TEHDİT KAYDEDİLDİ: {current_etiket} | Hız: {hiz:.2f} m/s ---")
    except Exception as e:
        print(f" ❌Resme veri gizleme hatası: {e}")

def cisim_hizi_hesapla_ve_mesaj_oluştur(current_etiket):
    global d1, b1, t1, hiz, b2, d2, t2
    if d1 is None or d2 is None : 
        return f"Etiket:{current_etiket}|Hiz:Hesaplanamadi|İlk Aci:{b1}| İlk Mesafe:{d1}cm|Yon:Belirsiz"
    
    dt = (t2 - t1) / 1000.0 # milisaniyeyi saniyeye çevir
    if dt <= 0: dt = 0.1 

    #KOsinüs teoremi ile gerçek dünya mesafesini hesaplama
    delta_b = math.radians(abs(b2 - b1))
    L = math.sqrt(max(0, (d1**2) + (d2**2) - (2*d1*d2*math.cos(delta_b))))
    hiz = L / dt

    # === YENİ: YÖN ANALİZ MANTIĞI ===
    if d2 > d1:
        yon = "YAKLASIYOR (Kritik Tehdit)"
    elif d2 < d1:
        yon = "UZAKLASIYOR"
    else:
        yon = "SABIT (Yorungede)"

    return f"Etiket:{current_etiket}|Hiz:{hiz:.2f}m/s|Aci:{b2}|Mesafe:{d2}cm|Yon:{yon}"

def nesne_tesbiti(results, frame_to_plot,frame_raw):
    global mevcut_kam_acisi, kamera_acik_mi, takip_modu, helikopter_takip_zamani, d1, b1, t1,d2,b2,t2, hiz, nesne_tesbiti_aktif,etiket,servo_hareket_zamani,kayit_durumu,son_gorulme,s
    
    # 🌟 GÜVENLİK ÖNLEMİ: Eğer alt taraftaki else bloklarına düşersek ve model o an hiçbir şey görmediyse 
    # etiket değişkeninin havada kalmaması için mevcut durumu kontrol ediyoruz.
    current_etiket = etiket if 'etiket' in globals() else "Belirsiz"
    if len(results[0].boxes) > 0:
    
        box = results[0].boxes[0]
        guven_skoru = box.conf[0].item()    
        etiket = model.names[int(box.cls[0])]
        current_etiket = etiket # Güncel tespiti eşitle

        # --- 🕊️ KUŞ KONTROLÜ ---
        if etiket == "Kus" and not takip_modu:
            print(f"YOLO Tespiti: 🕊️ {etiket} (%{guven_skoru*100:.1f})")
            sistemi_sifirla()
            return

        # --- ✈️ UÇAK / DRONE KONTROLÜ ---
        elif etiket in ["Ucak", "Drone"] and not takip_modu:
            if d2 is not None:       
                if abs(b2 - mevcut_kam_acisi) < 40 : # 5 derece sınırı
                    print(" 👩‍💻 Veriler kaydediliyor...")
                    gizli_mesaj = cisim_hizi_hesapla_ve_mesaj_oluştur(current_etiket)                      
                    veriyi_resime_gizle_ve_mesajı_kaydet(frame_raw, gizli_mesaj, current_etiket)
                    sistemi_sifirla()                    
                else:
                    d2,b2,t2 =None, None, None 
                    """Eğer radar farklı bir nesnenin tespitini yaparsa 
                        asıl hedefin 2. tesbitini yapmak için 2. tesbit 
                        verilerini temizliyoruz."""
                    
                    
            elif d1 is not None :
                global tesbit_uyari_basildi
                if not tesbit_uyari_basildi:
                    print(f" === ⚠️ Tehdit Sınıfı : {current_etiket} === ")
                    print(" === 2. Tesbit bekleniyor... === ")
                    tesbit_uyari_basildi = True # Kapıyı kapat, bir daha basma
                return
            print(f"YOLO Tespiti: {current_etiket} (%{guven_skoru*100:.1f})")

        # --- 🚁 HELİKOPTER VEYA KİLİTLENMİŞ TAKİP MODU ---
        elif etiket == "Helikopter" or takip_modu:
            
            helikopter_takip_zamani = time.time()
            if not takip_modu:
                print(f" === ⚠️ Tehdit Sınıfı : {current_etiket} === ")
                print(" === 🔒 Helikopter Hedefe Kilitlendi! Sürekli Takip Modu Aktif. ===")
                takip_modu = True

            # 🔄 90 DERECE YATIK KAMERA TAKİP MATEMATİĞİ DÜZELTMESİ:
            # Görüntü saat yönünde 90 derece döndürüldüğü için, fiziksel dünyadaki yatay (pan) hareket 
            # YOLO'nun tespit ettiği çerçevenin Y eksenindeki (y_merkez) değişime denk gelir.
            y_merkez = box.xywh[0][1].item()
            ekran_merkezi = W_yeni / 2 # 240 piksel
 
            # Tolerans (Ölü Bölge): Uçak merkezden 15 piksel sağa/sola kaymadığı sürece servo titremesin
            tolerans = 10.0
            adim_miktari = 2.0 # Her karede servonun kaç derece döneceği (Hassasiyete göre 1.5 - 3.0 yapabilirsin)

            if abs(y_merkez - ekran_merkezi) > tolerans:
                if y_merkez > ekran_merkezi:
                    mevcut_kam_acisi -= adim_miktari  
                elif y_merkez < ekran_merkezi:
                    mevcut_kam_acisi += adim_miktari
            
            # Sınır kontrolü ve komut gönderimi          
            if 10 <= mevcut_kam_acisi <= 170:
                komut_gonder(f"CAM:{int(mevcut_kam_acisi)}\n")
                servo_hareket_zamani = time.time() # Servo hareketi gerçekleştiği anı kaydet
                if etiket == "Helikopter":
                    print(f"YOLO Tespiti: {etiket} (%{guven_skoru*100:.1f})")
                    print(f"📹 Kamera açısı güncellendi: {mevcut_kam_acisi:.1f}°...")
                    if d2 is None:
                        print("🚁 Helikopter takip ediliyor...")            
                    elif d2 is not None and not kayit_durumu:                    
                        if abs(b2 - mevcut_kam_acisi) > 40: # 5 derece sınırı
                            d2,b2,t2 =None, None, None 
                            """Eğer radar farklı bir nesnenin tespitini yaparsa 
                                takip modunu sıfırlamak için radar verilerini 
                                temizliyoruz."""
                            print(" === 2.Tesbit bekleniyor... === ")
                        else :
                            kayit_durumu = True 
                            print("🚁 Helikopter 2. Konumu tesbit edildi.")
                            print(f"📊 Hız ve yön hesaplaması yapılıyor...")
                son_gorulme= frame_raw.copy()
                            
            
            else:
                print("     === ⚠️ Kamera sınırlarına ulaşıldı, takip durduruluyor. ===")
                print("🚁 Helikopter takibi sona erdi.  ")
                if d2 is not None :
                    print("🎯 Veriler eksiksiz. \n 👩‍💻 Kayıt işlemi eksiksiz yapılıyor...")
                elif d2 is None:
                    print("❌ Veri eksikliği tesbit edildi.\n 👩‍💻 Kayıt işlemi eksik yapılıyor...")
                gizli_mesaj = cisim_hizi_hesapla_ve_mesaj_oluştur(current_etiket)
                veriyi_resime_gizle_ve_mesajı_kaydet(frame_raw, gizli_mesaj, current_etiket)
                kayit_durumu = True
                sistemi_sifirla()
    else:
        frame_raw = son_gorulme
        # Eğer takip modundaysak ve obje 2 saniye boyunca hiç görünmediyse kaybettiğimizi varsayalım
        if takip_modu and (time.time() - helikopter_takip_zamani > 15.0):
            print("⚠️ Hedef gözden kayboldu.\n ♻️ Sistem sıfırlanıyor...")
            if d2 is not None :
                print("🎯 Veriler eksiksiz. \n 👩‍💻 Kayıt işlemi eksiksiz yapılıyor...")
            elif d2 is None:
                print("❌ Veri eksikliği tesbit edildi.\n 👩‍💻 Kayıt işlemi eksik yapılıyor...")                
            gizli_mesaj = cisim_hizi_hesapla_ve_mesaj_oluştur(current_etiket)
            veriyi_resime_gizle_ve_mesajı_kaydet(frame_raw, gizli_mesaj, current_etiket)
            sistemi_sifirla()

        else:
            if yolo_aktif and (time.time() - servo_hareket_zamani > 15.0):
                print("⚠️ Nesne yakalanamadı, bekleme süresi doldu. Sistem temizleniyor...")     
                sistemi_sifirla()

def sistemi_sifirla():
    print(" === ♻️ Sistem sıfırlanıyor.  ===")
    global nesne_tesbiti_aktif, takip_modu, kamera_acik_mi,helikopter_takip_zamani, d1, b1, t1, d2, b2, t2,s, mevcut_kam_acisi, cap, kayit_durumu,tesbit_uyari_basildi
    nesne_tesbiti_aktif = False
    takip_modu = False
    kamera_acik_mi = False
    helikopter_takip_zamani = 0.0
    d1, b1, t1 = None, None, None
    d2, b2, t2 = None, None, None
    mevcut_kam_acisi = 90.0
    current_etiket = "Belirsiz" # Sıfırlama esnasında temizle
    kayit_durumu = False
    tesbit_uyari_basildi = False

    komut_gonder("CAM:90\n")
    if cap:
        cap.release()
        cap = None # Döngü patlamasını engellemek için None yapıyoruz
    cv2.destroyAllWindows()
    print(" ---- Sistem temizlendi 🧹 🫧, ⏰ yeni tetik bekleniyor. ----\n ")

# --- ANA DÖNGÜ ---
cap = None
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Processing'den tetik veya koordinat güncellemesi bekle
    try:
        data, addr = sock_listen.recvfrom(1024)
        msg = data.decode().strip()
        
        if msg.startswith("DETEKT:"):
            parts = msg.split(":")[1].split(",")
            yeni_b, yeni_d, yeni_t = int(parts[0]), int(parts[1]), int(parts[2])
            
            if d1 is None:
                d1, b1, t1 = yeni_d, yeni_b, yeni_t

                # === 1. ADIM: KAMERA SERVO EMRE BASTIĞI AN... ===
                komut_gonder(f"CAM:{int(b1)}\n")  
                mevcut_kam_acisi = float(b1)

                yolo_aktif = False  
                servo_hareket_zamani = time.time()

                print(f" === ⚠️ Tehdit Algılandı ({b1}°). === \n === 📹 Kamera servosu {b1}° açısına yönlendiriliyor... ===")
            elif d2 is None:
                d2, b2, t2 = yeni_d, yeni_b, yeni_t
            
            # === 2. ADIM: ...AYNI ANDA ARKA PLANDA AKIŞI BAŞLATIYORUZ ===
            # Servo dönerken Python da ESP32'ye el sıkışma isteği atıyor (Zamandan kazanç)
            if not nesne_tesbiti_aktif and (time.time() - son_baglanti_denemesi > 3.0):
                print("📹 Kamera akışı eşzamanlı olarak başlatılıyor...")
                son_baglanti_denemesi = time.time() # Zamanı kilitle

                # Önceki açık kalmış hatalı soketleri temizle
                if cap is not None:
                    cap.release()

                cap = cv2.VideoCapture(ESP32_URL)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    print("✅ Kamera Modülüyle bağlantı sağlandı. YOLO aktif.") 
                    nesne_tesbiti_aktif = True
                    kamera_acik_mi = True
                else:
                    print("❌ Kamera akış hatası. Yeniden denenecek, servo konumunu koruyor...")
    except BlockingIOError:
        pass


    #Zaman Kontrolü (Servo mekanik dönüşünü bekletme)
    if nesne_tesbiti_aktif and not yolo_aktif:
        if time.time() - servo_hareket_zamani >= BEKLEME_SURESI:
            print(" 🚀 Kamera hedefe ulaştı ve sabitlendi. YOLO Tahmini Başlatılıyor! 🔥")
            yolo_aktif = True

    # Görüntü İşleme ve Takip Döngüsü
    if nesne_tesbiti_aktif and cap and cap.isOpened():  

        if not yolo_aktif:
            time.sleep(0.03) # Servo hareketini beklerken CPU'yu rahatlatmak için kısa bir uyku          

        kare_atlama_sayisi = 25 if (time.time() - servo_hareket_zamani < BEKLEME_SURESI +2.0 )else 5 
        # ESP32-CAM üzerindeki donanımsal buffer yığılmasını engellemek için kare atlama
        for _ in range(kare_atlama_sayisi): # Akışta birkaç kare atlayarak gecikmeyi azaltmaya çalışıyoruz
            cap.grab() # Karesi atla
        
       
        r, f = cap.retrieve()
        if not r or f is None:
            time.sleep(0.01) # Kameraya toparlanması için çok kısa bir nefes payı
            continue  
        
        # Görüntüyü döndürüyoruz ve yumuşatıyoruz
        f = cv2.rotate(f, cv2.ROTATE_90_CLOCKWISE)
        f_clean = cv2.GaussianBlur(f, (3, 3), 0)
        
        # Modele göndermek için uygun boyuta getiriyoruz
        frame_mini = cv2.resize(f_clean, (480, 360))
        
        if yolo_aktif:
            results = model(frame_mini, verbose=False, conf=0.7)
            annotated_frame = results[0].plot()
            nesne_tesbiti(results, annotated_frame,frame_mini)
        else:
            annotated_frame = frame_mini # YOLO aktif değilken sadece temiz görüntüyü gösteriyoruz

        if nesne_tesbiti_aktif:
            cv2.imshow(" 🎯 YOLO Takip Sistemi", annotated_frame)

if cap:
    cap.release()
cv2.destroyAllWindows()