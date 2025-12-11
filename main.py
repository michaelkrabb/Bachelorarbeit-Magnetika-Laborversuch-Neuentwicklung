#Hauptprogramm

"""
Im Hauptprogramm werden die Funktion aus dem Unterordner bib
importiert und nur aufgerufen.
Das ganze dient der Übersicht und um alles miteinander verknüpfen zu können.
"""

#Imports

from bib.gui import GUI


"""
Start des Hauptprogramms
Es werden die benötigten Funktionen aufgerufen

GUI: starte das GUI und führt es aus
"""

def main():

    hauptfenster_var = GUI()
    hauptfenster_var.mainloop()
    h = hauptfenster_var.state.get("scale_H")
    b = hauptfenster_var.state.get("scale_B")
    
    return h, b
        

if __name__ == "__main__":
    h,b = main()
    print("Skalierungsfaktoren: ")
    print(f"H = {h}", f"B = {b}")
    