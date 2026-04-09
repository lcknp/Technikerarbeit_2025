// =============================================================================
//  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
//  Datei:        luefter_ansteuerung.h
//  Autor:        Luca Knapp
//  Version:      1.0
//  Datum:        2025
//
//  Beschreibung: Header – Lüfteransteuerung (PWM, Push/Pull, Automatikbetrieb)
//
//  Lizenz:
//   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
//   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
//
// =============================================================================

#ifndef LUEFTER_ANSTEUERUNG_H
#define LUEFTER_ANSTEUERUNG_H

int  dutycycle(int Periode);
void Drehzahl_berechnung(int dutyCycle);

int  Luefter_ansteuerung_auto(int k, int l, const long pushpulldelay);
int  Luefter_ansteuerung_mode(int k, int l, int toggle);

#endif
