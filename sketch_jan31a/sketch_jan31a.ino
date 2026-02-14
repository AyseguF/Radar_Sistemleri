#include <Servo.h>

// --- Pinler ---
const int trigPin = 6;
const int echoPin = 7;
const int radarServoPin = 9;

// --- Servo ---
Servo radarServo;

// --- Ölçüm ---
long sure;
int mesafe;

void setup() {
  Serial.begin(9600);
  radarServo.attach(radarServoPin);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  radarServo.write(90);
}

void loop() {

  // 20° → 160°
  for (int aci = 20; aci <= 160; aci++) {
    tara(aci);
  }

  // 160° → 20°
  for (int aci = 160; aci >= 20; aci--) {
    tara(aci);
  }
}

void tara(int aci) {
  radarServo.write(aci);
  delay(15);

  mesafe = mesafeOlc();

  // Format: Açı*Mesafe#
  Serial.print(aci);
  Serial.print("*");
  Serial.print(mesafe);
  Serial.println("#");
}

int mesafeOlc() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  sure = pulseIn(echoPin, HIGH, 26000);
  int cm = sure / 58;

  if (cm <= 2 || cm > 45) return 50; // menzil dışı
  return cm;
}
