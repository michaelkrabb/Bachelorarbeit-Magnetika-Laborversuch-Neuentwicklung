#hier wird das komplette GUI(graphical user interface) erzeugt

"""
Was soll das GUI alles darstellen?
Das GUI muss Grundsätzlich den Hysterese sowie den Permeabilitätsplot 
darstellen. Das soll natürlich schon live dargestellt werden, also während der Messung.
Am Ende soll das gesamte Bild dargestellt werden, sowie eine Funktion um bestimmte Zeit-
punkte betrachten zu können. Außerdem soll das Signal live geplottet werden.

Ein weiterer wichtiger Punkt sind die Skalierungsfaktoren, welche die Studierenden
selbst eingeben müssen. So muss man im Programm nicht darauf achten, welches
Objekt (Ringkern) man vermisst. Wie die Berechnung dessen Skalierungsfaktoren funktioniert 
siehe schriftlichen Teil der Bachelorarbeit.

Weiters muss es natürlich Möglichkeiten geben die Daten zu speichern, sowie 
eine Eingabe welcher Versuch man durchführt und die Frequenz muss eingegeben werden.

Samples und Offsetkompensation soll mittels Settings in einem untergeordneten Menü eingestellt
werden können, aber das ist für Studierende nicht zugänglich.
"""

#Bibliotheken

#Standardbibliotheken in python
import numpy as np                                
import matplotlib.pyplot as plt #zum plotten
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import queue
import os

#Tkinter für GUI
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


#gemeinsame Objekte aus functions_ad3.py holen:
from .functions_ad3 import start_messung, stop_messung, data_queue,update_offset
from .functions_ad3 import set_fortsetzen_modus, sample_rate, get_offset
from .functions_ad3 import set_csv_ordner, index_csv, get_messung_index, reset_messung_index

def create_button(fenster, text, command=None, primary=False):

    """
    Diese Funktion erzeugt einheitlich gestaltete Buttons für das GUI, 
    um zu gewährleisten, dass man den gleichen Button hat oder
    schnell eine Änderung machen kann, vor allem für die Optik sehr einfach. 
    Somit hat man immer den gleichen Button für die wichtigsten Interaktionsfelder.
    Zu erwähnen ist dennoch, dass es vereinzelt Ausnahmen gibt, 
    welche andere Buttons erzeugen.

    Args:
        fenster (tk.Widget): 
            steht für das fenster in dem der Button angezeigt wird

        text (str):
            um den Button die Beschriftung zu geben

        command (callable, optional):
            um bei Button klick eine funktion aufrufen zu können (triggert aktion)

        primary (bool):
            Legt das Erscheinungsbild des Buttons fest
            True erzeugt einen hervorgehobenen (blauen) Button
            False einen grauen Standardbutton
            
    Returns:
        tk.Button:
            Generiert den Button mit den verschiedenen Konfigurationen

    """


    #zwei Buttontypen für die verschiedenen Anwendungen
    if primary:

        #erstellten Button zurückgeben
        return tk.Button(                   
            fenster,                        #GUI Fenster auf das sich der Button bezieht                                               
            text=text,                      #Beschriftung des Buttons             
            borderwidth= 1.5,               #Breite des Rahmens
            command=command,                #Funktionsaufruf
            bg="#1e88e5",                 #Hintergrundfarbe
            fg="white",                     #Schriftfarbe                
            activebackground="#1565c0",   #Hintergrundfarbe beim Klicken          
            activeforeground="white",       #Schriftfarbe beim Klicken
            relief="solid",                 #Art des Buttonrahmens
            padx=10,                        #Abstand x Koordinate
            pady=4,                         #Abstand y Koordinate            
        )
    else:
        #vergleiche mit zuvor
        return tk.Button(
            fenster,
            text=text,
            borderwidth= 1.5,
            command=command,
            bg="#e0e0e0",
            fg="#222222",
            activebackground="#d5d5d5",
            activeforeground="#222222",
            relief="solid",
            padx=10,
            pady=4,
        )


#damit die Skalierungswerte nicht verloren gehen werte abspeichern
def save_scale(entry_x, entry_y,hauptfenster):

    """
    Es werden die Skalierungsfaktoren aus dem erstellten entry gespeichert.
    Das bedeutet die Eingabe der Skalierungsfaktoren wird hier gespeichert.
    Als Dezimaltrennzeichen sind Punkt oder Beistrich erlaubt. Bei falscher Eingabe
    erscheint eine Fehlermeldung im GUI. Der State der Skalierungsfaktoren wird
    mit dem Hauptfenster gespeichert. Bei erfolgreicher Speicherung erfolgt 
    ebenfalls eine Meldung am GUI.

    Args:
        entry_x (tk.Entry):
            Eingabefeld für Skalierungsfaktor magnetische Feldstärke
        
        entry_y (tk.Entry):
            Eingabefeld für Skalierungsfaktor magnetische Flussdichte
        
        hauptfenster (Hauptfenster):
            Hauptfenster des GUI

    
    """



    try:

        h = float(entry_x.get().replace(",", "."))
        b = float(entry_y.get().replace(",", "."))

    except ValueError:
        messagebox.showerror("Eingabefehler", "Bitte gültige Zahlen eingeben.")
        return

    hauptfenster.state["scale_H"] = h
    hauptfenster.state["scale_B"] = b
    #print(f"[GUI] Gespeichert: H={h}, B={b}") #zum testen und Konsolen Anzeige

    messagebox.showinfo("Status", "Skalierungsfaktoren gespeichert")

def eingabe_skalierung(frame_scale,hauptfenster):

    """
    Die Funktion erzeugt die Frames, Labels, Eingabefelder sowie den Button
    Skalierungsfaktoren speichern. Der Frame wird erzeugt um die zwei Eingabefelder
    richtig anordnen zu können. Die Labels dienen der Beschriftung der Eingabefelder.
    Es werden zwei Frames erzeugt um eine Reihung untereinander zu ermöglichen.
    Der Button wird mittels der vordefinierten Funktion erzeugt und dient dazu
    bei Klick die eingegebenen Skalierungsfaktoren zu speichern.

    Args:
        frame_scale (tk.LabelFrame):
            Dient dazu die erzeugten Frames die richtige Position am GUI zuzuweisen
        
        hauptfenster (Hauptfenster):
            Zuweisung auf dem Hauptfenster

    Returns:
        entry_x (tk.Entry):
            Erzeugt das Eingabefeld für Skalierungsfaktor H

        entry_y (tk.Entry):
            Erzeugt das Eingabefeld für Skalierungsfaktor B     

    """
    
    #Frames erzeugen mit Zeile, Spalte und den Abständen
    frame_x = tk.Frame(frame_scale, bg="#f5f7fa")           #sticky welche Seite
    frame_x.grid(row=0, column=0,padx=4,pady=4,sticky="ew") 

    frame_y = tk.Frame(frame_scale, bg="#f5f7fa")
    frame_y.grid(row=1, column=0,padx=4,pady=4,sticky="ew")
    
    #Jetzt das Label so anpassen, das es mit grid und nicht mit pad funktioniert
    tk.Label(frame_x,text="1V... = ").grid(row=0,column=0,
                                        sticky="w",
                                        padx=5,pady=5)
   
    tk.Label(frame_x,text= "[A/m]").grid(row=0,column=2,
                                        sticky="w",
                                        padx=5,pady=5)
   
    #beschriftung der Felder magnetische Flussdichte
    tk.Label(frame_y,text="1V... = ").grid(row=1,column=0,
                                        sticky="w",
                                        padx=5,pady=5)

    tk.Label(frame_y,text= "[T]").grid(row=1,column=2,
                                        sticky="w",
                                        padx=5,pady=5)
    
    #Eingabefeld für Skalierungsfaktor H
    entry_x = tk.Entry(frame_x, width=12, bd=2, relief="solid")
    entry_x.grid(row=0,column=1,padx=5,pady=5)


    #Eingabefeld für Skalierungsfaktor B
    entry_y = tk.Entry(frame_y, width=12, bd=2, relief="solid")
    entry_y.grid(row=1,column=1,padx=5,pady=5)
    

    #Button erzeugen um Skalierungsfaktoren abzuspeichern
    button_scale = create_button(
        frame_scale,
        text="Skalierungsfaktoren speichern",
        command=lambda: save_scale(entry_x, entry_y, hauptfenster),
        primary=False,
    )
    button_scale.grid(row=2, column=0, sticky="w", padx=4, pady=8)

    return entry_x,entry_y

def clear_live_plots(hauptfenster):

    """
    Die Funktion setzt die Live-Plots zurück. Das bedeutet die aktuelle
    Anzeige wird entfernt und mit der neutralen Ansicht wieder belegt. Einfach gesagt
    die dargestellte Messung wird gelöscht und die neue kann angezeigt werden.
    Das Funktioniert parallel für alle drei mögliche Live-Plots. Nämlich für den
    Signalplot sowie für die Hysterese oder die Permeabilität. 
    Achtung die Daten queue muss auch entleert werden, weil ansonsten bei einer 
    neuen Messung alte bzw. falsche Daten geplottet werden.

    Args:
        hauptfenster (Hauptfenster):
            Zuweisung auf dem Hauptfenster
    


    """

    frame_signal = hauptfenster.frames["signal"]
    frame_hysterese = hauptfenster.frames["hysterese"]
    frame_permea = hauptfenster.frames["permeabilität"]
    
    #zurücksetzen Singale
    if hasattr(frame_signal, "live"):       #wenn der Frame ein Attribut hat

        #Live-Daten zurücksetzen
        live = frame_signal.live
        live["ts"].clear()
        live["ux"].clear()
        live["uy"].clear()
        live["line_x"].set_data([], [])
        live["line_y"].set_data([], [])

        #Achsen zurücksetzen
        ax = live["ax"]  
        live["ax"].relim()
        live["ax"].autoscale_view()
        live["canvas"].draw_idle()
    
    #zurücksetzen hysterese
    if hasattr(frame_hysterese, "live"):
        live_h = frame_hysterese.live
        live_h["H"].clear()
        live_h["B"].clear()
        live_h["line_hb"].set_data([], [])

        ax = live_h["ax"]
        ax.relim()
        ax.autoscale_view()
        live_h["canvas"].draw_idle()

    #zurücksetzen permeabilität
    if hasattr(frame_permea, "live"):
        live_p = frame_permea.live
        live_p["H"].clear()
        live_p["B"].clear()
        live_p["line_mu"].set_data([], [])
        ax = live_p["ax"]
        ax.relim()
        ax.autoscale_view()
        live_p["canvas"].draw_idle()

    #Dadurch wird die Daten-Queue auch noch entleert 
    with data_queue.mutex:
        data_queue.queue.clear()


def zoom_funktion(frame):

    """
    Die Zoomfunktion dient dazu in den einzelnen Live-Plots hinein- bzw.
    hinauszoomen zu können. Das ist möglich wenn man sich im Frame befindet und
    am Mausrad herumdreht. Durch gedrückte rechte Maustaste kann in den Live-Plots 
    gezoomt und die Ansicht verschoben werden. Das sind die zwei wesentlichen 
    Funktionen. Es gibt in dieser Funktion die aufgerufen werden, wenn das Event 
    ausgelöst wird. Das führt dazu, das die scroll oder Verschiebungsfunktion 
    eingeschaltet wird. 

    Args:
        frame (dict):
            Dictionary mit Achse und Canvas des Live-Plots

    Returns:
        None

    """

    ax = frame["ax"]
    canvas = frame["canvas"]
    #hier könnten man einstellen wie schnell man zoomen möchte
    zoom_faktor = 1.2                   
    status_maus = {"druecken": None}

    #Scrollfunktion mittels Mausrad
    def on_scroll(event):

        if event.inaxes is not ax:
            return

        #skaliert den zoomfaktor mittels Mausrad
        if event.button == "up":
            scale = 1/zoom_faktor
        elif event.button == "down":
            scale = zoom_faktor
        else:
            return

        #erhalte die Werte bzw. das Tupel
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        xdata = event.xdata if event.xdata is not None else (x_min + x_max) / 2
        ydata = event.ydata if event.ydata is not None else (y_min + y_max) / 2

        #die neue Breite und Höhe mit dem Skalierungsfaktor für Zoom anpassen
        new_width = (x_max - x_min) * scale
        new_height = (y_max - y_min) * scale

        ax.set_xlim([xdata - new_width / 2, xdata + new_width / 2])
        ax.set_ylim([ydata - new_height / 2, ydata + new_height / 2])

        #Anpassung des Live-Plot
        canvas.draw_idle()

    #sorgt dafür bei gedrückter rechter Maustaste das Bild zu verschieben
    def on_press(event):

        #Fallunterscheidung
        if event.inaxes is not ax:
            return
        if event.button != 3:
            return
        if event.xdata is None or event.ydata is None:
            return
        

        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        status_maus["druecken"] = (event.xdata, event.ydata, (x_min, x_max), (y_min, y_max))    

    #funktionen damit das verschieben wieder beendet ist also bei Maustaste loslassen
    def on_release(event):
        if event.button == 3:
            status_maus["druecken"] = None

    def on_move(event):
        if status_maus["druecken"] is None:
            return
        if event.inaxes is not ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        
        
        x0, y0, (x_min0, x_max0), (y_min0, y_max0) = status_maus["druecken"]
        dx = event.xdata - x0
        dy = event.ydata - y0

        #achsen anpassen dynamisch
        ax.set_xlim(x_min0 - dx, x_max0 - dx)
        ax.set_ylim(y_min0 - dy, y_max0 - dy)

        #Live-Plot
        canvas.draw_idle()
        
    #anpassungen des Live-Plots also zoomen scrollen
    canvas.mpl_connect("scroll_event", on_scroll)
    canvas.mpl_connect("button_press_event", on_press)
    canvas.mpl_connect("button_release_event", on_release)
    canvas.mpl_connect("motion_notify_event", on_move)

   
def get_plot_schritt(hauptfenster):
    
    """
    Bei sehr hohen Abtastraten kann es dazu kommen beim Bewegen des GUI oder
    allgemein aufgrund der großen Datenmenge das es zu Lags kommt. Im schlimmsten 
    Fall zu Abstürzen des GUI. Damit nicht jeder Messeintrag bei großen Sample
    Rates dargestellt wird verwendet man diese Funktion, welche die Anzahl
    an dargestellten Werten im Live-Plot verringert. Diese Veränderung hat keinen
    Einfluss auf die Datenmenge in der CSV-Datei dort werden immer noch alle
    Einträge abgespeichert.

    Args:
        hauptfenster (Hauptfenster):
            Wird verwendet um die derzeit gespeicherte Sample rate aufzurufen
    
    Returns:
        int:
            je nach Fallunterscheidung 200, 100, 50 oder 1
            
    """

    #Um die Sample rate zu erhalten
    sample = hauptfenster.state.get("sample_rate", 2000)

    #Fallunterscheidung für die verschiedenen Sample Rates
    if sample >= 10000:
        return 200
    elif sample >= 5000:
        return 100
    elif sample >= 2000:
        return 50
    else:
        return 1

def signal_live_plot(hauptfenster):

    """
    Die Funktion erzeugt den Live-Plot für die zwei Signale. Es wird an zwei 
    Stellen die Spannung gemessen. Die gemessenen Spannungen werden in einem Frame
    live über die Zeit dargestellt. Das bedeutet man kann die Signale über den Widerstand
    bzw. das Ausgangssignal des Integrators verfolgen. Aufgrund der Zoom Funktion
    gibt es auch einen Reset Button. Dieser sorgt dafür die ursprüngliche Ansicht 
    wieder herzustellen. Somit ist es möglich zu zoomen und verschieben und kann
    per Buttonklick die eigentliche Ansicht wieder herstellen.

    Args:
        hauptfenster (Hauptfenster):
            Hauptfenster um frame zuzuweisen oder Daten zu erhalten usw.
    
    Returns:
        frame_signal (tk.LabelFrame):
            Gibt den erzeugten Frame zurück. Dort findet die Darstellung
            der Signale statt.    
    """
    
    frame_signal = hauptfenster.frames["signal"]

    #Frame zuerst updaten, damit Breite/Höhe korrekt sind
    #frame_signal.update_idletasks()

    #erstellen des Plots mit Matplotlib
    fig = Figure(dpi=100)  #Keine feste figsize, nur DPI
    fig.patch.set_facecolor("#f5f7fa")
    ax = fig.add_subplot(111)
    #Platz für Titel und Achsen
    fig.subplots_adjust(top=0.98, bottom=0.32, left=0.08, right=0.92)
    #ax.set_title("Spannungen an den Messpunkten x und y")
    ax.set_xlabel("Zeit [s]", labelpad=2)
    ax.set_ylabel("Spannung [V]")
    ax.set_facecolor("#ffffff")
    ax.grid(True, linestyle=":", color="#d0d0d0", alpha=0.7)

    #anlegen von Linien
    (line_x,) = ax.plot([], [], linewidth=1.2, label=r"$u_x$(t)")
    (line_y,) = ax.plot([], [], linewidth=1.2, label=r"$u_y$(t)")
    fig.subplots_adjust(right=0.92)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))

    #Reset Button um die Ansicht wieder auf die Ausgangslage zu blicken
    reset_button = tk.Button(
        frame_signal,
        text="↺ Reset",
        command=lambda: reset_plot_ansicht(frame_signal.live),
        font=("Arial", 8)
    )
    reset_button.pack(anchor="ne")

    #Canvas in Tk platzieren
    canvas = FigureCanvasTkAgg(fig, master=frame_signal)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    #Beim Ändern der Framegröße neu zeichnen
    frame_signal.bind("<Configure>", lambda e: canvas.draw())
    
    #erstellen eines Puffer und update_data befüllt die Liste
    frame_signal.live = {
        #"frame": frame,      
        "ax": ax,
        "canvas": canvas,
        "line_x": line_x,
        "line_y": line_y,
        "ts": [],            #Zeit
        "ux": [],            #Spannung_x
        "uy": []             #Spannung_y
    }


    def on_move_signal(event):

        """
        Die Funktion ist dafür die Position des Mauszeigers einen Wert im Plot
        zuzuordnen. Das bedeutet man erhält, in diesem Fall den Wert im GUI angezeigt
        für die Spannungen U_x und U_y.

        Args:
            event:
                Wenn das Event also der Live-Plot vorhanden ist
        
        Returns:
            None
        """

        #überprüft wo der Zeiger ist
        if event.inaxes is not ax:
            return

        #dargestellten Werte im Plot
        ts = frame_signal.live["ts"]
        ux = frame_signal.live["ux"]
        uy = frame_signal.live["uy"]

        #Wenn keine Werte vorhanden sind dann wird auch None zurückgeben
        if not ts or not ux or not uy:
            return

        h_cursor = event.xdata

        if event.xdata is None:
            return

        #Cursor Variable
        t_cursor = event.xdata

        t_arr = np.asarray(ts)
        idx = int(np.argmin(np.abs(t_arr - t_cursor)))

        #man erhält die aktuellen Werte bezogen auf den Mauszeiger
        cursor_ux_var = hauptfenster.state.get("cursor_ux_var")
        cursor_uy_var = hauptfenster.state.get("cursor_uy_var")

        #Wenn es Werte gibt werden die gesetzt und angezeigt
        if cursor_ux_var is not None:
            cursor_ux_var.set(f"Ux = {ux[idx]:.3f} V")

        if cursor_uy_var is not None:
            cursor_uy_var.set(f"Uy = {uy[idx]:.3f} V")

    canvas.mpl_connect("motion_notify_event", on_move_signal)

    #Zoom per Mausrad aktivieren
    zoom_funktion(frame_signal.live)


    #update anstoßen
    hauptfenster.after(100, update_data, hauptfenster)

    return frame_signal    

def hysterese_live_plot(hauptfenster):

    """
    Dadurch erfolgt der Hysterese Live-Plot. An sich die exakt gleiche Funktion
    wie signal_live_plot. Der Unterschied ist hier geht es um die magnetische
    Feldstärke H und magnetische Flussdichte B. 

    Args:
        hauptfenster (Hauptfenster):
            Hauptfenster um frame zuzuweisen oder Daten zu erhalten usw.
    
    Returns:
        frame_hyst (tk.LabelFrame):
            Gibt den erzeugten Frame zurück. Dort findet die Darstellung
            der Hysterese statt.  

    """
     
    frame_hyst = hauptfenster.frames["hysterese"]

    #Frame zuerst updaten, damit Breite/Höhe korrekt sind
    frame_hyst.update_idletasks()

    #erstellen des Plots mit Matplotlib
    fig = Figure(dpi=100)  # Keine feste figsize, nur DPI
    fig.patch.set_facecolor("#f5f7fa")
    fig.subplots_adjust(
        left=0.07,   #links  (0..1, kleiner = näher am Rand)
        right=0.98,  #rechts
        top=0.95,    #oben
        bottom=0.1   #unten
    )
    ax = fig.add_subplot(111)
    #ax.set_title("Hysterese")
    ax.set_xlabel("H [A/m]")
    ax.set_ylabel("B [T]")
    ax.set_facecolor("#ffffff")
    ax.grid(True, linestyle=":", color="#d0d0d0", alpha=0.7)

    #anlegen von Linien
    (line_hb,) = ax.plot([], [], linewidth=1.2, label="B(H)")
    ax.legend(loc="best")

    #Reset Button 
    reset_button = tk.Button(
        frame_hyst,
        text="↺ Reset",
        command=lambda: reset_plot_ansicht(frame_hyst.live),
        font=("Arial", 8)
    )
    reset_button.pack(anchor="ne")

    #Canvas in Tk platzieren
    canvas = FigureCanvasTkAgg(fig, master=frame_hyst)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    #Beim Ändern der Framegröße neu zeichnen
    frame_hyst.bind("<Configure>", lambda e: canvas.draw())
    
    #erstellen eines Puffers und update_data befüllt die Liste
    frame_hyst.live = {
        #"frame": frame,      
        "ax": ax,
        "canvas": canvas,
        "line_hb": line_hb,
        "H": [],            #magnetische Feldstärke H
        "B": []             #magnetische Flussdichte B
    }

    

    #Cursor Maus update
    def on_move(event):

        #damit die Maus/Cursor nur reagiert wenn im Diagramm
        if event.inaxes is not ax:
            return
        
        H_vals = frame_hyst.live["H"]
        B_vals = frame_hyst.live["B"]

        if not H_vals or not B_vals:
            return
        
        if event.xdata is None:
            return

        #Position für x der Maus, also den Wert H
        h_cursor = event.xdata

        #neuer Messpunkt zu dieser H Position
        H_arr = np.asarray(H_vals)
        idx = int(np.argmin(np.abs(H_arr - h_cursor)))
        H_val = H_arr[idx]
        B_val = B_vals[idx]

        # StringVars aus dem Hauptfenster holen (im Cursor-Frame angelegt)
        cursor_H_var = hauptfenster.state.get("cursor_H_var")
        cursor_B_var = hauptfenster.state.get("cursor_B_var")

        if cursor_H_var is not None:
            cursor_H_var.set(f"H = {H_val:.2f} A/m")
        if cursor_B_var is not None:
            cursor_B_var.set(f"B = {B_val:.3f} T")

    #Event mit Canvas verbinden
    canvas.mpl_connect("motion_notify_event", on_move)

    #Zoom per Mausrad aktivieren
    zoom_funktion(frame_hyst.live)


    return frame_hyst    


def permeabilitaet_live_plot(hauptfenster):

    """
    Dadurch erfolgt der Permeabilitäts Live-Plot. An sich die exakt gleiche Funktion
    wie signal_live_plot. Der Unterschied ist hier geht es um die differentielle
    Permeabilität. 

    Args:
        hauptfenster (Hauptfenster):
            Hauptfenster um frame zuzuweisen oder Daten zu erhalten usw.
    
    Returns:
        frame_perm (tk.LabelFrame):
            Gibt den erzeugten Frame zurück. Dort findet die Darstellung
            der Permeabilität statt.  

    """
     
    frame_perm = hauptfenster.frames["permeabilität"]

    #Frame zuerst updaten, damit Breite/Höhe korrekt sind
    frame_perm.update_idletasks()

    #erstellen des Plots mit Matplotlib
    fig = Figure(dpi=100)  # Keine feste figsize, nur DPI
    fig.patch.set_facecolor("#f5f7fa")
    fig.subplots_adjust(
        left=0.07,  #links  (0..1, kleiner = näher am Rand)
        right=0.98, #rechts
        top=0.95,   #oben
        bottom=0.1  #unten
    )
    ax = fig.add_subplot(111)
    #ax.set_title("Hysterese")
    ax.set_xlabel("H [A/m]")
    ax.set_ylabel(r"differentielle Permeabilität $\mu_diff$")
    ax.set_facecolor("#ffffff")
    ax.grid(True, linestyle=":", color="#d0d0d0", alpha=0.7)

    #anlegen von Linien
    (line_mu,) = ax.plot([], [], linewidth=1.2, label="\u03BC(H)")
    ax.legend(loc="best")

    reset_button = tk.Button(
        frame_perm,
        text="↺ Reset",
        command=lambda: reset_plot_ansicht(frame_perm.live),
        font=("Arial", 8)
    )
    reset_button.pack(anchor="ne")


    #Canvas in Tk platzieren
    canvas = FigureCanvasTkAgg(fig, master=frame_perm)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Beim Ändern der Framegröße neu zeichnen
    frame_perm.bind("<Configure>", lambda e: canvas.draw())
    
    #erstellen eines Puffers und update_data befüllt die Liste
    frame_perm.live = {
        #"frame": frame,      
        "ax": ax,
        "canvas": canvas,
        "line_mu": line_mu,
        "H": [],            # Spannung_x
        "B": []             # Spannung_y
    }

    
    def on_move_mu(event):

        if event.inaxes is not ax:
            return

        H_vals = frame_perm.live["H"]
        B_vals = frame_perm.live["B"]

        if len(H_vals) < 3 or len(B_vals) < 3:
            return

        H_arr = np.asarray(H_vals)
        B_arr = np.asarray(B_vals)

        mu0 = 4 * np.pi * 1e-7
        dH = np.gradient(H_arr)
        dB = np.gradient(B_arr)

        with np.errstate(divide="ignore", invalid="ignore"):
            mu_r = dB / dH / mu0
            mu_r[~np.isfinite(mu_r)] = np.nan

        h_cursor = event.xdata
        idx = int(np.nanargmin(np.abs(H_arr - h_cursor)))

        cursor_H_var = hauptfenster.state.get("cursor_H_var")
        cursor_B_var = hauptfenster.state.get("cursor_B_var")

        if cursor_H_var is not None:
            cursor_H_var.set(f"H = {H_arr[idx]:.2f} A/m")

        if cursor_B_var is not None:
            mu_val = mu_r[idx]

            if np.isnan(mu_val):
                cursor_B_var.set("μdiff = –")
            else:
                cursor_B_var.set(f"μdiff = {mu_val:.0f}")

    canvas.mpl_connect("motion_notify_event", on_move_mu)

    #Zoom per Mausrad aktivieren
    zoom_funktion(frame_perm.live)

    

    return frame_perm   


 
def reset_plot_ansicht(live):

    """
    Es wird die Ansicht der Live-Plots zurückgesetzt. 

    Args:
        live (dict):
            Dictionary mit Canvas und Achse des Live-Plots.

    """

    #Achse zuordnen
    ax = live["ax"]

    #Live-Plot
    canvas = live["canvas"]

    #Achsen auf autoscale
    ax.set_autoscale_on(True)
    ax.relim()
    ax.autoscale_view()

    #Darstellung der Achsen usw.
    canvas.draw_idle()


def plot_frames(hauptfenster):

    """
    Der Container erzeugt eine Abteilung in Form von zwei Rahmen auf der rechten
    Seite des GUI. Der Container erzeugt eine Abteilung in Form von zwei Rahmen auf 
    der rechten Seite des GUI. Mittels einer Gewichtung ist der Container des Hysterese/
    Permeabilitäts Container größer als der Signal Container. Der Grund dafür
    ist, dass das Signal nicht so viel Platz benötigt und das Hauptaugenmerk
    sollte auf der Hysterese liegen. Es werden drei Frames erzeugt und dem 
    jeweiligen Container zugeordnet.
    
    Args:
        hauptfenster (Hauptfenster):
            zuzuordnen des Containers auf dem Hauptfenster des GUI
    
    Returns:
        frame_signal (tk.LabelFrame):
            Frame des Signals, ist dem Container reihe 0 zugeordnet

        frame_hysterese/frame_perme (tk.LabelFrame):
            Frame der Hysterese oder Permeabilität, ist dem Container reihe 1 
            zugeordnet. Zwei Frames für die verschieden Beschriftung des live
            Plots.
        

    """


    #Container für die Frames erzeugen
    right_container = tk.Frame(hauptfenster, bg="#e4e7ec")
    right_container.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    #Grid-Verhältnis: oben klein (Signal), unten groß (Hysterese)
    right_container.grid_rowconfigure(0, weight=2, uniform="rows")
    right_container.grid_rowconfigure(1, weight=4, uniform="rows")
    right_container.grid_columnconfigure(0, weight=2)

    #frame Signal
    frame_signal = tk.LabelFrame(right_container, text="Signale", relief="ridge",
                                bd=6,padx=10,pady=10,background="#f5f7fa",
                                font=("Arial", 10, "bold"))
    frame_signal.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 10))

    
    #Frame Hysterese
    frame_hysterese = tk.LabelFrame(right_container, text="Hysterese", relief="ridge",
                                    bd=6,padx=10,pady=10,background="#f5f7fa",
                                    font=("Arial", 10, "bold"))
    frame_hysterese.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 0))

   
    #Frame Permeabilität
    frame_perme = tk.LabelFrame(right_container, text="Permeabilität", relief="ridge",
                                    bd=6,padx=10,pady=10,background="#f5f7fa",
                                    font=("Arial", 10, "bold"))
    frame_perme.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 0))


    hauptfenster.frames = {"signal": frame_signal, "hysterese": frame_hysterese,
                           "permeabilität": frame_perme}

    #Permeabilität am Anfang ausblenden:
    frame_perme.grid_remove()

    return frame_signal, frame_hysterese, frame_perme



def update_data(hauptfenster):

    """
    Aktualisiert die Live-Plots mit den empfangenen Messdaten.
    Die Messdaten werden aus der Daten-Queue gelesen und in den Puffern
    für Signal, Hysterese und Permeabilität gespeichert. Anschließend
    werden die sichtbaren Plots aktualisiert. Bei hohen Abtastraten wird
    nur ein Teil der Messpunkte dargestellt, während weiterhin alle Werte
    in der CSV-Datei gespeichert werden.

    Args:
        hauptfenster (Hauptfenster):
            Hauptfenster mit den gespeicherten Plotdaten und Zuständen

    """

    frame_signal = hauptfenster.frames["signal"]
    frame_hyst   = hauptfenster.frames["hysterese"]
    frame_perm   = hauptfenster.frames["permeabilität"]  

    if not hasattr(frame_signal, "live"):
        return
    
    live = frame_signal.live
    ts, ux, uy = live["ts"], live["ux"], live["uy"]
    live_hyst = getattr(frame_hyst, "live", None)
    live_perm  = getattr(frame_perm, "live", None)

    drained = 0

    try:
        while True:
            t, x, y = data_queue.get_nowait()  #nicht blockieren
            ts.append(t); ux.append(x); uy.append(y)
            drained += 1

            if live_hyst is not None or live_perm is not None:
                h_scale = hauptfenster.state["scale_H"]
                b_scale = hauptfenster.state["scale_B"]

                if h_scale is None or b_scale is None:
                    continue  #noch nicht gesetzt überspringen
                
                H = x * h_scale
                B = y * b_scale

                if live_hyst is not None:
                    live_hyst["H"].append(H)
                    live_hyst["B"].append(B)

                if live_perm is not None:
                    live_perm["H"].append(H)
                    live_perm["B"].append(B)

    except queue.Empty:
        pass

    if drained:

        schritt = get_plot_schritt(hauptfenster)

        #optional Sichtfenster begrenzen
        max_pts = 5000

        #Signalplot
        if len(ts) > max_pts:
            ts[:] = ts[-max_pts:]
            ux[:] = ux[-max_pts:]
            uy[:] = uy[-max_pts:]

        live["line_x"].set_data(ts[::schritt], ux[::schritt])
        live["line_y"].set_data(ts[::schritt], uy[::schritt])
        live["ax"].relim(); live["ax"].autoscale_view()
        live["canvas"].draw_idle()

        #Hystereseplot
        if live_hyst is not None:
            H_arr = np.asarray(live_hyst["H"], dtype=float)
            B_arr = np.asarray(live_hyst["B"], dtype=float)

            # Regulär reduzierte Indizes
            indices = np.arange(0, len(H_arr), schritt)

            # Positionen der NaN-Trennstellen
            nan_indices = np.where(np.isnan(H_arr) | np.isnan(B_arr))[0]

            # Beide Indexmengen zusammenführen und sortieren
            indices = np.unique(np.concatenate((indices, nan_indices)))

            live_hyst["line_hb"].set_data(H_arr[indices],B_arr[indices])
            
            live_hyst["ax"].relim() 
            live_hyst["ax"].autoscale_view()
            live_hyst["canvas"].draw_idle()

        #Permeabilitätsplot
        if live_perm is not None and len(live_perm["H"]) > 2:
            H_arr = np.asarray(live_perm["H"])
            B_arr = np.asarray(live_perm["B"])

            mu0 = 4 * np.pi * 1e-7
            dH = np.gradient(H_arr)
            dB = np.gradient(B_arr)

            with np.errstate(divide="ignore", invalid="ignore"):
                mu_r = dB / dH / mu0
                mu_r[~np.isfinite(mu_r)] = np.nan  # NaN/Inf raus

            live_perm["line_mu"].set_data(H_arr[::schritt],mu_r[::schritt])
            live_perm["ax"].relim()
            live_perm["ax"].autoscale_view()
            live_perm["canvas"].draw_idle()

    hauptfenster.after(100, update_data, hauptfenster)    


def mess_button(frame_messung,hauptfenster,value_radio_klick):

    """
    Erzeugt den Messung starten Button. Dieser Button ist ein Toggle Button
    und wechselt von Messung starten auf Messung beenden und danach auf Messung
    neu starten. Der Button wird im Mess Frame erzeugt.

    Args:
        frame_messung (tk.LabelFrame):
            Mess frame Zuordnung der Buttons

        hauptfenster (Hauptfenster): 
            GUI Hauptfenster um die Zustände zu erhalten oder zu verändern
        
        value_radio_klick (tk.IntVar):
            Zur Auswahl welche Darstellung durchgeführt wird
    
    """
    
    #Flag im Hauptfenster Zustand ablegen
    hauptfenster.state["messung_laeuft"] = False

    #Statusanzeige
    status_var = tk.StringVar(value="Gestoppt")
    tk.Label(hauptfenster.frames["signal"], textvariable=status_var).pack(anchor="w", padx=200)

    #EIN Button für Start/Stop
    button_toggle = create_button(frame_messung, text="Messung starten", primary=True)
    button_toggle.pack(anchor="w", pady=10, padx=10)

    #Flag im Hauptfenster Zustand ablegen
    hauptfenster.state["status_var"] = status_var
    hauptfenster.state["button_toggle"] = button_toggle

    #Status für die LED setzen
    status_led =   tk.IntVar(value=1)
    hauptfenster.state["led_var"] = status_led

    def start_stop_button():

        """
        Ermöglicht einen stopp und Messungs fortsetzen Button. Man kann natürlich
        die Messung auch immer wieder von neuem starten, dennoch ist die Möglichkeit
        der pause usw. sowie fortsetzen vorhanden. Hier gilt besser haben als
        brauchen.
        """

        if not hauptfenster.state["messung_laeuft"]:
            #Messung STARTEN

            #Mit jeder neuen Messung muss das Interface entleert werden
            index_csv()

            #um den index hochzuzählen für jede einzelne Messung
            hauptfenster.state["messung_var"].set(f"{get_messung_index():02d}")

            clear_live_plots(hauptfenster)  

            start_messung()  #h weiter run_event.set() verwenden
            start_plot_nach_auswahl(value_radio_klick, hauptfenster)

            hauptfenster.state["messung_laeuft"] = True

            #Button wird verändert
            button_toggle.config(
                text="Messung beenden",
                bg="lightgreen",
                activebackground="limegreen",
                fg="black",
                activeforeground="black"
            )
            status_var.set("Messung läuft…")
            status_led.set(0)
        else:
            #Messung BEENDEN
            stop_messung()   #hier drin sollte run_event.clear() usw. stehen

            hauptfenster.state["messung_laeuft"] = False

            #Button wird verändert
            button_toggle.config(
                text="Messung neu starten",
                bg="#1e88e5",
                activebackground="#1565c0",
                fg="white",
                activeforeground="white"
            )
            status_var.set("Gestoppt")
            status_led.set(1)

    button_toggle.config(command=start_stop_button)    



def LED_status(frame_led, hauptfenster):

    """
    Erzeugt eine LED die zusätzlich als Indikator dient ob die Messung läuft
    (leuchtet grün) oder nicht (leuchtet rot). Das dient dazu falls eventuell
    keine Darstellung erfolgt die Messung aber läuft könnte man darauf schließen, 
    das Problem beim Messaufbau vorhanden sind. Das hauptfenster wird wieder für den 
    Status gespeichert.

    Args:
        frame_led (tk.Frame):
            Frame für die Zuordnung
        
        hauptfenster (Hauptfenster):
            Zuordnung der LED auf dem Hauptfenster des GUI
        
    """

    #LED/Anzeige erzeugen
    status_led = hauptfenster.state["led_var"]  
    led = tk.Canvas(frame_led, width=60, height=60, highlightthickness=0, bg="#f5f7fa")
    led.pack(expand=True, pady=(20, 0))
    dot = led.create_oval(5, 5, 55, 55, fill="red", outline="black",width=2)  #start rot

    def update_led(*_):

        """
        Update Funktion für die Farbe der LED
        """

        led.itemconfig(dot, fill="green" if status_led.get() == 0 else "red")
    
    update_led()
    status_led.trace_add("write", update_led)

    hauptfenster.state["led_canvas"] = led
    hauptfenster.state["led_dot"] = dot

def close_hauptfenster(frame_messung,hauptfenster):

    """
    Es wird ein Button erzeugt, welcher das GUI beendet. Man kann auch klassisch
    auf das "X" oder "ALT+F4". Dieser Button ist ein reiner Zusatz und befindet
    sich im selben Frame mit den Messbuttons. 

    Args:
        frame_messung (tk.LabelFrame):
            Frame für die Messsteuerung.

        hauptfenster (Hauptfenster):
            Hauptfenster des Messprogramms.

    """

    def programm_beenden():
        stop_messung()
        hauptfenster.destroy()

    hauptfenster.protocol("WM_DELETE_WINDOW", programm_beenden)

    #einen schließen Button erzeugen, welcher das gesamte GUI beendet
    close_button = create_button(
        frame_messung,
        text="Messprogramm schließen",
        command=programm_beenden,
        primary=False,
    )
    close_button.pack(side="bottom", fill="x", padx=10, pady=(15, 15))


def messung_pausieren(frame_messung,hauptfenster,messung_fort_button):

    """
    Erzeugt den Button Messung pausieren. Das bedeutet man hat die Möglichkeit 
    während der laufenden Messung die Messung zu stoppen/pausieren. Der Messung
    Pausieren Button hängt natürlich auch mit dem Messung fortsetzen Button
    zusammen. Der Messung fortsetzen Button wird nur eingeblendet, wenn
    die Messung überhaupt pausiert wurde.

    Args:
        frame_messung (tk.LabelFrame):
            Frame für die Messsteuerung
        
        hauptfenster (Hauptfenster):
            GUI Zuordnung
        
        messung_fort_button (tk.Button):
            Ist für den Messung fortsetzen Button, nur bei Pausierung möglich





    """ 
    def on_pause():

        """
        Pausiert die laufende Messung und aktualisiert die GUI-Anzeige.
        """

        #nur pausieren, wenn überhaupt eine Messung läuft
        if not hauptfenster.state.get("messung_laeuft", False):
            return


        #stoppt die Messung
        stop_messung()

        #State setzen
        hauptfenster.state["messung_laeuft"] = False

        #LED
        led_var = hauptfenster.state.get("led_var")
        if led_var is not None:
            led_var.set(1)

        #Status erhalten und abspeichern
        status_var = hauptfenster.state.get("status_var")
        button_toggle = hauptfenster.state.get("button_toggle")

        #Bedingungen für die Fälle und was passieren sollte
        if status_var is not None:
            status_var.set("Gestoppt (pausiert)")

        if button_toggle is not None:
            #Den bereits erzeugten Button neu konfigurieren
            button_toggle.config(
                text="Messung neu starten",     
                bg="#1e88e5",
                activebackground="#1565c0",
                fg="white",
                activeforeground="white",
            )

        #Messung fortsetzen
        if messung_fort_button is not None:

            #anpassen und positionieren des Messung fortsetzen button
            messung_fort_button.pack_configure(anchor="w", padx=10, pady=5)

        #LED für die Reihenfolge hier platzieren
        frame_led = hauptfenster.state.get("frame_led")
        if frame_led is not None:
            frame_led.pack_forget()
            frame_led.pack(expand=True, fill="both")

    #Messung stopp Button generieren
    messung_stopp_button = create_button(
        frame_messung,
        text="Messprogramm pausieren/stoppen",
        command=on_pause,
        primary=False,
    )
    #Messung stopp Button positionieren
    messung_stopp_button.pack(anchor="w", padx=10, pady=5)


def messung_fortsetzen(frame_messung,hauptfenster,value_radio_klick):

    """
    Dieser Button soll die Messung fortsetzen und die Datei an diesem Punkt 
    weiter beschreiben. Das heißt die Messung läuft wird pausiert bzw. gestoppt,
    dieser Zeitpunkt oder der letzte Eintrag ist relevant denn nach diesem, wenn 
    man den Button Messung fortsetzen klickt soll dann an dieser Stelle die
    Datenspeicherung weiter gehen.

    Args:
        frame_messung (tk.LabelFrame):
            Zuordnung des Buttons in den richtigen Frame
        
        hauptfenster (Hauptfenster):
            GUI Zuordnung
        
        value_radio_klick (tk.IntVar):
            Je nachdem welcher Frame aktiviert wird für die Beschriftung relevant

    Returns:
        messung_fort_button (tk.Button):
            Der erzeugte Messung fortsetzen Button wird zurückgegeben

    """



    def on_fortsetzen():

        if hauptfenster.state.get("messung_laeuft", False):
            print("Messung läuft bereits Fortsetzen ignoriert.")
            return

        #Trennstelle für die Plots einfügen
        #Somit gibt es keine Verbindungslinie, wenn man messung fortsetzen klickt
        frame_hyst = hauptfenster.frames["hysterese"]
        
        if value_radio_klick.get() == 0:

            frame_hyst = hauptfenster.frames["hysterese"]

            if hasattr(frame_hyst, "live"):
                print("NaN wird angehängt")
                print("Länge vorher:", len(frame_hyst.live["H"]))

                frame_hyst.live["H"].append(np.nan)
                frame_hyst.live["B"].append(np.nan)

                print("Letzte H-Werte:", frame_hyst.live["H"][-5:])
                print("Länge nachher:", len(frame_hyst.live["H"]))

        #Flag setzen
        set_fortsetzen_modus(True)

        #Messung starten (start_messung prüft fortsetzen_modus)
        start_messung()

        #Plot (wie beim normalen Start)
        start_plot_nach_auswahl(value_radio_klick, hauptfenster)

        #Zustand aktualisieren
        hauptfenster.state["messung_laeuft"] = True

        #Led
        led_var = hauptfenster.state.get("led_var")
        if led_var is not None:
            led_var.set(0)

        status_var = hauptfenster.state.get("status_var")
        button_toggle = hauptfenster.state.get("button_toggle")

        if status_var is not None:
            status_var.set("Messung läuft… (fortgesetzt)")

        if button_toggle is not None:
            button_toggle.config(
                text="Messung beenden",
                bg="lightgreen",
                activebackground="limegreen",
                fg="black",
                activeforeground="black",
            )
        
        #Fortsetzen-Button wieder ausblenden
        fort_btn = hauptfenster.state.get("fortsetzen_button")
        if fort_btn is not None:
            fort_btn.pack_forget()

    messung_fort_button = create_button(
        frame_messung,
        text="Messprogramm fortsetzen",
        command=on_fortsetzen,
        primary=False,
    )

    #Einmal an richtiger Stelle packen (Position wird festgelegt)
    messung_fort_button.pack(anchor="w", padx=10, pady=5)
    #Button nicht anzeigen, mit pack_forget Button ausblenden, aber dieser ist erzeugt
    messung_fort_button.pack_forget()

    #Referenz des Buttons speichern
    hauptfenster.state["fortsetzen_button"] = messung_fort_button
    return messung_fort_button

def container_left(hauptfenster):

    """
    Wie zuvor für die Live-Plots wird ein Container für die linke Seite des 
    Bildschirms erstellt. Es werden vier Container benötigt. Die Container
    beinhalten. Es werden vier Container mit unterschiedlicher Gewichtung 
    benötigt. Dazu werden wieder die jeweiligen Frames erzeugt. Diese dienen
    zur Beschriftung. Das macht man um die einzelne Funktion zu separieren
    und das GUI übersichtlicher zu gestalten.

    Args:
        hauptfenster (Hauptfenster):
            GUI Zuordnung
    
    Returns:
        frame_scale (tk.LabelFrame):
            beschriftet den Skalierungsfaktor Container

        frame_messung_ss (tk.LabelFrame):
            beschriftet den Messungs Container

        frame_hysterese_perme (tk.LabelFrame):
            beschriftet die Auswahl ob Permeabilität oder Hysterese gemessen wird Container

        frame_cursor (tk.LabelFrame):
            beschriftet den Cursor, Sample Rate, Anzahl Messungen Container
    """

    #Container für die Frames erzeugen
    left_container = tk.Frame(hauptfenster, bg="#e4e7ec")
    left_container.pack(side="left", fill="both", expand=False, padx=20, pady=20)

    #Grid-Verhältnis: oben flach (Signal), unten groß (Hysterese)
    left_container.grid_rowconfigure(0, weight=1, uniform="rows")
    left_container.grid_rowconfigure(1, weight=2, uniform="rows")
    left_container.grid_rowconfigure(2, weight=1, uniform="rows")
    left_container.grid_rowconfigure(3, weight=1, uniform="rows")
    left_container.grid_columnconfigure(0, weight=0)

    #frame Skalierungsfaktoren
    frame_scale = tk.LabelFrame(left_container, text="Skalierungsfaktoren", relief="ridge",
                                bd=6,padx=10,pady=10,background="#f5f7fa",
                                font=("Arial", 10, "bold"))
    frame_scale.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Frame Messung Start/Stopp
    frame_messung_ss = tk.LabelFrame(left_container, text="Messung Start/Stopp", relief="ridge",
                                bd=6,padx=10,pady=10,background="#f5f7fa",
                                font=("Arial", 10, "bold"))
    frame_messung_ss.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Messauswahl Hysterese/Permeabilität
    frame_hysterese_perme = tk.LabelFrame(left_container, text="Hysterese/Permeabilität", relief="ridge",
                                bd=6,padx=10,pady=10,background="#f5f7fa",
                                font=("Arial", 10, "bold"))
    frame_hysterese_perme.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Frame für Cursor erzeugen 
    frame_cursor = tk.LabelFrame(left_container, text="Cursor/Messwerte", relief="ridge",
                                bd=6,padx=10,pady=10,background="#f5f7fa",
                                font=("Arial", 10, "bold"))
    frame_cursor.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))                             

    

    #StringVars für H und B,Variable an widget binden
    cursor_H_var = tk.StringVar(value="H: –")
    cursor_B_var = tk.StringVar(value="B: –")

    cursor_ux_var = tk.StringVar(value="Ux: –")
    cursor_uy_var = tk.StringVar(value="Uy: –")

    #Zeile 1: H und Ux
    frame_cursor_zeile1 = tk.Frame(frame_cursor, bg="#f5f7fa")
    frame_cursor_zeile1.pack(anchor="w")

    #Zeile 2: B und Uy
    frame_cursor_zeile2 = tk.Frame(frame_cursor, bg="#f5f7fa")
    frame_cursor_zeile2.pack(anchor="w")

    #erstellen des Labels
    label_H = tk.Label(frame_cursor_zeile1,width=16, textvariable=cursor_H_var,
                     anchor="w", font=("Arial", 10))

    label_H.pack(side="left")

    label_B = tk.Label(frame_cursor_zeile2,width=16, textvariable=cursor_B_var,
                     anchor="w", font=("Arial", 10))

    label_B.pack(side="left")

    

    #für signal label
    label_Ux = tk.Label(frame_cursor_zeile1, width=14, textvariable=cursor_ux_var,
                     anchor="w", font=("Arial", 10))

    label_Ux.pack(side="left", padx=(10, 0))

    label_Uy = tk.Label(frame_cursor_zeile2, width=14, textvariable=cursor_uy_var,
                     anchor="w", font=("Arial", 10))

    label_Uy.pack(side="left", padx=(10, 0))

    #Frame für Informationen wie Sample Rate und Messung Anzahl
    frame_info = tk.Frame(frame_cursor, bg="#f5f7fa")
    frame_info.pack(anchor="w", pady=(15, 2))

    #Linker Block: Messung
    frame_messung_anzeige = tk.Frame(frame_info, bg="#f5f7fa")
    frame_messung_anzeige.pack(side="left")

    #Rechter Block: Sample Rate
    frame_sample_anzeige = tk.Frame(frame_info, bg="#f5f7fa")
    frame_sample_anzeige.pack(side="left", padx=(25, 0))

    #Anzeige der aktuellen Messung die Anzahl wird angezeigt
    messung_var = tk.StringVar(value="00")

    def reset_index_anzeige():
        reset_messung_index()
        messung_var.set("00")

    tk.Label(
        frame_messung_anzeige,
        text="Messung:",
        font=("Arial", 10, "bold")
    ).pack(anchor="w")

    tk.Label(
        frame_messung_anzeige,
        textvariable=messung_var,
        width=4,
        relief="sunken",
        bd=2,
        bg="white",
        font=("Arial", 12, "bold")
    ).pack(side="left")

    tk.Button(
        frame_messung_anzeige,
        text="Reset",
        command=reset_index_anzeige,
        width=5,
        font=("Arial", 8)
    ).pack(side="left", padx=5)


    sample_var = tk.StringVar(value="2000 S/s")

    tk.Label(
        frame_sample_anzeige,
        text="Sample Rate:",
        font=("Arial", 10, "bold")
    ).pack(anchor="w")

    tk.Label(
        frame_sample_anzeige,
        textvariable=sample_var,
        width=8,
        relief="sunken",
        bd=2,
        bg="white",
        font=("Arial", 10)
    ).pack(anchor="w")
        
    #Im GUI-Zustand speichern
    hauptfenster.state["messung_var"] = messung_var
    hauptfenster.state["sample_var"] = sample_var    

    #im Zustand des Hauptfensters merken, damit der Plot darauf zugreifen kann
    hauptfenster.state["cursor_H_var"] = cursor_H_var
    hauptfenster.state["cursor_B_var"] = cursor_B_var
    hauptfenster.state["cursor_ux_var"] = cursor_ux_var
    hauptfenster.state["cursor_uy_var"] = cursor_uy_var
    hauptfenster.state["label_B"] = label_B

    return frame_scale,frame_messung_ss,frame_hysterese_perme,frame_cursor


def hyst_perm_auswahl(frame_hyst_perm,hauptfenster):
    
    """
    Die Funktion wird benötigt, weil ein Teil des Labors ist es die 
    differentielle Permeabilität zu messen. Es ändern sich ausgehend 
    von den Skalierungsfaktoren die neuen Skalierungen bzw. die Berechnung
    der differentiellen Permeabilität. Daher muss mittels Radio Button
    eine Unterscheidung durchgeführt werden, ob Hysterese oder Permeabilität
    gemessen wird.

    Args:
        frame_hyst_perm (tk.LabelFrame):
            Der benötigte Frame in dem der Radio Button erzeugt wird

        hauptfenster (Hauptfenster):
            GUI Zuordnung und für den Status von Variablen benötigt
    
    Returns:
        value_radio (tk.IntVar):
            Man bekommt eine 0 oder 1 zurück
    """

    #Value Variable zuweisen
    value_radio = tk.IntVar(value=0)
    label_B = hauptfenster.state["label_B"] 
    cursor_B_var = hauptfenster.state["cursor_B_var"]


    def on_radio_change(*args):
        
        """
        Bei Änderung des Buttons erfolgt die Unterscheidung und somit
        eine neue Beschriftung. Es muss sich der Frame des Live-Plots
        und der Cursor ändern
        """

        if value_radio.get() == 0:
            hauptfenster.frames["permeabilität"].grid_remove()
            hauptfenster.frames["hysterese"].grid()
            label_B.config(textvariable=cursor_B_var)
            cursor_B_var.set("B: –")

        else:
            hauptfenster.frames["hysterese"].grid_remove()
            hauptfenster.frames["permeabilität"].grid()
            cursor_B_var.set("μdiff: –")

    value_radio.trace_add("write", on_radio_change)
    on_radio_change()

    #Hysterese Radio Button Wert = 0
    hysterese_radio = tk.Radiobutton(frame_hyst_perm, text="Messung Hysterese", 
                                        variable=value_radio, value=0,
                                        background="#f5f7fa",
                                        selectcolor="#f5f7fa",
                                        font=("Arial", 12, "bold"))
                                    
    
    #Permeabilität Radio Button Wert = 1
    permeabilitaet_radio = tk.Radiobutton(frame_hyst_perm, text="Messung Permeabilität", 
                                            variable=value_radio, value=1,
                                            background="#f5f7fa",
                                            selectcolor="#f5f7fa",
                                            font=("Arial", 12, "bold"),pady=5)

    hysterese_radio.grid(column=0, row=0, sticky="W")
    permeabilitaet_radio.grid(column=0, row=1, sticky="W")

    return value_radio

def datei_laden(hauptfenster,pfad):

    """
    Diese Funktion ermöglicht es die gemessenen Daten darzustellen. 
    Dabei ist eine Mehrfachauswahl möglich. Somit kann man im Anschluss
    an die Messungen die Daten laden und die einzelnen Versuche besprechen.
    Alle ausgewählten Dateien werden in einen Plot dargestellt. Somit ist eine
    sofortige Besprechung einer Hystereseschleife bei verschiedenen Frequenzen
    möglich. Man kann auch nur einzelne Dateien betrachten. Außerdem ist es
    möglich den neuen Dateityp CSV sowie den alten .dat-Dateien zu laden und darzustellen.
    Wichtig ist es müssen zuvor die Skalierungsfaktoren eingegeben werden.

    Args:
        hauptfenster (Hauptfenster):
            Hauptfenster für States benötigt
        
        pfad (str):
            Man erhält den aktuellen Pfad der Dateien bzw. wird beim 
            Aufrufen von Daten laden benötigt
    
    Returns:
        h (numpy.ndarray):
            Skalierungsfaktor für magnetische Feldstärke H
        
        b (numpy.ndarray):
            Skalierungsfaktor für die magnetische Flussdichte B
    """

    #Datei laden
    ext = os.path.splitext(pfad)[1].lower()

    #prüfen auf Dateityp das ist für die alten Dateien
    if ext in [".cfg",".dat"]:

        #Skalierung berücksichtigen, das heißt Reihe 2 und Reihe 3 Daten 
        #müssen skaliert werden

        data_l = np.loadtxt(pfad, dtype=str)
        data_l = np.char.replace(data_l, ",",".")

        data = data_l.astype(float)

        #3 Spalten extrahieren
        t  = data[:, 0]
        ux = data[:, 1]
        uy = data[:, 2]

    #für die neuen Dateien
    elif ext == ".csv":
        
        #Die ersten beiden Zeilen der Kopfzeile lesen
        with open(pfad, "r", encoding="utf-8") as file:
            offset_zeile = file.readline().strip()

        #Offset auslesen
        offset = float(
            offset_zeile.split("=")[1]
            .replace("V", "")
            .strip()
        )

        data = np.genfromtxt(pfad,delimiter=";",skip_header=2)

        #Prüfen ob Datei leer ist
        if data.size == 0:
            messagebox.showerror(
                "Fehlerhafte Datei",
                "Keine Daten in der Datei vorhanden."
            )
            return None

        #3 Spalten extrahieren
        t  = data[:, 0]
        ux = data[:, 1]
        uy = data[:, 2]

        

    #Falls kein gültiger Dateityp verwendet wird kommt es zu dieser Fehlermeldung
    else: 
        messagebox.showerror("Ungültiger Dateityp",
                            "Bitte verwenden Sie eine .cfg-, .dat- oder .csv-Datei."
                            )
        return None
            
       
    #Berechnen mit den Skalierungsfaktoren und Offset
    h_scale = hauptfenster.state.get("scale_H")
    b_scale = hauptfenster.state.get("scale_B")
    
    if h_scale is None or b_scale is None:
        
        #Warnung wenn keine Skalierungsfaktoren eingeben und gespeichert wurden
        messagebox.showerror(
            "Fehlende Skalierungsfaktoren",
            "Bitte zuerst gültige Skalierungsfaktoren eingeben."
        )
        return None

    h = ux * h_scale

    #Diese if else ist entscheident für das Datei laden, ist die Datei
    #bereits Offset korrigiert wird ein eingestellter Offset nicht mehr berücksichtigt
    #ist die Messung mit keinem Offset durchgeführt worden wird dieser bei der
    #Darstellung berücksichtigt
    if ext in [".cfg", ".dat"]:
        b = uy * b_scale


    if ext == ".csv":

        print("Offset aus Datei:", offset)

        if offset != 0:
            #Die CSV-Datei wurde bereits mit einem Offset korrigiert
            #print("Offset wurde bereits berücksichtigt")
            b = uy * b_scale

        else:
            #Aktuell im Programm eingestellten Offset abrufen
            eingestellter_offset = get_offset()

            #print("Aktuell eingestellter Offset:", eingestellter_offset)

            b = (uy - eingestellter_offset) * b_scale

    return h,b


def plotten_kurven(value,hauptfenster,pfade):

    """
    Die geladenen Daten werden dargestellt. Die Plots werden immer mittels
    der klassischen Matplotlib Bibliothek dargestellt man erhält also für jedes 
    neue Daten laden einen neuen Plot.

    Args:
        value (int):
            Für die Unterscheidung welche Darstellung wird benötigt. Entweder
            die Hysterese oder die Permeabilität wird dargestellt.

        hauptfenster (Hauptfenster):
            Für Status von Variablen
        
        pfade (str):
            Für die Dateipfade der Messdateien

    """
    
    plt.figure()

    #um die Pfade sowie die Skalierungsfaktoren zu erhalten
    for pfad in pfade:
        
        result = datei_laden(hauptfenster, pfad)

        #Sicherheit überprüfen was angekommen ist
        if result is None:
            continue

        H, B = result
        label = os.path.splitext(os.path.basename(pfad))[0]


        #Mittels Unterscheidung auswählen ob Permeabilität oder Hysterese 
        if value == 0:
            plt.plot(H, B, label=label)

        elif value == 1:
            mu0 = 4 * np.pi * 1e-7
            dH = np.gradient(H)
            dB = np.gradient(B)

            with np.errstate(divide="ignore", invalid="ignore"):
                mu_r = dB / dH / mu0
                mu_r[~np.isfinite(mu_r)] = np.nan

            plt.plot(H, mu_r, label=label)

    plt.xlabel("H [A/m]")

    if value == 0:

        plt.ylabel("B [T]")
        plt.title("Hysteresekurven")

    else:

        plt.ylabel(r"$\mu_{r,\mathrm{diff}}$ [-]")
        plt.title("Differentielle Permeabilität")


    plt.subplots_adjust(right=0.75)
    plt.grid(True)
    plt.legend(loc="center left",bbox_to_anchor=(1.02, 0.5))
    plt.show()




def daten_laden(hauptfenster):

    """
    Durch diese Funktion ist es möglich Messdaten zu laden und diese darzustellen.
    Achtung Skalierungsfaktoren und die verschiedenen Messungen berücksichtigt 
    werden. Das heißt Skalierungsfaktoren überprüfen und dann Auswahl welche 
    Messung dargestellt werden soll. Erzeugen der Radiobutton um zu Überprüfen, 
    welche Messung dargestellt werden soll. Das bedeutet Messung Hysterese oder
    Permeabilität. Es erscheint ein Pop up Fenster für die Auswahl.

    Args:
        hauptfenster (Hauptfenster):
            Um den Status von bestimmten Variablen zu erhalten
    """

    h = hauptfenster.state.get("scale_H")
    b = hauptfenster.state.get("scale_B")

    

    if h is None or b is None:
        messagebox.showerror(
                            "Fehlende Skalierungsfaktoren",
                            "Bitte zuerst die Skalierungsfaktoren eingeben."
                            )
        return

    #müssen für die Radiobutton ein neues Fenster erzeugen

    radio_button_fenster = tk.Toplevel(hauptfenster)
    radio_button_fenster.title("Welche Messung soll dargestellt werden?")
    radio_button_fenster.geometry("600x400")
    radio_button_fenster.configure(bg="#e4e7ec")

    #Variable für Radiobutton zuordnen
    auswahl_radio = tk.IntVar(value=0)

    #Erzeugen Radiobutton
    hysterese_frequenzen_radio = tk.Radiobutton(radio_button_fenster,
                                                text="Hysterese",
                                                variable = auswahl_radio, value= 0,
                                                background="#e4e7ec",
                                                selectcolor="#e4e7ec",
                                                font=("Arial",10,"bold"))
    hysterese_frequenzen_radio.pack(anchor="w", padx=20, pady=5)

    """
    hysterese_neukurve_radio = tk.Radiobutton(radio_button_fenster,
                                                text="Hysterese Entmagnetisierung",
                                                variable = auswahl_radio, value= 1,
                                                background="#e4e7ec",
                                                selectcolor="#e4e7ec",
                                                font=("Arial",10,"bold"))
    hysterese_neukurve_radio.pack(anchor="w", padx=20, pady=5)

    hysterese_entmagnet_radio = tk.Radiobutton(radio_button_fenster,
                                                text="Hysterese Neukurve",
                                                variable = auswahl_radio, value= 2,
                                                background="#e4e7ec",
                                                selectcolor="#e4e7ec",
                                                font=("Arial",10,"bold"))
    hysterese_entmagnet_radio .pack(anchor="w", padx=20, pady=5)
    """
    
    hysterese_permeabilitaet_radio = tk.Radiobutton(radio_button_fenster,
                                                text="Permeabilität",
                                                variable = auswahl_radio, value= 1,
                                                background="#e4e7ec",
                                                selectcolor="#e4e7ec",
                                                font=("Arial",10,"bold"))
    hysterese_permeabilitaet_radio.pack(anchor="w", padx=20, pady=5)


    #Datei pfad beliebig auswählen
    pfade = filedialog.askopenfilenames(
        parent=hauptfenster,
        title="Messdatei auswählen",
        filetypes=(
            ("Messdateien", "*.csv *.dat *.cfg"),
            ("Alle Dateien", "*.*"),))

    
    if not pfade:
        messagebox.showerror("Fehlender Dateipfad",
                                "Es wurde keine Messdatei ausgewählt."
                                )
        return 

    def on_weiter():
        value = auswahl_radio.get()
        radio_button_fenster.destroy()
        plotten_kurven(value,hauptfenster,pfade)



    #Man braucht noch eine weiter Button nach der Eingabe 
    weiter_button = create_button(
        radio_button_fenster,
        text="Weiter",
        command=on_weiter,
        primary=False,
    )
    weiter_button.pack(anchor="w", padx=20, pady=5)
    

    

def start_plot_nach_auswahl(value_radio_klick,hauptfenster):

    """
    Damit werden die jeweiligen Live-Plot Darstellungen ausgewählt.
    Wie wird der Frame beschriftet und die Skalierungsfaktoren werden
    verändert. Änderung über die Radio Button.

    Args:
        value_radio_klick (tk.IntVar):
            Je nachdem welcher Button aktiv ist, ist der Zustand null oder 
            eins und wird für die Fallunterscheidung verändert.
        
        hauptfenster (Hauptfenster):
            Für den Frame benötigt und um den Funktionsaufruf anderer Funktionen
            zu ermöglichen.
    """

    if value_radio_klick.get() == 0:
        print("Hysterese-Messung")
        frame_hyst = hauptfenster.frames["hysterese"]
        if not hasattr(frame_hyst, "live"):
            hysterese_live_plot(hauptfenster)
            
    else:
        print("Permeabilitäts-Messung")
        frame_perm = hauptfenster.frames["permeabilität"]
        if not hasattr(frame_perm, "live"):
            permeabilitaet_live_plot(hauptfenster)


def eingabe_daten(fenster,hauptfenster):

    """
    Es handelt sich um ein eigenes Fenster, welches mittels einem Container in
    drei Bereiche unterteilt wird. In einem Offset, Abtastrate und einen Daten
    laden Bereich. Man kann dort einen Offset eingeben und so Korrekturen vornehmen.
    Der Button Daten laden für eine Plot wird dort dargestellt. Außerdem können
    ausgewählte Abtastrate gewählt werden. Es ist nicht möglich selbst eine
    Abtastrate einzugeben. Außerdem sollte die zur Verfügung gestellten Werte
    für dieses Labor ausreichend sein. 

    Args:
        fenster (tk.Toplevel):
            Für die Zuweisung in das neue Fenster was sich öffnet. Das Haupt GUI
            bleibt erhalten.

        hauptfenster (Hauptfenster):
            Für den Status von Variablen
    """
    #Container für saubere Anordnung erzeugen
    ein_container = tk.Frame(fenster,  bg="#e4e7ec")
    ein_container.pack()

    #Verhältnis der Reihen des Container
    ein_container.grid_rowconfigure(0,weight = 1, uniform = "rows")
    ein_container.grid_rowconfigure(1,weight = 1, uniform = "rows")
    ein_container.grid_rowconfigure(2,weight = 1, uniform = "rows")
    ein_container.grid_columnconfigure(0, weight=0)
    
    #Frame für Sample rate
    frame_sample = tk.LabelFrame(ein_container, text="Sample rate [S/s]", relief="ridge",
                                    bd=6,padx=10,pady=10,background="#f5f7fa",
                                    font=("Arial", 10, "bold"))
    frame_sample.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Frame für Offset
    frame_offset = tk.LabelFrame(ein_container, text="UB-Offset", relief="ridge",
                                    bd=6,padx=10,pady=10,background="#f5f7fa",
                                    font=("Arial", 10, "bold"))
    frame_offset.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Frame für Daten laden
    frame_daten_laden = tk.LabelFrame(ein_container, text="Daten laden", relief="ridge",
                                    bd=6,padx=10,pady=10,background="#f5f7fa",
                                    font=("Arial", 10, "bold"))
    frame_daten_laden.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Daten laden Button
    daten_laden_button = create_button(
        frame_daten_laden,
        text="Daten laden",
        command=lambda: daten_laden(hauptfenster),
        primary=False,
    )
    daten_laden_button.pack()

    #Sample Spin Box, also Dropdown Menü
    #Label für die Beschriftung der Eingabe
    lbl_sample = tk.Label(frame_sample, text="Sample rate [S/s]:", bg="#f5f7fa")
    lbl_sample.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    sample_box = ttk.Combobox(frame_sample,values=[100, 200, 500, 1000, 2000, 5000, 10000],
                                state="readonly",width=10)
    sample_box.set(2000)  #Standardwert
    sample_box.grid(row=0, column=1, padx=5, pady=5)
    sample_rate(2000)

    #Werte bei jeder Änderung übernehmen, ändert die Sample rate
    def sample_change(event):

        """
        Übernimmt die ausgewählte Abtastrate und aktualisiert die GUI-Anzeige.
        """

        try:
            wert = int(sample_box.get())
            sample_rate(wert)
            hauptfenster.state["sample_rate"] = wert
            hauptfenster.state["sample_var"].set(f"{wert} S/s")
            messagebox.showinfo("Neue Sample Rate: [S/s]",f"{wert}")
        except ValueError:
            messagebox.showerror("Fehler", "Ungültige Sample-Rate.")
 

    sample_box.bind("<<ComboboxSelected>>", sample_change)

    #Eingabefeld Offset
    offset_eingabe(frame_offset)
    
    

def fenster_einstellungen(hauptfenster):

    """
    Es handelt sich um das Unterfenster für die Einstellungen für das Messprogramm Fenster.
    Es wird ein neues Fenster erstellt, welches dazu dient neue Funktionen, 
    welche nicht zugänglich sind für die Studierenden zu ermöglichen. Man kann
    Daten laden die Sample rate verändern sowie einen Offset einstellen.

    Args: 
        hauptfenster (Hauptfenster):
            Für die Zuordnung der Einstellungen 

    Returns:
        ein_fenster (tk.Toplevel):
            man erhält das neu erzeugte Fenster
    """

    #Fenster erstellen
    ein_fenster =tk.Toplevel(hauptfenster)

    #Beschriftung
    ein_fenster.title("Erweiterte Einstellungen für das Messprogramm")

    #Größe
    ein_fenster.geometry("600x400")

    #Hintergrundfarbe
    ein_fenster.configure(bg="#e4e7ec") #Hexcode für hellgrau 

    eingabe_daten(ein_fenster,hauptfenster)
    
    return ein_fenster

def login_passwort(pw_entry,fenster,hauptfenster):

    """
    Damit nicht jeder in das Menü gelangen kann, wird zuvor ein Passwort
    abgefragt. Das Passwort lautet hysterese. Bei erfolgreicher Eingabe
    erhält man Zugriff auf neue Funktionen in einem eigenen Fenster.

    Args:
        pw_entry (tk.Entry):
            Man erhält das eingegebene Passwort
        
        fenster (tk.Toplevel):
            Das Login Fenster was erzeugt wurde wo die Passworteingabe stattfindet
            wird am Ende zerstört also ist nicht mehr sichtbar
        
        hauptfenster (Hauptfenster):
            Für weitere Funktionsaufrufe benötigt

    
    """

    #eingetragenen Passwort in Variable abspeichern
    password = pw_entry.get()

    #Login Meldung 
    if password == "hysterese":
        messagebox.showinfo("Login erfolgreich", "Zugriff erlaubt.")
        fenster.destroy()   #Login-Fenster schließen

        #hier dann das neue Einstellungsfenster öffnen
        fenster_einstellungen(hauptfenster)
    else:
        messagebox.showerror("Login fehlgeschlagen", "Ungültiges Passwort")


def offset_eingabe(frame_offset):

    """
    Erzeugt ein Eingabefeld in dem man einen Spannungswert eingeben kann, welcher
    mit dem ein Offset korrigiert wird.

    Args:
        frame_offset (tk.LabelFrame):
            Frame in erweiterte Einstellung wird zur Zuordnung benötigt des
            neu erstellten Eingabefeldes
    """

    #Label für die Beschriftung
    label_offset = tk.Label(frame_offset, text="UB-Offset [V]:", bg="#f5f7fa")
    label_offset.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    #Eingabefeld Offset erzeugen
    entry_offset = tk.Entry(frame_offset, width=10)
    entry_offset.grid(row=0, column=1, padx=5, pady=5)
    entry_offset.insert(0, "0.0")

    #Ausgabefunktion
    def offset_uebernehmen():

        """
        Prüft und übernimmt den eingegebenen Offsetwert.
        """

        text = entry_offset.get().replace(",", ".")
        try:
            wert = float(text)
            update_offset(wert) #Updaten des aktuellen Offsetwertes
            messagebox.showinfo("UB-Offset", f"UB-Offset auf {wert} V gesetzt.")
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige Offset-Spannung eingeben.")

    #Button für das Speichern bzw. Übernehmen des Offsets
    btn_offset = create_button(
        frame_offset,
        text="Offset übernehmen",
        command=offset_uebernehmen,
        primary=False,
    )
    btn_offset.grid(row=1, column=0, columnspan=2, pady=5)

def optionen(hauptfenster):

    """
    Erzeugt das Fenster für den Login in das Einstellungsfenster. 
    Das Fenster öffnet sich und fragt nach dem Passwort. 

    Args:
        hauptfenster (Hauptfenster):
            Zuordnung des Menüaufrufs im Haupt GUI

    Returns:
        nebenfenster (tk.Toplevel):
            Erzeugtes Login-Fenster zurückgegeben        
    
    """

    #Erzeugen des Nebenfenster für den Login
    nebenfenster =tk.Toplevel(hauptfenster)
    nebenfenster.title("Login für Einstellungen")
    nebenfenster.geometry("200x200")
    nebenfenster.configure(bg="#e4e7ec") #Hexcode für hellgrau 

    #Erzeugen und Platzieren des Eingabefeldes des Passwort
    #Label Passwort
    pw_label = tk.Label(nebenfenster, text="Passwort: ", bg="#e4e7ec",font=14)

    #entry Feld für Passwort
    pw_entry = tk.Entry(nebenfenster, show="*")
    
    #Cursor sofort in das Eingabefeld setzen
    pw_entry.focus()

    #Erzeugen und platzieren des Login Button
    login_button = create_button(
        nebenfenster,
        text="Login",
        command=lambda: login_passwort(pw_entry,nebenfenster, hauptfenster),
        primary=False,
    )
    

    #Für die Überprüfung des Passworts
    pw_entry.bind("<Return>", lambda event: login_passwort(pw_entry, nebenfenster,
                                                           hauptfenster))

    #Platzierung des Eingabefeldes
    pw_label.pack(pady=5)
    pw_entry.pack(pady=10)
    login_button.pack(pady=5)

    return nebenfenster

def neuen_ordner(hauptfenster):

    """
    Dadurch wird ermöglicht das man den Speicherort ändern kann in dem 
    die Messdateien abgelegt werden. Kann im Hauptfenster verändert werden.

    Args:
        hauptfenster (Hauptfenster):
            Für die Zuordnung des Auswahlfeldes

    Returns:
        bool:
            True, wenn ein Speicherordner ausgewählt wurde,
            andernfalls False
    """

    #Nach einem neuen Speicherordner fragen
    pfad = filedialog.askdirectory(

        parent=hauptfenster,
        title="Speicherordner für CSV-Dateien auswählen"
    )

    #bei keinem gültigen Pfad
    if not pfad:
        return False

    #danach wird der neue Pfad gesetzt
    set_csv_ordner(pfad)
    messagebox.showinfo(
        "Speicherort gesetzt",
        f"CSV-Dateien werden nun hier gespeichert:\n{pfad}"
    )
   
    return True

def untermenue(hauptfenster):

    """
    Die Funktion erzeugt ein Untermenü um Messprogramm, welches Passwort 
    geschützt ist. In diesem Unterprogramm ist es möglich einen Offset einzustellen,
    Daten zu laden und die Plots anzuzeigen und die Abtastrate soll hier einstellbar
    sein. Grundsätzlich ist für die Abtastrate wenn man nichts hineinschreibt ein 
    fixer Wert vorgesehen, wenn dieser aber eingetragen wird dann wird damit dieser
    Wert überschrieben für Messungen so lange, bis das Messprogramm neu gestartet
    wird.

    Args:
        hauptfenster (Hauptfenster):
            Für die Zuordnung des Untermenüs
    """

    #um eine Menüleiste zu erzeugen
    menuebar = tk.Menu(hauptfenster)

    #Den Reiter erzeugen und darauf folgend die Optionsleiste
    optionmenu = tk.Menu(menuebar, tearoff=0)
    optionmenu.add_command(label="Optionen",command=lambda:optionen(hauptfenster))

    #um den Speicherort flexibel zu gestalten, von Gruppe zu Gruppe anpassbar
    optionmenu.add_command(label="Speicherort erstellen",
                           command=lambda:neuen_ordner(hauptfenster))

    menuebar.add_cascade(label="Einstellungen", menu=optionmenu)
    

    hauptfenster.config(menu=menuebar)


def willkommensfenster(hauptfenster):

    """
    Beim Start des Programms startet das GUI und es kommt dieses neue Fenster.
    Es geht darum, dass sofort ein Ordner ausgewählt wird für die Messdateien. 
    Das heißt der Speicherort wird festgelegt. Sobald dieser festgelegt wird
    schließt sich dieses Fenster automatisch.

    Args:
        hauptfenster (Hauptfenster):
            Zuordnung des Popup Fensters benötigt
    """

    #erzeugen des Popup Fenster
    popup = tk.Toplevel(hauptfenster)
    popup.title("Willkommen")
    popup.geometry("500x250")

    popup.transient(hauptfenster)
    popup.grab_set()

    #hier erfolgt die Ordnerauswahl
    def ordner_auswaehlen():
        if neuen_ordner(hauptfenster):
            popup.destroy()

    #Beschriftungen des Popup fensters
    tk.Label(
        popup,
        text="Willkommen zum Messprogramm Magnetika",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    tk.Label(
        popup,
        text="Bitte wählen Sie einen Speicherort\nfür die Messdaten aus."
    ).pack(pady=10)

    #Button für Ordner auswählen generieren
    create_button(
        popup,
        text="Ordner auswählen",
        command = ordner_auswaehlen
    ).pack(pady=5)

    




class Hauptfenster(tk.Tk):

    """
    Erzeugt und konfiguriert das Hauptfenster des Messprogramms.
    Das Fenster wird an die Bildschirmgröße angepasst. Zusätzlich werden
    zentrale Zustandsvariablen für Skalierungsfaktoren, Messstatus,
    Cursorwerte und Abtastrate gespeichert.
    """
     
    def __init__(self):

        """
        Initialisiert und konfiguriert das Hauptfenster.
        """

        super().__init__()

        #Titel setzen
        self.title("Messprogramm Laborversuch Magnetika Hysterese")

        #Bildschirmgröße
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.geometry(f"{screen_width}x{screen_height}")
        self.configure(bg="#e4e7ec")

        #Globale Farben und Schriftarten festlegen
        self.option_add("*Font", "Arial 10")
        self.option_add("*Label.background", "#f5f7fa")
        self.option_add("*Label.foreground", "#222222")
        self.option_add("*Button.font", "Arial 10")

        #Zustands-Variablen der GUI
        self.state = {
            "scale_H": None,
            "scale_B": None,
            "messung_laeuft": False,
            "cursor_H_var": None,
            "cursor_B_var": None,
            "sample_rate": 2000
            }
        



def GUI():

    """
    Hier werden die wichtigsten Funktionen aufgerufen. Damit das GUI startet
    und die programmierten Eigenschaften hat. Dient also als reine Funktion zum 
    Aufruf der einzelnen GUI-Bestandteile

    Returns:
        hauptfenster (Hauptfenster):
            Wird für alles benötigt, Zuweisung von Buttons, Funktionen, Live-Plot
            usw., es können Zustände von Variablen gespeichert werden.
    """

    #Hauptfenster
    hauptfenster = Hauptfenster()

    #Willkommensfenster und Speicherort
    willkommensfenster(hauptfenster)

    #LINKS
    frame_scale, frame_messung_ss, frame_hyst_perm,frame_cursor = container_left(hauptfenster)

    #RECHTS: Frames
    frame_signal, frame_hysterese, frame_perme = plot_frames(hauptfenster)

    #Live-Plot oben
    signal_live_plot(hauptfenster)

    #Radiobuttons + Umschaltlogik
    value_radio_klick = hyst_perm_auswahl(frame_hyst_perm, hauptfenster)

    #Buttons links
    mess_button(frame_messung_ss, hauptfenster,value_radio_klick)
    messung_fort_button = messung_fortsetzen(frame_messung_ss,hauptfenster,
                                             value_radio_klick)
    messung_pausieren(frame_messung_ss, hauptfenster,messung_fort_button)

    #LED erzeugen usw
    frame_led = tk.Frame(frame_messung_ss, bg="#f5f7fa")
    frame_led.pack(expand=True, fill="both")
    hauptfenster.state["frame_led"] = frame_led
    LED_status(frame_led, hauptfenster)

    close_hauptfenster(frame_messung_ss, hauptfenster)
    eingabe_skalierung(frame_scale, hauptfenster)

    #Untermenü
    untermenue(hauptfenster)

    return hauptfenster
