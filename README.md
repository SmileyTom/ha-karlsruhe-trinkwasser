# Karlsruhe Trinkwasser – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Zeigt die aktuellen Messwerte des Karlsruher Trinkwassers direkt in Home Assistant an.  
Datenquelle: [Stadtwerke Karlsruhe – Wasserqualität](https://www.stadtwerke-karlsruhe.de/de/gk/wohnungswirtschaft/trinkwasser/wasserqualitaet.php)

---

## Sensoren

| Sensor | Einheit | Beschreibung |
|---|---|---|
| Temperatur | °C | Wassertemperatur |
| pH-Wert | – | Säure-/Basenwert |
| Leitfähigkeit | µS/cm | Elektrische Leitfähigkeit |
| Trübung | NTU | Trübungswert |
| Sauerstoff | mg/l | Gelöster Sauerstoff |
| Nitrat | mg/l | Nitratgehalt |
| Letzte Abfrage | – | Zeitstempel der letzten Messung |

Die Werte werden alle **10 Minuten** von der Stadtwerke-Website abgerufen.

---

## Installation via HACS

1. HACS öffnen → **Integrations** → ⋮ → **Custom repositories**
2. URL eingeben: `https://github.com/SmileyTom/ha-karlsruhe-trinkwasser`  
   Kategorie: **Integration**
3. Integration suchen und installieren
4. Home Assistant neu starten
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Karlsruhe Trinkwasser**

---

## Manuelle Installation

1. Ordner `custom_components/karlsruhe_trinkwasser/` in dein `config/custom_components/`-Verzeichnis kopieren
2. Home Assistant neu starten
3. Integration über die UI hinzufügen

---

## Technischer Hinweis

Die Stadtwerke Karlsruhe stellen die Messwerte ausschließlich als dynamisch erzeugte  
PNG-Bilder bereit (kein JSON-API). Diese Integration liest die Pixeldaten der Gauge-Bilder  
mit einem eingebetteten Bilderkennungs-Algorithmus (reines Python, keine externen  
Abhängigkeiten) und extrahiert daraus die Zahlenwerte.

Falls Stadtwerke das Bildformat ändert, kann die Erkennung temporär ausfallen –  
die Sensoren zeigen dann `unavailable`.

---

## Lizenz

MIT
