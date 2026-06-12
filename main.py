#Hauptprogramm

"""
Im Hauptprogramm werden die Funktion aus dem Unterordner bib
importiert und nur aufgerufen.
Das ganze dient der Übersicht und um alles miteinander verknüpfen zu können.
"""

#Imports

from bib.gui import GUI


"""
Hauptprogramm
startet das Programm, alle Funktion sind ausgelagert 
In eien functions_ac3.py und eine gui.py datei

GUI: starte das GUI und führt es aus
"""

def main():

    """
    Ruft das Hauptfenster auf und startet mittels der Funktion 
    GUI das User Interface. Außerdem erhält man die Skalierungsfaktoren,
    mit den die Messwerte für die Spannung sklaiert werden um die Hysterese 
    darstellen zu können.

    Args:
        None

    Returns:
        gibt die Skalierungsfaktoren für h und b zurück
    
    """

    hauptfenster_var = GUI()
    hauptfenster_var.mainloop()
    h = hauptfenster_var.state.get("scale_H")
    b = hauptfenster_var.state.get("scale_B")
    
    return h, b
        

if __name__ == "__main__":
    h,b = main()
    print("Skalierungsfaktoren: ")
    print(f"H = {h}", f"B = {b}")
    