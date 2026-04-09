// =============================================================================
//  Projekt:      EBM-Papst Lüftungssteuerung – Technikerarbeit 2025/26
//  Datei:        bt.h
//  Autor:        Luca Knapp
//  Version:      1.0
//  Datum:        2025
//
//  Beschreibung: Header – Bluetooth-Kommunikation (HC-05)
//
//  Lizenz:
//   Dieses Projekt wurde im Rahmen der Technikerarbeit 2025/26 erstellt.
//   Nutzung und Weitergabe nur mit Erlaubnis des Autors.
//
// =============================================================================

#ifndef BT_H
#define BT_H

// Kümmert sich um das Einlesen einer BT-Zeile und das Setzen
// von ctl, toggle_bt, rasp_read, rasp_time[...] etc.
void btread();

#endif
