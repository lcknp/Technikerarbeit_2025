/******************************************************************************
 * Lüftungssteuerung V2.0
 * Author: Luca Knapp
 * Technikerarbeit FTS 2025/26
*******************************************************************************/

//Includes

//Bib Einbinden
#include "RTClib.h"                                         //Bibliothek für die Echtzeituhr
//Initialisierung 
RTC_DS1307 rtc;                                             //Initialisierung des RTC-Moduls

//Bib Einbinden
#include <DHT.h>                                            //Bibliothek für die Sesnoren
//Pin definitionen
#define DHT_Innen 4                                         //Pin für den inneren Sensor
#define DHT_Aussen 5                                        //Pin für den äußeren Sensor
//Initialisierung                                            
DHT dht1(DHT_Innen, DHT22);                                 //Pin und Typ den Sensor zuweisen
DHT dht2(DHT_Aussen, DHT22);                                //Pin und Typ den Sensor zuweisen


//Eigene Bib Einbinden
#include "zeitanpassung.h"
#include "ausgaben.h"
#include "luefter_ansteuerung.h"

//Pin definitionen
#define Luefter1 9                                          // Pin für Lüfter 1


//Nummer der Einheit//
byte einheit = 2;
//******************//

//************************************************************************************************************//
//Variablen declariren
//************************************************************************************************************//

byte k = 30;
byte l = 70;

long Zeitanpassung = 0;                                     //Variable für die Zeitanpassung
int var_dutyCycle;                                          //Variable für den Duty Cycle
byte mode = 1;                                              //MODE einstellung 0 = bedarfsorientierte lüftungen / 1 = Push/Pull auto mit intervall

//Timing und delays
unsigned long currentMillis = 0;

const long delaysekunde = 1000;                             //Zeit für Intervall / 1 Sekunde für Programmdurchlauf
unsigned long letzteMillis = 0;                             //Variable für Programmdurchlauf
unsigned long previousMillis = 0;                           //Speichert letzter Wert des durchgangs

const long delayauto = 300000;                               //Delay für Push/Pull belüftung 5 min

const unsigned long TIMEOUT = 15000;                         //timeout für btdata, d.h. wenn nach x(millis) nichts kommt schält er in mode 1
unsigned long lastReceiveTime = 0;                          //Variable für Letzte zeit die BT Data gesendet wurde


//************************************************************************************************************//
//Befehlssatz und BT Kommunikation
//************************************************************************************************************//

String btData = "";                                                   //raw Data
String strvalue;                                                      //stgvalue -> String Wert der in int konvertiert werden muss.
String cmd[] = {"day_name", "month", "day", "time", "year", "ctl"};   //Befehlssatz
String param;                                                         //<Parameter/Kommand>
int ctl = 50;                                                         //<Value/Wert>

//************************************************************************************************************//
//Zeitanpassung Raspi
//************************************************************************************************************//

String tage[] = {"Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"}; // Array für die Wochentage
String mon[] = {"Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};

int tempor; //Temporäre variable

//                 year, month, day, hour, minute, second
int rasp_time[6] = {0, 0, 0, 0, 0, 0};
int rasp_time_alt[6] = {0, 0, 0, 0, 0, 0};

String day_name_rasp;
String mon_rasp;
String time_rasp;

int cout_timerasp = 0;

//Zeitanpassung ohne Raspi / Nach einer Woche
int cout_timeadj = 0;

//************************************************************************************************************//

void btread(){

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
            rasp_time[1] = i + 1;
          }  
        }
      }
    if(param == cmd[2]){
        tempor = strvalue.toInt();
        if (tempor >= 1 && tempor <= 31) rasp_time[2] = tempor;
      }
    if(param == cmd[3]){
        time_rasp = strvalue;
        String stunden_str = time_rasp.substring(0, 2);
        String minuten_str = time_rasp.substring(3, 5);
        String sekunden_str = time_rasp.substring(6, 8);
        int stunden = stunden_str.toInt();
        int minuten = minuten_str.toInt();
        int sekunden = sekunden_str.toInt();
        
        if (stunden >= 0 && stunden <= 23) rasp_time[3] = stunden;
        if (minuten>= 0 && minuten <= 59) rasp_time[4] = minuten;
        if (sekunden >= 0 && sekunden <= 59) rasp_time[5] = sekunden;
      }
    if(param == cmd[4]){
        tempor = strvalue.toInt();
        if (tempor > 2000) rasp_time[0] = tempor;
      }
    if(param == cmd[5]){
        ctl = strvalue.toInt();
        
        if(ctl <= 0){
          k = 128;
          l = 128;
          }
        if(ctl > 0){
          l = map(ctl, 0, 100, 50, 0);
          k = map(ctl, 0, 100, 50, 100);
          }
    }

}

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
  currentMillis = millis();

  if (Serial.available()) {
    mode = 0; //Wenn Raspi Schickt mode 0 / Bedarfsorientiert
    btread(); //funktion btread
  }

  //Wenn Raspi nichts mehr sendet Mode umashcalten
  if (currentMillis - lastReceiveTime > TIMEOUT) { //lastReceiveTime wird in void btread() gesetzt
    mode = 1;
    k = 30;
    l = 70;
  } 

  //Zeitjustierung Automatisch wenn Raspi neue Daten liefert
  if (mode == 0 && (rasp_time[0] != rasp_time_alt[0] || rasp_time[1] != rasp_time_alt[1] || rasp_time[2] != rasp_time_alt[2] || rasp_time[3] != rasp_time_alt[3] || rasp_time[4] != rasp_time_alt[4]|| rasp_time[5] != rasp_time_alt[5])) {
    
    // Übergabe der neuen Zeit
    raspi_zeitanpassung(rasp_time[0], rasp_time[1], rasp_time[2], rasp_time[3], rasp_time[4], rasp_time[5]);

    // Alte Zeit speichern
    for (int i = 0; i < 6; i++) {
        rasp_time_alt[i] = rasp_time[i];
    }
    cout_timerasp++;
  }

  //Wöchentliche Zeitjustierung, um Abweichungen des RTC-Moduls zu korrigieren wenn der Raspi nichts Sendet
  if (mode == 0 && Zeitanpassung >= 604800000) {
      Zeitanpassung = zeitanpassung_auto(Zeitanpassung);
      cout_timeadj++;
  }

  if (currentMillis - previousMillis >= delaysekunde) {
    previousMillis = currentMillis;
    Zeitanpassung++;
    Serial.println("Mode:          " + String(mode));
    Serial.println("Fan:           " + String(ctl));
    Serial.println("bttime:        " + 
                   String(rasp_time[0]) + " " + 
                   String(rasp_time[1]) + " " + 
                   String(rasp_time[2]) + " " + 
                   String(rasp_time[3]) + " " + 
                   String(rasp_time[4]) + " " + 
                   String(rasp_time[5]));
    Serial.println("cout_timerasp: " + String(cout_timerasp));
    Datum_Zeit_ausgabe();                                                             // Funktionsaufruf zur Ausgabe des aktuellen Datums und der aktuellen Uhrzeit
    Serial.println("----------------------------------------------------------------------------------");
    Serial.print("unit=");
    Serial.println(einheit);
    Drehzahl_berechnung(var_dutyCycle);                                               // Funktionsaufruf zur Drehzahlberechnung
    Einmalige_Zeitanpassung();                                                        // Einmalige Zeitjustierung nach Programmstart
    var_dutyCycle = Luefter_ansteuerung(k, l, delayauto);                             // Funktionsaufruf zur Zeitabhängigen Lüfteransteuerung
    Sensor_auswertung();                                                              // Funktionsaufruf zur Ausgabe der aktuellen Temperatur und Feuchtigkeit
    Serial.println("----------------------------------------------------------------------------------");
  }
}
