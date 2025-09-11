void Einmalige_Zeitanpassung() {
  
  DateTime now = rtc.now();
  if (x == 1) {
    rtc.adjust(DateTime(now.year(), now.month(), now.day(), now.hour() - 1, now.minute(), now.second() + 9)); // Sekunden +9 wegen Verzögerung beim Hochladen
    Serial.println("Zeit justiert");
    x = 0;
    Serial.println("x = " + String(x));
  }
}
