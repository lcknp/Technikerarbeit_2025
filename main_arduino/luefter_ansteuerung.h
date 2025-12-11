#ifndef LUEFTER_ANSTEUERUNG_H
#define LUEFTER_ANSTEUERUNG_H

int  dutycycle(int Periode);
void Drehzahl_berechnung(int dutyCycle);

int  Luefter_ansteuerung_auto(int k, int l, const long pushpulldelay);
int  Luefter_ansteuerung_mode(int k, int l, int toggle);

#endif
