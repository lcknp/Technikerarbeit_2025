void Einmalige_Zeitanpassung() {

  static byte x = 0;// Variable zur einmaligen Zeitjustierung Static also nur am Start 0
  
  DateTime now = rtc.now();
  if (x == 1) {
    rtc.adjust(DateTime(now.year(), now.month(), now.day(), now.hour() - 1, now.minute(), now.second() + 9)); // Sekunden +9 wegen Verzögerung beim Hochladen
    Serial.println("Zeit justiert");
    x = 0;
    Serial.println("x = " + String(x));
  }
}

void raspi_zeitanpassung(int year_rasp, int month_num_rasp, int day_rasp, int hour_rasp, int minute_rasp, int second_rasp){

      rtc.adjust(DateTime(year_rasp, month_num_rasp, day_rasp, hour_rasp, minute_rasp, second_rasp));
      Serial.println("Zeitanpassung durch Raspi");
}


int zeitanpassung_auto(int Zeitanpassung){

  DateTime now = rtc.now(); //Hole die aktuelle Zeit vom RTC-Modul
  
  rtc.adjust(DateTime(now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second() + 1)); // Nach 7 Tagen + 3 Sekunden
    Serial.println("Zeitanpassung +3 Sekunden");
    Zeitanpassung = 0;
    return Zeitanpassung;
}

// Funktion zur Berechnung und Ausgabe der Laufzeit der Einheit
void Betriebszeit_berechnung() {
  byte Sek = 0; // Sekunden
  byte Min = 0; // Minuten
  byte Std = 0; // Stunden
  byte Tag = 0; // Tag
  
  // Berechnung der Sekunden, Minuten und Stunden seit dem Start des Programms
  Sek = (millis() / 1000) % 60;
  Min = (millis() / 60000) % 60;
  Std = (millis() / 3600000) % 24;
  Tag = (millis() / 86400000);
  // Ausgabe der Laufzeit im Format HH:MM:SS
  Serial.print("Laufzeit:      ");
  Serial.print(Tag);
  Serial.print(":");
  if (Std < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn die Stunde einstellig ist
  Serial.print(Std);
  Serial.print(":");
  if (Min < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn die Minute einstellig ist
  Serial.print(Min);
  Serial.print(":");
  if (Sek < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn die Sekunde einstellig ist
  Serial.println(Sek);
}
