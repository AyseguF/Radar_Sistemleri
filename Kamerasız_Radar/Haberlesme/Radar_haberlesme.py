import serial
import time
import socket

# --- AYARLAR ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
COM_PORT = 'COM8' # Aygıt yöneticisinden kontrol et

# Soket Bağlantısı (Python -> Processing)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Seri Port Bağlantısı (Python <-> Arduino)
try:
    ser = serial.Serial(COM_PORT, 9600, timeout=0.1)
    ser.setDTR(False)
    time.sleep(2)
    ser.flushInput()
    print(f"{COM_PORT} üzerinden Arduino'ya bağlandı!")
except Exception as e:
    print(f"Bağlantı Hatası: {e}")
    exit()

def processinge_pasla(aci, mesafe,hiz,nesne):
    # Processing'e gidecek format: "aci,mesafe,hiz,nesne"
    mesaj = f"{aci},{mesafe},{hiz},{nesne}"
    sock.sendto(mesaj.encode(), (UDP_IP, UDP_PORT))

while True:
    try:
        if ser.in_waiting > 0:
            # Arduino'dan gelen veri: "45*20#"
            line = ser.readline().decode('utf-8').strip()
            
            if '#' in line and '*' in line:
                data = line.replace('#', '')
                parts = data.split('*')
                
                if len(parts) >= 2:
                    aci = parts[0]
                    mesafe = parts[1]
                    hiz = 0 # Şimdilik 0, ileride hesaplayacağız
                    nesne = "Taramada"
                    
                    # Veriyi Processing'e gönder
                    processinge_pasla(aci, mesafe, hiz, nesne)
                    
                    # Eğer mesafe 20'den küçükse YOLO'yu burada tetikleyeceğiz!
                    if int(mesafe) < 20:
                        print(f"Hedef Tespit Edildi! Açı: {aci}")
                        
    except KeyboardInterrupt:
        print("Sistem kapatılıyor...")
        ser.close()
        break