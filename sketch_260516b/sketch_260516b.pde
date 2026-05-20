import hypermedia.net.*; // UDP kütüphanesi (HyperMedia)
import processing.serial.*; // Port veri okuma

UDP udp; 
Serial arduinoPort;

int aci = 0;
int mesafe = 0;
String mesafeYazisi = "";
String NesneDurumu = "Sistem Hazır";
int sonSinyalZamani = 0; // Zamanlayıcı
int sonOnayZamani = 0; // Aşırı paket gönderimini engelleyen zaman kilidi

boolean radarBaslatildi = false; // String kontrolü yerine güvenli flag


// === YENİ EKLEMELER: VERİ TUTMA ZAMANLAYICISI ===
int veriTutmaSuresi = 1000; // Yazının ekranda kalacağı süre (2000 ms = 2 saniye)
int sonTespitZamani = 0;    // Son nesnenin tespit edildiği anın milisaniyesi
String sonMesafeYazisi = "---";
String sonDurumYazisi = "Arama Yapılıyor / Temiz";

ArrayList<NesneIzi> izler = new ArrayList<NesneIzi>();

class NesneIzi {
  float x, y, parlaklik;
  int kayitliMesafe = 0;
  
  NesneIzi(float _x, float _y) {
    x = _x;
    y = _y;
    parlaklik = 255; 
  }
  void guncelle() {
    parlaklik -= 5; 
  }
}

void setup() {
  size(1230, 800);
  
  // 1. Doğrudan Arduino'ya bağlantı
  arduinoPort = new Serial(this, "COM8", 9600);
  arduinoPort.bufferUntil('#'); // Paket sonu karakteri

  // 2. Python'dan gelecek servo ve fren komutlarını dinliyoruz
  udp = new UDP(this, 5005); 
  udp.listen(true);
  
  smooth();
  NesneDurumu = "Arduino Aranıyor...";
}

void draw() {
  fill(0, 20);
  noStroke();
  rect(0, 0, width, height);
  
  // === ARDUINO KALP ATIŞI SİNYALİ ===
  // Her 1000 milisaniyede (1 saniye) Arduino'ya "yaşıyorum" sinyali gönderir.
  if (millis() - sonSinyalZamani > 1000) {
    sonSinyalZamani = millis();
    if (arduinoPort != null && radarBaslatildi) {
      arduinoPort.write("HEARTBEAT\n");
    }
  }

  drawRadarCizgileri();
  drawTaramaCizgisi();
  drawNesne();
  drawText();
}

// ARDUINO'DAN VERİ GELİNCE
void serialEvent(Serial p) {
  String rawData = p.readStringUntil('#');
  if (rawData != null) {
    rawData = trim(rawData.replace("#", ""));
    
    // === EL SIKIŞMA KONTROLÜ ===
    if (rawData.contains("R")) {
      arduinoPort.write("RADAR:START\n");
      NesneDurumu = "Bağlantı Kuruldu, Radar Başlatıldı.";
      return; 
    }
    
    if (rawData.contains("TIMEOUT")) {
      radarBaslatildi = false;
      NesneDurumu = "Bağlantı Koptu / Zaman Aşımı";
      return;
    }    
    
    String[] list = split(rawData, '*');
    
    if (list.length >= 3) {
      try {
        aci = Integer.parseInt(list[0]);
        mesafe = Integer.parseInt(list[1]);
        int zaman = Integer.parseInt(list[2]);
        
        if (mesafe > 4 && mesafe < 45) {
          float pixMes = map(mesafe, 0, 45, 0, 600);
          float x = pixMes * cos(radians(-aci));
          float y = pixMes * sin(radians(-aci));
          
          if (!ayniNesneMi(x, y)) {
            izler.add(new NesneIzi(x, y));
            
            // === ZAMANLAYICIYI TETİKLE VE VERİLERİ DONDUR ===
            sonTespitZamani = millis(); // Tespit anını kaydet
            sonMesafeYazisi = mesafe + " cm";
            sonDurumYazisi = "Aralık İçinde / TEHDİT (" + aci + "°)";
            
            String udpMesaj = "DETEKT:" + (180-aci) + "," + mesafe + "," + zaman;
            
             // KRİTİK DÜZELTME: Saniyede maksimum 1 kere OK göndererek ağ tıkanmasını engelliyoruz (1000 = 1sn)
            if (millis() - sonOnayZamani > 800) {
                udp.send(udpMesaj, "127.0.0.1", 5006);
                sonOnayZamani = millis();
        }
          }
        }
      } catch (Exception e) {
        println("Paket ayrıştırma hatası, atlandı.");
      }
    }
  }
  // Seri port tamponunu temizle ki hayalet/gecikmeli çizgiler tamamen silinsin
  p.clear();
}

// PYTHON'DAN EMİR GELİNCE
void receive(byte[] data, String ip, int port) {
  String mesaj = new String(data).strip();
  
  if (mesaj.startsWith("CMD:")) {
    // CMD:CAM:115 gelirse baştaki "CMD:" kısmını (4 karakter) kesip atıyoruz.
    String arduinoKomutu = mesaj.substring(4); 
    if(arduinoPort != null) {
       arduinoPort.write(arduinoKomutu + "\n"); // Arduino'ya "CAM:115\n" gider.
    }
  }
}

void drawRadarCizgileri() {
  pushMatrix();
  translate(width/2, height-100);
  strokeWeight(2);
  stroke(10, 255, 10, 100);
  
  for (int r=150; r<=600; r+=150) {
    noFill();
    arc(0, 0, r*2, r*2, PI, TWO_PI);
    fill(98, 245, 31);
    textSize(15);
    text((r/15) + " cm", r-40, 20);
  }
  
  for (int a=30; a<=150; a+=30) {
    float x = 600 * cos(radians(-a));
    float y = 600 * sin(radians(-a));
    line(0, 0, x, y);
    fill(92, 245, 31);
    textSize(18);
    float textX = 630 * cos(radians(-a));
    float textY = 630 * sin(radians(-a));
    
    // Grid üzerindeki sayıların yönünü de fiziksel akışa göre aynalıyoruz
    text((180-a)+"°", textX-10, textY);
  }
  line(-600, 0, 600, 0);
  popMatrix();
}

void drawTaramaCizgisi() {
  pushMatrix();
  translate(width/2, height-100);
  strokeWeight(5); 
  stroke(0, 255, 0); 
  
  float x = 600 * cos(radians(-aci));
  float y = 600 * sin(radians(-aci));
  
  line(0, 0, x, y);
  fill(255, 255, 255); 
  noStroke();
  ellipse(x, y, 8, 8);
  popMatrix();
}

void drawNesne() {
  pushMatrix();
  translate(width/2, height-100);
  for (int i = izler.size() - 1; i >= 0; i--) {
    NesneIzi iz = izler.get(i);
    float yayilma = map(iz.parlaklik, 255, 0, 1, 2.5);
    noFill();
    stroke(255, 10, 10, iz.parlaklik * 0.3);
    ellipse(iz.x, iz.y, 40 * yayilma, 40 * yayilma);
    fill(255, 10, 10, iz.parlaklik);
    noStroke();
    ellipse(iz.x, iz.y, 10, 10);
    iz.guncelle();
    if (iz.parlaklik <= 0) izler.remove(i);
  }
  popMatrix();
}

void drawText() {
  // === SÜRE KONTROLÜ ===
  // Son tespitten bu yana 2 saniyeden az zaman geçmişse tehdit yazılarını koru.
  // Eğer 2 saniyeden fazla zaman geçmişse "Temiz" moduna geri dön.
  if (millis() - sonTespitZamani < veriTutmaSuresi) {
    NesneDurumu = sonDurumYazisi;
    mesafeYazisi = sonMesafeYazisi;
  } else {
    if (!NesneDurumu.contains("Arduino Aranıyor...") && !NesneDurumu.equals("KÜME ALARM!")) {
      NesneDurumu = "Arama Yapılıyor / Temiz";
    }
    mesafeYazisi = "---";
  }

  pushStyle();
  fill(0);
  noStroke();
  rect(0, height-80, width, 80); 
  popStyle();
  
  // Görsel Bildirim Rengi
  if (millis() - sonTespitZamani < veriTutmaSuresi) {
    fill(255, 50, 50); // Tehdit okunurken kırmızı font
  } else {
    fill(98, 245, 31); // Normal modda yeşil font
  }
  
  textSize(25);
  text("Durum: " + NesneDurumu, 85, height-35);
  
  fill(98, 245, 31); // Açı her zaman yeşil kalsın
  text("Radar Açısı: " + aci + "°", width/2-100, height-35);
  
  if (millis() - sonTespitZamani < veriTutmaSuresi) fill(255, 50, 50);
  text("Uzaklık: " + mesafeYazisi, width-310, height-35);
}

boolean ayniNesneMi(float x, float y){
  for (NesneIzi iz : izler) {
    float d = dist(x, y, iz.x, iz.y);
    if (d < 400) { 
      return true;
    }
  }
  return false;
}
