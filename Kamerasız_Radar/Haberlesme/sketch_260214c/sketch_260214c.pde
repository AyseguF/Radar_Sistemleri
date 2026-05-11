import hypermedia.net.*; // UDP kütüphanesi (HyperMedia)

UDP udp; 
int aci = 0;
int mesafe = 0;
float hiz = 0;
String mesafeYazisi = "";
String NesneDurumu = "Beklemede";

ArrayList<NesneIzi> izler = new ArrayList<NesneIzi>();

// NesneIzi class'ın aynı kalıyor... (Kısaltmak için buraya yazmadım)

class NesneIzi {
  float x, y, parlaklik;
  NesneIzi(float _x, float _y) {
    x = _x;
    y = _y;
    parlaklik = 255; 
  }
  void guncelle() {
    parlaklik -= 5; // İzlerin silinme hızı (Gerektiğinde 2-10 arası ayarlanabilir)
  }
}

void setup() {
  size(1230, 800);
  udp = new UDP(this, 5005); // Python'un gönderdiği portu dinle
  udp.listen(true);
  smooth();
}

void draw() {
  fill(0, 20);
  noStroke();
  rect(0, 0, width, height);
  
  drawRadarCizgileri();
  drawTaramaCizgisi();
  drawNesne();
  drawText();
}

// BU KISIM DEĞİŞTİ: Artık veri Seri Port'tan değil UDP'den geliyor
void receive(byte[] data, String ip, int port) {
  String mesaj = new String(data);
  String[] list = split(mesaj, ',');
  
  if (list.length == 4) {
    aci = Integer.parseInt(list[0]);
    mesafe = Integer.parseInt(list[1]);
    hiz = float(list[2]);
    NesneDurumu = list[3];

    if (mesafe > 2 && mesafe < 45) {
      float pixMes = map(mesafe, 0, 45, 0, 600);
      float x = pixMes * cos(radians(-aci));
      float y = pixMes * sin(radians(-aci));
      if (!ayniNesneMi(x, y)) {
        izler.add(new NesneIzi(x,y));
      }
    }
  }
}

// Diğer drawRadarCizgileri, drawNesne vb. fonksiyonların AYNI kalıyor...


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
    text(a+"°", textX-10, textY);
  }
  line(-600, 0, 600, 0);
  popMatrix();
}

void drawTaramaCizgisi() {
  pushMatrix();
  translate(width/2, height-100);
  
  // Çizgi ayarları
  strokeWeight(5); // Biraz daha kalınlaştırdık
  stroke(0, 255, 0); // Parlak saf yeşil
  
  // Açı hesaplama (Radyan cinsinden)
  // Not: Eğer radar ters yöne gidiyorsa -aci yerine aci deneyebilirsin
  float x = 600 * cos(radians(-aci));
  float y = 600 * sin(radians(-aci));
  
  line(0, 0, x, y);
  
  // Ucundaki nokta
  fill(255, 255, 255); // Beyaz bir uç noktası daha görünür olur
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
  if (mesafe > 45) {
    NesneDurumu = "Aralık Dışında";
    mesafeYazisi = "---";
  } else {
    NesneDurumu = "Aralık İçinde";
    mesafeYazisi = mesafe + " cm";
  }

  fill(0);
  noStroke();
  rect(0, height-80, width, 80); 

  fill(98, 245, 31);
  textSize(25); 
  text("Durum: " + NesneDurumu, 85, height-35);
  text("Anlık Açı: " + aci + "°",width/2-60, height-35);
  text("Mesafe: " + mesafeYazisi,width-310, height-35);
  
}

boolean ayniNesneMi(float x, float y){
  for (NesneIzi iz : izler) {
    float d = dist(x, y, iz.x, iz.y);
    if (d < 80) { // 50 piksel tolerans
      return true;
    }
  }
  return false;
}
