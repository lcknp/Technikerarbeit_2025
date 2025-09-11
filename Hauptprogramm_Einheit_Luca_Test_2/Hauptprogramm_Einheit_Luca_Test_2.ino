/******************************************************************************
 * Lüftungssteuerung V2.0
 * Author: Luca Knapp
 * Technikerarbeit FTS 2025/26
*******************************************************************************/

//Includes

#include "RTClib.h"                                         // Bibliothek für die Echtzeituhr
#include <DHT.h>                                            //Bibliothek für die Sesnoren

//Pin definitionen

#define DHT_Innen 4                                         //Pin für den inneren Sensor
#define DHT_Aussen 5                                        //Pin für den äußeren Sensor
#define Luefter1 9                                          // Pin für Lüfter 1

//Initialisierung

RTC_DS1307 rtc;                                             //Initialisierung des RTC-Moduls

DHT dht1(DHT_Innen, DHT22);                                 //Pin und Typ den Sensor zuweisen
DHT dht2(DHT_Aussen, DHT22);                                //Pin und Typ den Sensor zuweisen

//Nummer der Einheit//
byte einheit = 2;
//******************//

//Variablen declariren

byte x = 0;                                                 // Variable zur einmaligen Zeitjustierung
byte y = 0;                                                 //Variable wie oft die Zeitanpassung durchgeführt wurde

byte k = 30;
byte l = 70;
//int lastData;

long Zeitanpassung = 0;                                     // Variable für die Zeitanpassung
int var_dutyCycle;                                              // Variable für den Duty Cycle
byte mode = 1;                                              // MODE einstellung 0 = bedarfsorientierte lüftungen / 1 = Push/Pull mit delay interval2

//Timing und delays
unsigned long letzteMillis = 0;                             //Variable für Programmdurchlauf
const long delayauto = 20000;                              //Delay für Push/Pull belüftung / 300000
unsigned long previousMillis = 0;                           //Speichert letzter Wert des durchgangs
const long delaysekunde = 1000;                             //Zeit für Intervall / 1 Sekunde für Programmdurchlauf
const unsigned long TIMEOUT = 1500;                      //timeout für btdata
unsigned long lastReceiveTime = 0;                          //Variable für Letzte zeit die BT Data gesendet wurde

//Befehlssatz und BT Kommunikation
String btData = "50";                                       //raw Data
String strvalue;                                            //stgvalue -> String Wert der in int konvertiert werden muss.
String cmd[] = {"day_name", "month", "day", "time", "year", "ctl"};   //Befehlssatz
String param;                                               //<Parameter/Kommand>
int value = 0;                                              //<Value/Wert>
String ctl;                                                 //Controll

String tage[] = {"Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"}; // Array für die Wochentage
String mon[] = {"Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
String day_name_rasp;
int day_rasp;
String mon_rasp;
int month_num_rasp;
String time_rasp;
int second_rasp;
int minute_rasp;
int hour_rasp;
int year_rasp;

int temp;

int diffMin;
int diffSec;

//************************************************************************************************************//

void setup () {
  Serial.begin(9600); // Initialisierung der seriellen Kommunikation
  dht1.begin(); // Initialisierung des Sensors
  dht2.begin(); // Initialisierung des Sensors

  pinMode(Luefter1, OUTPUT); // Lüfter 1 als Ausgang

  // Timer1 Konfiguration für PWM
  TCCR1A = (1 << COM1A1) | (1 << COM1B1) | (1 << WGM11);
  TCCR1B = (1 << WGM13) | (1 << WGM12) | (1 << CS11);

  ICR1 = 999; // Setze den Top-Wert für den Timer

  // Initialisiere das RTC-Modul und überprüfe, ob es vorhanden ist
  while (! rtc.begin()) {
    Serial.println("Kein Real-Time-Clock Modul gefunden");
    Serial.flush();
    delay(1000);
  }

  // Überprüfe, ob das RTC-Modul läuft und stelle die Zeit ein, falls nicht
  /*if (! rtc.isrunning()) {
      Serial.println("Real-Time-Clock Modul läuft nicht, eine Zeit wird eingestellt");
      rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
     }
  */
  //rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
}

//************************************************************************************************************//

void loop () {

  DateTime now = rtc.now(); //Hole die aktuelle Zeit vom RTC-Modul

  // Berechne die Anzahl der Millisekunden seit Programmstart
  unsigned long currentMillis = millis();

  if (Serial.available()) {

    mode = 0;

    lastReceiveTime = currentMillis;
  
    btData = Serial.readStringUntil('\n');
    
    int seperator = btData.indexOf('=');

    if (seperator != -1) {
      param = btData.substring(0, seperator);
      strvalue = btData.substring(seperator + 1);
    }
    
    //value = strvalue.toInt();
    
    if(param == cmd[0]){
        day_name_rasp = strvalue;
      }
    if(param == cmd[1]){
        mon_rasp = strvalue;
        for(int i=0; i < 12; i++){
          if(mon_rasp == mon[i]){
            month_num_rasp = i + 1;
          }  
        }
      }
    if(param == cmd[2]){
        temp = strvalue.toInt();
        if (temp >= 1 && temp <= 31) day_rasp = temp;
      }
    if(param == cmd[3]){
        time_rasp = strvalue;
        String stunden_str = time_rasp.substring(0, 2);
        String minuten_str = time_rasp.substring(3, 5);
        String sekunden_str = time_rasp.substring(6, 8);
        int stunden = stunden_str.toInt();
        int minuten = minuten_str.toInt();
        int sekunden = sekunden_str.toInt();
        
        if (stunden >= 0 && stunden <= 23) hour_rasp = stunden;
        if (minuten>= 0 && minuten <= 59) minute_rasp = minuten;
        if (sekunden >= 0 && sekunden <= 59) second_rasp = sekunden;
      }
    if(param == cmd[4]){
        temp = strvalue.toInt();
        if (temp > 2000) year_rasp = temp;
      }
    if(param == cmd[5]){
        value = strvalue.toInt();
        //Serial.println(value);
        
        if(value <= 0){
          k = 128;
          l = 128;
          }
        if(value > 0){
          l = map(value, 0, 100, 50, 0);
          k = map(value, 0, 100, 50, 100);
          }
    }
  }

  if (currentMillis - lastReceiveTime > TIMEOUT) {
    mode = 1;
  } 

  //Mode 0 wenn Daten über den Raspi gesendet werden und Wenn Minute oder Sekunde +-2 ist dann anpassen
  if(mode == 0){
    diffMin = (now.minute() - minute_rasp + 60) % 60;   //bsp: 55 - 57 = -2 oder 3 + 60 = 63 --> ( -2 + 60 ) % 60 = 58 oder ( 3 + 60 ) % 60 = 3
    diffSec = (now.second() - second_rasp + 60) % 60;
    if(now.year() != year_rasp ||
       now.month() != month_num_rasp ||
       now.day() != day_rasp ||
       now.hour() != hour_rasp ||
       (diffMin > 10 && diffMin < 50) ||
       (diffSec > 10 && diffSec < 50)){
        
      rtc.adjust(DateTime(year_rasp, month_num_rasp, day_rasp, hour_rasp, minute_rasp, second_rasp));
      Serial.println("Zeitanpassung durch Raspi");
    }
  }
  
  // Wöchentliche Zeitjustierung, um Abweichungen des RTC-Moduls zu korrigieren
  if (Zeitanpassung >= 604800000) {
    rtc.adjust(DateTime(now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second() + 1)); // Nach 7 Tagen + 3 Sekunden
    Serial.println("Zeitanpassung +3 Sekunden");
    y++;
    Zeitanpassung = 0;
  }

  if (currentMillis - previousMillis >= delaysekunde) {
    previousMillis = currentMillis;
    Zeitanpassung++;
    Serial.print("Einheit: ");
    Serial.println(einheit);
    //Serial.print("BTData:        ");
    //Serial.println(btData);
    //Serial.println("Zeitanpassung: " + String(y) + "x");

    Datum_Zeit_ausgabe();                                                             // Funktionsaufruf zur Ausgabe des aktuellen Datums und der aktuellen Uhrzeit
    Drehzahl_berechnung(var_dutyCycle);                                               // Funktionsaufruf zur Drehzahlberechnung
    Einmalige_Zeitanpassung();                                                        // Einmalige Zeitjustierung nach Programmstart
    //Betriebszeit_berechnung();                                                      // Funktionsaufruf zur Berechnung und Ausgabe der Laufzeit der Einheit
    var_dutyCycle = Luefter_ansteuerung(k, l, delayauto);                             // Funktionsaufruf zur Zeitabhängigen Lüfteransteuerung
    Sensor_auswertung();                                                              // Funktionsaufruf zur Ausgabe der aktuellen Temperatur und Feuchtigkeit

    Serial.println("--------------------------------------------------------------------------");
  }
}
