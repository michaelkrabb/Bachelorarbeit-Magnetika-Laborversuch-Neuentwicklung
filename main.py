"""
Hauptprogramm des Messprogramms für die Lehrveranstaltung
366.110 Materialien der Elektrotechnik.

Das Programm wurde im Rahmen dieser Bachelorarbeit entwickelt und besteht
aus der Datei main.py sowie den Modulen gui.py und
functions_ad3.py.

Die Datei main.py startet die grafische Benutzeroberfläche (GUI).
Über diese können Studierende Messungen durchführen, Messdaten als
CSV-Dateien speichern, Skalierungsfaktoren eingeben sowie wichtige
Messinformationen und eine Live-Darstellung der Messdaten anzeigen.
"""

#Import der GUI Datei aus dem Ordner bib
from bib.gui import GUI


def main():

    """
        Startet die grafische Benutzeroberfläche und gibt die eingestellten
        Skalierungsfaktoren zurück.

        Returns:
            tuple[float, float]:
            Skalierungsfaktoren für H und B.
    """

    #für den start des GUI 
    hauptfenster_var = GUI()
    hauptfenster_var.mainloop()

    #man erhält die Werte für h und b 
    #über den state vom Hauptfenster gepeichert
    h = hauptfenster_var.state.get("scale_H")
    b = hauptfenster_var.state.get("scale_B")
    
    return h, b
        

if __name__ == "__main__":

    #Programm start
    h,b = main()
    print("Skalierungsfaktoren: ")
    print(f"H = {h}", f"B = {b}")
    