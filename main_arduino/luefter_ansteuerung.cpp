#include "luefter_ansteuerung.h"
#include <Arduino.h>
#include "RTClib.h"

// rtc kommt aus main
extern RTC_DS1307 rtc;

// ---------------- Dutycycle ----------------

int dutycycle(int Periode) {
  int var_dutyCycle = (Periode * 255) / 100;

  Serial.print("cycle=");
  Serial.println(var_dutyCycle);

  Serial.print("period=");
  Serial.print(Periode);
  Serial.println(" %");

  return var_dutyCycle;
}

// ---------------- Drehzahl-Berechnung ----------------

void Drehzahl_berechnung(int dutyCycle) {
  int y = 0;

  Serial.print("speed=");

  if (dutyCycle >= 114 && dutyCycle <= 140) {
    Serial.print("0");
  }
  else if (dutyCycle >= 229 && dutyCycle <= 255) {
    Serial.print("4250");
  }
  else if (dutyCycle >= 0 && dutyCycle <= 25) {
    Serial.print("4250");
  }
  else if (dutyCycle > 28 && dutyCycle < 99) {
    y = (-52.82 * dutyCycle) + 5728.96;
    Serial.print(y);
  }
  else if (dutyCycle > 155 && dutyCycle < 226) {
    y = (52.82 * dutyCycle) - 7687.1;
    Serial.print(y);
  }
  Serial.println(" U/min");
}

// ---------------- Lüfter-Automatik ----------------

int Luefter_ansteuerung_auto(int k, int l, const long pushpulldelay){
  DateTime now = rtc.now();

  static int z = 50;
  static unsigned long letzteMillis = 0;
  unsigned long derzeitMillis = millis();

  static bool toggle = 0;
  if (derzeitMillis - letzteMillis >= (unsigned long)pushpulldelay) {
    letzteMillis = derzeitMillis;
    toggle = ((millis() / pushpulldelay) % 2) == 0;
  }

  byte a         = now.hour();
  byte wochentag = now.dayOfTheWeek();

  if ((wochentag >= 1 && wochentag <= 5) && (a >= 6 && a <= 17)) {
    if (toggle) {
      z = k;
    } else {
      z = l;
    }
  }
  else if ((wochentag >= 1 && wochentag <= 5) && a == 4) {
    z = 85;
  } 
  else {
    z = 50;
  }

  int var_dutyCycle = dutycycle(z);
  OCR1A = map(var_dutyCycle, 0, 255, 0, ICR1);
  return var_dutyCycle;
}

// ---------------- Lüfter-Mode (Raspi-gesteuert) ----------------

int Luefter_ansteuerung_mode(int k, int l, int toggle){
  static int z = 50;

  if (toggle) {
    z = k;
  } else {
    z = l;
  }

  int var_dutyCycle = dutycycle(z);
  OCR1A = map(var_dutyCycle, 0, 255, 0, ICR1);
  return var_dutyCycle;
}
