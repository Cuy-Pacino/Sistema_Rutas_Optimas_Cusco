"""
gui.py — Interfaz Gráfica del Sistema de Rutas Óptimas
San Sebastián, Cusco — Programación III UNSAAC 2026

La GUI expone visualmente TODOS los algoritmos:
Modelos   : Bubble Sort, Shell Sort, Counting Sort,
            Búsqueda Lineal, Búsqueda Binaria, Huffman
Grafo     : Merge Sort, Quick Sort (grados), Par de Puntos,
            Coloreo de Grafos, Exponenciación Rápida
Algoritmos: Mochila Fraccionaria, Selección de Actividades,
            Quick Sort, Heap Sort, Radix Sort, Subset Sum,
            Greedy, Divide y Vencerás, Backtracking
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
from modelos import ResultadoAlgoritmo

from grafo_san_sebastian import GrafoSanSebastian, ZONAS
from modelos import (Pedido, Repartidor, Prioridad, PRIORIDAD_LABEL,
                    bubble_sort, shell_sort, counting_sort_prioridad,
                    busqueda_lineal_cliente, busqueda_lineal_sector,
                    busqueda_binaria_id, demo_huffman, huffman_comprimir)
from algoritmos import (
    quick_sort_pedidos, heap_sort_pedidos, radix_sort_por_valor,
    seleccion_actividades, mochila_fraccionaria,
    subset_sum_carga_exacta,
    greedy_vecino_cercano, divide_y_venceras,
    backtracking_rutas_restringidas, comparar_algoritmos,
)

# ─────────────────────── Paleta ──────────────────────────────
BG_DARK   = "#0f1117"
BG_PANEL  = "#1a1d27"
BG_CARD   = "#22253a"
ACCENT    = "#f5a623"
ACCENT2   = "#4ecdc4"
RED_VIF   = "#e74c3c"
GREEN_VIF = "#2ecc71"
PURPLE    = "#9b59b6"
TEXT_MAIN = "#eaeaea"
TEXT_DIM  = "#7f8c8d"

ZONA_COLORES = {"NORTE": "#3498db", "CENTRO": "#f5a623", "SUR": "#2ecc71"}

# Paleta de coloreo de grafo (hasta 8 colores)
COLOREO_PALETA = [
    "#e74c3c","#3498db","#2ecc71","#f39c12",
    "#9b59b6","#1abc9c","#e67e22","#34495e",
]

ALGO_COLORES = {
    "Greedy Vecino Más Cercano":            "#f5a623",
    "Mochila Fraccionaria":                 "#1abc9c",
    "Divide y Vencerás":                    "#4ecdc4",
    "Programación Dinámica (Knapsack 0/1)": "#9b59b6",
    "Backtracking":                         "#e74c3c",
}
NODE_R = 8


# ══════════════════════════════════════════════════════════════
class App(tk.Tk):
# ══════════════════════════════════════════════════════════════

    def __init__(self):
        super().__init__()
        self.title("Rutas Óptimas — San Sebastián, Cusco | UNSAAC 2026")
        self.configure(bg=BG_DARK)
        self.state("zoomed")
        self.resizable(True, True)

        self.grafo         = GrafoSanSebastian()
        self.pedidos: list[Pedido]       = []
        self.repartidores: list[Repartidor] = self._crear_repartidores()
        self._id_counter   = 1
        self._bloqueadas: list[tuple[str,str]] = []
        self._coloreo_activo = False      # si mostrar coloreo en canvas
        # Zoom y paneo del canvas
        self._zoom        = 1.0
        self._pan_x       = 0
        self._pan_y       = 0
        self._drag_start  = None
        # Dibujar canvas
        self._build_ui()
        self._dibujar_grafo()
        self._cargar_demo()

    # ── datos iniciales ───────────────────────────────────────

    def _crear_repartidores(self):
        return [
            Repartidor("R1", "Carlos Quispe", "DEPOSITO", 30.0, 60.0, 25.0),
            Repartidor("R2", "Ana Huanca",    "DEPOSITO", 25.0, 50.0, 25.0),
            Repartidor("R3", "Luis Ccopa",    "DEPOSITO", 20.0, 40.0, 20.0),
        ]

    def _cargar_demo(self):
        demos = [
            ("P001","Farmacia San Blas","HOSP_SS",  1.5, 3.0, 45.0,Prioridad.URGENTE),
            ("P002","Rest. El Fogón",  "MERCADO",   3.0, 8.0, 30.0,Prioridad.ALTA),
            ("P003","Ferretería Larapa","LARAPA",   8.0,15.0, 80.0,Prioridad.NORMAL),
            ("P004","Tienda Villa Sol","VILLA_SOL", 2.0, 5.0, 25.0,Prioridad.NORMAL),
            ("P005","Bodega Angostura","ANGOSTURA", 5.0,10.0, 60.0,Prioridad.BAJA),
            ("P006","Clínica Koripata","KORIPATA",  0.5, 1.0, 90.0,Prioridad.URGENTE),
            ("P007","Librería Clorinda","CLORINDA", 1.0, 2.0, 20.0,Prioridad.BAJA),
            ("P008","Mercado Santa Ana","SANTA_ANA",4.0, 9.0, 50.0,Prioridad.ALTA),
        ]
        for id_,cli,nodo,peso,vol,val,pri in demos:
            self.pedidos.append(Pedido(
                id=id_,cliente=cli,nodo_destino=nodo,
                peso=peso,volumen=vol,valor=val,prioridad=pri,
                hora_registro=time.time()
            ))
        self._actualizar_tabla()

    # ── helpers UI ────────────────────────────────────────────

    def _lbl(self, p, txt, sz=10, bold=False, color=TEXT_MAIN, **kw):
        return tk.Label(p, text=txt, bg=p["bg"], fg=color,
                        font=("Courier New", sz, "bold" if bold else "normal"), **kw)

    def _btn(self, p, txt, cmd, color=ACCENT, **kw):
        b = tk.Button(p, text=txt, command=cmd,
                      bg=color, fg=BG_DARK,
                      font=("Courier New", 8, "bold"),
                      relief="flat", bd=0, padx=6, pady=4,
                      cursor="hand2", activebackground=TEXT_DIM, **kw)
        b.bind("<Enter>", lambda e: b.config(bg=TEXT_DIM))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def _sep(self, p):
        tk.Frame(p, bg=BG_CARD, height=1).pack(fill="x", padx=8, pady=5)

    def _entry(self, p, **kw):
        return tk.Entry(p, bg=BG_CARD, fg=TEXT_MAIN,
                        insertbackground=TEXT_MAIN,
                        font=("Courier New", 9), relief="flat", bd=4, **kw)

    def _style_ttk(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("D.TNotebook",     background=BG_PANEL, borderwidth=0)
        s.configure("D.TNotebook.Tab", background=BG_CARD, foreground=TEXT_DIM,
                    font=("Courier New", 8, "bold"), padding=[7,3])
        s.map("D.TNotebook.Tab",
              background=[("selected", BG_DARK)],
              foreground=[("selected", ACCENT)])
        s.configure("D.Treeview",
                    background=BG_CARD, foreground=TEXT_MAIN,
                    fieldbackground=BG_CARD, rowheight=21,
                    font=("Courier New", 8))
        s.configure("D.Treeview.Heading",
                    background=BG_DARK, foreground=ACCENT,
                    font=("Courier New", 8, "bold"))
        s.map("D.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG_DARK)])

    # ── layout principal ─────────────────────────────────────

    def _build_ui(self):
        self._style_ttk()
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._panel_izq = tk.Frame(self, bg=BG_PANEL, width=390)
        self._panel_izq.grid(row=0, column=0, sticky="nsew", padx=(8,0), pady=8)
        self._panel_izq.grid_propagate(False)

        self._panel_der = tk.Frame(self, bg=BG_DARK)
        self._panel_der.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self._panel_der.rowconfigure(0, weight=3)
        self._panel_der.rowconfigure(1, weight=2)
        self._panel_der.columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_canvas()
        self._build_panel_resultados()

    # ══ SIDEBAR ══════════════════════════════════════════════

    def _build_sidebar(self):
        p = self._panel_izq
        tk.Frame(p, bg=ACCENT, height=3).pack(fill="x")
        self._lbl(p,"🚚  RUTAS ÓPTIMAS",13,True,ACCENT).pack(pady=(8,2))
        self._lbl(p,"San Sebastián · Cusco · UNSAAC 2026",8,color=TEXT_DIM).pack()
        self._sep(p)

        nb = ttk.Notebook(p, style="D.TNotebook")
        nb.pack(fill="both", expand=True, padx=4, pady=2)

        tabs = {
            " 📦 Pedidos ":    tk.Frame(nb, bg=BG_PANEL),
            " ⚙ Algoritmos ": tk.Frame(nb, bg=BG_PANEL),
            " 🔍 Búsqueda ":  tk.Frame(nb, bg=BG_PANEL),
            " 🗺 Grafo ":     tk.Frame(nb, bg=BG_PANEL),
            " 🔧 Config ":    tk.Frame(nb, bg=BG_PANEL),
        }
        for nombre, frame in tabs.items():
            nb.add(frame, text=nombre)

        (self.tab_ped, self.tab_alg,
         self.tab_bus, self.tab_grafo,
         self.tab_cfg) = tabs.values()

        self._build_tab_pedidos()
        self._build_tab_algoritmos()
        self._build_tab_busqueda()
        self._build_tab_grafo()
        self._build_tab_config()

    # ── Pestaña Pedidos ───────────────────────────────────────

    def _build_tab_pedidos(self):
        t = self.tab_ped
        self._lbl(t,"─ Nuevo Pedido ─",9,True,ACCENT).pack(pady=(8,4))

        ff = tk.Frame(t, bg=BG_PANEL); ff.pack(fill="x", padx=8)
        ff.columnconfigure(1, weight=1)

        def fila(lbl, row, widget):
            self._lbl(ff, lbl, 8, color=TEXT_DIM).grid(row=row,column=0,sticky="w",pady=2)
            widget.grid(row=row, column=1, sticky="ew", padx=(4,0), pady=2)
            return widget

        self.e_cli  = fila("Cliente:",   0, self._entry(ff))
        self.e_peso = fila("Peso kg:",   1, self._entry(ff))
        self.e_vol  = fila("Vol L:",     2, self._entry(ff))
        self.e_val  = fila("Valor S/.:", 3, self._entry(ff))

        nids = [nid for nid in self.grafo.nodos
                if not self.grafo.nodos[nid].es_deposito]
        self._lbl(ff,"Destino:",8,color=TEXT_DIM).grid(row=4,column=0,sticky="w",pady=2)
        self.cb_dest = ttk.Combobox(
            ff, values=[f"{n} | {self.grafo.nodos[n].nombre}" for n in nids],
            font=("Courier New",8), state="readonly")
        self.cb_dest.current(0)
        self.cb_dest.grid(row=4, column=1, sticky="ew", padx=(4,0), pady=2)

        self._lbl(ff,"Prioridad:",8,color=TEXT_DIM).grid(row=5,column=0,sticky="w",pady=2)
        self.cb_pri = ttk.Combobox(
            ff, values=["URGENTE","ALTA","NORMAL","BAJA"],
            font=("Courier New",8), state="readonly")
        self.cb_pri.current(2)
        self.cb_pri.grid(row=5, column=1, sticky="ew", padx=(4,0), pady=2)

        # Botones agregar / limpiar
        bf = tk.Frame(t,bg=BG_PANEL); bf.pack(fill="x",padx=8,pady=5)
        self._btn(bf,"➕ Agregar", self._agregar_pedido,ACCENT).pack(side="left",expand=True,fill="x",padx=(0,3))
        self._btn(bf,"🗑 Limpiar", self._limpiar_pedidos,RED_VIF).pack(side="left",expand=True,fill="x",padx=(3,0))

        self._sep(t)
        # Ordenamiento
        self._lbl(t,"─ Ordenar Pedidos ─",9,True,ACCENT).pack()
        sf = tk.Frame(t,bg=BG_PANEL); sf.pack(fill="x",padx=8,pady=4)
        algoritmos_orden = [
            ("Bubble",   lambda: self._ordenar("bubble")),
            ("Shell",    lambda: self._ordenar("shell")),
            ("Counting", lambda: self._ordenar("counting")),
            ("Quick",    lambda: self._ordenar("quick")),
            ("Heap",     lambda: self._ordenar("heap")),
            ("Radix",    lambda: self._ordenar("radix")),
        ]
        for i,(lbl,cmd) in enumerate(algoritmos_orden):
            self._btn(sf, lbl, cmd, ACCENT2 if i%2==0 else PURPLE
                      ).grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
        sf.columnconfigure(0,weight=1); sf.columnconfigure(1,weight=1); sf.columnconfigure(2,weight=1)

        self._sep(t)
        self._lbl(t,"─ Lista de Pedidos ─",9,True,ACCENT).pack()

        cols = ("ID","Cliente","Destino","Prioridad","Peso","Valor")
        ftree = tk.Frame(t,bg=BG_PANEL); ftree.pack(fill="both",expand=True,padx=6,pady=(0,6))
        self.tree = ttk.Treeview(ftree, columns=cols, show="headings",
                                 style="D.Treeview", height=7)
        for c,w in zip(cols,[50,100,80,70,50,60]):
            self.tree.heading(c,text=c); self.tree.column(c,width=w,anchor="center")
        sb = ttk.Scrollbar(ftree,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")

    # ── Pestaña Algoritmos ────────────────────────────────────

    def _build_tab_algoritmos(self):
        t = self.tab_alg
        self._lbl(t,"─ Ejecutar Algoritmo ─",9,True,ACCENT).pack(pady=(8,4))

        rf = tk.Frame(t,bg=BG_PANEL); rf.pack(fill="x",padx=8,pady=2)
        self._lbl(rf,"Repartidor:",8,color=TEXT_DIM).pack(side="left")
        self.cb_rep = ttk.Combobox(
            rf, values=[f"{r.id} – {r.nombre}" for r in self.repartidores],
            font=("Courier New",8), state="readonly")
        self.cb_rep.current(0)
        self.cb_rep.pack(side="left",padx=6,fill="x",expand=True)

        self._sep(t)

        botones = [
            ("🟠  Greedy — Vecino Más Cercano",    ACCENT,    self._run_greedy),
            ("🟢  Mochila Fraccionaria",            ACCENT2,   self._run_mochila_frac),
            ("🔵  Divide y Vencerás (3 Zonas)",     "#3498db", self._run_dyv),
            ("🔴  Backtracking — Rutas Restric.",   RED_VIF,   self._run_backtracking),
            ("🟣  Selección de Actividades",        PURPLE,    self._run_seleccion_act),
            ("⚪  Subset Sum — Carga Exacta",       TEXT_DIM,  self._run_subset_sum),
            ("📊  Comparar Greedy vs Fraccionaria", GREEN_VIF, self._comparar),
        ]
        for txt,color,cmd in botones:
            self._btn(t,txt,cmd,color).pack(fill="x",padx=10,pady=2)

        self._sep(t)
        self._lbl(t,"─ Resumen ─",9,True,ACCENT).pack()
        self.txt_resumen = tk.Text(
            t,bg=BG_CARD,fg=TEXT_MAIN,
            font=("Courier New",8),height=8,
            relief="flat",state="disabled",wrap="word")
        self.txt_resumen.pack(fill="both",expand=True,padx=8,pady=(0,6))

    # ── Pestaña Búsqueda ──────────────────────────────────────

    def _build_tab_busqueda(self):
        t = self.tab_bus
        self._lbl(t,"─ Búsqueda ─",9,True,ACCENT).pack(pady=(8,4))

        # Búsqueda binaria por ID
        f1 = tk.Frame(t,bg=BG_PANEL); f1.pack(fill="x",padx=8,pady=3)
        self._lbl(f1,"ID Pedido:",8,color=TEXT_DIM).pack(side="left")
        self.e_bid = self._entry(f1, width=10); self.e_bid.pack(side="left",padx=4)
        self._btn(f1,"🔍 Binaria O(log n)",self._buscar_binaria,ACCENT).pack(side="left")

        # Búsqueda lineal por cliente
        f2 = tk.Frame(t,bg=BG_PANEL); f2.pack(fill="x",padx=8,pady=3)
        self._lbl(f2,"Cliente:",8,color=TEXT_DIM).pack(side="left")
        self.e_bcli = self._entry(f2, width=12); self.e_bcli.pack(side="left",padx=4)
        self._btn(f2,"🔍 Lineal O(n)",self._buscar_lineal_cli,ACCENT2).pack(side="left")

        # Búsqueda lineal por sector
        f3 = tk.Frame(t,bg=BG_PANEL); f3.pack(fill="x",padx=8,pady=3)
        self._lbl(f3,"Sector:",8,color=TEXT_DIM).pack(side="left")
        self.cb_sec = ttk.Combobox(
            f3, values=list(self.grafo.nodos.keys()),
            font=("Courier New",8), state="readonly", width=14)
        self.cb_sec.current(0); self.cb_sec.pack(side="left",padx=4)
        self._btn(f3,"🔍 Sector O(n)",self._buscar_lineal_sec,PURPLE).pack(side="left")

        self._sep(t)
        # Huffman
        self._lbl(t,"─ Huffman — comprimir texto ─",9,True,ACCENT).pack()
        fh = tk.Frame(t,bg=BG_PANEL); fh.pack(fill="x",padx=8,pady=3)
        self._lbl(fh,"Texto:",8,color=TEXT_DIM).pack(side="left")
        self.e_huf = self._entry(fh); self.e_huf.pack(side="left",fill="x",expand=True,padx=4)
        self._btn(fh,"⚡ Comprimir",self._run_huffman,ACCENT).pack(side="left")

        self._sep(t)
        self._lbl(t,"─ Resultado ─",9,True,ACCENT).pack()
        self.txt_bus = tk.Text(
            t,bg=BG_CARD,fg=TEXT_MAIN,
            font=("Courier New",8),height=12,
            relief="flat",state="disabled",wrap="word")
        self.txt_bus.pack(fill="both",expand=True,padx=8,pady=(0,6))

    # ── Pestaña Grafo ─────────────────────────────────────────

    def _build_tab_grafo(self):
        t = self.tab_grafo
        self._lbl(t,"─ Herramientas del Grafo ─",9,True,ACCENT).pack(pady=(8,4))

        botones = [
            ("🎨 Coloreo de Grafos (Welsh-Powell)", ACCENT,  self._run_coloreo),
            ("📍 Par de Puntos Más Cercanos",        ACCENT2, self._run_par_cercano),
            ("📊 Merge Sort Nodos por X",            PURPLE,  self._run_merge_nodos),
            ("🔢 Exponenciación Rápida — demo",      TEXT_DIM,self._run_expo),
        ]
        for txt,color,cmd in botones:
            self._btn(t,txt,cmd,color).pack(fill="x",padx=10,pady=3)

        self._sep(t)
        var_coloreo = tk.BooleanVar(value=False)
        self._coloreo_var = var_coloreo
        tk.Checkbutton(
            t, text="Mostrar coloreo en el mapa",
            variable=var_coloreo,
            command=self._toggle_coloreo,
            bg=BG_PANEL, fg=TEXT_MAIN, selectcolor=BG_CARD,
            activebackground=BG_PANEL, activeforeground=ACCENT,
            font=("Courier New",8)
        ).pack(padx=10, pady=4, anchor="w")

        self._sep(t)
        self._lbl(t,"─ Resultado ─",9,True,ACCENT).pack()
        self.txt_grafo = tk.Text(
            t,bg=BG_CARD,fg=TEXT_MAIN,
            font=("Courier New",8),height=14,
            relief="flat",state="disabled",wrap="word")
        self.txt_grafo.pack(fill="both",expand=True,padx=8,pady=(0,6))

    # ── Pestaña Config ────────────────────────────────────────

    def _build_tab_config(self):
        t = self.tab_cfg
        self._lbl(t,"─ Bloquear Calles ─",9,True,ACCENT).pack(pady=(8,4))

        edges = [(a.origen, a.destino) for a in self.grafo._aristas_raw]
        self.cb_blq = ttk.Combobox(
            t,values=[f"{o} ↔ {d}" for o,d in edges],
            font=("Courier New",8),state="readonly")
        self.cb_blq.current(0)
        self.cb_blq.pack(fill="x",padx=8,pady=4)

        bf2 = tk.Frame(t,bg=BG_PANEL); bf2.pack(fill="x",padx=8)
        self._btn(bf2,"🚧 Bloquear",   self._bloquear,  RED_VIF).pack(side="left",expand=True,fill="x",padx=(0,3))
        self._btn(bf2,"✅ Desbloquear",self._desbloquear,GREEN_VIF).pack(side="left",expand=True,fill="x",padx=(3,0))

        self._sep(t)
        self._lbl(t,"Calles bloqueadas:",8,color=TEXT_DIM).pack(padx=8,anchor="w")
        self.lst_blq = tk.Listbox(
            t,bg=BG_CARD,fg=RED_VIF,
            font=("Courier New",8),height=4,
            relief="flat",selectbackground=ACCENT)
        self.lst_blq.pack(fill="x",padx=8,pady=4)

        self._sep(t)
        # Backtracking origen/destino
        self._lbl(t,"─ Backtracking ─",9,True,ACCENT).pack()
        bf3 = tk.Frame(t,bg=BG_PANEL); bf3.pack(fill="x",padx=8,pady=4)
        bf3.columnconfigure(1,weight=1)
        nids = list(self.grafo.nodos.keys())
        self._lbl(bf3,"Desde:",8,color=TEXT_DIM).grid(row=0,column=0,sticky="w")
        self.cb_bt_ini = ttk.Combobox(bf3,values=nids,font=("Courier New",8),state="readonly",width=15)
        self.cb_bt_ini.current(0); self.cb_bt_ini.grid(row=0,column=1,padx=4,pady=2)
        self._lbl(bf3,"Hasta:",8,color=TEXT_DIM).grid(row=1,column=0,sticky="w")
        self.cb_bt_fin = ttk.Combobox(bf3,values=nids,font=("Courier New",8),state="readonly",width=15)
        self.cb_bt_fin.current(min(2, len(nids)-1)); self.cb_bt_fin.grid(row=1,column=1,padx=4,pady=2)

        # Selección de actividades
        self._sep(t)
        self._lbl(t,"─ Ventanas Horarias (demo) ─",9,True,ACCENT).pack()
        self._lbl(t,
            "Se usan los 8 pedidos demo con\n"
            "ventanas 8:00-9:00, 8:30-10:00…",
            8,color=TEXT_DIM).pack(padx=8)

    # ── Canvas ────────────────────────────────────────────────

    def _build_canvas(self):
        frame = tk.Frame(self._panel_der, bg=BG_DARK)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(frame, bg="#0d1117",
                                highlightthickness=1,
                                highlightbackground=BG_CARD)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>",      lambda e: self._dibujar_grafo())
        # Zoom con scroll
        self.canvas.bind("<MouseWheel>",     self._on_scroll)       # Windows
        self.canvas.bind("<Button-4>",       self._on_scroll)       # Linux scroll up
        self.canvas.bind("<Button-5>",       self._on_scroll)       # Linux scroll down
        # Paneo con click izquierdo + arrastre
        self.canvas.bind("<ButtonPress-1>",  self._on_pan_start)
        self.canvas.bind("<B1-Motion>",      self._on_pan_move)
        self.canvas.bind("<ButtonRelease-1>",self._on_pan_end)
        # Doble click para resetear vista
        self.canvas.bind("<Double-Button-1>",self._reset_vista)
        self._lbl(frame, "🗺  San Sebastián, Cusco  |  scroll: zoom  |  arrastrar: paneo  |  doble-click: resetear", 9, True, ACCENT).place(x=10, y=6)
    
    
    #Métodos para zoom y paneo del canvas
    def _on_scroll(self, event):
        # Determinar dirección
        if event.num == 4 or event.delta > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15
        nuevo_zoom = self._zoom * factor
        # Límites de zoom
        if not (0.3 <= nuevo_zoom <= 5.0):
            return
        # Zoom centrado en el cursor
        mx, my = event.x, event.y
        self._pan_x = mx - factor * (mx - self._pan_x)
        self._pan_y = my - factor * (my - self._pan_y)
        self._zoom  = nuevo_zoom
        self._dibujar_grafo()

    def _on_pan_start(self, event):
        self._drag_start = (event.x, event.y)

    def _on_pan_move(self, event):
        if self._drag_start is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._pan_x += dx
        self._pan_y += dy
        self._drag_start = (event.x, event.y)
        self._dibujar_grafo()

    def _on_pan_end(self, event):
        self._drag_start = None

    def _reset_vista(self, event=None):
        self._zoom  = 1.0
        self._pan_x = 0
        self._pan_y = 0
        self._dibujar_grafo()



    def _build_panel_resultados(self):
        frame = tk.Frame(self._panel_der,bg=BG_PANEL)
        frame.grid(row=1,column=0,sticky="nsew",pady=(6,0))
        frame.rowconfigure(1,weight=1); frame.columnconfigure(0,weight=1)

        self._lbl(frame,"📋  Resultados y Análisis Big-O",10,True,ACCENT
                ).grid(row=0,column=0,sticky="w",padx=10,pady=4)

        self.txt_res = tk.Text(
            frame,bg=BG_CARD,fg=TEXT_MAIN,
            font=("Courier New",8),wrap="word",
            relief="flat",state="disabled")
        self.txt_res.grid(row=1,column=0,sticky="nsew",padx=6,pady=(0,6))

        sb = ttk.Scrollbar(frame,orient="vertical",command=self.txt_res.yview)
        self.txt_res.configure(yscrollcommand=sb.set)
        sb.grid(row=1,column=1,sticky="ns",pady=(0,6))

    # ══ DIBUJO DEL GRAFO ════════════════════════════════════

    def _dibujar_grafo(self, rutas: list[list[str]] = None,
                        colores: list[str] = None):
        c = self.canvas
        c.delete("all")

        def tx(x): return int(x * self._zoom + self._pan_x)
        def ty(y): return int(y * self._zoom + self._pan_y)
        r_zoom = max(3, int(NODE_R * self._zoom))

        coloreo = None
        if self._coloreo_activo:
            coloreo = self.grafo.obtener_coloreo()

        # Zonas de fondo
        for zona, nids in ZONAS.items():
            color = ZONA_COLORES[zona]
            xs = [self.grafo.nodos[n].x for n in nids if n in self.grafo.nodos]
            ys = [self.grafo.nodos[n].y for n in nids if n in self.grafo.nodos]
            if xs and ys:
                mx, my = tx(sum(xs)//len(xs)), ty(sum(ys)//len(ys))
                off = int(70 * self._zoom)
                c.create_oval(mx-off, my-int(50*self._zoom),
                            mx+off, my+int(50*self._zoom),
                            fill=color, outline="", stipple="gray12")
                c.create_text(mx, my - int(62*self._zoom),
                            text=f"Zona {zona}",
                            fill=color, font=("Courier New", 7, "bold"))

        # Aristas
        for nid, vecinos in self.grafo.adyacencia.items():
            n1 = self.grafo.nodos.get(nid)
            for vid, dist, tiempo, calle, bloq in vecinos:
                if vid > nid:
                    n2 = self.grafo.nodos.get(vid)
                    if n1 and n2:
                        col_a = RED_VIF if bloq else "#2d3748"
                        c.create_line(tx(n1.x), ty(n1.y), tx(n2.x), ty(n2.y),
                                    fill=col_a, width=max(1, self._zoom),
                                    dash=(4, 4) if bloq else ())

        # Rutas resaltadas
        if rutas:
            for idx, ruta in enumerate(rutas):
                col_r = (colores[idx] if colores and idx < len(colores) else ACCENT)
                for i in range(len(ruta) - 1):
                    n1 = self.grafo.nodos.get(ruta[i])
                    n2 = self.grafo.nodos.get(ruta[i+1])
                    if n1 and n2:
                        c.create_line(tx(n1.x), ty(n1.y), tx(n2.x), ty(n2.y),
                                    fill=col_r, width=max(2, int(4*self._zoom)),
                                    arrow=tk.LAST, arrowshape=(10, 12, 4))

        # Nodos
        for nid, nodo in self.grafo.nodos.items():
            r = r_zoom + (2 if nodo.es_deposito else 0)
            cx, cy = tx(nodo.x), ty(nodo.y)

            if coloreo:
                idx_c = coloreo.get(nid, 0)
                fill = COLOREO_PALETA[idx_c % len(COLOREO_PALETA)]
            elif nodo.es_deposito:
                fill = RED_VIF
            else:
                for zona, nids in ZONAS.items():
                    if nid in nids:
                        fill = ZONA_COLORES[zona]
                        break
                else:
                    fill = "#2c3e50"

            if any(p.nodo_destino == nid and not p.entregado for p in self.pedidos):
                c.create_oval(cx-r-5, cy-r-5, cx+r+5, cy+r+5,
                            fill="", outline=ACCENT, width=2)

            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                        fill=fill, outline=BG_DARK, width=1.5)
            c.create_text(cx, cy - r - 6,
                        text=nid[:6], fill=TEXT_MAIN,
                        font=("Courier New", max(5, int(6*self._zoom)), "bold"))

        # Leyenda
        ly = 22
        for zona, color in ZONA_COLORES.items():
            c.create_rectangle(10, ly, 20, ly+10, fill=color, outline="")
            c.create_text(24, ly+5, text=f"Zona {zona}",
                        fill=color, font=("Courier New", 7), anchor="w")
            ly += 15

        if coloreo:
            n_col = len(set(coloreo.values()))
            c.create_text(10, ly+10,
                        text=f"Coloreo: {n_col} colores",
                        fill=ACCENT, font=("Courier New", 7, "bold"), anchor="w")

    # ══ ACCIONES PEDIDOS ════════════════════════════════════

    def _agregar_pedido(self):
        try:
            cli  = self.e_cli.get().strip()  or f"Cliente {self._id_counter}"
            peso = float(self.e_peso.get() or "2")
            vol  = float(self.e_vol.get()  or "4")
            val  = float(self.e_val.get()  or "30")
        except ValueError:
            messagebox.showerror("Error","Peso, Volumen y Valor deben ser números.")
            return
        dest = self.cb_dest.get().split("|")[0].strip()
        pri  = Prioridad[self.cb_pri.get()]
        pid  = f"P{self._id_counter:03d}"; self._id_counter += 1
        self.pedidos.append(Pedido(
            id=pid,cliente=cli,nodo_destino=dest,
            peso=peso,volumen=vol,valor=val,
            prioridad=pri,hora_registro=time.time()))
        self._actualizar_tabla(); self._dibujar_grafo()
        for e in (self.e_cli,self.e_peso,self.e_vol,self.e_val):
            e.delete(0,"end")

    def _limpiar_pedidos(self):
        if messagebox.askyesno("Confirmar","¿Limpiar todos los pedidos?"):
            self.pedidos.clear()
            self._actualizar_tabla(); self._dibujar_grafo()

    def _ordenar(self, metodo: str):
        antes = [p.id for p in self.pedidos]
        if metodo == "bubble":
            self.pedidos = bubble_sort(self.pedidos,"prioridad")
            big_o = "O(n²)"
        elif metodo == "shell":
            self.pedidos = shell_sort(self.pedidos,"prioridad")
            big_o = "O(n log² n)"
        elif metodo == "counting":
            self.pedidos = counting_sort_prioridad(self.pedidos)
            big_o = "O(n + k)  k=4"
        elif metodo == "quick":
            self.pedidos = quick_sort_pedidos(self.pedidos,"prioridad")
            big_o = "O(n log n)"
        elif metodo == "heap":
            self.pedidos = heap_sort_pedidos(self.pedidos)
            big_o = "O(n log n)"
        elif metodo == "radix":
            self.pedidos = radix_sort_por_valor(self.pedidos)
            big_o = "O(n·k)"
        else:
            return
        self._actualizar_tabla()
        despues = [p.id for p in self.pedidos]
        self._escribir_resumen(
            f"✅ Ordenado con {metodo.upper()} — {big_o}\n"
            f"Antes  : {antes}\n"
            f"Después: {despues}"
        )

    def _actualizar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for p in self.pedidos:
            self.tree.insert("","end",values=(
                p.id, p.cliente[:12], p.nodo_destino,
                PRIORIDAD_LABEL[p.prioridad],
                f"{p.peso}kg", f"S/{p.valor}"
            ))

    # ══ ACCIONES ALGORITMOS ═════════════════════════════════

    def _rep(self) -> Repartidor:
        return self.repartidores[self.cb_rep.current()]

    def _run_greedy(self):
        if not self.pedidos: return messagebox.showwarning("","Agrega pedidos.")
        r = greedy_vecino_cercano(self.grafo, self._rep(), self.pedidos)
        self._mostrar(r); self._dibujar_grafo([r.ruta],[ALGO_COLORES["Greedy Vecino Más Cercano"]])

    def _run_mochila_frac(self):
        if not self.pedidos: return messagebox.showwarning("","Agrega pedidos.")
        r = mochila_fraccionaria(self._rep(), self.pedidos, self.grafo)
        self._mostrar(r); self._dibujar_grafo([r.ruta],[ALGO_COLORES["Mochila Fraccionaria"]])

    def _run_dyv(self):
        if not self.pedidos: return messagebox.showwarning("","Agrega pedidos.")
        rs = divide_y_venceras(self.grafo, self.repartidores, self.pedidos)
        self._dibujar_grafo([r.ruta for r in rs],
                            [ALGO_COLORES["Divide y Vencerás"]]*len(rs))
        self._escribir_resultado(comparar_algoritmos(rs))
        self._escribir_resumen(f"D&V — {len(rs)} zona(s) | "
                               f"{sum(len(r.pedidos_incluidos) for r in rs)} pedidos")

    def _run_backtracking(self):
        ini = self.cb_bt_ini.get()
        fin = self.cb_bt_fin.get()
        if ini == fin:
            return messagebox.showwarning("", "Inicio ≠ Fin.")
        # Si el destino no corresponde a ningún pedido, avisarlo
        destinos_con_pedido = {p.nodo_destino for p in self.pedidos if not p.entregado}
        if fin not in destinos_con_pedido and destinos_con_pedido:
            fin_sugerido = next(iter(destinos_con_pedido))
            respuesta = messagebox.askyesno(
                "Destino sin pedido",
                f"El nodo destino '{fin}' no tiene pedidos pendientes.\n"
                f"¿Usar '{fin_sugerido}' (primer nodo con pedido) en su lugar?"
            )
            if respuesta:
                fin = fin_sugerido

        self._escribir_resultado("⏳ Backtracking en ejecución…")
        self.update()

        def run():
            r = backtracking_rutas_restringidas(
                self.grafo, ini, fin, list(self._bloqueadas), 30)
            self.after(0, lambda: self._mostrar(r))
            self.after(0, lambda: self._dibujar_grafo(
                [r.ruta], [ALGO_COLORES["Backtracking"]]))

        threading.Thread(target=run, daemon=True).start()

    def _run_seleccion_act(self):
        if not self.pedidos: return messagebox.showwarning("","Agrega pedidos.")
        # Ventanas demo: cada pedido tiene una ventana de 1h con inicio escalonado
        ventanas = []
        for i,p in enumerate(self.pedidos):
            inicio = 8.0 + i * 0.5
            fin    = inicio + 1.0
            ventanas.append((p.id, inicio, fin))
        sel = seleccion_actividades(self.pedidos, ventanas)
        lineas = [
            "SELECCIÓN DE ACTIVIDADES — O(n log n)",
            "Ordenar por hora fin, elegir sin solapamiento.",
            "",
            f"Total pedidos  : {len(self.pedidos)}",
            f"Seleccionados  : {len(sel)}",
            "",
            "Pedidos seleccionados:"
        ]
        for p in sel:
            vent = next(v for v in ventanas if v[0]==p.id)
            lineas.append(f"  • {p.id} | {p.cliente} | "
                          f"{vent[1]:.1f}h – {vent[2]:.1f}h")
        self._escribir_resultado("\n".join(lineas))
        self._escribir_resumen(f"Selección actividades: {len(sel)}/{len(self.pedidos)} pedidos")

    def _run_subset_sum(self):
        if not self.pedidos: return messagebox.showwarning("","Agrega pedidos.")
        rep = self._rep()
        encontrado, sub = subset_sum_carga_exacta(
            self.pedidos, rep.capacidad_peso)
        lineas = [
            "SUBSET SUM — CARGA EXACTA  O(n·W)",
            f"Capacidad objetivo: {rep.capacidad_peso} kg",
            f"Repartidor: {rep.nombre}",
            "",
        ]
        if encontrado:
            lineas += [
                f"✅ ¡Subconjunto encontrado! Carga perfecta.",
                f"Pedidos: {[p.id for p in sub]}",
                f"Pesos  : {[p.peso for p in sub]}",
                f"Total  : {sum(p.peso for p in sub):.1f} kg",
            ]
        else:
            lineas.append("❌ No existe subconjunto con ese peso exacto.")
        self._escribir_resultado("\n".join(lineas))
        self._escribir_resumen(
            f"Subset Sum: {'encontrado' if encontrado else 'no encontrado'}")

    def _comparar(self):
        if not self.pedidos: return messagebox.showwarning("","Agrega pedidos.")
        self._escribir_resultado("⏳ Comparando algoritmos…"); self.update()
        def run():
            rep = self._rep()
            r_greedy = greedy_vecino_cercano(self.grafo, rep, self.pedidos)
            r_frac   = mochila_fraccionaria(rep, self.pedidos, self.grafo)
            r_dyv    = divide_y_venceras(self.grafo, self.repartidores, self.pedidos)
            destinos = [p.nodo_destino for p in self.pedidos if not p.entregado]
            fin_bt = destinos[0] if destinos else "PLAZA_SS"
            r_bt = backtracking_rutas_restringidas(
                self.grafo, "DEPOSITO", fin_bt, list(self._bloqueadas), 20)
            todos = [r_greedy, r_frac] + r_dyv + [r_bt]
            texto = comparar_algoritmos(todos)
            rutas   = [r.ruta for r in todos if r.ruta]
            col_lst = [ALGO_COLORES.get(r.nombre_algoritmo, ACCENT) for r in todos if r.ruta]
            self.after(0, lambda: self._dibujar_grafo(rutas, col_lst))
            self.after(0, lambda: self._escribir_resultado(texto))
            self.after(0, lambda: self._escribir_resumen("✅ Comparación completa"))
        threading.Thread(target=run, daemon=True).start()

    # ══ ACCIONES BÚSQUEDA ══════════════════════════════════

    def _buscar_binaria(self):
        pid = self.e_bid.get().strip()
        r   = busqueda_binaria_id(self.pedidos, pid)
        if r:
            txt = (f"✅ Búsqueda Binaria — O(log n)\n\n"
                   f"  ID       : {r.id}\n"
                   f"  Cliente  : {r.cliente}\n"
                   f"  Destino  : {r.nodo_destino}\n"
                   f"  Prioridad: {PRIORIDAD_LABEL[r.prioridad]}\n"
                   f"  Peso     : {r.peso} kg\n"
                   f"  Valor    : S/. {r.valor}\n")
        else:
            txt = f"❌ ID '{pid}' no encontrado. — O(log n)"
        self._escribir_busqueda(txt)

    def _buscar_lineal_cli(self):
        termino = self.e_bcli.get().strip()
        rs = busqueda_lineal_cliente(self.pedidos, termino)
        txt = f"🔍 Búsqueda Lineal por cliente — O(n)\nTérmino: '{termino}'\n\n"
        if rs:
            for p in rs:
                txt += f"  • {p.id} | {p.cliente} | {p.nodo_destino} | S/.{p.valor}\n"
        else:
            txt += "❌ Sin resultados."
        self._escribir_busqueda(txt)

    def _buscar_lineal_sec(self):
        sec = self.cb_sec.get()
        rs  = busqueda_lineal_sector(self.pedidos, sec)
        txt = f"🗺 Búsqueda Lineal por sector — O(n)\nSector: {sec}\n\n"
        if rs:
            for p in rs:
                txt += f"  • {p.id} | {p.cliente} | {PRIORIDAD_LABEL[p.prioridad]}\n"
        else:
            txt += "ℹ Sin pedidos en este sector."
        self._escribir_busqueda(txt)

    def _run_huffman(self):
        texto = self.e_huf.get().strip()
        if not texto:
            texto = " ".join(p.cliente for p in self.pedidos[:3])
        self._escribir_busqueda(demo_huffman(texto))

    # ══ ACCIONES GRAFO ══════════════════════════════════════

    def _run_coloreo(self):
        coloreo = self.grafo.obtener_coloreo(recalcular=True)
        grupos  = self.grafo.nodos_por_color()
        n_col   = len(set(coloreo.values()))
        lineas  = [
            "COLOREO DE GRAFOS — Welsh-Powell  O(V²+E)",
            f"Nodos: {len(coloreo)} | Colores usados: {n_col}",
            "Garantía: nodos adyacentes tienen colores distintos.",
            "",
        ]
        for color,nids in sorted(grupos.items()):
            lineas.append(f"  Color {color}: {nids}")
        lineas += [
            "",
            "Aplicación en el sistema:",
            "  Repartidor R1 → Color 0",
            "  Repartidor R2 → Color 1",
            "  Repartidor R3 → Color 2",
            "  → Sin solapamiento de zonas asignadas.",
        ]
        self._escribir_grafo("\n".join(lineas))
        self._coloreo_activo = True
        self._coloreo_var.set(True)
        self._dibujar_grafo()

    def _run_par_cercano(self):
        ids_con_pedido = list({p.nodo_destino for p in self.pedidos})
        if len(ids_con_pedido) < 2:
            ids_con_pedido = list(self.grafo.nodos.keys())
        dist, a, b = self.grafo.par_nodos_mas_cercanos(ids_con_pedido)
        na = self.grafo.nodos[a].nombre
        nb = self.grafo.nodos[b].nombre
        lineas = [
            "PAR DE PUNTOS MÁS CERCANOS — O(n log n)",
            "Divide y Vencerás geométrico.",
            "",
            f"Par más cercano:",
            f"  {a}: {na}",
            f"  {b}: {nb}",
            f"  Distancia canvas: {dist:.1f} px",
            f"  Distancia real  : {self.grafo.distancia_directa(a,b):.0f} m",
            "",
            "Uso: punto de partida óptimo para el repartidor.",
        ]
        self._escribir_grafo("\n".join(lineas))
        # Resaltar el par en el canvas
        self._dibujar_grafo()
        na_obj = self.grafo.nodos[a]; nb_obj = self.grafo.nodos[b]
        self.canvas.create_line(
            na_obj.x,na_obj.y,nb_obj.x,nb_obj.y,
            fill=RED_VIF,width=4,dash=(6,3))
        self.canvas.create_text(
            (na_obj.x+nb_obj.x)//2,(na_obj.y+nb_obj.y)//2-10,
            text=f"Par más cercano ({dist:.0f}px)",
            fill=RED_VIF,font=("Courier New",7,"bold"))

    def _run_merge_nodos(self):
        ordenados = self.grafo.nodos_ordenados_por("x")
        lineas = [
            "MERGE SORT de Nodos por coordenada X — O(n log n)",
            "Divide la lista a la mitad recursivamente y fusiona.",
            "",
            "Nodo         X    Y    Zona",
            "─" * 40,
        ]
        for n in ordenados:
            zona = next((z for z,ids in ZONAS.items() if n.id in ids), "?")
            lineas.append(f"  {n.id:<14} {n.x:>4}  {n.y:>4}  {zona}")
        self._escribir_grafo("\n".join(lineas))

    def _run_expo(self):
        from grafo_san_sebastian import expo_rapida, penalizacion_distancia
        lineas = [
            "EXPONENCIACIÓN RÁPIDA — O(log e)",
            "Square-and-multiply: multiplica solo log(e) veces.",
            "",
            "Ejemplos de penalización por tramos:",
            f"  {'Tramos':<10} {'Factor':<12} {'Dist base 1000m':<18} {'Con penalización':<18}",
            "─" * 58,
        ]
        for tramos in [1,2,5,10,20,50]:
            factor = expo_rapida(1.0001, tramos)
            base   = 1000.0
            con_p  = penalizacion_distancia(base, 1.0001, tramos)
            lineas.append(
                f"  {tramos:<10} {factor:<12.6f} {base:<18.1f} {con_p:<18.2f}")
        lineas += [
            "",
            "Uso: rutas con muchos tramos acumulan una leve",
            "penalización que favorece rutas directas.",
        ]
        self._escribir_grafo("\n".join(lineas))

    def _toggle_coloreo(self):
        self._coloreo_activo = self._coloreo_var.get()
        self._dibujar_grafo()

    # ══ CONFIG ══════════════════════════════════════════════

    def _bloquear(self):
        val = self.cb_blq.get()
        parts = [p.strip() for p in val.split("↔")]
        if len(parts)==2:
            par = (parts[0],parts[1])
            if par not in self._bloqueadas:
                self._bloqueadas.append(par)
                self.grafo.bloquear_calle(*par)
                self.lst_blq.insert("end",f"{par[0]} ↔ {par[1]}")
                self._dibujar_grafo()

    def _desbloquear(self):
        val = self.cb_blq.get()
        parts = [p.strip() for p in val.split("↔")]
        if len(parts)==2:
            par = (parts[0],parts[1])
            if par in self._bloqueadas:
                self._bloqueadas.remove(par)
                self.grafo.desbloquear_calle(*par)
                items = list(self.lst_blq.get(0,"end"))
                self.lst_blq.delete(0,"end")
                for item in items:
                    if item != f"{par[0]} ↔ {par[1]}":
                        self.lst_blq.insert("end",item)
                self._dibujar_grafo()

    # ══ HELPERS ESCRITURA ══════════════════════════════════

    def _mostrar(self, r: ResultadoAlgoritmo):
        noms = " → ".join(
            self.grafo.nodos[n].nombre.split("(")[0].strip()[:14]
            for n in r.ruta if n in self.grafo.nodos)
        pids = ", ".join(p.id for p in r.pedidos_incluidos) or "N/A"
        txt = (
            f"{'='*55}\n"
            f"  {r.nombre_algoritmo.upper()}\n"
            f"{'='*55}\n"
            f"  Big-O           : {r.complejidad_big_o}\n"
            f"  Distancia total : {r.distancia_total:.0f} m\n"
            f"  Tiempo de viaje : {r.tiempo_total:.1f} min\n"
            f"  Pedidos         : {pids}\n"
            f"  Valor total     : S/. {r.valor_total:.2f}\n"
            f"  T. cómputo      : {r.tiempo_computo*1000:.2f} ms\n"
            f"\n  Ruta:\n  {noms}\n"
            f"\n  Notas:\n  {r.notas}\n"
            f"{'='*55}\n"
        )
        self._escribir_resultado(txt)
        self._escribir_resumen(
            f"{r.nombre_algoritmo}\n"
            f"Dist: {r.distancia_total:.0f}m | "
            f"Tiempo: {r.tiempo_total:.1f}min | "
            f"Big-O: {r.complejidad_big_o}")

    def _write_text(self, widget, texto):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", texto)
        widget.configure(state="disabled")

    def _escribir_resultado(self, t): self._write_text(self.txt_res, t)
    def _escribir_resumen(self,   t): self._write_text(self.txt_resumen, t)
    def _escribir_busqueda(self,  t): self._write_text(self.txt_bus, t)
    def _escribir_grafo(self,     t): self._write_text(self.txt_grafo, t)

