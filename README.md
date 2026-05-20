# Çoklu Sensör Füzyonu ve YOLOv8 Tabanlı Akıllı Hava Gözetim Sistemi

Düşük maliyetli gömülü donanımlar (Arduino Uno ve ESP32-CAM) ile üst seviye yapay zeka işleme sunucusunu (PythonYOLOv8) bir araya getiren, Karar Seviyesinde Çoklu Sensör Füzyonu (Decision-Level Sensor Fusion) tabanlı otonom bir hava hedefi algılama, sınıflandırma ve takip sistemi prototipidir.

---

## 🚀 Proje Mimarisi ve Çalışma Mantığı

Sistem, tek bir sensör türünün (sadece optik kamera veya sadece radar) zafiyetlerini ortadan kaldırmak amacıyla iki aşamalı bir füzyon mimarisiyle çalışır

1. Ön Algılama (Radar Döngüsü) Arduino Uno'ya bağlı servo motor üzerindeki ultrasonik sensör sürekli yatay tarama yapar. Nesne $4text{ cm} - 45text{ cm}$ eşik değerine girdiğinde Asenkron UDP Tetikleme Sinyali (Port 5006) üzerinden Python sunucusuna bildirilir.
2. Sınıflandırma ve Takip (Görüntü İşleme) Tetikleme sinyaliyle birlikte ESP32-CAM video akışı aktive edilir. Görüntüler, hava araçlarına özel AOD-4 veri kümesiyle eğitilen YOLOv8s modeline beslenir ve anlık hedef tespiti gerçekleştirilir.

---

## 🛠️ Donanım Bileşenleri

 Arduino Uno Alt seviye donanım kontrol birimi.
 HC-SR04 Ultrasonic Sensor Mesafe ve radar tarama sensörü.
 SG90 Servo Motor (x2) Radar yatay tarama ve Kamera yönlendirme mekanizması.
 ESP32-CAM Gerçek zamanlı video yayın modülü.

---

## 📐 Matematiksel Model (Sürat ve Yön Kestirimi)

Ardışık iki radar döngüsünden elde edilen konum verileri $[(d_1, beta_1, t_1) text{ ve } (d_2, beta_2, t_2)]$ üzerinden açısal fark ($Deltabeta = beta_2 - beta_1$) kullanılarak Kosinüs Teoremi ile doğrusal yer değiştirme ($L$) ve ortalama radyal sürat ($V$) hesaplanır

$$L = sqrt{d_1^2 + d_2^2 - 2d_1d_2cos(Deltabeta)}$$

$$V = frac{L}{Delta t}$$

 Yön Analizi $d_2  d_1$ ise hedef Yaklaşıyor (Kritik Tehdit), $d_2  d_1$ ise Uzaklaşıyor olarak etiketlenir.

---

## 🎯 Tehdit Sınıflandırma Stratejisi

 Helikopter Kritik Tehdit. Sistem Aktif Takip Moduna geçer. Görüş açısı ($FOV_h$) ve sınırlayıcı kutu merkezi ($X_{text{bbox}}$) hesaplanarak kamera servosu anlık güncellenir ve hedef kilitlenerek sürekli izlenir.
 Drone & Uçak Algılandığı an hız ve yön analizleri tamamlanır. Tüm uçuş verileri Steganografi (Veri Gizleme) yöntemiyle yakalanan suçüstü resminin içerisine gömülerek `TEHDIT_...png` olarak arşivlenir ve sistem sıfırlanır.
 Kuş Yanıltıcı Gürültü. Takip döngüsü tetiklenmez, sistem anında radar tarama moduna geri döner.

---

## 📊 Deneysel Bulgular ve Performans

 YOLOv8s Doğruluk Oranı AOD-4 veri setinde $0.969text{ mAP@50}$ skoruna ulaşılmıştır.
 Çıkarım Süresi (Latency) YOLOv8n modeli $14text{ ms}$ çıkarım süresi ile gerçek zamanlı gömülü sistem döngüsünü doğrulamıştır.
 Yanlış Alarm Engelleme Gelişmiş veri artırımı (Mosaic, Mixup) sayesinde Kuş-İHA karışıklık oranı %15'ten %3'e düşürülmüştür.

---

## 📂 Dosya Yapısı

```text
├── arduino_radar
│   └── radar_control.ino      # Servo motor, mesafe ölçümü ve yumuşak takip motoru kodları
├── processing_gui
│   └── radar_interface.pde    # Grafiksel radar ekranı, UDP haberleşme ve el sıkışma köprüsü
├── python_ai
│   ├── main.py                # YOLOv8 çıkarım, UDP dinleyici ve takip kararı ana motoru
│   └── stego_logger.py        # Stepic kütüphanesi ile resim içine veri gizleme modülü
└── README.md                  # Proje genel dökümantasyonu