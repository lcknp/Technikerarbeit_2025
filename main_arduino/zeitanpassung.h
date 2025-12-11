#ifndef ZEITANPASSUNG_H
#define ZEITANPASSUNG_H

int  zeitanpassung_auto(int Zeitanpassung);
void Einmalige_Zeitanpassung();
void raspi_zeitanpassung(int year_rasp, int month_num_rasp, int day_rasp,
                         int hour_rasp, int minute_rasp, int second_rasp);
void Betriebszeit_berechnung();

#endif
