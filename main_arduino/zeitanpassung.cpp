#include "zeitanpassung.h"
#include <Arduino.h>
#include "RTClib.h"

// rtc kommt aus main.ino
extern RTC_DS1307 rtc;

void Einmalige_Zeitanpassung() {

  static byte x = 0; // Variable zur einmaligen Zeitjustierung

  DateTime now = rtc.now();
  if (x == 1) {
    rtc.adjust(DateTime(now.year(), now.month(), now.day(),
                        now.hour() - 1, now.minute(), now.second() + 9));
    Serial.println("Zeit justiert");
    x = 0;
    Serial.print("x = ");
    Serial.println(x);
  }
}

void raspi_zeitanpassung(int year_rasp, int month_num_rasp, int day_rasp,
                         int hour_rasp, int minute_rasp, int second_rasp){
  rtc.adjust(DateTime(year_rasp, month_num_rasp, day_rasp,
                      hour_rasp, minute_rasp, second_rasp));
  Serial.println("Zeitanpassung durch Raspi");
}

int zeitanpassung_auto(int Zeitanpassung){
  DateTime now = rtc.now();
  rtc.adjust(DateTime(now.year(), now.month(), now.day(),
                      now.hour(), now.minute(), now.second() + 1));
  Serial.println("Zeitanpassung +3 Sekunden");
  Zeitanpassung = 0;
  return Zeitanpassung;
}

// Funktion zur Berechnung und Ausgabe der Laufzeit der Einheit
void Betriebszeit_berechnung() {
  byte Sek = 0;
  byte Min = 0;
  byte Std = 0;
  byte Tag = 0;

  unsigned long ms = millis();

  Sek = (ms / 1000) % 60;
  Min = (ms / 60000) % 60;
  Std = (ms / 3600000) % 24;
  Tag = (ms / 86400000);

  Serial.print("Laufzeit:      ");
  Serial.print(Tag);
  Serial.print(":");
  if (Std < 10) Serial.print("0");
  Serial.print(Std);
  Serial.print(":");
  if (Min < 10) Serial.print("0");
  Serial.print(Min);
  Serial.print(":");
  if (Sek < 10) Serial.print("0");
  Serial.println(Sek);
}
