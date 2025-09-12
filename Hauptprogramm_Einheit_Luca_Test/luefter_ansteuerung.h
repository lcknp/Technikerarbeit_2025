// Funktion zur Berechnung des Duty Cycles
int dutycycle(int Periode) {
  
  int var_dutyCycle = 0;
  // Berechnung des Duty Cycles basierend auf der Periode
  var_dutyCycle = (Periode * 255) / 100;
  Serial.print("cycle=");
  Serial.println(var_dutyCycle);

  // Ausgabe der Periode auf der seriellen Schnittstelle
  Serial.print("period=");
  Serial.print(Periode);
  Serial.println(" %");

  // Rückgabe des berechneten Duty Cycles
  return var_dutyCycle;
}

//********************************************************************************************************************************************

int Drehzahl_berechnung(int dutyCycle) {

  int y = 0;

  Serial.print("speed=");

  if (dutyCycle >= 114 && dutyCycle <= 140) {
    Serial.print("0");
  }
  else if (dutyCycle >= 229 && dutyCycle <= 255) {
    Serial.print("4250");
  }
  else if (dutyCycle >= 0 && dutyCycle <= 25) {
    Serial.print("4250");
  }
  else if (dutyCycle > 28 && dutyCycle < 99) {
    y = (-52.82 * dutyCycle) + 5728.96;
    Serial.print(y);
  }
  else if (dutyCycle > 155 && dutyCycle < 226) {
    y = (52.82 * dutyCycle) - 7687.1;
    Serial.print(y);
  }
  Serial.println(" U/min");
}

//********************************************************************************************************************************************

int Luefter_ansteuerung(int k, int l, const long pushpulldelay) {
  DateTime now = rtc.now(); //Hole die aktuelle Zeit vom RTC-Modul

  static int z = 50; //Variable für Periode aber static das heist im programm veränderbar
  static unsigned long letzteMillis = 0;
  unsigned long derzeitMillis = millis();
  
  char Tage[7][12] = {"Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"}; // Array für die Wochentage

  static bool toggle = 0;
  if (derzeitMillis - letzteMillis >= pushpulldelay) {
      letzteMillis = derzeitMillis;
      toggle = ((millis() / pushpulldelay) % 2) == 0;
  }
  byte a = now.hour();
  if ((Tage[now.dayOfTheWeek()] == "Montag" || "Dienstag" || "Mittwoch" || "Donnerstag" || "Freitag") && (a >= 6 && a <= 17)) {
      if (toggle) {
        z = k;
        //Serial.println("zuluft");
        //lastData = k;
      } else{
        z = l;
        //Serial.println("abluft");
        //lastData = l;
      }
    }
  else if ((now.day() >= 1 && now.day() <= 5) && a == 4) {
    z = 85;
  } 
  else {
    z = 50;
  }
  
  int var_dutyCycle = dutycycle(z); // Zahl gibt die Laufrichtung des Lüfters an
  OCR1A = map(var_dutyCycle, 0, 255, 0, ICR1);
  return var_dutyCycle;
}
