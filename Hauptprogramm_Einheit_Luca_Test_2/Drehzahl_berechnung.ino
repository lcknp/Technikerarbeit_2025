int Drehzahl_berechnung(int dutyCycle) {

  int y = 0;

  Serial.print("Drehzahl:       ");

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
  Serial.println(" U/min ");
}
