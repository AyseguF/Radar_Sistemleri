#include <Servo.h>

const int trigPin = 6;
const int echoPin = 7;
const int radarServoPin = 9;

Servo radarServo;
int mesafe;

void setup() {
  Serial.begin(9600);
  radarServo.attach(radarServoPin);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  // Eğer Python'dan bir kilitlenme açısı gelirse onu uygula
  if (Serial.available() > 0) {
    int kilitAci = Serial.parseInt();
    if (kilitAci >= 20 && kilitAci <= 160) {
       tara(kilitAci); 
       delay(500); // Hedefe odaklanması için bekle
       return; // loop'un başına dön, taramayı durdurmuş oluruz
    }
  }

  // Normal Tarama
  for (int i = 20; i <= 160; i++) { tara(i); }
  for (int i = 160; i >= 20; i--) { tara(i); }
}

void tara(int aci) {
  radarServo.write(aci);
  delay(20); // Servo hızı
  mesafe = mesafeOlc();
  Serial.print(aci);
  Serial.print("*");
  Serial.print(mesafe);
  Serial.println("#");
}

int mesafeOlc() {
  digitalWrite(trigPin, LOW); delayMicroseconds(2);
  digitalWrite(trigPin, HIGH); delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long sure = pulseIn(echoPin, HIGH, 26000);
  int cm = sure / 58;
  return (cm <= 2 || cm > 45) ? 50 : cm;
}