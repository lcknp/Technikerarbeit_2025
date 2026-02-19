/******************************************************************************
*  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
*  Datei:        main_arduino.ino
*  Autor:        Luca Knapp
*  Version:      3.0
*  Datum:        2025
*
*  Beschreibung:
*  ---------------------------------------------------------------------------
*  Dieses Projekt implementiert eine Lüftungssteuerung auf einem Arduino, die
*  mit einem Raspberry Pi kommuniziert. Es werden Sensorwerte von DHT22-Sensoren
*  erfasst, die Zeit über eine RTC verwaltet und die Lüftergeschwindigkeit basierend
*  auf den Sensorwerten und Befehlen vom Raspberry Pi gesteuert. Das Projekt
*  ist in zwei Modi konfigurierbar: bedarfsorientiert (Mode 0) und Automatik mit
*  (Mode 1).
*
*  Lizenz:
*   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
*   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
*
*******************************************************************************/


#include <Arduino.h>
#include <string.h>
#include <stdlib.h>

#include "RTClib.h"
#include <DHT.h>

// -------------------- Pins --------------------
#define DHT_Innen  4            // innerer Sensor
#define DHT_Aussen 5            // äußerer Sensor
#define Luefter1   9            // Lüfter-PWM

// -------------------- Hardware-Objekte --------------------
RTC_DS1307 rtc;                 // RTC-Modul

DHT dht1(DHT_Innen, DHT22);
DHT dht2(DHT_Aussen, DHT22);

// -------------------- eigene Module --------------------
#include "bt.h"
#include "zeitanpassung.h"
#include "luefter_ansteuerung.h"
#include "ausgaben.h"

// -------------------- Konfiguration --------------------
byte einheit = 1;               // Nummer der Einheit

//************************************************************************************************************//
// Globale Variablen
//************************************************************************************************************//

byte k = 30;                      //Variablen für PWM
byte l = 70;                      //Variablen für PWM

long Zeitanpassung = 0;            // Zähler für automatische Zeitkorrektur
int  var_dutyCycle;                // aktueller Duty Cycle
byte mode = 1;                     // 0 = bedarfsorientiert, 1 = Automatik mit Intervall

unsigned long currentMillis = 0;
const unsigned long delaysekunde   = 1000;   // 1 s
unsigned long previousMillis = 0;

// Push/Pull-Verzögerung
long pushpulldelay = 30000;                 // ms
byte toggle = 0;

// Timeout für BT-Daten
const unsigned long TIMEOUT = 60000UL;      // 60 s
unsigned long lastReceiveTime = 0;          // letzte BT-Aktivität

// -------------------- BT-relevante globale Variablen --------------------
// werden von bt.cpp beschrieben

// Lüftersteuerungswert vom Raspi
int  ctl = 50;           // 0..100
byte rasp_read = 0;      // Raspi will Messwerte
// Togglestatus kommt vom Raspi
// (für Luefter_ansteuerung_mode)
byte toggle_bt = 0;

// Zeit vom Raspi
//              year, month, day, hour, minute, second
int rasp_time[6]     = {0, 0, 0, 0, 0, 0};
int rasp_time_alt[6] = {0, 0, 0, 0, 0, 0};

// Strings für Zeitinfos vom Raspi (optional nutzbar)
char day_name_rasp[12];
char mon_rasp[4];
char time_rasp[9];

//************************************************************************************************************//
// Setup
//************************************************************************************************************//

void setup () {
  Serial.begin(9600);
  Serial.setTimeout(50);       // Timeout für die BT-Lese-Funktionen

  dht1.begin();
  dht2.begin();

  pinMode(Luefter1, OUTPUT);

  // Timer1 für PWM konfigurieren
  TCCR1A = (1 << COM1A1) | (1 << COM1B1) | (1 << WGM11);
  TCCR1B = (1 << WGM13) | (1 << WGM12) | (1 << CS11);
  ICR1 = 999; // TOP-Wert für Timer1

  // RTC initialisieren
  while (!rtc.begin()) {
    Serial.println("Kein Real-Time-Clock Modul gefunden");
    Serial.flush();
    delay(1000);
  }

  // Zeit initial setzen (Compile-Zeitpunkt)
  rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));

  lastReceiveTime = millis();
}

//************************************************************************************************************//
// Loop
//************************************************************************************************************//

void loop () {

  DateTime now = rtc.now();
  (void)now; // nur um Compiler-Warnung zu vermeiden, falls unbenutzt

  currentMillis = millis();

  // ------------ BT-Empfang ------------
  if (Serial.available()) {
    mode = 0;                         // Bedarfsorientiert
    lastReceiveTime = currentMillis;
    btread();                         // in bt.cpp implementiert
  }

  // ------------ Timeout -> Automatik ------------
  if ((currentMillis - lastReceiveTime) > TIMEOUT) {
    mode           = 1;
    k              = 30;
    l              = 70;
    pushpulldelay  = 30000;
  }

  // ------------ Zeitjustierung per Raspi ------------
  bool neueZeitVomRaspi =
    (rasp_time[0] != rasp_time_alt[0] ||
     rasp_time[1] != rasp_time_alt[1] ||
     rasp_time[2] != rasp_time_alt[2] ||
     rasp_time[3] != rasp_time_alt[3] ||
     rasp_time[4] != rasp_time_alt[4] ||
     rasp_time[5] != rasp_time_alt[5]);

  if (mode == 0 && neueZeitVomRaspi) {
    raspi_zeitanpassung(rasp_time[0], rasp_time[1], rasp_time[2],
                        rasp_time[3], rasp_time[4], rasp_time[5]);

    for (int i = 0; i < 6; i++) {
      rasp_time_alt[i] = rasp_time[i];
    }
  }

  // ------------ Wöchentliche RTC-Korrektur ------------
  if (mode == 0 && Zeitanpassung >= 604800000) {
    Zeitanpassung = zeitanpassung_auto(Zeitanpassung);
    // optional: cout_timeadj++ o.ä.
  }

  // ------------ Mode 0: Bedarfsorientiert ------------
  if (mode == 0) {
    if (rasp_read == 1) {
      rasp_read = 0;

      Serial.print("Mode:          ");
      Serial.println(mode);

      Serial.print("Fan:           ");
      Serial.println(ctl);

      Serial.print("bttime:        ");
      Serial.print(rasp_time[0]);
      Serial.print(" ");
      Serial.print(rasp_time[1]);
      Serial.print(" ");
      Serial.print(rasp_time[2]);
      Serial.print(" ");
      Serial.print(rasp_time[3]);
      Serial.print(" ");
      Serial.print(rasp_time[4]);
      Serial.print(" ");
      Serial.println(rasp_time[5]);

      Datum_Zeit_ausgabe();
      Serial.println("----------------------------------------------------------------------------------");
      Serial.print("unit=");
      Serial.println(einheit);

      Drehzahl_berechnung(var_dutyCycle);
      Einmalige_Zeitanpassung();

      var_dutyCycle = Luefter_ansteuerung_mode(k, l, toggle_bt);

      Sensor_auswertung();
      Serial.println("----------------------------------------------------------------------------------");
    }
  }

  // ------------ Mode 1: Automatik ------------
  if (mode == 1) {
    if (currentMillis - previousMillis >= delaysekunde) {
      previousMillis = currentMillis;
      Zeitanpassung++;

      Serial.print("Mode:          ");
      Serial.println(mode);

      Serial.print("Fan:           ");
      Serial.println(ctl);

      Serial.print("bttime:        ");
      Serial.print(rasp_time[0]);
      Serial.print(" ");
      Serial.print(rasp_time[1]);
      Serial.print(" ");
      Serial.print(rasp_time[2]);
      Serial.print(" ");
      Serial.print(rasp_time[3]);
      Serial.print(" ");
      Serial.print(rasp_time[4]);
      Serial.print(" ");
      Serial.println(rasp_time[5]);

      Datum_Zeit_ausgabe();
      Serial.println("----------------------------------------------------------------------------------");

      Serial.print("unit=");
      Serial.println(einheit);

      Drehzahl_berechnung(var_dutyCycle);
      Einmalige_Zeitanpassung();
      var_dutyCycle = Luefter_ansteuerung_auto(k, l, pushpulldelay);

      Sensor_auswertung();
      Serial.println("----------------------------------------------------------------------------------");
    }
  }
}
