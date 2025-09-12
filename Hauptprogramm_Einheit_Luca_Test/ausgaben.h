void Sensor_auswertung() {
  float f1_aussen; // Variable für die Luftfeuchtigkeit
  float t1_aussen; // Variable für die Temperatur
  float f2_innen; // Variable für die Luftfeuchtigkeit
  float t2_innen; // Variable für die Temperatur

  // Lesen der Luftfeuchtigkeit und Temperatur von Sensor 1 (außen)
  f1_aussen = dht1.readHumidity();
  t1_aussen = dht1.readTemperature();

  // Lesen der Luftfeuchtigkeit und Temperatur von Sensor 2 (innen)
  f2_innen = dht2.readHumidity();
  t2_innen = dht2.readTemperature();

  // Überprüfen, ob die Werte von Sensor 1 gültig sind
  if (isnan(f1_aussen) || isnan(t1_aussen)) {
    // Fehlermeldung ausgeben, wenn das Lesen fehlgeschlagen ist
    Serial.println(F("Failed to read from DHT sensor!"));
    return; // Funktion beenden
  }

  // Überprüfen, ob die Werte von Sensor 2 gültig sind
  if (isnan(f2_innen) || isnan(t2_innen)) {
    // Fehlermeldung ausgeben, wenn das Lesen fehlgeschlagen ist
    Serial.println(F("Failed to read from DHT sensor!"));
    return; // Funktion beenden
  }

  // Ausgabe der Luftfeuchtigkeit und Temperatur von Sensor 1 (außen)
  Serial.print("temp_out=");
  Serial.print(t1_aussen);
  Serial.println(" °C ");
  Serial.print("humi_out=");
  Serial.print(f1_aussen);
  Serial.println(" %");

  // Ausgabe der Luftfeuchtigkeit und Temperatur von Sensor 2 (innen)
  Serial.print("temp_in=");
  Serial.print(t2_innen);
  Serial.println(" °C");
  Serial.print("humi_in=");
  Serial.print(f2_innen);
  Serial.println(" %");
}


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
