#include <Servo.h>

const int trigPin = 6;
const int echoPin = 7;
const int radarServoPin = 9;
const int kamServoPin = 5;

Servo radarServo, kamServo;

unsigned long eskiZaman = 0;
unsigned long handshakeZamani = 0; 
unsigned long sonSinyalZamani = 0; 
unsigned long sonKamZamani = 0; // Kamera servosu zamanlayıcısı

const int taramaHizi = 30; 
int aci = 0;
int yon = 1;
bool radarAktif = false; 

// === YENİ: YUMUŞAK KAMERA HAREKET DEĞİŞKENLERİ ===
int hedefKamAcisi = 90;   // Python'dan gelen gitmek istediğimiz açı
int mevcutKamAcisi = 90;  // Kameranın o anki fiziksel açısı
const int kamAdimHizi = 15; // Milisaniye cinsinden her 1 derecelik adımın hızı (Değeri büyütürsen daha da yavaşlar)

void setup() {
  Serial.begin(9600); 
  radarServo.attach(radarServoPin);
  kamServo.attach(kamServoPin);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  radarServo.write(aci);
  kamServo.write(mevcutKamAcisi); 
}

void loop() {
  // === BAĞLANTI GARANTİ BARİYERİ ===
  if (!radarAktif) {
    unsigned long simdiki = millis();
    if (simdiki - handshakeZamani >= 500) {
      handshakeZamani = simdiki;
      Serial.println("R#"); 
    }
  }

  // === TIMEOUT KONTROLÜ ===
  if (radarAktif && (millis() - sonSinyalZamani > 2500)) {
    radarAktif = false;
    Serial.println("TIMEOUT#");
  }

  // Komutları dinle
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "HEARTBEAT" || cmd == "RADAR:START" || cmd == "RADAR:DEVAM" || cmd.startsWith("CAM:")) {
      sonSinyalZamani = millis(); 
    }

    if (cmd.startsWith("CAM:")) {
      int gelenAci = cmd.substring(4).toInt();
      if (gelenAci >= 0 && gelenAci <= 180) {
        hedefKamAcisi = gelenAci; // Direkt servo yazdırmak yerine HEDEFE eşitledik
      }
    }
    else if (cmd == "RADAR:START" || cmd == "RADAR:DEVAM") {
      radarAktif = true;
    }
    else if (cmd == "RADAR:DUR") {
      radarAktif = false;
    }
  }

  // === YENİ: YUMUŞAK KAMERA TAKİP MOTORU ===
  if (millis() - sonKamZamani >= kamAdimHizi) {
    sonKamZamani = millis();
    if (mevcutKamAcisi < hedefKamAcisi) {
      mevcutKamAcisi++;
      kamServo.write(mevcutKamAcisi);
    } 
    else if (mevcutKamAcisi > hedefKamAcisi) {
      mevcutKamAcisi--;
      kamServo.write(mevcutKamAcisi);
    }
  }

  // Radar Aktifse Dönüş ve Ölçüm
  if (radarAktif) {
    unsigned long simdikiZaman = millis();
    if (simdikiZaman - eskiZaman >= taramaHizi) {
      eskiZaman = simdikiZaman;
      
      radarServo.write(aci);
      int mesafe = mesafeOlc();

      Serial.print(180-aci);
      Serial.print("*");
      Serial.print(mesafe);
      Serial.print("*");
      Serial.print(simdikiZaman);
      Serial.println("#");

      aci += (yon * 2); 
      if (aci <= 0 || aci >= 180) yon *= -1;
    }
  }
}

int mesafeOlc() {
  digitalWrite(trigPin, LOW); delayMicroseconds(2);
  digitalWrite(trigPin, HIGH); delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long sure = pulseIn(echoPin, HIGH, 20000);
  int cm = sure / 58;
  
  if (cm <= 4 || cm > 45 || sure == 0) {
    return 50; 
  }
  return cm;
}