#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/Technikerarbeit_2025"
VENV_DIR="$PROJECT_DIR/.venv"
BOOT_CONFIG="/boot/firmware/config.txt"   # Raspberry Pi OS (Bookworm/Trixie)

echo "== 0) apt update/upgrade =="
sudo apt update
sudo apt full-upgrade -y

echo "== 1) Pakete installieren =="
sudo apt install -y \
  git curl nano htop \
  python3 python3-dev python3-pip python3-venv python3-full \
  i2c-tools build-essential pkg-config \
  mariadb-server \
  apache2 \
  bluetooth bluez libbluetooth-dev \
  python3-bluez \
  php php-mbstring php-zip php-gd php-json php-curl php-mysql \
  phpmyadmin

echo "== 2) Dienste aktivieren =="
sudo systemctl enable --now mariadb
sudo systemctl enable --now apache2
sudo systemctl enable --now bluetooth

echo "== 3) I2C aktivieren =="
if [ -f "$BOOT_CONFIG" ]; then
  sudo sed -i 's/^\s*#\s*dtparam=i2c_arm=on\s*$/dtparam=i2c_arm=on/' "$BOOT_CONFIG" || true
  grep -q '^dtparam=i2c_arm=on' "$BOOT_CONFIG" || echo 'dtparam=i2c_arm=on' | sudo tee -a "$BOOT_CONFIG" >/dev/null
else
  echo "WARN: $BOOT_CONFIG nicht gefunden. I2C bitte via raspi-config aktivieren."
fi

# i2c-dev Kernelmodul sicher laden
echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf >/dev/null

echo "== 4) venv (mit system-site-packages) =="
cd "$PROJECT_DIR"
python3 -m venv "$VENV_DIR" --system-site-packages
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
pip install pymysql smbus2 adafruit-blinka adafruit-circuitpython-bme280

echo "== 5) Datenbank anlegen (data + ebmuser) =="
sudo mysql < "$PROJECT_DIR/setup_db.sql"

echo "== 6) Web-Dateien nach /var/www/html kopieren =="
if [ -d "$PROJECT_DIR/html" ]; then
  sudo rsync -a --delete "$PROJECT_DIR/html/" /var/www/html/
fi

echo "== 7) Apache Rechte =="
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 775 /var/www/html
sudo usermod -aG www-data "$USER" || true

echo "== 8) Quick-Tests =="
source "$VENV_DIR/bin/activate"
python -c "import board, busio, adafruit_bme280, pymysql; print('Python Imports OK')"
python -c "import bluetooth; print('Bluetooth Import OK')"
i2cdetect -y 1 || true

echo "FERTIG. Bitte reboot:"
echo "sudo reboot"
