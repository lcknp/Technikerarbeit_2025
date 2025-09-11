// Funktion zur Ausgabe des aktuellen Datums und der aktuellen Uhrzeit
void Datum_Zeit_ausgabe() {
  String Tage[] = {"Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"}; // Array für die Wochentage
  // Hole die aktuelle Zeit vom RTC-Modul
  DateTime now = rtc.now(); 
  
  // Ausgabe des Datums
  Serial.print("Datum:         ");
  if (now.day() < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn der Tag einstellig ist
  Serial.print(now.day(), DEC);
  Serial.print('.');
  if (now.month() < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn der Monat einstellig ist
  Serial.print(now.month(), DEC);
  Serial.print('.');
  Serial.print(now.year(), DEC); // Ausgabe des Jahres
  Serial.print(" ");
  
  // Ausgabe des Wochentags
  Serial.print(Tage[now.dayOfTheWeek()]); // Ausgabe des Wochentags basierend auf einem Array von Wochentagsnamen
  Serial.println(" ");
  
  // Ausgabe der Uhrzeit
  Serial.print("Uhrzeit:       ");
  if (now.hour() < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn die Stunde einstellig ist
  Serial.print(now.hour(), DEC);
  Serial.print(':');
  if (now.minute() < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn die Minute einstellig ist
  Serial.print(now.minute(), DEC);
  Serial.print(':');
  if (now.second() < 10) Serial.print("0"); // Füge eine führende Null hinzu, wenn die Sekunde einstellig ist
  Serial.print(now.second(), DEC);
  Serial.println(); // Neue Zeile für die nächste Ausgabe
}
