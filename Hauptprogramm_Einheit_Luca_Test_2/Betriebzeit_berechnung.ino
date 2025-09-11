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
