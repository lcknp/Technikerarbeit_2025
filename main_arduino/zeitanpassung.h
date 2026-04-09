// =============================================================================
//  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
//  Datei:        zeitanpassung.h
//  Autor:        Luca Knapp
//  Version:      1.0
//  Datum:        2025
//
//  Beschreibung: Header – Zeitsynchronisation mit dem Raspberry Pi
//
//  Lizenz:
//   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
//   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
//
// =============================================================================

#ifndef ZEITANPASSUNG_H
#define ZEITANPASSUNG_H

int  zeitanpassung_auto(int Zeitanpassung);
void Einmalige_Zeitanpassung();
void raspi_zeitanpassung(int year_rasp, int month_num_rasp, int day_rasp,
                         int hour_rasp, int minute_rasp, int second_rasp);
void Betriebszeit_berechnung();

#endif
