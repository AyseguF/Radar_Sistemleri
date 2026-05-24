# Çoklu Sensör Füzyonu ve YOLOv8 Tabanlı Akıllı Hava Gözetim Sistemi

Düşük maliyetli gömülü donanımlar (Arduino Uno ve ESP32-CAM) ile üst seviye yapay zeka işleme sunucusunu (PythonYOLOv8) bir araya getiren, Karar Seviyesinde Çoklu Sensör Füzyonu (Decision-Level Sensor Fusion) tabanlı otonom bir hava hedefi algılama, sınıflandırma ve takip sistemi prototipidir.

---

## 🚀 Proje Mimarisi ve Çalışma Mantığı

Sistem, tek bir sensör türünün (sadece optik kamera veya sadece radar) zafiyetlerini ortadan kaldırmak amacıyla iki aşamalı bir füzyon mimarisiyle çalışır

**1. Ön Algılama (Radar Döngüsü)** :  Arduino Uno'ya bağlı servo motor üzerindeki ultrasonik sensör sürekli yatay tarama yapar. Nesne 4cm - 45cm eşik değerine girdiğinde **mAsenkron UDP Tetikleme Sinyali** (Port 5006) üzerinden Python sunucusuna bildirilir.
**2. Sınıflandırma ve Takip (Görüntü İşleme)** :  Tetikleme sinyaliyle birlikte ESP32-CAM video akışı aktive edilir. Görüntüler, hava araçlarına özel **AOD-4** veri kümesiyle eğitilen **YOLOv8s** modeline beslenir ve anlık hedef tespiti gerçekleştirilir.

---

## 📡 UDP ve Port Haberleşme Mimarisi

Projenin en kritik mühendislik altyapısı, farklı platformların (Arduino [C++], Processing [Java] ve Python) birbirleriyle sıfır gecikmeye yakın ve asenkron olarak haberleşmesini sağlayan **UDP (User Datagram Protocol)** ağ katmanıdır. 

Seri port (UART) kilitlenmelerini ve iş parçacığı (thread) bloklanmalarını engellemek için tasarlanan ağ şeması şu şekildedir:

* **Arduino <-> Processing (Seri Port):** Alt seviye donanım, milisaniyelik mesafe ve servo açı verilerini seri port üzerinden Processing köprüsüne aktarır.
* **Processing <-> Python Sunucusu (Port 5006):** Radar taraması esnasında kritik bir mesafe eşiği aşıldığı an, Processing bu port üzerinden Python'a asenkron bir tetikleme datagramı fırlatır. Python bu sinyali alana kadar arka planda derin öğrenme modelini uyku modunda tutarak işlemciyi yormaz.
* **Python Sunucusu <-> Processing / Arduino (Port 5005):** YOLOv8 modeli görüntüyü işleyip hedef merkezini kestirdikten sonra, hesaplanan yeni açısal komutları bu port üzerinden geri gönderir. Arduino, bu paketi çözerek kamerayı hedefe kilitler.

---

## 🎬 Sistem Çalışma Demoları (Videolar)

Sistemin farklı senaryolardaki çalışma durumlarına ait otonom tepki demoları aşağıda listelenmiştir:

### Durum 1: Helikopter Algılama (Aktif Kilitlenme ve Sürekli Takip)
*Sistem ultrasonik radarla hedefi yakalar, YOLOv8 nesneyi "Helikopter" olarak sınıflandırır ve kamera servoları hedef kadrajdan çıkana kadar sürekli otonom takip gerçekleştirir.*

| Radar Arayüzü Görünümü / Donanım ve Kamera Takip Döngüsü |
|---|
| <img src="Media\helikopter.gif" width="400"> |

---
### Durum 2: Drone ve Uçak Algılama (Hız/Yön Kestirimi ve Steganografik Kayıt)
*Hedef algılanır, sürat ve yaklaşma/uzaklaşma yönü Kosinüs Teoremi ile hesaplanır. Veriler `stepic` ile suçüstü fotoğrafının içine gizlenerek arşivlenir ve sistem tarama moduna sıfırlanır.*

| Otonom Veri Kayıt Süreci (Video) |
|---|
| <img src="Media\uçak.gif" width="600"> |

---

### Durum 3: Kuş Algılama (Yanıltıcı Gürültü Filtreleme)
*YOLOv8 nesneyi "Kuş" (tehdit değil) olarak sınıflandırdığında sistem gereksiz mekanik takip yapmaz, döngüyü kırar ve anında radar moduna geri döner.*

| Yanlış Alarm Filtreleme Demosu |
|---|
| <img src="Media\kuş.gif" width="600"> |

---

## 🛠️ Donanım Bileşenleri

 * **Arduino Uno** :  Alt seviye donanım kontrol birimi.
 * **HC-SR04 Ultrasonic Sensor** : Mesafe ve radar tarama sensörü.
 * **SG90 Servo Motor (x2)** : Radar yatay tarama ve Kamera yönlendirme mekanizması.
 * **ESP32-CAM** : Gerçek zamanlı video yayın modülü.

---

## 📐 Matematiksel Model (Sürat ve Yön Kestirimi)

Ardışık iki radar döngüsünden elde edilen konum verileri (d₁, β₁, t₁) ve (d₂, β₂, t₂) üzerinden açısal fark (∆β = | β₁ - β₂ |) kullanılarak Kosinüs Teoremi ile doğrusal yer değiştirme L ve ortalama radyal sürat V hesaplanır

>                                                         L = √d₁² + d₂²- 2 x d₁ x d₂ x cos(∆β)

>                                                                      V = L/∆t

 Yön Analizi d₁ < d₂ ise hedef Yaklaşıyor (Kritik Tehdit), d₁ > d₂ ise Uzaklaşıyor olarak etiketlenir.

---

## 🎯 Tehdit Sınıflandırma Stratejisi

 Helikopter Kritik Tehdit. Sistem Aktif Takip Moduna geçer. Görüş açısı ($FOV_h$) ve sınırlayıcı kutu merkezi ($X_{text{bbox}}$) hesaplanarak kamera servosu anlık güncellenir ve hedef kilitlenerek sürekli izlenir.
 Drone & Uçak Algılandığı an hız ve yön analizleri tamamlanır. Tüm uçuş verileri Steganografi (Veri Gizleme) yöntemiyle yakalanan suçüstü resminin içerisine gömülerek `TEHDIT_...png` olarak arşivlenir ve sistem sıfırlanır.
 Kuş Yanıltıcı Gürültü. Takip döngüsü tetiklenmez, sistem anında radar tarama moduna geri döner.

---

## 📊 Deneysel Bulgular ve Performans

 YOLOv8s Doğruluk Oranı AOD-4 veri setinde $0.969 mAP@50 skoruna ulaşılmıştır.
---

## 📂 Dosya Yapısı

```text
├──Media
│   ├──Helikopter.gif
│   ├──Kuş.gif
│   └──Uçak.gif
├──CameraWebServer
│   └──CameraWebServer.ino         #Kamera kodları
├── sketch_may16a
│   └── sketch_may16a.ino          # Servo motor, mesafe ölçümü ve yumuşak takip motoru kodları
├── sketch_260516b
│   └── sketch_260516b.pde         # Grafiksel radar ekranı, UDP haberleşme ve el sıkışma köprüsü
├── python_ai
│   ├── Nesne_Tesbit_ve_Takip.py   # YOLOv8 çıkarım, UDP dinleyici ve takip kararı ana motoru
│   └── Kayıt_Okuma.py             # Stepic kütüphanesi ile resim içine | eri gizleme modülü
└── README.md                      # Proje genel dökümantasyonu
