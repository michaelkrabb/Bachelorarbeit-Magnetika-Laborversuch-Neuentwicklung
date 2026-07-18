"""
Die Datei functions_ad3 enthält alle wichtigen Funktionen die mit dem
Analog Discovery 3 und der Datenspeicherung zu tun hat. Außerdem sind 
einige Funktionen vorhanden die vor allem für das Messgerät relevant sind.

"""

#Bibliotheken

#Standardbibliotheken in python
import numpy as np                  #für numpy Anwendungen   
import queue                        #um die Daten queue zu ermöglichen
import csv                          #erzeugen von csv datei
from datetime import datetime       #Datum/Zeit
import os                           #Für Dateinen Ordner und Pfade
import threading                    #Thread für die Parallelisierung 


#der import dwfpy ist die Bibliothek für das analog discovery 3
#muss zuvor installiert werden um diese verwenden zu können
import dwfpy as dwf    
from dwfpy.constants import AcquisitionMode

#Globale Events für das Messprogramm
run_event = threading.Event()
data_queue = queue.Queue()

#Parameter der Messung 

fs = 1000           #Sample per seconds
sc = 10             #Zeit 
R = 1               #Ohm, Wert des Shunt-Widerstands
t_index = 0         #Zeitindex für alle Messungen (in Samples)
u_offset = 0        #Offset 
messung_index = 0

#globale Variable für Messung fortsetzen
fortsetzen_modus = False    

#aktuelle CSV-Datei
aktuelle_csv_datei = None

def set_csv_ordner(pfad):

    """
    Ändert bzw. speichert in der Variable CSV_Ordner den
    aktuellen Pfad in dem die Daten als csv abgespeichert werden.

    Args:
        pfad (str): Pfad zum Speicherordner
    """

    global CSV_Ordner
    CSV_Ordner = pfad


def sample_rate(new_rate):

    """
    Speichert die neuste Sample Rate S/s ab. Das bedeutet die ausgewählte
    Sample Rate wird für die Messung verwendet.
        
    Args:
        new_rate (int): 
            Neue Abtastrate in Samples pro Sekunde

    """
    global fs
    fs = new_rate

def update_offset(wert):

    """
    Speichert den eingestellen Offsetwert ab
        
    Args:
        wert (float): 
            Neuer Offsetwert

    """
    
    global u_offset
    u_offset = wert

def get_offset():

    """
    Gibt den aktuell eingestellten Offsetwert zurück.
    Die Funktion wird vom GUI verwendet.
    Als Funktion programmiert um diese im GUI aufrufen zu können.

    Returns:
        u_offset (float): 
            Aktueller Offsetwert   
    """

    return u_offset

def index_csv():

    """
    Die Funktion erhöht den globalen Wert von messung_index um eins.
    Wird im Programm verwendet um die Messungen zu nummerieren.
    """

    global messung_index
    messung_index += 1

def get_messung_index():

    """
    Dient nur um den aktuellen messung_index Wert im GUI abzufragen.
    Als Funktion programmiert um diese im GUI aufrufen zu können.

    Returns:
        messung_index (int): 
            Gibt die aktuelle Anzahl an Messungen zurück
  
    """

    return messung_index

def reset_messung_index():

    
    """
    Die Funktion setzt den Wert der globalen Variable messung_index auf
    null zurück. Wird im verwendet um die Messungen zu reseten zB. bei
    einem Speicherort wechsel. Damit werden auch die CSV-Dateien nummeriert.
    """

    global messung_index
    messung_index = 0

def kontrolle(x_werte,y_werte,n):

    """
    Dient zur Kontrolle der Messwerte es muss zu jedem x eine 
    y Wert geben. Ist das nicht der Fall wird ein runtime Error ausgelöst.
    Das bedeutet also die gleiche Anzahl an Spannungs x Werten muss man für 
    Spannungswerte y haben. Wird nciht am Gui dargestellt ist ein
    Kontrollwerkzeug für den oder die Programmier:in für die csv datei

    Args:
        x_werte (numpy.ndarray): 
            Messwerte des ersten Oszilloskopkanals

        y_werte (numpy.ndarray): 
            Messwerte des zweiten Oszilloskopkanals

        n (int): 
            Anzahl der gültigen Samples
        
    Returns/Raise:
        RuntimeError: 
            Wenn keine Samples empfangen wurden
    """

    if len(x_werte) != len(y_werte):
        return print("Unterschiedliche Anzahl an x- und y-Werten."
                    "Überprüfen Sie die Verbindungen")
    if n == 0:
        raise RuntimeError("Keine Samples empfangen.")

def berechnungen(ux_werte,uy_werte,zeit_s):

    """
    Fasst die Zeitwerte und Messdaten in einem NumPy-Array zusammen.

    Args:
        zeit_s (numpy.ndarray):
            Fortlaufende Zeitwerte der Messung

        ux_werte (numpy.ndarray): 
            Spannungswerte des ersten Oszilloskopkanals

        uy_werte (numpy.ndarray): 
            Spannungswerte des zweiten Oszilloskopkanals
        
    Returns:
        numpy.ndarray: 
            Array mit den Spalten Zeit, Ux und Uy

    """
    
    daten = np.column_stack([zeit_s, ux_werte, uy_werte - u_offset])
    return daten


def csv_append_rows(pfad,daten):

    """
    Diese Funktion erstellt eine neue Zeile für die CSV-Datei. Die neuen
    Messdaten werden auch in die Datei geschrieben.

    Args:
        pfad (str): 
            Pfad zur CSV-Datei

        daten (numpy.ndarray): 
            Messdaten, die in die CSV-Datei geschrieben werden
        
    """


    #Eine neue Messzeile anhängen
    with open(pfad, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerows(daten)


def csv_initialisieren():

    """
    In dieser Funktion wird die csv Initialisiert. Das bedeutet es wird
    geprüft ob der Ordner erstellt ist in dem die csv erzeugt wird. 
    Jede Datei wird als Messung und mit einem Zeitstempel ausgestattet.

    In dieser FUnktion wird die Kopfzeile erstellt.
        "Zeit","Spannung_x","Spannung_y"

    Returns:
        CSV_PATH (str): 
            Vollständiger Pfad der erzeugten CSV-Datei

    """


    #prüfung ob ordner erstellt ist
    os.makedirs(CSV_Ordner, exist_ok=True)

    #Aktuelles Datum und Uhrzeit im Format YYYYMMDD_HHMMSS
    zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    #Dateiname mit Zeitstempel und der globalen Messung index Variable
    dateiname = f"messung_{zeitstempel}_{messung_index}.csv"
    
    #Gesamter Pfad: Ordner + Dateiname
    CSV_Path = os.path.join(CSV_Ordner, dateiname)

    with open(CSV_Path, mode="w", newline="",encoding="utf-8") as file:

        #Verwendeten Offset und Status der Korrektur speichern
        file.write(f"Offset = {u_offset} V\n")

        #erzeugen der kopfzeile für die Messeinträge
        writer = csv.writer(file, delimiter=";")
        kopfzeile = np.array(["Zeit","Spannung_x","Spannung_y"])
        writer.writerow(kopfzeile)

    print("CSV-Datei wurde erfolgreich erstellt!")
    print(f"Die CSV-Datei hat den Pfad: {CSV_Path}")
    return CSV_Path


def device_verfügbar():

    """ 
    Prüft ob das Gerät angesteckt ist. Ohne Gerät funktioniert keine 
    Messung. 

    Returns:
        int:
            Anzahl der gefundenen Geräte
            Gibt 0 zurück, wenn kein Gerät erkannt wurde
    """

    try:
        list_geräte = list(dwf.Device.enumerate())
        return len(list_geräte)
    except Exception as e:
        print("Keine Geräte gefunden:", e)
        return 0


def try_open_device():

    """
    Öffnet das Messgerät, stellt also Verbindung mit dem AD3 her.
    Zuerst erfolgt die Überprüfung ob überhaupt ein Gerät angesteckt ist.
    Danach wird es geöffnet.
        
    Return:
        dwf.Device | None:
            Geöffnetes Gerät oder None, falls kein Gerät verfügbar ist

    """


    if device_verfügbar() == 0:
        return None

    try:
        device = dwf.Device()           #Gerät
        _ = device.name                 #Name des Geräts
        _ = device.serial_number        #Seriennummer des Geräts
        return device
        
    #Prüft ob Treiber vorhanden ist    
    except dwf.DeviceNotFound as e:
        print("Kein WaveForms-Gerät gefunden. USB/Treiber prüfen.", e)
        return None

    #kein Gerät gefunden bzw. Problem aufgetreten
    except Exception as e:
        print("Unerwarteter Fehler beim Öffnen:", e)
        return None

def set_fortsetzen_modus(value: bool):

    """
    Dient dazu die Messung fortzusetzen. Das bedeute wird im GUI
    der Button Messung fortsetzen gedrückt wird die boolsche Variable 
    gesetzt und die funktion aufgerufen. Die globale Variable 
    fortsetzen_modus wird der boolsche Wert zugewiesen.

    Args:
        value (bool):
            True, wenn die aktuelle Messung fortgesetzt werden soll
            False, wenn eine neue Messung gestartet werden soll
    """

    global fortsetzen_modus
    fortsetzen_modus = value

def start_device():

    """
    Diese Funktion öffnet bzw. startet das device, das bedeutet
    die Verbindung zwischen Software und Gerät wird versucht herzustellen

    Returns:
        dwf.Device | None:
            Geöffnetes Gerät oder None, falls kein Gerät gefunden wurde

    """

    #Verbindung zum Messgerät herstellen
    device = try_open_device()
    if device is None:
        print("Device nicht gefunden überprüfen Sie USB/Treiber")    
    else:
        print("Device erfolgreich gestartet")
       
    return device

def start_messung():

    """
    Die Funktion startet die Messung. Das bedeutet es wird entweder 
    die aktuelle Messung fortgesetzt oder eine neue Messung gestartet.
    Außerdem wird das run_event gestartet. Das bedeutet es findet eine 
    Parallelisierung statt der Messung. Es ist somit möglich den Wert
    live darzustellen und diesen gleichzeitig abzuspeichern. Es wird 
    somit die Funktion sample_update gestartet. Man startet daher den 
    Thread welcher genau für die Parallelisierung sorgt.
        
    """

    #aufrufen der globalen Variablen
    global fortsetzen_modus, aktuelle_csv_datei, t_index, messung_index


    #prüfen ob einen aktuelle Messung fortgesetzt wird
    if fortsetzen_modus:
        print("Messung wird fortgesetzt")

        if aktuelle_csv_datei is None:
            #Sicherheit falls noch keine CSV-Datei erstellt wurde.
            aktuelle_csv_datei = csv_initialisieren()

    #Verbindungstest: Gerät kurz öffnen und anschließend wieder schließen.
    #Die eigentliche Messung öffnet das Gerät später in sample_update().
    else:
        print("NEUE Messung")
        t_index = 0
        device = start_device() #startet das Device
        print(f"{device}")
        print("Gerät: ", tuple(d.name for d in dwf.Device.enumerate()))
        close_device(device) #zuvor war nur sicherheit daher Gerät schließen, weil in oszi richtig aufgemacht
    

    #Messung in separatem Thread starten 
    run_event.set()
    th = threading.Thread(target=sample_update, daemon=True)    #Parallelen ablauf
    th.start()  #start des threads

    #Variable zurücksetzen
    fortsetzen_modus = False

def sample_update():

    """
    In dieser Funktion wird das AD3 konfiguriert. Das bedeutet, es handelt
    sich um die eigentliche wichtige Messfunktion. Es werden die beiden
    Oszilloskopkanäle konfiguriert. Man stellt die Kanäle als Input ein.
    Zusätzlich werden die Range und der Offset eingestellt. In diesem Fall beträgt
    die Range ±25 V.
    Es könnte ebenfalls ein Offset eingestellt werden, dieser wird jedoch mittels
    Software anders behoben.

    Durch das Event wird zuerst die Record-Konfiguration durchgeführt und
    im Anschluss werden durch `scope.record` die jeweiligen Werte in einer Variable
    gespeichert. Das hat zur Folge, dass der Messaufbau richtig sein muss, denn
    es wird klar unterschieden, welcher Kanal die Spannung x und welcher die Spannung
    y misst. Die Messwerte werden kurz geprüft und als letzten Schritt in die
    Daten-Queue gegeben. Dadurch werden die einzelnen Messdaten aneinandergereiht.
    Dies erlaubt den Zugriff durch den späteren Live-Plot. Die Daten werden
    abschließend in der CSV-Datei gespeichert.

        
    """
    global aktuelle_csv_datei, t_index

    chunk_s = 0.2                           #Blocklänge in Sekunden (z.B. 0.2s)
    #chunk_n = max(1, int(fs * chunk_s))    #Samples pro Block
                                            #fortlaufender Sample-Index
    
    #Falls noch keine CSV-Datei existiert, wird eine neue Datei erstellt
    if fortsetzen_modus:

        if aktuelle_csv_datei is None:
            aktuelle_csv_datei = csv_initialisieren()
    else:
        aktuelle_csv_datei = csv_initialisieren()
        t_index = 0

    pfad = aktuelle_csv_datei 

    #Oszilloskopkanäle konfigurieren
    with dwf.Device() as device:
        #Konfiguration beider Eingangskanäle
        scope = device.analog_input             #Kanal als Input definieren
        scope[0].setup(range = 25, offset = 0)  #Konfigurieren von Kanal 1
        scope[1].setup(range = 25, offset = 0)  #Konfigurieren von Kanal 2
        scope.acquisition_mode = AcquisitionMode.RECORD

        while run_event.is_set():

            #Datenerfassung starten
            recorder = scope.record(sample_rate=fs, length=chunk_s, configure=True, start=True)

            #abspeichern der Messdaten bzw. die Messdaten werden ausgelesen
            x_werte = np.asarray(recorder.channels[0].data_samples, dtype=float)
            y_werte = np.asarray(recorder.channels[1].data_samples, dtype=float)
            n = min(len(x_werte), len(y_werte))

            #Kontrolle der Länge bzw. Prüfung ob Daten empfangen wurden
            if n == 0:
                continue

            #Kontrolle der Messdaten 
            kontrolle(x_werte,y_werte,n)

            t_arr = (t_index + np.arange(n, dtype=float)) / fs
            t_index += n

            #Daten queue, Messdaten für den Live-Plot bereitstellen
            for j in range(n):
                try:
                    data_queue.put((float(t_arr[j]), float(x_werte[j]), float(y_werte[j] - u_offset)))
                except queue.Full:
                    break

            #Messdaten in der CSV-Datei speichern        
            daten = berechnungen(x_werte, y_werte, t_arr)
            csv_append_rows(pfad, daten)
            


def close_device(device):

    """
    Schließt die Verbindung zum Messgerät.

    Args:
        device (dwf.Device | None):
            Zu schließendes Gerät. Falls der Wert None ist, wird keine Aktion
            ausgeführt
    """

    if device is not None:
        try:
            device.close()   #schließt das device
        except Exception as e:
            print(f"Fehler beim Schließen: {e}")


def stop_messung():

    """
    Stoppt die laufende Messung.

    Das globale Event run_event wird zurückgesetzt. Dadurch wird die
    Messschleife in sample_update beendet.

    Returns:
        int:
            Gibt 1 zurück, wenn die Messung gestoppt wurde
                
    """
    run_event.clear()
    return 1

