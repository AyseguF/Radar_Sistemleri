#include "esp_camera.h"
#include <WiFi.h>
#include "soc/soc.h"           
#include "soc/rtc_cntl_reg.h"  

// ===================
// Kamera Model Seçimi
// ===================
#define CAMERA_MODEL_AI_THINKER 
#include "camera_pins.h"

// ===========================
// WiFi Bilgilerin
// ===========================
const char* ssid = "Galaxy A51 D346"; 
const char* password = "12345678";

// === SABİT IP AYARLARI ===
IPAddress local_IP(192, 168, 167, 242);  
IPAddress gateway(192, 168, 167, 1);    
IPAddress subnet(255, 255, 255, 0);     
IPAddress primaryDNS(8, 8, 8, 8);       

void startCameraServer();

void setup() {
  // Brownout dedektörünü kapat (Güç dalgalanmasında çökmeyi önler)
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); 
  
  Serial.begin(115200);
  Serial.setDebugOutput(false); // Gereksiz log yükünü kapatıyoruz

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  
  // Kesintisiz akış için ideal kalite ve buffer ayarları
  config.frame_size = FRAMESIZE_CIF;     // Yüksek FPS ve sıfır takılma için CIF en iyisidir
  config.pixel_format = PIXFORMAT_JPEG; 
  config.grab_mode = CAMERA_GRAB_LATEST; // Python'a her zaman en son kareyi gönderir
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 10;              // 10-12 arası kalite/boyut dengesidir
  config.fb_count = 2;                   // Çift buffer kilitlenmeleri önler

  // Kamera donanımını başlatma
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Kamera Sensörünü default ayarlara çekiyoruz (Ekstra yükleri temizledik)
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 0);     
    s->set_contrast(s, 0);       
    s->set_saturation(s, 0);     
    s->set_whitebal(s, 1);       // Otomatik beyaz dengesi açık (Görüntü kalitesi için)
    s->set_awb_gain(s, 1);       
    s->set_exposure_ctrl(s, 1);  // Otomatik pozlama açık
    s->set_hmirror(s, 0);        // Aynalama kapalı (Python yapacak)
    s->set_vflip(s, 0);          // Döndürme kapalı (Python yapacak)
  }

  // Sabit IP ayarı
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS)) {
    Serial.println("Statik IP Yapılandırması Başarısız Oldu!");
  }

  // Kablosuz ağa bağlanma
  Serial.print("Bağlantı kuruluyor: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  // Web Sunucusunu Başlat
  startCameraServer();

  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

void loop() {
  delay(10000); // Ana döngü tamamen boş, işlemci sadece arka planda stream yapıyor
}