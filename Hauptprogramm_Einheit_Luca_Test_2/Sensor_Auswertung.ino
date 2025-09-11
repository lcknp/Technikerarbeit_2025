void Sensor_auswertung() {
  float f1_innen; // Variable für die Luftfeuchtigkeit
  float t1_innen; // Variable für die Temperatur
  float f2_aussen; // Variable für die Luftfeuchtigkeit
  float t2_aussen; // Variable für die Temperatur

  // Lesen der Luftfeuchtigkeit und Temperatur von Sensor 1 (innen)
  f1_innen = dht1.readHumidity();
  t1_innen = dht1.readTemperature();

  // Lesen der Luftfeuchtigkeit und Temperatur von Sensor 2 (außen)
  f2_aussen = dht2.readHumidity();
  t2_aussen = dht2.readTemperature();

  // Überprüfen, ob die Werte von Sensor 1 gültig sind
  if (isnan(f1_innen) || isnan(t1_innen)) {
    // Fehlermeldung ausgeben, wenn das Lesen fehlgeschlagen ist
    Serial.println(F("Failed to read from DHT sensor!"));
    return; // Funktion beenden
  }

  // Überprüfen, ob die Werte von Sensor 2 gültig sind
  if (isnan(f2_aussen) || isnan(t2_aussen)) {
    // Fehlermeldung ausgeben, wenn das Lesen fehlgeschlagen ist
    Serial.println(F("Failed to read from DHT sensor!"));
    return; // Funktion beenden
  }

  // Ausgabe der Luftfeuchtigkeit und Temperatur von Sensor 1 (innen)
  Serial.print("Temp_Innen:     ");
  Serial.print(t1_innen);
  Serial.println(" °C ");
  Serial.print("Humi_Innen:     ");
  Serial.print(f1_innen);
  Serial.println(" %");

  // Ausgabe der Luftfeuchtigkeit und Temperatur von Sensor 2 (außen)
  Serial.print("Temp_Aussen:     ");
  Serial.print(t2_aussen);
  Serial.println(" °C");
  Serial.print("Humi_Aussen:     ");
  Serial.print(f2_aussen);
  Serial.println(" %");
}
