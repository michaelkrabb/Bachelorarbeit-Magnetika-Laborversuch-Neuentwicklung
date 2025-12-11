"""
Die Datei functions_ac3 enthält alle wichtigen FUnktionen die mit dem
Analog Discovery 3 und der Datenspeicherung zu tun hat.

Außerdem sind hier nützliche andere Funktion zum Beispiel für das GUI 
enthalten. Diese diene der MEssung und sind mit Buttons oder anderem verknüpft.

"""

#Bibliotheken
#Standardbibliotheken in python
import numpy as np                                
import matplotlib.pyplot as plt #zum plotten
import matplotlib.animation as animation #für Messdaten parallel plotten

#der import dwfpy ist die Bibliothek für das analog discovery 3
#muss zuvor installiert werden um diese verwenden zu können
import dwfpy as dwf    
from dwfpy.constants import AcquisitionMode

#für Zeit einstellungen benötigt
import time
import queue
import math

#um csv Dateien erstellen zu können 
import csv 
from datetime import datetime
from pathlib import Path
import os

#für paralleles abarbeiten von Funktionen
import threading
from concurrent.futures import ThreadPoolExecutor


#Für die Daten queue ein globales Event
run_event = threading.Event()
data_queue = queue.Queue()

#Angaben des Pfads für die Datei der Messdaten

CSV_Ordner= r'C:\Users\Michael Krabb\Desktop\python_freifach\BAC_CSV'

#Variablen
fs =  250           #Sample per seconds
sc = 10             #Zeit 
R = 1               #Ohm, Wert des Shunt-Widerstands
t_index = 0         # Zeitindex für alle Messungen (in Samples)
u_offset = 0        #Offset 

#globale Variable für Messung fortsetzen
fortsetzen_modus = False    #wir setzen eigentlich eine Flag 

# aktuelle CSV-Datei
aktuelle_csv_datei = None

def sample_rate(new_rate):
    global fs
    fs = new_rate

def update_offset(wert):
    global u_offset
    u_offset = wert


def kontrolle(x_werte,y_werte,n):
    if len(x_werte) != len(y_werte):
        return print("Ein Fehler ist in der Messung aufgetreten" 
        "Überprüfen Sie die Verbindungen")
    if n == 0:
        raise RuntimeError("Keine Samples empfangen.")

def berechnungen(x_werte,y_werte,n):

    #Berechnungen
    ix_werte = x_werte/R
    zeit_s = np.arange(n, dtype=float) / fs         #relative Messzeit in Sekunden
    mess_frequenz = np.full(n, "", dtype=object)    #hier dann mittels GUI die werte einspeichern
    daten = np.column_stack([zeit_s,mess_frequenz,x_werte,ix_werte,y_werte-u_offset])
    return daten


def csv_append_rows(pfad,daten):
    """Eine neue Messzeile anhängen"""
    with open(pfad, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerows(daten)


def csv_initialisieren():

    # Aktuelles Datum und Uhrzeit im Format YYYYMMDD_HHMMSS
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Dateiname mit Zeitstempel
    dateiname = f"messung_{zeitstempel}.csv"
    
    # Gesamter Pfad: Ordner + Dateiname
    CSV_Path = os.path.join(CSV_Ordner, dateiname)

    with open(CSV_Path, mode="w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        kopfzeile = np.array(["Zeit","Frequenz","Spannung_x","Strom_x","Spannung_y"])
        writer.writerow(kopfzeile)

    print("CSV-Datei wurde erfolgreich erstellt!")
    print(f"Die CSV-Datei hat den Pfad: {CSV_Path}")
    return CSV_Path


def device_verfügbar():
    try:
        list_geräte = list(dwf.Device.enumerate())
        return len(list_geräte)
    except Exception as e:
        print("Keine Geräte gefunden:", e)
        return 0


def try_open_device():

    if device_verfügbar() == 0:
        return None

    try:
        device = dwf.Device()
        # Lazy-Open-Schutz: Zugriff erzwingen
        _ = device.name
        _ = device.serial_number
        return device
        
    except dwf.DeviceNotFound as e:
        print("Kein WaveForms-Gerät gefunden. USB/Treiber prüfen.", e)
        return None
        
    except Exception as e:
        print("Unerwarteter Fehler beim Öffnen:", e)
        return None

def set_fortsetzen_modus(value: bool):
    global fortsetzen_modus
    fortsetzen_modus = value

def start_device():
    #dient nur dazu das Device zu starten
    device = try_open_device()
    if device == None:
        print("Device nicht gefunden überprüfen Sie USB/Treiber")    
    else:
        print("Device erfolgreich gestartet")
       
    return device

def start_messung():

    global fortsetzen_modus, aktuelle_csv_datei, t_index

    if fortsetzen_modus:
        print("Messung wird fortgesetzt")

        if aktuelle_csv_datei is None:
            # Sicherheitsnetz: falls doch keine Datei existiert, neu anlegen
            aktuelle_csv_datei = csv_initialisieren()

    else:
        print("NEUE Messung")
        t_index = 0
        device = start_device()
        print(f"{device}")
        print("Gerät: ", tuple(d.name for d in dwf.Device.enumerate()))

        close_device(device) #zuvor war nur sicherheit daher Gerät schließen, weil in oszi richtig aufgemacht
  
    run_event.set()
    th = threading.Thread(target=sample_update, daemon=True)
    th.start()

    fortsetzen_modus = False

def sample_update():

    """
    Diese Funktion holt fortlaufend Daten und speichert diese ab
    """
    global aktuelle_csv_datei, t_index

    chunk_s = 0.2                           # Blocklänge in Sekunden (z.B. 0.2s)
    chunk_n = max(1, int(fs * chunk_s))     # Samples pro Block
                          # fortlaufender Sample-Index
    
    # Sicherheitsnetz: falls doch None, neu anlegen

    if fortsetzen_modus:

        if aktuelle_csv_datei is None:
            aktuelle_csv_datei = csv_initialisieren()
    else:
        aktuelle_csv_datei = csv_initialisieren()
        t_index = 0

    pfad = aktuelle_csv_datei 

    #Oszi Kanal konfigurieren 
    with dwf.Device() as device:
        #die beiden Kanäle konfigurieren
        scope = device.analog_input             #Kanal als Input definieren
        scope[0].setup(range = 25, offset = 0)  #Konfigurieren von Kanal 1
        scope[1].setup(range = 25, offset = 0)  #Konfigurieren von Kanal 2
        scope.acquisition_mode = AcquisitionMode.RECORD

        while run_event.is_set():
            recorder = scope.record(sample_rate=fs, length=chunk_s, configure=True, start=True)

            x_werte = np.asarray(recorder.channels[0].data_samples, dtype=float)
            y_werte = np.asarray(recorder.channels[1].data_samples, dtype=float)
            n = min(len(x_werte), len(y_werte))
            if n == 0:
                continue

            #Länge und Konrtolle
            kontrolle(x_werte,y_werte,n)

            t_arr = (t_index + np.arange(n, dtype=float)) / fs
            t_index += n

            for j in range(n):
                try:
                    data_queue.put((float(t_arr[j]), float(x_werte[j]), float(y_werte[j])), timeout=0.1)
                except queue.Full:
                    break

            daten = berechnungen(x_werte, y_werte, n)
            csv_append_rows(pfad, daten)
            


def close_device(device):
    if device is not None:
        try:
            device.close()   # () wirklich aufrufen
        except Exception as e:
            print(f"Fehler beim Schließen: {e}")


def stop_messung():
    run_event.clear()
    return 1


"""
if __name__ == "__main__":
    
    start_messung()
"""
