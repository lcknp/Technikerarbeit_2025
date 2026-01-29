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

Zielsystem: **Raspberry Pi OS (Trixie)**, **Python 3.13**.

---

## Systemvoraussetzungen
- Raspberry Pi OS (Trixie)
- Internetverbindung
- sudo-Rechte

---

## ✅ Automatische Installation (empfohlen)

Im Projektordner ausführen:

```bash
cd ~/Technikerarbeit_2025
chmod +x setup.sh
./setup.sh
sudo reboot
```

### setup.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/Technikerarbeit_2025"
VENV_DIR="$PROJECT_DIR/.venv"
BOOT_CONFIG="/boot/firmware/config.txt"

sudo apt update
sudo apt full-upgrade -y

sudo apt install -y \
  git curl nano htop \
  python3 python3-dev python3-pip python3-venv python3-full \
  i2c-tools build-essential pkg-config \
  mariadb-server \
  apache2 \
  bluetooth bluez libbluetooth-dev python3-bluez \
  php php-mbstring php-zip php-gd php-json php-curl php-mysql phpmyadmin

sudo systemctl enable --now mariadb
sudo systemctl enable --now apache2
sudo systemctl enable --now bluetooth

if [ -f "$BOOT_CONFIG" ]; then
  sudo sed -i 's/^\s*#\s*dtparam=i2c_arm=on\s*$/dtparam=i2c_arm=on/' "$BOOT_CONFIG" || true
  grep -q '^dtparam=i2c_arm=on' "$BOOT_CONFIG" || echo 'dtparam=i2c_arm=on' | sudo tee -a "$BOOT_CONFIG" >/dev/null
fi
echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf >/dev/null

cd "$PROJECT_DIR"
python3 -m venv "$VENV_DIR" --system-site-packages
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
pip install pymysql smbus2 adafruit-blinka adafruit-circuitpython-bme280

sudo mysql < "$PROJECT_DIR/setup_db.sql"

if [ -d "$PROJECT_DIR/html" ]; then
  sudo rsync -a --delete "$PROJECT_DIR/html/" /var/www/html/
fi

sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 775 /var/www/html
sudo usermod -aG www-data "$USER" || true

source "$VENV_DIR/bin/activate"
python -c "import board, busio, adafruit_bme280, pymysql; print('Python Imports OK')"
python -c "import bluetooth; print('Bluetooth Import OK')" || true
i2cdetect -y 1 || true

echo "FERTIG. Bitte reboot: sudo reboot"
```

### setup_db.sql
```sql
CREATE DATABASE IF NOT EXISTS data
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'ebmuser'@'localhost'
IDENTIFIED BY '12345678';

GRANT ALL PRIVILEGES ON data.* TO 'ebmuser'@'localhost';
FLUSH PRIVILEGES;
```

---

## 🔧 Manuelle Installation (Bash-Kommandos)

### System aktualisieren
```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

### Pakete installieren
```bash
sudo apt install -y \
  git curl nano htop \
  python3 python3-dev python3-pip python3-venv python3-full \
  i2c-tools build-essential pkg-config \
  mariadb-server \
  apache2 \
  bluetooth bluez libbluetooth-dev python3-bluez \
  php php-mbstring php-zip php-gd php-json php-curl php-mysql phpmyadmin
```

### I2C aktivieren
```bash
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot
```

### Projekt klonen
```bash
cd ~
git clone https://github.com/lcknp/Technikerarbeit_2025.git
cd Technikerarbeit_2025
```

### venv erstellen (mit System-Packages) + Python-Abhängigkeiten
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install pymysql smbus2 adafruit-blinka adafruit-circuitpython-bme280
```

### Dienste aktivieren
```bash
sudo systemctl enable --now mariadb
sudo systemctl enable --now apache2
sudo systemctl enable --now bluetooth
```

### Datenbank (data) + Benutzer (ebmuser)
```bash
sudo mysql
```

```sql
CREATE DATABASE IF NOT EXISTS data
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'ebmuser'@'localhost'
IDENTIFIED BY '12345678';

GRANT ALL PRIVILEGES ON data.* TO 'ebmuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Apache Rechte
```bash
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 775 /var/www/html
sudo usermod -aG www-data $USER
sudo reboot
```

### Quick-Tests
```bash
source ~/Technikerarbeit_2025/.venv/bin/activate
python -c "import board, busio, adafruit_bme280, pymysql; print('Imports OK')"
python -c "import bluetooth; print('Bluetooth OK')"
i2cdetect -y 1
```

---

## Web & Datenbank
- Web: `http://<raspi-ip>/`
- phpMyAdmin: `http://<raspi-ip>/phpmyadmin`
- DB: `data`
- User: `ebmuser`

---

## Hinweis
Autostart (systemd) ist bewusst nicht enthalten.
