#hier wird das komplette GUI(graphical user interface) erzeugt

"""
Was soll das GUI alles darstellen?
Das GUI muss Grundsätzlich den Hysterese sowie den Permeabilitätsplot 
darstellen. Das soll natürlich schon live dargestellt werden, also während der Messung.
Am Ende soll das gesamte Bild dargestellt werden, sowie eien FUnktion um bestimmte Zeit-
punkte betrachten zu können. Außerdem soll das Signal live geplottet werden.

Ein weiter wichtiger Punkt sind die Skalierungsfaktoren, welche die Studenteninnen
selbst eingeben müssen. So muss man im Programm nicht darauf achten, welchen 
SPulering man vermisst. Wie die Berechnung dessen Skalierungsfaktor funktioniert 
siehe schriftlichen Teil der Bachelorarbeit.

Weiters muss es natürlich möglichkeiten geben die Daten zu speichern, sowie 
eine Eingabe welche Versuch man durchführt und die Frequenz muss eingegeben werden.

Samples und Offset kompensation soll mittels Settings in eine Untergeordneten Menü eingestellt
werden können, aber das ist für Studierenden nicht zugänglich
"""

#Bibliotheken

#Standardbibliotheken in python
import numpy as np                                
import matplotlib.pyplot as plt #zum plotten
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import queue
import os
import getpass

#Tkinter für GUI
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tk_tools

# gemeinsame Objekte aus functions_ac3.py holen:
from .functions_ac3 import start_messung, stop_messung, data_queue, run_event,update_offset
from .functions_ac3 import set_fortsetzen_modus, fortsetzen_modus, sample_rate, u_offset
from .functions_ac3 import set_csv_ordner

#Erstellen der Skalierungsfaktor Eingabe 

def create_button(fenster, text, command=None, primary=False):

    """
    Folgende Funktion erzeugt Buttons welche dann einfahc verwenden werden 
    können, um zu gewährleisten, dass man den gleichen button hat oder
    schnell eine Änderung machen kann, vor allem für dei Optik sehr einfach
    """



    if primary:
        return tk.Button(
            fenster,
            text=text,
            borderwidth= 1.5,
            command=command,
            bg="#1e88e5",
            fg="white",
            activebackground="#1565c0",
            activeforeground="white",
            relief="solid",
            padx=10,
            pady=4,
        )
    else:
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
    Die Funktion skalierung speichert die beiden Skalierungsfaktoren ab,
    welche die Studierenden berechnen und eingeben müssen.

    Parameter:
        zwei neue Variablen speichern den Wert über die get() Funktion

    Rückgabewert:
        der Saklierungsfaktor wird als Array zurückgegeben
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
        Erstellt die frames im Hauptfenster 
        erzeugt die Labels und Entrys also Eingabefelder
    """
    
    frame_x = tk.Frame(frame_scale, bg="#f5f7fa")
    frame_x.grid(row=0, column=0,padx=4,pady=4,sticky="ew")

    frame_y = tk.Frame(frame_scale, bg="#f5f7fa")
    frame_y.grid(row=1, column=0,padx=4,pady=4,sticky="ew")
    
    #Jetzt das Label so anpassen, das es mit grid und nciht mit pad funktioniert
    label_x = tk.Label(frame_x,text="1V... = ").grid(row=0,column=0,
                                                     sticky="w",
                                                     padx=5,pady=5)
   
    label_x = tk.Label(frame_x,text= "[A/m]").grid(row=0,column=2,
                                                     sticky="w",
                                                     padx=5,pady=5)
   
    #beschriftung der Felder magenetische Flussdichte
    label_y = tk.Label(frame_y,text="1V... = ").grid(row=1,column=0,
                                                     sticky="w",
                                                     padx=5,pady=5)

    label_y = tk.Label(frame_y,text= "[T]").grid(row=1,column=2,
                                                     sticky="w",
                                                     padx=5,pady=5)
    
    #Eingabefeld
    entry_x = tk.Entry(frame_x, width=12, bd=2, relief="solid")
    entry_x.grid(row=0,column=1,padx=5,pady=5)


    #Eingabefeld
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
    Die live Darstellungen sollen bevor man Messung neu startet nichtz mehr 
    angezeigt werden. Dadurch wird immer nur die aktuelle Messung dargestellt. 

    """

    frame_signal = hauptfenster.frames["signal"]
    frame_hysterese = hauptfenster.frames["hysterese"]
    frame_permea = hauptfenster.frames["permeabilität"]
    
    #zurücksetzen Singale
    if hasattr(frame_signal, "live"):
        live = frame_signal.live
        live["ts"].clear()
        live["ux"].clear()
        live["uy"].clear()
        live["line_x"].set_data([], [])
        live["line_y"].set_data([], [])
        # Achsen zurücksetzen
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

    #Dadurch wird die Daten Q auch noch entleert

    with data_queue.mutex:
        data_queue.queue.clear()


def zoom_funktion(frame):

    """
        Zoom Funktion mittels Mausrad. Funktioniert nur im Messframe
    """

    ax = frame["ax"]
    canvas = frame["canvas"]
    zoom_faktor = 1.2
    status_maus = {"druecken": None}

    def on_scroll(event):

        if event.inaxes is not ax:
            return

        if event.button == "up":
            scale = 1/zoom_faktor
        elif event.button == "down":
            scale = zoom_faktor
        else:
            return

        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        xdata = event.xdata if event.xdata is not None else (x_min + x_max) / 2
        ydata = event.ydata if event.ydata is not None else (y_min + y_max) / 2

        new_width = (x_max - x_min) * scale
        new_height = (y_max - y_min) * scale

        ax.set_xlim([xdata - new_width / 2, xdata + new_width / 2])
        ax.set_ylim([ydata - new_height / 2, ydata + new_height / 2])

        canvas.draw_idle()

    def on_press(event):
        if event.inaxes is not ax:
            return
        if event.button != 3:
            return
        if event.xdata is None or event.ydata is None:
            return
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        status_maus["druecken"] = (event.xdata, event.ydata, (x_min, x_max), (y_min, y_max))    

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

        ax.set_xlim(x_min0 - dx, x_max0 - dx)
        ax.set_ylim(y_min0 - dy, y_max0 - dy)

        canvas.draw_idle()
        

    canvas.mpl_connect("scroll_event", on_scroll)
    canvas.mpl_connect("button_press_event", on_press)
    canvas.mpl_connect("button_release_event", on_release)
    canvas.mpl_connect("motion_notify_event", on_move)

   


def signal_live_plot(hauptfenster):

    """
    live Plot des Signales über die Zeit.
    Das bedeutet die Spannung an der Stelle x über den Shunt Widerstand und
    die Spannung an der Stelle y über den Integrator wird über die Zeit 
    dargestellt. Das soll live sein um den Verlauf dazu betrachten zu können.

    Die Funktion ist als thread erstellt und sollte daher parallel zur Messung funktionieren.
    """
    """
    Erstellt ein Diagramm welches parallel zur Messung die beiden Spannungswerte
    plottet. 
    """
    
    frame_signal = hauptfenster.frames["signal"]

    # Frame zuerst updaten, damit Breite/Höhe korrekt sind
    #frame_signal.update_idletasks()

    #erstellen des Plots mit Matplotlib
    fig = Figure(dpi=100)  # Keine feste figsize, nur DPI
    fig.patch.set_facecolor("#f5f7fa")
    ax = fig.add_subplot(111)
    # Platz für Titel und Achsen
    fig.subplots_adjust(top=0.9, bottom=0.25, left=0.07, right=0.98)
    #ax.set_title("Spannungen an den Messpunkten x und y")
    ax.set_xlabel("Zeit [s]")
    ax.set_ylabel("Spannung [V]")
    ax.set_facecolor("#ffffff")
    ax.grid(True, linestyle=":", color="#d0d0d0", alpha=0.7)

    #anlegen von Linien
    (line_x,) = ax.plot([], [], linewidth=1.2, label="Spannung_x")
    (line_y,) = ax.plot([], [], linewidth=1.2, label="Spannung_y")
    ax.legend(loc="best")


    #Canvas in Tk platzieren
    canvas = FigureCanvasTkAgg(fig, master=frame_signal)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Beim Ändern der Framegröße neu zeichnen
    frame_signal.bind("<Configure>", lambda e: canvas.draw())
    
    #erstellen eines Puffers und update_data befüllt die Liste
    frame_signal.live = {
        #"frame": frame,      
        "ax": ax,
        "canvas": canvas,
        "line_x": line_x,
        "line_y": line_y,
        "ts": [],            # Zeit
        "ux": [],            # Spannung_x
        "uy": []             # Spannung_y
    }

    #Zoom per Mausrad aktivieren
    zoom_funktion(frame_signal.live)


    #update anstoßen
    hauptfenster.after(100, update_data, hauptfenster)

    return frame_signal    

def hysterese_live_plot(hauptfenster):

    """
        Erstellt ein Digramm welches die Hysterese darstellt. Verwendet die 
        Skalierungsfaktoren.

    """
     
    frame_signal = hauptfenster.frames["hysterese"]

    # Frame zuerst updaten, damit Breite/Höhe korrekt sind
    frame_signal.update_idletasks()

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


    #Cancas in Tk platzieren
    canvas = FigureCanvasTkAgg(fig, master=frame_signal)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Beim Ändern der Framegröße neu zeichnen
    frame_signal.bind("<Configure>", lambda e: canvas.draw())
    
    #erstellen eines Puffers und update_data befüllt die Liste
    frame_signal.live = {
        #"frame": frame,      
        "ax": ax,
        "canvas": canvas,
        "line_hb": line_hb,
        "H": [],            # Spannung_x
        "B": []             # Spannung_y
    }

    #Cursor Maus update
    def on_move(event):

        #damit die Maus/Cursor nur reagiert wenn im Diagramm
        if event.inaxes is not ax:
            return
        
        H_vals = frame_signal.live["H"]
        B_vals = frame_signal.live["B"]

        if not H_vals or not B_vals:
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
    zoom_funktion(frame_signal.live)

    #update anstoßen
    hauptfenster.after(100, update_data, hauptfenster)

    return frame_signal    


def permeabilitaet_live_plot(hauptfenster):
    """
    Erstellt ein Digramm welches die differentielle Permeabiliät darstellt
    """
     
    frame_signal = hauptfenster.frames["permeabilität"]

    # Frame zuerst updaten, damit Breite/Höhe korrekt sind
    frame_signal.update_idletasks()

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


    #Cancas in Tk platzieren
    canvas = FigureCanvasTkAgg(fig, master=frame_signal)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Beim Ändern der Framegröße neu zeichnen
    frame_signal.bind("<Configure>", lambda e: canvas.draw())
    
    #erstellen eines Puffers und update_data befüllt die Liste
    frame_signal.live = {
        #"frame": frame,      
        "ax": ax,
        "canvas": canvas,
        "line_mu": line_mu,
        "H": [],            # Spannung_x
        "B": []             # Spannung_y
    }

    #Zoom per Mausrad aktivieren
    zoom_funktion(frame_signal.live)

    #update anstoßen
    hauptfenster.after(100, update_data, hauptfenster)

    return frame_signal    
    



def plot_frames(hauptfenster):

    """
        Die folgende Funktion erzeugt Rahmen für die zwei Diagramme.
        Das bedeutet die Container in dennen man die entrys usw. zuordnen kann
        Dient zur Positionierung und um das Gui aufgeräumter darzustellen.

    """


    #Container für die Frames erzeugen
    right_container = tk.Frame(hauptfenster, bg="#e4e7ec")
    right_container.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    #Grid-Verhältnis: oben flach (Signal), unten groß (Hysterese)
    right_container.grid_rowconfigure(0, weight=1, uniform="rows")
    right_container.grid_rowconfigure(1, weight=3, uniform="rows")
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

    # Permeabilität am Anfang ausblenden:
    frame_perme.grid_remove()

    return frame_signal, frame_hysterese, frame_perme



def update_data(hauptfenster):

    """
    
        Funktion wird benötigt um die Daten zu aktualisieren
        Die Daten kann man sich aus der queue holen.
        Somit muss man nicht auf die csv zugreifen und erhält eine einfache Aktualisierung 
        der Daten
        
        Wir holen also die neuen Daten aus der queue
    """
    frame_signal = hauptfenster.frames["signal"]
    frame_hyst   = hauptfenster.frames["hysterese"]
    frame_perm   = hauptfenster.frames["permeabilität"]  #NEU

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
                    continue  #noch nicht gesetzt → überspringen
                
                H = x * h_scale
                B = (y - u_offset) * b_scale

                if live_hyst is not None:
                    live_hyst["H"].append(H)
                    live_hyst["B"].append(B)

                if live_perm is not None:
                    live_perm["H"].append(H)
                    live_perm["B"].append(B)

    except queue.Empty:
        pass

    if drained:
        #optional Sichtfenster begrenzen
        max_pts = 5000

        if len(ts) > max_pts:
            ts[:] = ts[-max_pts:]
            ux[:] = ux[-max_pts:]
            uy[:] = uy[-max_pts:]

        live["line_x"].set_data(ts, ux)
        live["line_y"].set_data(ts, uy)
        live["ax"].relim(); live["ax"].autoscale_view()
        live["canvas"].draw_idle()

        #Hystereseplot
        if live_hyst is not None:
            live_hyst["line_hb"].set_data(live_hyst["H"], live_hyst["B"])
            live_hyst["ax"].relim(); live_hyst["ax"].autoscale_view()
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

            live_perm["line_mu"].set_data(H_arr, mu_r)
            live_perm["ax"].relim()
            live_perm["ax"].autoscale_view()
            live_perm["canvas"].draw_idle()

    hauptfenster.after(100, update_data, hauptfenster)    


def mess_button(frame_messung,hauptfenster,value_radio_klick):

    """
    Die Funktion mess_button erzeugt die Buttons
    Messung starten und stoppen

    DIe FUnktion gibt nichts zurück. Gleichbedeutent ist der klick einer der 
    Buttons wiochtig für die Messung denn wirklich erst beim klicken wird die 
    Messung gestartet oder gestopp. Außerdem wird die LED als anzeige hier 
    implementiert.
    """
    #Flag im Hauptfenster-Zustand ablegen
    hauptfenster.state["messung_laeuft"] = False

    #Statusanzeige
    status_var = tk.StringVar(value="Gestoppt")
    tk.Label(hauptfenster.frames["signal"], textvariable=status_var).pack(anchor="w", padx=200)

    #EIN Button für Start/Stop
    button_toggle = create_button(frame_messung, text="Messung starten", primary=True)
    button_toggle.pack(anchor="w", pady=10, padx=10)

    #Flag im Hauptfenster-Zustand ablegen
    hauptfenster.state["status_var"] = status_var
    hauptfenster.state["button_toggle"] = button_toggle

    #Status für dei LED setzen
    status_led =   tk.IntVar(value=1)
    hauptfenster.state["led_var"] = status_led

    def start_stop_button():
        if not hauptfenster.state["messung_laeuft"]:
            # --- Messung STARTEN ---

            #Mit jeder neuen Messung muss das Interface entleert werden
            clear_live_plots(hauptfenster)  

            start_messung()  #h weiter run_event.set() verwenden
            start_plot_nach_auswahl(value_radio_klick, hauptfenster)

            hauptfenster.state["messung_laeuft"] = True

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
            # --- Messung BEENDEN ---
            stop_messung()   #hier drin sollte run_event.clear() usw. stehen

            hauptfenster.state["messung_laeuft"] = False

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
        Erzeugt die LED. Dient als reiner Indikator das die Messung läuft.
        Das bedeutet selbst wenn nichts angezeigt wird weis man dennoch, dass
        die Messung gestartet wurde
        
    """

    #LED/Anzeige erzeugen
    status_led = hauptfenster.state["led_var"]
    led = tk.Canvas(frame_led, width=60, height=60, highlightthickness=0, bg="#f5f7fa")
    led.pack(expand=True, pady=(20, 0))
    dot = led.create_oval(5, 5, 55, 55, fill="red", outline="black",width=2)  #start rot

    def update_led(*_):
        led.itemconfig(dot, fill="green" if status_led.get() == 0 else "red")
    
    update_led()
    status_led.trace_add("write", update_led)

    hauptfenster.state["led_canvas"] = led
    hauptfenster.state["led_dot"] = dot

def close_hauptfenster(frame_messung,hauptfenster):

    """
    Die Funktion close_Hauptfenster erzeugt den Button zum schließen 
    des Fensters.
    """

    #eine schließen Button erzeugen, welcher das gesamte GUI beendet
    close_button = create_button(
        frame_messung,
        text="Messprogramm schließen",
        command=hauptfenster.destroy,
        primary=False,
    )
    close_button.pack(side="bottom", fill="x", padx=10, pady=(15, 15))

def messung_pausieren(frame_messung,hauptfenster,messung_fort_button):

    """
    Button für Messung stoppen
    """ 
    def on_pause():
        # nur pausieren, wenn überhaupt eine Messung läuft
        if not hauptfenster.state.get("messung_laeuft", False):
            return

        stop_messung()
        hauptfenster.state["messung_laeuft"] = False

        #Led
        led_var = hauptfenster.state.get("led_var")
        if led_var is not None:
            led_var.set(1)

        status_var = hauptfenster.state.get("status_var")
        button_toggle = hauptfenster.state.get("button_toggle")

        if status_var is not None:
            status_var.set("Gestoppt (pausiert)")

        if button_toggle is not None:
            button_toggle.config(
                text="Messung neu starten",
                bg="#1e88e5",
                activebackground="#1565c0",
                fg="white",
                activeforeground="white",
            )

        if messung_fort_button is not None:
            messung_fort_button.pack_configure(anchor="w", padx=10, pady=5)

        #LED für die Reihenfolge hier paltzieren
        frame_led = hauptfenster.state.get("frame_led")
        if frame_led is not None:
            frame_led.pack_forget()
            frame_led.pack(expand=True, fill="both")

    messung_stopp_button = create_button(
        frame_messung,
        text="Messprogramm pausieren/stoppen",
        command=on_pause,
        primary=False,
    )
    messung_stopp_button.pack(anchor="w", padx=10, pady=5)


def messung_fortsetzen(frame_messung,hauptfenster,value_radio_klick):

    """
    Dieser Button soll die Messung fortsetzen und die Datei an diesem Punkt 
    weiter beschreiben. Das heißt die Messung läuft wird pausiert bzw. gestopp,
    dieser Zeitpunkt oder der letzte Eintrag ist relevant denn dnach diesem, wenn 
    man den Button Messung fortsetzen klickt soll dann an dieser Stelle die
    Dateineintragung weiter gehen 
    """

    def on_fortsetzen():

        if hauptfenster.state.get("messung_laeuft", False):
            print("Messung läuft bereits Fortsetzen ignoriert.")
            return
    
        # Flag setzen
        set_fortsetzen_modus(True)

        # Messung starten (start_messung prüft fortsetzen_modus)
        start_messung()

        # Plot (wie beim normalen Start)
        start_plot_nach_auswahl(value_radio_klick, hauptfenster)

        # Zustand aktualisieren
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
    für die drei Bereiche links Container erstellen um die Buttons und Anzeigen
    richitg anzuordnen.
    Damit ist auch gewährleistet dass das ganze GUI sauber aussieht
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

    #Frame für Courser erzeugen 
    frame_cursor = tk.LabelFrame(left_container, text="Cursor/Messwerte", relief="ridge",
                                bd=6,padx=10,pady=10,background="#f5f7fa",
                                font=("Arial", 10, "bold"))
    frame_cursor.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))                             

    #StringVars für H und B,Variable an widget binden
    cursor_H_var = tk.StringVar(value="H: –")
    cursor_B_var = tk.StringVar(value="B: –")

    #erstellen des Labels
    label_H = tk.Label(frame_cursor, textvariable=cursor_H_var,
                     anchor="w", font=("Arial", 10))

    label_H.pack(anchor="w")

    label_B = tk.Label(frame_cursor, textvariable=cursor_B_var,
                     anchor="w", font=("Arial", 10))

    label_B.pack(anchor="w")

    #im Zustand des Hauptfensters merken, damit der Plot darauf zugreifen kann
    hauptfenster.state["cursor_H_var"] = cursor_H_var
    hauptfenster.state["cursor_B_var"] = cursor_B_var

    return frame_scale,frame_messung_ss,frame_hysterese_perme,frame_cursor


def hyst_perm_auswahl(frame_hyst_perm,hauptfenster):
    
    value_radio = tk.IntVar(value=0)

    def on_radio_change(*args):

        if value_radio.get() == 0:
            hauptfenster.frames["permeabilität"].grid_remove()
            hauptfenster.frames["hysterese"].grid()
        else:
            hauptfenster.frames["hysterese"].grid_remove()
            hauptfenster.frames["permeabilität"].grid()


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
    Funktion behandelt das öffnen und laden einer alten Datei. 
    Es wird hier berücksichtight, dass man zu Beginn der Übergangsphase auch
    die alte Datei geladen werden kann
    """

    #Datei laden

    ext = os.path.splitext(pfad)[1].lower()

    if ext in [".cfg",".dat"]:

        #Skalierung berücksichtigen, das heißt Reihe 2 und Reihe 3 Daten 
        #müssen skaliert werden

        data_l = np.loadtxt(pfad, dtype=str)
        data_l = np.char.replace(data_l, ",",".")

        data = data_l.astype(float)

        # 3 Spalten extrahieren
        t  = data[:, 0]
        ux = data[:, 1]
        uy = data[:, 2]


    elif ext == ".csv":

        data = np.genfromtxt(pfad,delimiter=";",skip_header=1)
    
        #3 Spalten extrahieren
        t  = data[:, 0]
        ux = data[:, 1]
        uy = data[:, 2]

    else: 
        messagebox.showerror("Kein gültiger Dateityp, bitte verwenden Sie" \
        ".cfg, .data oder .csv")
            
       
    #Berechnen mit den Skalierungsfaktoren und Offset
    h = ux * hauptfenster.state.get("scale_H")
    b = (uy - u_offset) * hauptfenster.state.get("scale_B")

    if h is None or b is None:

        messagebox.showwarning("Achtung keine gültigen Skalierungsfaktoren")
        return h,b 

    return h,b


def ploten_kurven(value,hauptfenster,pfad):

    """
    Darstellung der geladenen Dateien 
    """


    H,B = datei_laden(hauptfenster,pfad)

    #Mittels Unterscheidung 

    if value == 0:

        plt.figure()
        plt.plot(H, B, label="Hysterese")
        plt.xlabel("H [A/m]")
        plt.ylabel("B [T]")
        plt.grid(True)
        plt.legend()
        plt.show()
        
    if value == 1:

        plt.figure()
        plt.plot(H, B, color="red", label="Entmagnetisierung")
        plt.xlabel("H [A/m]")
        plt.ylabel("B [T]")
        plt.grid(True)
        plt.legend()
        plt.show()

    if value == 2:

        plt.figure()
        plt.plot(H, B, color="green", label="Neukurve")
        plt.xlabel("H [A/m]")
        plt.ylabel("B [T]")
        plt.grid(True)
        plt.legend()
        plt.show()

    if value == 3:

        mu0 = 4 * np.pi * 1e-7
        dH = np.gradient(H)
        dB = np.gradient(B)
        mu_r = dB / dH / mu0

        plt.figure()
        plt.plot(H, mu_r, label="µ(H)")
        plt.xlabel("H [A/m]")
        plt.ylabel("µr [-]")
        plt.grid(True)
        plt.legend()
        plt.show()

    return 



def daten_laden(hauptfenster):

    """
    Druch diese FUnktion ist es möglich Messdaten zu laden und diese darzustellen.
    Achtung Skalierungsfaktoren und die verschiedene Messungen berücksichtigt 
    werden. Das heißt Skalierungsfaktoren überprüfen und dann Auswahl welche 
    Messung geprintet werden soll.
    """

    h = hauptfenster.state.get("scale_H")
    b = hauptfenster.state.get("scale_B")

    if h is None and b is None:
        messagebox.showwarning("Fehler","Keine Skalierungsfaktoren eingeben")
        return
    """
    Erzeugen der Radiobutton um zu Überprüfen, welche Mesung dargestellt 
    werden soll. DAS bedeutet Messung Hysterese verschiedene Frequenzen, 
    Entmagnetisierung, Permeabilität und Neukurve. Diese 4 Varianten gibt es
    und müssen berücksichtigt werden.
    """

    #müssen für dei Radiobutton ein neues Fenster erzeugen

    radio_button_fenster = tk.Toplevel(hauptfenster)
    radio_button_fenster.title("Welche Messung soll dargestellt werden?")
    radio_button_fenster.geometry("600x400")
    radio_button_fenster.configure(bg="#e4e7ec")

    #Variable für Radbiobutton zuordnen
    auswahl_radio = tk.IntVar(value=0)

    #Erzeugen Radiobutton
    hysterese_frequenzen_radio = tk.Radiobutton(radio_button_fenster,
                                                text="Hysterese bei verschiedene " \
                                                "Frequenzen",
                                                variable = auswahl_radio, value= 0,
                                                background="#e4e7ec",
                                                selectcolor="#e4e7ec",
                                                font=("Arial",10,"bold"))
    hysterese_frequenzen_radio.pack(anchor="w", padx=20, pady=5)

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

    hysterese_permeabilitaet_radio = tk.Radiobutton(radio_button_fenster,
                                                text="Permeabilität",
                                                variable = auswahl_radio, value= 3,
                                                background="#e4e7ec",
                                                selectcolor="#e4e7ec",
                                                font=("Arial",10,"bold"))
    hysterese_permeabilitaet_radio.pack(anchor="w", padx=20, pady=5)


    #Datei pfad beliebig auswählen
    pfad = filedialog.askopenfilename(
        parent=hauptfenster,
        title="Messdatei auswählen",
        filetypes=(
            ("Messdateien", "*.csv *.dat *.cfg"),
            ("Alle Dateien", "*.*"),))


    if not pfad:
        messagebox.showerror("Keinen gültigen Dateipfad angegeben")
        return 

    def on_weiter():
        value = auswahl_radio.get()
        radio_button_fenster.destroy()
        ploten_kurven(value,hauptfenster,pfad)



    #Man braucht noch eine weiter Button nach der Eingabe 
    weiter_button = create_button(
        radio_button_fenster,
        text="Weiter",
        command=on_weiter,
        primary=False,
    )
    weiter_button.pack(anchor="w", padx=20, pady=5)
    

    

def start_plot_nach_auswahl(value_radio_klick,hauptfenster):

    if value_radio_klick.get() == 0:
        print("→ Hysterese-Messung")
        frame_hyst = hauptfenster.frames["hysterese"]
        if not hasattr(frame_hyst, "live"):
            hysterese_live_plot(hauptfenster)
            
    else:
        print("→ Permeabilitäts-Messung")
        frame_perm = hauptfenster.frames["permeabilität"]
        if not hasattr(frame_perm, "live"):
            permeabilitaet_live_plot(hauptfenster)


def eingabe_daten(fenster,hauptfenster):

    """
    Die Funktion erzeugt mehrer Eingabefelder, welche wie gewünscht umgesetzt
    werden soll. DAbei geht es um die Sample rate und eine UB-Offset kompensation.
    Außerdem soll es ein Daten laden Button geben, welcher alte Datein (csv-Datein)
    laden kann um bei eventuellen Problemen des Hauptprogramms oder eine fehlerhafte 
    Messung dennoch eine alternative bietet Ergebnisse mit den Studierenden zu 
    besprechen.
    """
    #Kontainer für sauber Anordnung erzeugen

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
    #Frame für Offset
    frame_daten_laden = tk.LabelFrame(ein_container, text="Daten laden", relief="ridge",
                                    bd=6,padx=10,pady=10,background="#f5f7fa",
                                    font=("Arial", 10, "bold"))
    frame_daten_laden.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    #Eingabefelder und Button erzeugen und den Frames zuweisen

    #Daten laden Button
    daten_laden_button = create_button(
        frame_daten_laden,
        text="Daten laden",
        command=lambda: daten_laden(hauptfenster),
        primary=False,
    )
    daten_laden_button.pack()

    #Sample Spin Box, also Dropdown menü

    #Label für die Beschriftung der eingabe 
    lbl_sample = tk.Label(frame_sample, text="Sample rate [S/s]:", bg="#f5f7fa")
    lbl_sample.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    sample_box = ttk.Combobox(frame_sample,values=[100,200,500,750,1000,1500,2000,5000],
                                state="readonly",width=10)
    sample_box.set(250)  # Standardwert
    sample_box.grid(row=0, column=1, padx=5, pady=5)

    #Werte bei jeder Änderung übernehmen
    def sample_change(event):
        try:
            wert = int(sample_box.get())
            sample_rate(wert)
            messagebox.showinfo("Neue Sample Rate: [S/s]",f"{wert}")
        except ValueError:
            messagebox.showerror("Fehler", "Ungültige Sample-Rate.")
 

    sample_box.bind("<<ComboboxSelected>>", sample_change)

    #Eingabefeld Offset
    offset_eingabe(frame_offset)
    

    

def fenster_einstellungen(hauptfenster):
    ein_fenster =tk.Toplevel()
    ein_fenster.title("Erweiterte Eintstellung für das Messprogramm")
    ein_fenster.geometry("600x400")
    ein_fenster.configure(bg="#e4e7ec") #Hexcode für hellgrau 

    eingabe_daten(ein_fenster,hauptfenster)
    
    return ein_fenster

def login_passwort(pw_entry,fenster,hauptfenster):

    password = pw_entry.get()

    #Login Meldung 
    if password == "hysterese":
        messagebox.showinfo("Login Successful", "Zugriff erlaubt.")
        fenster.destroy()  # Login-Fenster schließen

        #hier dann das neue Einstellungsfenster öffnen
        fenster_einstellungen(hauptfenster)
    else:
        messagebox.showerror("Login Failed", "Invalid password")


def offset_eingabe(frame_offset):

    #Label und Entry erzeugen, welches dann den Offset speichern soll

    # Label
    label_offset = tk.Label(frame_offset, text="UB-Offset [V]:", bg="#f5f7fa")
    label_offset.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    # Entry
    entry_offset = tk.Entry(frame_offset, width=10)
    entry_offset.grid(row=0, column=1, padx=5, pady=5)
    entry_offset.insert(0, "0.0")

     # Ausgabefunktion
    def offset_uebernehmen():
        text = entry_offset.get().replace(",", ".")
        try:
            wert = float(text)
            update_offset(wert)
            messagebox.showinfo("UB-Offset", f"UB-Offset auf {wert} V gesetzt.")
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige Offset-Spannung eingeben.")

    # Button
    btn_offset = create_button(
        frame_offset,
        text="Offset übernehmen",
        command=offset_uebernehmen,
        primary=False,
    )
    btn_offset.grid(row=1, column=0, columnspan=2, pady=5)

def optionen(hauptfenster):

    nebenfenster =tk.Toplevel()
    nebenfenster.title("Login für Einstellungen")
    nebenfenster.geometry("200x200")
    nebenfenster.configure(bg="#e4e7ec") #Hexcode für hellgrau 

    #Erzeugen und Platzieren des Eingabefeldes des Passwort
    
    #Label Passwort
    pw_label = tk.Label(nebenfenster, text="Passwort: ", bg="#e4e7ec",font=14)
    pw_label.pack()

    #entry Feld für Passwort
    pw_entry = tk.Entry(nebenfenster, show="*")
    pw_entry.pack()

    #Cursor sofort in das Eingabefeld setzen
    pw_entry.focus()

    #Erzeugen und platzieren des Login Button
    login_button = create_button(
        nebenfenster,
        text="Login",
        command=lambda: login_passwort(pw_entry,nebenfenster, hauptfenster),
        primary=False,
    )
    login_button.pack()

    pw_entry.bind("<Return>", lambda event: login_passwort(pw_entry, nebenfenster,
                                                           hauptfenster))

    pw_entry.pack(pady = 10)
    pw_label.pack(pady= 5)

    return nebenfenster

def neuen_ordner(hauptfenster):

    pfad = filedialog.askdirectory(
        parent=hauptfenster,
        title="Speicherordner für CSV-Dateien auswählen"
    )

    if not pfad:
        return

    set_csv_ordner(pfad)
    messagebox.showinfo(
        "Speicherort gesetzt",
        f"CSV-Dateien werden nun hier gespeichert:\n{pfad}"
    )
   
    return None

def untermenue(hauptfenster):
    """
    Die Funktion erzeugt eine Untermenü um Messpprogramm, welches Passwort 
    geschützt ist. In diesem Unterprogramm ist es möglich eine Offset einzustellen,
    Daten zu laden und die Plots anzuzeigen und die Samplerate soll heir einstellbar
    sein. Grunstäzlich ist für dei Samplerate wenn man nichts hineinschreibt ein 
    fixer Wert vorgesehen, wenn dieser aber eingetragen wird dann wird damit dieser
    Wert überschrieben für Messungen so lange, bis das Messprogramm neu gestartet
    wird.
    """

    #um eine Menüleiste zu erzeugen
    menuebar = tk.Menu(hauptfenster)

    #Den Reiter erzeugen und darauf folgend die Optionen leiste
    optionmenu = tk.Menu(menuebar)
    optionmenu.add_command(label="Optionen",command=lambda:optionen(hauptfenster))

    #um den Speicherort flexibel zu gestalten, von Gruppe zu Gruppe anpassbar
    optionmenu.add_command(label="Speicherort erstellen",
                           command=lambda:neuen_ordner(hauptfenster))

    menuebar.add_cascade(label="Einstellungen", menu=optionmenu)
    

    hauptfenster.config(menu=menuebar)


def willkommensfenster(hauptfenster):

    popup = tk.Toplevel(hauptfenster)
    popup.title("Willkommen")
    popup.geometry("500x250")

    popup.transient(hauptfenster)
    popup.grab_set()

    tk.Label(
        popup,
        text="Willkommen zum Messprogramm Magnetika",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    tk.Label(
        popup,
        text="Bitte wählen Sie einen Speicherort\nfür die Messdaten aus."
    ).pack(pady=10)

    create_button(
        popup,
        text="Ordner auswählen",
        command=lambda: neuen_ordner(hauptfenster)
    ).pack(pady=5)

    return None

class Hauptfenster(tk.Tk):
    """
    Die Klasse erzeugt das Hauptfenster 

    Rückgabewert: 
        Hauptfenster
    
    Das Gui wird auch als FUnktion erstellt, weil man es dann einfach in der Main
    aufrufen kann

    """
     
    def __init__(self):
        super().__init__()

        self.title("Messprogramm Laborversuch Magnetika Hysterese")

        # Bildschirmgröße
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        self.geometry(f"{screen_width}x{screen_height}")
        self.configure(bg="#e4e7ec")

        self.option_add("*Font", "Arial 10")
        self.option_add("*Label.background", "#f5f7fa")
        self.option_add("*Label.foreground", "#222222")
        self.option_add("*Button.font", "Arial 10")

        # Zustands-Variablen der GUI
        self.state = {
            "scale_H": None,
            "scale_B": None,
            "messung_laeuft": False,
            "cursor_H_var": None,
            "cursor_B_var": None
            }
        



def GUI():

    #Hauptfenster
    hauptfenster = Hauptfenster()

    #Willkommensfenster udn Speicherort
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
