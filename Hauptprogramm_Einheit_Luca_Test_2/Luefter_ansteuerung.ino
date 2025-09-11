int Luefter_ansteuerung(int k, int l, const long delayauto) {
  DateTime now = rtc.now(); //Hole die aktuelle Zeit vom RTC-Modul

  static int z = 50; //Variable für Periode aber static das heist im programm veränderbar
  int var_dutyCycle = 0;
  unsigned long derzeitMillis = millis();
  byte a = now.hour();
  char Tage[7][12] = {"Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"}; // Array für die Wochentage

  bool toggle = ((millis() / delayauto) % 2) == 0;
  
  if ((Tage[now.dayOfTheWeek()] == "Montag" || "Dienstag" || "Mittwoch" || "Donnerstag" || "Freitag") && (a >= 6 && a <= 17)) {
    if (derzeitMillis - letzteMillis >= delayauto) {
      letzteMillis = derzeitMillis;
      if (toggle) {
        z = k;
        Serial.println("zuluft");
        //lastData = k;
      } else{
        z = l;
        Serial.println("abluft");
        //lastData = l;
      }
    }
  } else if ((now.day() >= 1 && now.day() <= 5) && a == 4) {
    z = 85;
  } else {
    z = 50;
  }
  var_dutyCycle = dutycycle(z); // Zahl gibt die Laufrichtung des Lüfters an
  OCR1A = map(var_dutyCycle, 0, 255, 0, ICR1);
  return var_dutyCycle;
}
