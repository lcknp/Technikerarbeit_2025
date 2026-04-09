// =============================================================================
//  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
//  Datei:        bt.cpp
//  Autor:        Luca Knapp
//  Version:      1.0
//  Datum:        2025
//
//  Beschreibung: Implementierung der Bluetooth-Kommunikation (HC-05)
//
//  Lizenz:
//   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
//   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
//
// =============================================================================

#include "bt.h"
#include <Arduino.h>
#include <string.h>
#include <stdlib.h>

// -------------------- externe Variablen aus main.ino --------------------

extern int  ctl;               // Lüfterleistung vom Raspi (0–100)
extern byte rasp_read;         // Flag: Raspi will Daten lesen
extern byte toggle_bt;         // Richtungsumschaltung vom Raspi

extern int rasp_time[6];       // Zeitdaten vom Raspi: year, month, day, hour, minute, second
extern char day_name_rasp[12]; // Wochentag vom Raspi als Text
extern char mon_rasp[4];       // Monat vom Raspi als Text (Jan, Feb, ...)
extern char time_rasp[9];      // Uhrzeit vom Raspi als Text (HH:MM:SS)

extern byte k;                 // PWM-Grenzwert 1 (wird aus ctl berechnet)
extern byte l;                 // PWM-Grenzwert 2 (wird aus ctl berechnet)

// -------------------- interne Puffer --------------------
// Alles, was nur für die BT-Verarbeitung gebraucht wird

// Zeilenpuffer für eine eingehende BT-Zeile, z.B. "ctl=50"
static char btLine[64];    // max. Zeilenlänge (an Protokoll angepasst)
static char btKey[16];     // Schlüssel-Teil vor dem '='
static char btValue[32];   // Wert-Teil nach dem '='

// Befehlssatz als C-Strings, Reihenfolge ist egal, wird nur für strcmp genutzt
static const char* cmd[] = {
  "day_name",   // 0
  "month",      // 1
  "day",        // 2
  "time",       // 3
  "year",       // 4
  "ctl",        // 5
  "toggle",     // 6
  "rasp_read"   // 7
};

// Monatsnamen, um "Jan" 1, "Feb" 2 usw. umzusetzen
static const char* monName[] = {
  "Jan", "Feb", "Mar", "Apr", "Mai", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
};

// temporäre Variable für Umrechnungen
static int tempor = 0;

// -------------------- Hilfsfunktionen --------------------

// Liest eine komplette Zeile bis '\n' in btLine.
// Gibt true zurück, wenn etwas gelesen wurde.
// Achtung: Timeout wird über Serial.setTimeout() im setup() eingestellt.
static bool read_bt_line() {
  // liest bis '\n', max. (sizeof(btLine)-1) Zeichen
  size_t len = Serial.readBytesUntil('\n', btLine, sizeof(btLine) - 1);
  if (len == 0) {
    // es kam innerhalb des Timeouts nichts an
    return false;
  }

  // String sauber terminieren
  btLine[len] = '\0';

  // Wenn die Zeile mit "\r\n" endet, das '\r' noch wegschneiden
  if (len > 0 && btLine[len - 1] == '\r') {
    btLine[len - 1] = '\0';
  }

  return true;
}

// Parst "key=value" aus btLine in btKey und btValue.
// Gibt true zurück, wenn ein '=' gefunden wurde.
static bool parse_key_value() {
  // Trennzeichen suchen
  char* sep = strchr(btLine, '=');
  if (!sep) {
    // Kein '=' ungültige Zeile fürs Protokoll
    return false;
  }

  // String an der Stelle auftrennen
  *sep = '\0';
  char* key   = btLine;   // alles vor '='
  char* value = sep + 1;  // alles nach '='

  // In die globalen Buffer kopieren (mit Länge begrenzt)
  strncpy(btKey, key, sizeof(btKey) - 1);
  btKey[sizeof(btKey) - 1] = '\0';

  strncpy(btValue, value, sizeof(btValue) - 1);
  btValue[sizeof(btValue) - 1] = '\0';

  return true;
}

// -------------------- öffentliche Funktion --------------------
// Wird von main.ino aufgerufen, sobald Daten auf der seriellen Schnittstelle anliegen

void btread() {
  // Erst versuchen, eine komplette Zeile einzulesen
  if (!read_bt_line()) {
    return;   // nichts sinnvolles angekommen
  }

  // Dann "key=value" daraus machen
  if (!parse_key_value()) {
    return;   // keine gültige Protokollzeile
  }

  // Ab hier stehen btKey und btValue bereit und werden ausgewertet

  // ---------------- day_name ----------------
  if (strcmp(btKey, cmd[0]) == 0) {
    // Wochentags-String vom Raspi merken
    strncpy(day_name_rasp, btValue, sizeof(day_name_rasp) - 1);
    day_name_rasp[sizeof(day_name_rasp) - 1] = '\0';
  }

  // ---------------- month ----------------
  else if (strcmp(btKey, cmd[1]) == 0) {
    // Monat als Text merken, z.B. "Jan"
    strncpy(mon_rasp, btValue, sizeof(mon_rasp) - 1);
    mon_rasp[sizeof(mon_rasp) - 1] = '\0';

    // passenden Monatsindex 1..12 in rasp_time[1] schreiben
    for (int i = 0; i < 12; i++) {
      if (strcmp(mon_rasp, monName[i]) == 0) {
        rasp_time[1] = i + 1;
        break;
      }
    }
  }

  // ---------------- day ----------------
  else if (strcmp(btKey, cmd[2]) == 0) {
    tempor = atoi(btValue);
    if (tempor >= 1 && tempor <= 31) {
      rasp_time[2] = tempor;
    }
  }

  // ---------------- time HH:MM:SS ----------------
  else if (strcmp(btKey, cmd[3]) == 0) {
    // Uhrzeit-Text übernehmen
    strncpy(time_rasp, btValue, sizeof(time_rasp) - 1);
    time_rasp[sizeof(time_rasp) - 1] = '\0';

    // Nur wenn Format mindestens "HH:MM:SS" (8 Zeichen) ist
    if (strlen(time_rasp) >= 8) {
      char h_str[3] = { time_rasp[0], time_rasp[1], '\0' };
      char m_str[3] = { time_rasp[3], time_rasp[4], '\0' };
      char s_str[3] = { time_rasp[6], time_rasp[7], '\0' };

      int stunden  = atoi(h_str);
      int minuten  = atoi(m_str);
      int sekunden = atoi(s_str);

      if (stunden  >= 0 && stunden  <= 23) rasp_time[3] = stunden;
      if (minuten  >= 0 && minuten  <= 59) rasp_time[4] = minuten;
      if (sekunden >= 0 && sekunden <= 59) rasp_time[5] = sekunden;
    }
  }

  // ---------------- year ----------------
  else if (strcmp(btKey, cmd[4]) == 0) {
    tempor = atoi(btValue);
    if (tempor > 2000) {
      rasp_time[0] = tempor;
    }
  }

  // ---------------- ctl (Lüfterleistung) ----------------
  else if (strcmp(btKey, cmd[5]) == 0) {
    // 0..100 vom Raspi
    ctl = atoi(btValue);

    // ctl = 0 → Lüfter neutral (128/128)
    if (ctl <= 0) {
      k = 128;
      l = 128;
    } else {
      // Mapping von 0..100 auf die beiden Parameter k, l
      l = map(ctl, 0, 100, 50, 0);
      k = map(ctl, 0, 100, 50, 100);
    }
  }

  // ---------------- toggle (Richtung) ----------------
  else if (strcmp(btKey, cmd[6]) == 0) {
    // 0/1 vom Raspi für Richtung
    toggle_bt = (byte)atoi(btValue);
  }

  // ---------------- rasp_read (Raspi will Daten lesen) ----------------
  else if (strcmp(btKey, cmd[7]) == 0) {
    // Flag setzen, wird in main.ino wieder auf 0 zurückgesetzt,
    // nachdem die Daten ausgegeben wurden
    rasp_read = 1;
  }

  // andere Keys werden ignoriert
}
