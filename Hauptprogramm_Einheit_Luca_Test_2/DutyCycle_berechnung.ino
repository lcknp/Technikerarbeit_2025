// Funktion zur Berechnung des Duty Cycles
int dutycycle(int Periode) {
  
  int var_dutyCycle = 0;
  // Berechnung des Duty Cycles basierend auf der Periode
  var_dutyCycle = (Periode * 255) / 100;
  Serial.print("Cycle:         ");
  Serial.println(var_dutyCycle);

  // Ausgabe der Periode auf der seriellen Schnittstelle
  Serial.print("Periode:       ");
  Serial.print(Periode);
  Serial.println(" %");

  // Rückgabe des berechneten Duty Cycles
  return var_dutyCycle;
}
