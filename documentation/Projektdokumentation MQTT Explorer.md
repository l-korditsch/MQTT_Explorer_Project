# Projektdokumentation: MQTT Explorer

## 1. Projektübersicht

**Projektname:** MQTT Explorer  
**Projektteam:** Lucas Korditsch, Lukas Oberthür, Lukas Wolter, Nils Thomas  
**Zeitraum:** 02.04.2025 – 11.06.2025

**Kurzbeschreibung:**  
Der MQTT Explorer ist ein objektorientiertes Python-Programm mit grafischer Oberfläche, das die Verbindung zu einem MQTT-Broker ermöglicht. Nutzer können Topics abonnieren, Nachrichten senden und empfangen sowie den Nachrichtenverlauf einsehen und exportieren. Ziel ist es, eine benutzerfreundliche und erweiterbare Anwendung für Test- und Analysezwecke im Bereich IoT/MQTT zu schaffen.

---

## 2. Funktionsweise

- **Verbindung:**  
  Der Nutzer gibt die Broker-Adresse und Port ein und stellt eine Verbindung her.
- **Abonnieren/Publizieren:**  
  Topics können abonniert und Nachrichten an beliebige Topics gesendet werden.
- **Nachrichtenanzeige:**  
  Empfangene Nachrichten werden in Echtzeit angezeigt und in einer lokalen Datenbank gespeichert.
- **Verlauf & Export:**  
  Der Nachrichtenverlauf kann eingesehen, gelöscht oder als Datei exportiert werden.
- **Autoskalierung:**  
  Die grafische Oberfläche passt sich automatisch der Fenstergröße an.

**Sequenzdiagramm:**  
*(siehe beigefügtes Klassendiagramm als Bild)*
---

## 3. Architektur & Aufbau

Das Projekt ist in mehrere Python-Module unterteilt:

- **main.py:** Einstiegspunkt, initialisiert GUI, Backend und Datenbank.
- **frontend.py:** Enthält die Klasse für die grafische Oberfläche (Tkinter).
- **backend.py:** Beinhaltet die MQTT-Logik (Verbindung, Abonnieren, Publizieren).
- **database.py:** Verwaltet die Speicherung und den Zugriff auf Nachrichten (SQLite).

**Klassendiagramm:**  
*(siehe beigefügtes Klassendiagramm als Bild)*

---

## 4. Technologiewahl & Begründung

- **Python:**  
  Weit verbreitet, leicht verständlich, viele Bibliotheken für GUI, MQTT und Datenbanken.
- **Tkinter:**  
  Standard-GUI-Bibliothek in Python, keine zusätzlichen Abhängigkeiten, plattformunabhängig.
- **paho-mqtt:**  
  Standardbibliothek für MQTT in Python, zuverlässig und einfach zu verwenden.
- **SQLite:**  
  Leichtgewichtig, keine Serverinstallation nötig, ideal für lokale Speicherung.
- **Threading:**  
  Für die sichere parallele Verarbeitung von GUI, MQTT und Datenbankzugriffen.

---

## 5. Besonderheiten & Herausforderungen

- **Thread-Sicherheit:**  
  Datenbankzugriffe werden mit Locks abgesichert, da MQTT-Callbacks in eigenen Threads laufen.
- **Fehlerbehandlung:**  
  Das Programm fängt Verbindungs- und Decodierungsfehler ab und informiert den Nutzer.
- **Benutzerfreundlichkeit:**  
  Die Oberfläche ist übersichtlich, selbsterklärend und passt sich der Fenstergröße an.
- **Versionskontrolle:**  
  Das Projekt wurde mit Git versioniert (siehe GitHub-Repository).

---

## 6. Nutzung & Installation

1. **Repository klonen:**  
   `git clone https://github.com/l-korditsch/MQTT_Explorer_Project.git`
2. **Abhängigkeiten installieren:**  
   `pip install paho-mqtt`
3. **Programm starten:**  
   `python main.py`

---

## 7. Fazit

Das Projekt erfüllt die Anforderungen des Product Owners:  
- Objektorientierte Struktur  
- Moderne, skalierbare GUI  
- Speicherung und Export von Nachrichten  
- Nutzung von Versionskontrolle  
- Erweiterbarkeit für zukünftige Features

---

## 8. Anhang

- Klassendiagramm (siehe Bild im Repository)
- Sequenzdiagramm (siehe Bild im Repository)
- Beispiel-Screenshots der Anwendung
- Quellcode im GitHub-Repository