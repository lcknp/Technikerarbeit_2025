# Technikerarbeit_2025

Meine Technikerareit 2025/26


Monitoring & Steuerung – CO₂/BME280 (Raspberry Pi)
Arduino - HC05 Modul

Dieses Projekt liest Sensordaten (CO₂ via PAS CO2 über I²C, Temperatur/Feuchte/Druck via BME280) auf einem Raspberry Pi aus, steuert zwei HC-05-Bluetooth-Einheiten (z. B. Lüfter) abhängig von CO₂/Feuchte, stellt einen kleinen Flask-Webserver bereit und speichert zyklisch Messwerte (JSON für Website + Datenbank).

Autor: Luca Knapp
Datei: main_test.py

⸻

Features
	
	Flask-Server mit Endpunkten: (Noch nicht benutzt)
	•	GET /btn1, GET /btn2 → Klick-Aktionen (leiten auf http://raspberrypi.local/Monitoring_V2.html um)
	•	POST /sendtext → Textkommandos an Einheiten (z. B. "E1 50" → Einheit 1 auf Wert 50)
	•	Bluetooth (HC-05): Zwei Geräte per MAC verbunden, Kommandos aus App/Website → hc05lib
	
	Sensorik:
	•	CO₂ (pasco2 via I²C, Addr 0x28)
	•	BME280 (Temp/Feuchte/Druck/Altitude) via adafruit_bme280 + adafruit_blinka
	
	Steuerlogik:
	•	Lüfterleistung in % abhängig von CO₂-Schwellen (Idle/Normal/Boost) + Feuchte-Override
	
	Datenausgabe:
	•	Aktuelle Messwerte als latest.json nach /var/www/html/
	•	Periodische DB-Sicherung über funktion_db.databasesafe(...)
	•	Zeit-Sync: Stündlich an beide Einheiten übertragen
	•	Robustheit: CO₂-Sensor-Fehler → Fallback-Modus (50 %)

	Hardware
	•	Raspberry Pi (mit aktivem I²C und Bluetooth)
	•	PAS CO₂-Sensor (I²C, Addr 0x28)
	•	BME280 (I²C, typ. Addr 0x76 oder 0x77)
	•	2× HC-05 Bluetooth-Module

	Steuerlogik (Kurzüberblick)
	•	Fallback: CO₂-Wert 0 (Sensorfehler) → 50 %
	•	CO₂-Schwellen:
	•	< 700 ppm: 25 % (IDLE)
	•	700–1200 ppm: linear 25 % → 85 % (NORMAL)
	•	>= 1200 ppm: 90 % (BOOST)
	•	Feuchte-Override: humi > 60 % → mindestens 60 %

	Die jeweils berechnete fan_percent wird als ctl=<WERT> an beide HC-05-Einheiten gesendet.

⸻

Datenablage
	•	JSON für Website: /var/www/html/latest.json (atomar via .tmp → os.replace)
	•	DB-Logging: alle 15 Minuten (ca. wenn datasafedelay >= 90 bei measure_sec=10):
	•	funktion_db.databasesafe("raspi", ...) – BME280/PAS-Werte
	•	für jede BT-Einheit (wenn Daten vorhanden): funktion_db.databasesafe(f"ardu{row[0]}", ...) – Innen/Außen-Werte
