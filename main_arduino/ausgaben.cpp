// =============================================================================
//  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
//  Datei:        ausgaben.cpp
//  Autor:        Luca Knapp / Andreas Breitmoser (Vorprojekt)
//  Version:      1.0
//  Datum:        2025
//
//  Beschreibung: Ausgabe von Statusinformationen und Debug-Daten
//                (unverändert aus Vorprojekt übernommen)
//
//  Lizenz:
//   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
//   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
//
// =============================================================================

#include "ausgaben.h"
#include <Arduino.h>
#include "RTClib.h"
#include <DHT.h>

// rtc & DHT-Sensoren kommen aus main.ino
extern RTC_DS1307 rtc;
extern DHT dht1;
extern DHT dht2;

// ---------------- Sensor-Auswertung ----------------

void Sensor_auswertung() {
  float f1_aussen; // Luftfeuchtigkeit außen
  float t1_aussen; // Temperatur außen
  float f2_innen;  // Luftfeuchtigkeit innen
  float t2_innen;  // Temperatur innen

  f1_aussen = dht1.readHumidity();
  t1_aussen = dht1.readTemperature();

  f2_innen  = dht2.readHumidity();
  t2_innen  = dht2.readTemperature();

  if (isnan(f1_aussen) || isnan(t1_aussen)) {
    Serial.println(F("Failed to read from DHT sensor (aussen)!"));
    return;
  }

  if (isnan(f2_innen) || isnan(t2_innen)) {
    Serial.println(F("Failed to read from DHT sensor (innen)!"));
    return;
  }

  Serial.print("temp_out=");
  Serial.print(t1_aussen);
  Serial.println(" °C ");
  Serial.print("humi_out=");
  Serial.print(f1_aussen);
  Serial.println(" %");

  Serial.print("temp_in=");
  Serial.print(t2_innen);
  Serial.println(" °C");
  Serial.print("humi_in=");
  Serial.print(f2_innen);
  Serial.println(" %");
}

// ---------------- Datum/Uhrzeit-Ausgabe ----------------

void Datum_Zeit_ausgabe() {
  static const char* Tage[] = {
    "Sonntag", "Montag", "Dienstag", "Mittwoch",
    "Donnerstag", "Freitag", "Samstag"
  };

  DateTime now = rtc.now();

  Serial.print("Datum:         ");
  if (now.day() < 10) Serial.print("0");
  Serial.print(now.day(), DEC);
  Serial.print('.');
  if (now.month() < 10) Serial.print("0");
  Serial.print(now.month(), DEC);
  Serial.print('.');
  Serial.print(now.year(), DEC);
  Serial.print(" ");

  Serial.print(Tage[now.dayOfTheWeek()]);
  Serial.println(" ");

  Serial.print("Uhrzeit:       ");
  if (now.hour() < 10) Serial.print("0");
  Serial.print(now.hour(), DEC);
  Serial.print(':');
  if (now.minute() < 10) Serial.print("0");
  Serial.print(now.minute(), DEC);
  Serial.print(':');
  if (now.second() < 10) Serial.print("0");
  Serial.print(now.second(), DEC);
  Serial.println();
}
