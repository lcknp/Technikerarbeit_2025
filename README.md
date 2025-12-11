# Technikerarbeit_2025

Meine Technikerareit 2025/26


Monitoring & Steuerung – PASCO₂/BME280 (Raspberry Pi)

Arduino sind verbunden mit den Einheiten

Autor: Luca Knapp

## Installation auf dem Raspberry Pi (Python)

### 1. Voraussetzungen

- Raspberry Pi mit Raspberry Pi OS (mit Internetzugang)
- CO₂-Sensor PASCO2 per I²C (Adresse 0x28)
- BME280 Sensor per I²C (typisch 0x76 oder 0x77)

#### I²C aktivieren

```bash
sudo raspi-config
 ...) – BME280/PAS-Werte
	•	für jede BT-Einheit (wenn Daten vorhanden): funktion_db.databasesafe(f"ardu{row[0]}", ...) – Innen/Außen-Werte
sudo reboot
```
Repository klonen
```bash
cd ~
git clone https://github.com/lcknp/Technikerarbeit_2025.git
cd Technikerarbeit_2025
```

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip

python3 -m venv .venv
source .venv/bin/activate

```
Systempakete
```bash
sudo apt install -y \
  python3-smbus \
  i2c-tools \
  bluetooth \
  bluez \
  libbluetooth-dev \
  mariadb-server
```
Python-Abhängigkeiten
```bash
pip install --upgrade pip
pip install \
  adafruit-blinka \
  adafruit-circuitpython-bme280 \
  smbus2 \
  pybluez \
  pymysql \
  flask
```
Datenbank einrichten
```bash
sudo mysql

CREATE DATABASE data;
CREATE USER 'luca'@'localhost' IDENTIFIED BY '12345678';
GRANT ALL PRIVILEGES ON data.* TO 'luca'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Web-Verzeichnis
```bash
/var/www/html/latest.json
sudo chown -R $USER:$USER /var/www/html
```

Script starten
```bash
cd ~/Technikerarbeit_2025

Mit Virtualenv
source .venv/bin/activate
sudo .venv/bin/python main_test.py

Ohne Virtualenv (Pakete global installiert)
sudo python3 main_test.py
```
