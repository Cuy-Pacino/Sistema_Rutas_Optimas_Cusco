"""
gui_pyqt.py — Interfaz Gráfica PyQt6
Sistema de Gestión de Rutas Óptimas — San Sebastián, Cusco
Programación III — UNSAAC 2026

Reemplaza gui.py (Tkinter) con PyQt6, manteniendo todas las
funcionalidades y algoritmos expuestos visualmente.

Dependencias:
    pip install PyQt6 pyqtgraph

Uso (en main.py):
    from gui_pyqt import App
    app = App()
    app.exec()
"""

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import folium
import os
import sys
import time
import threading
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QListWidget, QMessageBox, QFrame,
    QSizePolicy, QScrollArea, QSplitterHandle,
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF,
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QPolygonF,
)

from grafo_osm import GrafoOSM as GrafoSanSebastian, ZONAS
from modelos import (
    Pedido, Repartidor, Prioridad, PRIORIDAD_LABEL,
    bubble_sort, shell_sort, counting_sort_prioridad,
    busqueda_lineal_cliente, busqueda_lineal_sector,
    busqueda_binaria_id, demo_huffman,
)
from algoritmos import (
    quick_sort_pedidos, heap_sort_pedidos, radix_sort_por_valor,
    seleccion_actividades, mochila_fraccionaria,
    subset_sum_carga_exacta, greedy_vecino_cercano,
    divide_y_venceras, backtracking_rutas_restringidas,
    comparar_algoritmos,
)

# ─────────────────────────── Paleta de colores ───────────────────────────────

BG_DARK   = "#0f1117"
BG_PANEL  = "#1a1d27"
BG_CARD   = "#22253a"
ACCENT    = "#f5a623"
ACCENT2   = "#4ecdc4"
RED_VIF   = "#e74c3c"
GREEN_VIF = "#2ecc71"
PURPLE    = "#9b59b6"
BLUE      = "#3498db"
TEXT_MAIN = "#eaeaea"
TEXT_DIM  = "#7f8c8d"

ZONA_COLORES = {
    "OESTE":  "#3498db",
    "CENTRO": "#f5a623",
    "ESTE":   "#2ecc71",
    # compatibilidad con nombres anteriores
    "NORTE":  "#3498db",
    "SUR":    "#2ecc71",
}
COLOREO_PALETA = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
]
ALGO_COLORES = {
    "Greedy Vecino Más Cercano": "#f5a623",
    "Mochila Fraccionaria":      "#1abc9c",
    "Divide y Vencerás":         "#4ecdc4",
    "Backtracking":              "#e74c3c",
}
NODE_R = 7


# ─────────────────────────── Helpers de estilo ───────────────────────────────

def _c(hex_str: str) -> QColor:
    return QColor(hex_str)


def _btn(text: str, color: str = ACCENT, min_h: int = 30) -> QPushButton:
    b = QPushButton(text)
    b.setMinimumHeight(min_h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: {BG_DARK};
            border: none;
            border-radius: 4px;
            padding: 4px 10px;
            font-family: 'Courier New';
            font-size: 9pt;
            font-weight: bold;
        }}
        QPushButton:hover  {{ background: #aabbcc; color: #111; }}
        QPushButton:pressed {{ background: {color}; opacity: 0.7; }}
    """)
    return b


def _lbl(text: str, size: int = 9, bold: bool = False,
         color: str = TEXT_MAIN) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(
        f"color: {color}; font-family: 'Courier New'; "
        f"font-size: {size}pt; {'font-weight: bold;' if bold else ''}"
        f"background: transparent;"
    )
    return l


def _entry(placeholder: str = "") -> QLineEdit:
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    e.setStyleSheet(f"""
        QLineEdit {{
            background: {BG_CARD};
            color: {TEXT_MAIN};
            border: 1px solid #2d3748;
            border-radius: 3px;
            padding: 4px 6px;
            font-family: 'Courier New';
            font-size: 9pt;
        }}
        QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
    """)
    return e


def _combo(items: list[str]) -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    c.setStyleSheet(f"""
        QComboBox {{
            background: {BG_CARD};
            color: {TEXT_MAIN};
            border: 1px solid #2d3748;
            border-radius: 3px;
            padding: 3px 6px;
            font-family: 'Courier New';
            font-size: 8pt;
        }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background: {BG_CARD};
            color: {TEXT_MAIN};
            selection-background-color: {ACCENT};
            selection-color: {BG_DARK};
        }}
    """)
    return c


def _textedit() -> QTextEdit:
    t = QTextEdit()
    t.setReadOnly(True)
    t.setFont(QFont("Courier New", 8))
    t.setStyleSheet(f"""
        QTextEdit {{
            background: {BG_CARD};
            color: {TEXT_MAIN};
            border: none;
            border-radius: 4px;
            padding: 6px;
        }}
    """)
    return t


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color: {BG_CARD}; margin: 4px 0;")
    return f


GLOBAL_STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {BG_DARK};
    color: {TEXT_MAIN};
}}
QTabWidget::pane {{
    border: none;
    background: {BG_PANEL};
}}
QTabBar::tab {{
    background: {BG_CARD};
    color: {TEXT_DIM};
    font-family: 'Courier New';
    font-size: 8pt;
    font-weight: bold;
    padding: 5px 10px;
    border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    background: {BG_DARK};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{ color: {TEXT_MAIN}; }}
QScrollBar:vertical {{
    background: {BG_CARD};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #3d4460;
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QTableWidget {{
    background: {BG_CARD};
    color: {TEXT_MAIN};
    gridline-color: #2d3748;
    border: none;
    font-family: 'Courier New';
    font-size: 8pt;
}}
QTableWidget::item:selected {{
    background: {ACCENT};
    color: {BG_DARK};
}}
QHeaderView::section {{
    background: {BG_DARK};
    color: {ACCENT};
    font-family: 'Courier New';
    font-size: 8pt;
    font-weight: bold;
    padding: 4px;
    border: none;
    border-bottom: 1px solid #2d3748;
}}
QListWidget {{
    background: {BG_CARD};
    color: {RED_VIF};
    border: none;
    font-family: 'Courier New';
    font-size: 8pt;
}}
QCheckBox {{
    color: {TEXT_MAIN};
    font-family: 'Courier New';
    font-size: 8pt;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid #3d4460;
    border-radius: 2px;
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QSplitter::handle {{
    background: {BG_CARD};
    width: 3px;
    height: 3px;
}}
"""


# ─────────────────────────── Hilo worker ─────────────────────────────────────

class _Worker(QThread):
    """Ejecuta una función en segundo plano y emite el resultado."""
    finished = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        result = self._fn()
        self.finished.emit(result)


# ─────────────────────────── Ventana principal ───────────────────────────────

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Rutas Óptimas — San Sebastián, Cusco  |  UNSAAC 2026")
        self.showMaximized()

        # Datos
        self.grafo        = GrafoSanSebastian()
        self.pedidos: list[Pedido]        = []
        self.repartidores: list[Repartidor] = self._crear_repartidores()
        self._id_counter  = 1
        self._bloqueadas: list[tuple[str, str]] = []
        self._coloreo_on  = False

        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._build_ui()
        self._cargar_demo()

    # ── Datos iniciales ──────────────────────────────────────

    def _crear_repartidores(self):
        return [
            Repartidor("R1", "Carlos Quispe", "DEPOSITO", 30.0, 60.0, 25.0),
            Repartidor("R2", "Ana Huanca",    "DEPOSITO", 25.0, 50.0, 25.0),
            Repartidor("R3", "Luis Ccopa",    "DEPOSITO", 20.0, 40.0, 20.0),
        ]

    def _cargar_demo(self):
        # Tomamos una lista de IDs reales disponibles en el mapa descargado
        nodos_reales = list(self.grafo.nodos.keys())
        if not nodos_reales:
            return
            
        import random
        demos = [
        ("P001", "Farmacia San Sebastián", random.choice(nodos_reales), 1.5, 3.0,  45.0, Prioridad.URGENTE),
        ("P002", "Abastos Central",       random.choice(nodos_reales), 3.0, 8.0,  30.0, Prioridad.ALTA),
        ("P003", "Accesorios Cachimayo",  random.choice(nodos_reales), 8.0, 15.0, 80.0, Prioridad.NORMAL),
        ("P004", "Vivanderas Enaco",      random.choice(nodos_reales), 2.0, 5.0,  25.0, Prioridad.NORMAL),
        ("P005", "Urb. Túpac Amaru",      random.choice(nodos_reales), 5.0, 10.0, 60.0, Prioridad.BAJA)
        ]
        
        for id_, cli, nodo, peso, vol, val, pri in demos:
            self.pedidos.append(Pedido(
                id=id_, cliente=cli, nodo_destino=nodo,
                peso=peso, volumen=vol, valor=val, prioridad=pri,
                hora_registro=time.time()
            ))
        self._actualizar_tabla()

    # ── Layout principal ─────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Splitter principal izquierda / derecha
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        root.addWidget(splitter)

        # Panel izquierdo
        sidebar = QWidget()
        sidebar.setFixedWidth(400)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"#sidebar {{ background: {BG_PANEL}; border-radius: 6px; }}")
        splitter.addWidget(sidebar)
        self._build_sidebar(sidebar)

        # Panel derecho
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        splitter.addWidget(right)

        # Visor de mapa con folium
        self.web_view = QWebEngineView()
        right_layout.addWidget(self.web_view, stretch=3)
        
        # Cargar el mapa por primera vez
        self.actualizar_mapa_interactivo()

        # Panel resultados
        res_frame = QWidget()
        res_frame.setStyleSheet(
            f"background: {BG_PANEL}; border-radius: 6px;")
        res_layout = QVBoxLayout(res_frame)
        res_layout.setContentsMargins(8, 6, 8, 6)
        res_layout.addWidget(_lbl("📋  Resultados y Análisis Big-O",
                                   10, True, ACCENT))
        self.txt_res = _textedit()
        res_layout.addWidget(self.txt_res)
        right_layout.addWidget(res_frame, stretch=2)

        splitter.setSizes([400, 900])

    # ── Sidebar ──────────────────────────────────────────────

    def _build_sidebar(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header
        header = QWidget()
        header.setStyleSheet(
            f"background: {BG_DARK}; border-radius: 4px; padding: 4px;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(8, 6, 8, 6)
        title = _lbl("🚚  RUTAS ÓPTIMAS", 13, True, ACCENT)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(title)
        sub = _lbl("San Sebastián · Cusco · UNSAAC 2026", 8, False, TEXT_DIM)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(sub)
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)

        self.tab_ped   = QWidget()
        self.tab_alg   = QWidget()
        self.tab_bus   = QWidget()
        self.tab_grafo = QWidget()
        self.tab_cfg   = QWidget()

        for tab, icon, name in [
            (self.tab_ped,   "📦", "Pedidos"),
            (self.tab_alg,   "⚙",  "Algoritmos"),
            (self.tab_bus,   "🔍", "Búsqueda"),
            (self.tab_grafo, "🗺", "Grafo"),
            (self.tab_cfg,   "🔧", "Config"),
        ]:
            tabs.addTab(tab, f"{icon} {name}")

        self._build_tab_pedidos()
        self._build_tab_algoritmos()
        self._build_tab_busqueda()
        self._build_tab_grafo()
        self._build_tab_config()

    # ══ TAB PEDIDOS ══════════════════════════════════════════

    def _build_tab_pedidos(self):
        lay = QVBoxLayout(self.tab_ped)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        lay.addWidget(_lbl("── Nuevo Pedido ──", 9, True, ACCENT))

        grid = QGridLayout()
        grid.setSpacing(4)
        fields = [("Cliente:", ""), ("Peso kg:", "2.0"),
                ("Vol L:",   "4.0"), ("Valor S/.:", "30.0")]
        entries = []
        for i, (lbl_txt, ph) in enumerate(fields):
            grid.addWidget(_lbl(lbl_txt, 8, False, TEXT_DIM), i, 0)
            e = _entry(ph)
            grid.addWidget(e, i, 1)
            entries.append(e)
        self.e_cli, self.e_peso, self.e_vol, self.e_val = entries

        # Destino
        nids = [n for n in self.grafo.nodos
                if not self.grafo.nodos[n].es_deposito]
        grid.addWidget(_lbl("Destino:", 8, False, TEXT_DIM), 4, 0)
        self.cb_dest = _combo(
            [f"{n} | {self.grafo.nodos[n].nombre}" for n in nids])
        grid.addWidget(self.cb_dest, 4, 1)

        # Prioridad
        grid.addWidget(_lbl("Prioridad:", 8, False, TEXT_DIM), 5, 0)
        self.cb_pri = _combo(["URGENTE", "ALTA", "NORMAL", "BAJA"])
        self.cb_pri.setCurrentIndex(2)
        grid.addWidget(self.cb_pri, 5, 1)
        lay.addLayout(grid)

        # Botones agregar / limpiar
        bf = QHBoxLayout()
        b_add = _btn("➕ Agregar", ACCENT)
        b_cls = _btn("🗑 Limpiar", RED_VIF)
        b_add.clicked.connect(self._agregar_pedido)
        b_cls.clicked.connect(self._limpiar_pedidos)
        bf.addWidget(b_add)
        bf.addWidget(b_cls)
        lay.addLayout(bf)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Ordenar Pedidos ──", 9, True, ACCENT))

        # Botones de ordenamiento — 2 filas × 3 columnas
        sort_grid = QGridLayout()
        sort_grid.setSpacing(3)
        sorts = [
            ("Bubble O(n²)",      ACCENT2,  lambda: self._ordenar("bubble")),
            ("Shell O(n log²n)",  PURPLE,   lambda: self._ordenar("shell")),
            ("Counting O(n+k)",   ACCENT2,  lambda: self._ordenar("counting")),
            ("Quick O(n log n)",  PURPLE,   lambda: self._ordenar("quick")),
            ("Heap O(n log n)",   ACCENT2,  lambda: self._ordenar("heap")),
            ("Radix O(n·k)",      PURPLE,   lambda: self._ordenar("radix")),
        ]
        for i, (txt, col, fn) in enumerate(sorts):
            b = _btn(txt, col, 26)
            b.clicked.connect(fn)
            sort_grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(sort_grid)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Lista de Pedidos ──", 9, True, ACCENT))

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Cliente", "Destino", "Prior.", "Peso", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, stretch=1)

    # ══ TAB ALGORITMOS ═══════════════════════════════════════

    def _build_tab_algoritmos(self):
        lay = QVBoxLayout(self.tab_alg)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        lay.addWidget(_lbl("── Repartidor ──", 9, True, ACCENT))
        self.cb_rep = _combo(
            [f"{r.id} – {r.nombre}" for r in self.repartidores])
        lay.addWidget(self.cb_rep)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Ejecutar Algoritmo ──", 9, True, ACCENT))

        botones = [
            ("🟠  Greedy — Vecino Más Cercano",   ACCENT,    self._run_greedy),
            ("🟢  Mochila Fraccionaria",           ACCENT2,   self._run_mochila_frac),
            ("🔵  Divide y Vencerás (3 Zonas)",    BLUE,      self._run_dyv),
            ("🔴  Backtracking — Rutas Restric.",  RED_VIF,   self._run_backtracking),
            ("🟣  Selección de Actividades",       PURPLE,    self._run_seleccion_act),
            ("⚪  Subset Sum — Carga Exacta",      TEXT_DIM,  self._run_subset_sum),
            ("📊  Comparar Todos",                 GREEN_VIF, self._comparar),
        ]
        for txt, col, fn in botones:
            b = _btn(txt, col, 32)
            b.clicked.connect(fn)
            lay.addWidget(b)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Resumen ──", 9, True, ACCENT))
        self.txt_resumen = _textedit()
        self.txt_resumen.setMaximumHeight(130)
        lay.addWidget(self.txt_resumen)
        lay.addStretch()

    # ══ TAB BÚSQUEDA ═════════════════════════════════════════

    def _build_tab_busqueda(self):
        lay = QVBoxLayout(self.tab_bus)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        lay.addWidget(_lbl("── Búsqueda Binaria por ID ──", 9, True, ACCENT))
        r1 = QHBoxLayout()
        self.e_bid = _entry("P001")
        b_bin = _btn("🔍 Binaria O(log n)", ACCENT, 28)
        b_bin.clicked.connect(self._buscar_binaria)
        r1.addWidget(self.e_bid)
        r1.addWidget(b_bin)
        lay.addLayout(r1)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Búsqueda Lineal por Cliente ──", 9, True, ACCENT))
        r2 = QHBoxLayout()
        self.e_bcli = _entry("nombre...")
        b_cli = _btn("🔍 Lineal O(n)", ACCENT2, 28)
        b_cli.clicked.connect(self._buscar_lineal_cli)
        r2.addWidget(self.e_bcli)
        r2.addWidget(b_cli)
        lay.addLayout(r2)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Búsqueda por Sector ──", 9, True, ACCENT))
        r3 = QHBoxLayout()
        self.cb_sec = _combo(list(self.grafo.nodos.keys()))
        b_sec = _btn("🔍 Sector O(n)", PURPLE, 28)
        b_sec.clicked.connect(self._buscar_lineal_sec)
        r3.addWidget(self.cb_sec)
        r3.addWidget(b_sec)
        lay.addLayout(r3)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Huffman — Comprimir Texto ──", 9, True, ACCENT))
        r4 = QHBoxLayout()
        self.e_huf = _entry("texto a comprimir…")
        b_huf = _btn("⚡ Comprimir", ACCENT, 28)
        b_huf.clicked.connect(self._run_huffman)
        r4.addWidget(self.e_huf, stretch=1)
        r4.addWidget(b_huf)
        lay.addLayout(r4)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Resultado ──", 9, True, ACCENT))
        self.txt_bus = _textedit()
        lay.addWidget(self.txt_bus, stretch=1)

    # ══ TAB GRAFO ════════════════════════════════════════════

    def _build_tab_grafo(self):
        lay = QVBoxLayout(self.tab_grafo)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        lay.addWidget(_lbl("── Herramientas del Grafo ──", 9, True, ACCENT))

        botones = [
            ("🎨 Coloreo de Grafos (Welsh-Powell)", ACCENT,   self._run_coloreo),
            ("📍 Par de Puntos Más Cercanos",        ACCENT2,  self._run_par_cercano),
            ("📊 Merge Sort Nodos por X",            PURPLE,   self._run_merge_nodos),
            ("🔢 Exponenciación Rápida — demo",      TEXT_DIM, self._run_expo),
        ]
        for txt, col, fn in botones:
            b = _btn(txt, col, 32)
            b.clicked.connect(fn)
            lay.addWidget(b)

        lay.addWidget(_sep())
        self.chk_coloreo = QCheckBox("Mostrar coloreo en el mapa")
        self.chk_coloreo.stateChanged.connect(self._toggle_coloreo)
        lay.addWidget(self.chk_coloreo)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Resultado ──", 9, True, ACCENT))
        self.txt_grafo = _textedit()
        lay.addWidget(self.txt_grafo, stretch=1)

    # ══ TAB CONFIG ═══════════════════════════════════════════

    def _build_tab_config(self):
        lay = QVBoxLayout(self.tab_cfg)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        lay.addWidget(_lbl("── Bloquear Calles ──", 9, True, ACCENT))
        edges = [(a.origen, a.destino) for a in self.grafo._aristas_raw]
        self.cb_blq = _combo([f"{o} ↔ {d}" for o, d in edges])
        lay.addWidget(self.cb_blq)

        bf = QHBoxLayout()
        b_blq = _btn("🚧 Bloquear",    RED_VIF)
        b_des = _btn("✅ Desbloquear", GREEN_VIF)
        b_blq.clicked.connect(self._bloquear)
        b_des.clicked.connect(self._desbloquear)
        bf.addWidget(b_blq)
        bf.addWidget(b_des)
        lay.addLayout(bf)

        lay.addWidget(_lbl("Calles bloqueadas:", 8, False, TEXT_DIM))
        self.lst_blq = QListWidget()
        self.lst_blq.setMaximumHeight(80)
        lay.addWidget(self.lst_blq)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Backtracking — Origen/Destino ──",
                           9, True, ACCENT))
        nids = list(self.grafo.nodos.keys())
        bt_grid = QGridLayout()
        bt_grid.setSpacing(4)
        bt_grid.addWidget(_lbl("Desde:", 8, False, TEXT_DIM), 0, 0)
        self.cb_bt_ini = _combo(nids)
        bt_grid.addWidget(self.cb_bt_ini, 0, 1)
        bt_grid.addWidget(_lbl("Hasta:", 8, False, TEXT_DIM), 1, 0)
        self.cb_bt_fin = _combo(nids)
        self.cb_bt_fin.setCurrentIndex(min(2, len(nids) - 1))
        bt_grid.addWidget(self.cb_bt_fin, 1, 1)
        lay.addLayout(bt_grid)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Ventanas Horarias (Selec. Actividades) ──",
                           9, True, ACCENT))
        lay.addWidget(_lbl(
            "Ventanas demo: pedido i  →  [8+i×0.5 h, 8+i×0.5+1 h]\n"
            "Ej: P001 = 8:00-9:00, P002 = 8:30-9:30…",
            8, False, TEXT_DIM))

        lay.addWidget(_sep())
        # Fuente del grafo
        st = self.grafo.stats() if hasattr(self.grafo, "stats") else {}
        info = (f"Grafo: {st.get('fuente','?').upper()}  |  "
                f"{st.get('nodos', len(self.grafo.nodos))} nodos  |  "
                f"{st.get('aristas','?')} aristas")
        lay.addWidget(_lbl(info, 8, False, TEXT_DIM))

        lay.addStretch()

    # ══ HELPERS ══════════════════════════════════════════════

    def _rep(self) -> Repartidor:
        return self.repartidores[self.cb_rep.currentIndex()]

    def _write(self, widget: QTextEdit, text: str):
        widget.setPlainText(text)

    def _mostrar(self, r):
        """Muestra un ResultadoAlgoritmo en el panel de resultados."""
        noms = " → ".join(
            self.grafo.nodos[n].nombre.split("(")[0].strip()[:14]
            for n in r.ruta if n in self.grafo.nodos
        )
        pids = ", ".join(p.id for p in r.pedidos_incluidos) or "N/A"
        txt = (
            f"{'='*52}\n"
            f"  {r.nombre_algoritmo.upper()}\n"
            f"{'='*52}\n"
            f"  Big-O           : {r.complejidad_big_o}\n"
            f"  Distancia total : {r.distancia_total:.0f} m\n"
            f"  Tiempo de viaje : {r.tiempo_total:.1f} min\n"
            f"  Pedidos         : {pids}\n"
            f"  Valor total     : S/. {r.valor_total:.2f}\n"
            f"  T. cómputo      : {r.tiempo_computo*1000:.2f} ms\n"
            f"\n  Ruta:\n  {noms}\n"
            f"\n  Notas:\n  {r.notas}\n"
            f"{'='*52}\n"
        )
        self._write(self.txt_res, txt)
        self._write(self.txt_resumen,
                    f"{r.nombre_algoritmo}\n"
                    f"Dist: {r.distancia_total:.0f}m | "
                    f"Tiempo: {r.tiempo_total:.1f}min | "
                    f"Big-O: {r.complejidad_big_o}")

    def _actualizar_tabla(self):
        self.table.setRowCount(0)
        for p in self.pedidos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate([
                p.id, p.cliente[:14], p.nodo_destino,
                PRIORIDAD_LABEL[p.prioridad],
                f"{p.peso}kg", f"S/{p.valor}"
            ]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

    # ══ ACCIONES PEDIDOS ═════════════════════════════════════

    def _agregar_pedido(self):
        try:
            cli  = self.e_cli.text().strip() or f"Cliente {self._id_counter}"
            peso = float(self.e_peso.text() or "2")
            vol  = float(self.e_vol.text()  or "4")
            val  = float(self.e_val.text()  or "30")
        except ValueError:
            QMessageBox.critical(self, "Error",
                                 "Peso, Volumen y Valor deben ser números.")
            return
        dest = self.cb_dest.currentText().split("|")[0].strip()
        pri  = Prioridad[self.cb_pri.currentText()]
        pid  = f"P{self._id_counter:03d}"
        self._id_counter += 1
        self.pedidos.append(Pedido(
            id=pid, cliente=cli, nodo_destino=dest,
            peso=peso, volumen=vol, valor=val,
            prioridad=pri, hora_registro=time.time()
        ))
        self._actualizar_tabla()
        self._canvas.update()
        for e in (self.e_cli, self.e_peso, self.e_vol, self.e_val):
            e.clear()

    def _limpiar_pedidos(self):
        if QMessageBox.question(
            self, "Confirmar", "¿Limpiar todos los pedidos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.pedidos.clear()
            self._actualizar_tabla()
            self.actualizar_mapa_interactivo()

    def _ordenar(self, metodo: str):
        antes = [p.id for p in self.pedidos]
        tabla = {
            "bubble":   (lambda: bubble_sort(self.pedidos, "prioridad"),   "O(n²)"),
            "shell":    (lambda: shell_sort(self.pedidos, "prioridad"),    "O(n log² n)"),
            "counting": (lambda: counting_sort_prioridad(self.pedidos),    "O(n + k)"),
            "quick":    (lambda: quick_sort_pedidos(self.pedidos, "prioridad"), "O(n log n)"),
            "heap":     (lambda: heap_sort_pedidos(self.pedidos),          "O(n log n)"),
            "radix":    (lambda: radix_sort_por_valor(self.pedidos),       "O(n·k)"),
        }
        if metodo not in tabla:
            return
        fn, big_o = tabla[metodo]
        self.pedidos = fn()
        self._actualizar_tabla()
        despues = [p.id for p in self.pedidos]
        self._write(self.txt_resumen,
                    f"✅ Ordenado con {metodo.upper()} — {big_o}\n"
                    f"Antes  : {antes}\nDespués: {despues}")

    # ══ ACCIONES ALGORITMOS ══════════════════════════════════

    def _run_greedy(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        r = greedy_vecino_cercano(self.grafo, self._rep(), self.pedidos)
        self._mostrar(r)
        self.actualizar_mapa_interactivo(ruta_nodos_ids=r.ruta)

    def _run_mochila_frac(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        r = mochila_fraccionaria(self._rep(), self.pedidos, self.grafo)
        self._mostrar(r)
        self.actualizar_mapa_interactivo(ruta_nodos_ids=r.ruta)

    def _run_dyv(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        rs = divide_y_venceras(self.grafo, self.repartidores, self.pedidos)
        ruta_completa = []
        for r in rs:
            ruta_completa.extend(r.ruta)
            
        self.actualizar_mapa_interactivo(ruta_nodos_ids=ruta_completa)
        self._write(self.txt_res, comparar_algoritmos(rs))
        self._write(self.txt_resumen,
                    f"D&V — {len(rs)} zona(s) | "
                    f"{sum(len(r.pedidos_incluidos) for r in rs)} pedidos")

    def _run_backtracking(self):
        ini = self.cb_bt_ini.currentText()
        fin = self.cb_bt_fin.currentText()
        if ini == fin:
            return QMessageBox.warning(self, "", "Inicio y destino deben ser distintos.")
        # Sugerir destino con pedido si el actual no tiene
        destinos_con_pedido = {p.nodo_destino for p in self.pedidos if not p.entregado}
        if fin not in destinos_con_pedido and destinos_con_pedido:
            sugerido = next(iter(destinos_con_pedido))
            resp = QMessageBox.question(
                self, "Destino sin pedido",
                f"'{fin}' no tiene pedidos pendientes.\n"
                f"¿Usar '{sugerido}' en su lugar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp == QMessageBox.StandardButton.Yes:
                fin = sugerido

        self._write(self.txt_res, "⏳ Backtracking en ejecución…")

        _ini, _fin = ini, fin
        def _fn():
            return backtracking_rutas_restringidas(
                self.grafo, _ini, _fin, list(self._bloqueadas), 30)

        self._worker = _Worker(_fn)
        self._worker.finished.connect(lambda r: (
            self._mostrar(r),
            self._canvas.set_rutas([r.ruta], [ALGO_COLORES["Backtracking"]])
        ))
        self._worker.start()

    def _run_seleccion_act(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        ventanas = [(p.id, 8.0 + i * 0.5, 8.0 + i * 0.5 + 1.0)
                    for i, p in enumerate(self.pedidos)]
        sel = seleccion_actividades(self.pedidos, ventanas)
        lineas = [
            "SELECCIÓN DE ACTIVIDADES — O(n log n)",
            "Ordenar por hora fin, elegir sin solapamiento.", "",
            f"Total pedidos : {len(self.pedidos)}",
            f"Seleccionados : {len(sel)}", "",
            "Pedidos seleccionados:"
        ]
        for p in sel:
            v = next(x for x in ventanas if x[0] == p.id)
            lineas.append(f"  • {p.id} | {p.cliente} | {v[1]:.1f}h–{v[2]:.1f}h")
        self._write(self.txt_res, "\n".join(lineas))
        self._write(self.txt_resumen,
                    f"Selección actividades: {len(sel)}/{len(self.pedidos)}")

    def _run_subset_sum(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        rep = self._rep()
        encontrado, sub = subset_sum_carga_exacta(
            self.pedidos, rep.capacidad_peso)
        lineas = [
            "SUBSET SUM — CARGA EXACTA  O(n·W)",
            f"Capacidad objetivo: {rep.capacidad_peso} kg",
            f"Repartidor: {rep.nombre}", "",
        ]
        if encontrado:
            lineas += [
                "✅ Subconjunto encontrado — carga perfecta.",
                f"Pedidos: {[p.id for p in sub]}",
                f"Pesos  : {[p.peso for p in sub]}",
                f"Total  : {sum(p.peso for p in sub):.1f} kg",
            ]
        else:
            lineas.append("❌ No existe subconjunto con ese peso exacto.")
        self._write(self.txt_res, "\n".join(lineas))
        self._write(self.txt_resumen,
                    f"Subset Sum: {'encontrado' if encontrado else 'no encontrado'}")

    def _comparar(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        self._write(self.txt_res, "⏳ Comparando todos los algoritmos…")

        rep = self._rep()
        bloq = list(self._bloqueadas)
        destinos = [p.nodo_destino for p in self.pedidos if not p.entregado]
        fin_bt = destinos[0] if destinos else list(self.grafo.nodos.keys())[2]

        def _fn():
            r_g   = greedy_vecino_cercano(self.grafo, rep, self.pedidos)
            r_f   = mochila_fraccionaria(rep, self.pedidos, self.grafo)
            r_d   = divide_y_venceras(self.grafo, self.repartidores, self.pedidos)
            r_bt  = backtracking_rutas_restringidas(
                self.grafo, "DEPOSITO", fin_bt, bloq, 20)
            return [r_g, r_f] + r_d + [r_bt]

        def _on_done(todos):
            texto   = comparar_algoritmos(todos)
            rutas   = [r.ruta for r in todos if r.ruta]
            colores = [ALGO_COLORES.get(r.nombre_algoritmo, ACCENT)
                       for r in todos if r.ruta]
            self._canvas.set_rutas(rutas, colores)
            self._write(self.txt_res, texto)
            self._write(self.txt_resumen, "✅ Comparación completa")

        self._worker = _Worker(_fn)
        self._worker.finished.connect(_on_done)
        self._worker.start()

    # ══ ACCIONES BÚSQUEDA ════════════════════════════════════

    def _buscar_binaria(self):
        pid = self.e_bid.text().strip()
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
        self._write(self.txt_bus, txt)

    def _buscar_lineal_cli(self):
        termino = self.e_bcli.text().strip()
        rs  = busqueda_lineal_cliente(self.pedidos, termino)
        txt = f"🔍 Búsqueda Lineal por cliente — O(n)\nTérmino: '{termino}'\n\n"
        txt += "\n".join(
            f"  • {p.id} | {p.cliente} | {p.nodo_destino} | S/.{p.valor}"
            for p in rs
        ) if rs else "❌ Sin resultados."
        self._write(self.txt_bus, txt)

    def _buscar_lineal_sec(self):
        sec = self.cb_sec.currentText()
        rs  = busqueda_lineal_sector(self.pedidos, sec)
        txt = f"🗺 Búsqueda por sector — O(n)\nSector: {sec}\n\n"
        txt += "\n".join(
            f"  • {p.id} | {p.cliente} | {PRIORIDAD_LABEL[p.prioridad]}"
            for p in rs
        ) if rs else "ℹ Sin pedidos en este sector."
        self._write(self.txt_bus, txt)

    def _run_huffman(self):
        texto = self.e_huf.text().strip()
        if not texto:
            texto = " ".join(p.cliente for p in self.pedidos[:3])
        self._write(self.txt_bus, demo_huffman(texto))

    # ══ ACCIONES GRAFO ════════════════════════════════════════

    def _run_coloreo(self):
        coloreo = self.grafo.obtener_coloreo(recalcular=True)
        grupos  = self.grafo.nodos_por_color()
        n_col   = len(set(coloreo.values()))
        lineas  = [
            "COLOREO DE GRAFOS — Welsh-Powell  O(V²+E)",
            f"Nodos: {len(coloreo)} | Colores: {n_col}",
            "Garantía: nodos adyacentes con colores distintos.", "",
        ]
        for color, nids in sorted(grupos.items()):
            lineas.append(f"  Color {color}: {nids}")
        lineas += [
            "",
            "Aplicación: asignar repartidores a zonas sin solapamiento.",
            "  R1 → Color 0  |  R2 → Color 1  |  R3 → Color 2",
        ]
        self._write(self.txt_grafo, "\n".join(lineas))
        self.chk_coloreo.setChecked(True)
        self._canvas.set_coloreo(True, coloreo)

    def _run_par_cercano(self):
        ids = list({p.nodo_destino for p in self.pedidos})
        if len(ids) < 2:
            ids = list(self.grafo.nodos.keys())
        dist, a, b = self.grafo.par_nodos_mas_cercanos(ids)
        na = self.grafo.nodos[a].nombre
        nb = self.grafo.nodos[b].nombre
        lineas = [
            "PAR DE PUNTOS MÁS CERCANOS — O(n log n)",
            "Divide y Vencerás geométrico.", "",
            f"Par más cercano:",
            f"  {a}: {na}",
            f"  {b}: {nb}",
            f"  Dist. canvas: {dist:.1f} px",
            f"  Dist. real  : {self.grafo.distancia_directa(a, b):.0f} m", "",
            "Uso: punto de partida óptimo para el repartidor.",
        ]
        self._write(self.txt_grafo, "\n".join(lineas))
        self._canvas.set_par_cercano(a, b)

    def _run_merge_nodos(self):
        ordenados = self.grafo.nodos_ordenados_por("x")
        lineas = [
            "MERGE SORT de Nodos por coordenada X — O(n log n)", "",
            f"{'Nodo':<16} {'X':>5} {'Y':>5}  Zona",
            "─" * 40,
        ]
        for n in ordenados:
            zona = next((z for z, ids in ZONAS.items() if n.id in ids), "?")
            lineas.append(f"  {n.id:<14} {n.x:>5}  {n.y:>5}  {zona}")
        self._write(self.txt_grafo, "\n".join(lineas))

    def _run_expo(self):
        try:
            from grafo_osm import expo_rapida, penalizacion_distancia
        except ImportError:
            from grafo_osm import expo_rapida, penalizacion_distancia
        lineas = [
            "EXPONENCIACIÓN RÁPIDA — O(log e)",
            "Square-and-multiply: log(e) multiplicaciones.", "",
            f"  {'Tramos':<8} {'Factor':>12} {'Base 1000m':>12} {'Con penal.':>12}",
            "─" * 50,
        ]
        for t in [1, 2, 5, 10, 20, 50]:
            factor = expo_rapida(1.0001, t)
            con_p  = penalizacion_distancia(1000.0, 1.0001, t)
            lineas.append(
                f"  {t:<8} {factor:>12.6f} {1000.0:>12.1f} {con_p:>12.2f}")
        lineas += [
            "",
            "Rutas con más tramos acumulan penalización suave",
            "que favorece caminos directos sobre rodeos.",
        ]
        self._write(self.txt_grafo, "\n".join(lineas))

    def _toggle_coloreo(self, state: int):
        self._coloreo_on = bool(state)
        if self._coloreo_on:
            coloreo = self.grafo.obtener_coloreo()
            self._canvas.set_coloreo(True, coloreo)
        else:
            self._canvas.set_coloreo(False, {})

    # ══ ACCIONES CONFIG ═══════════════════════════════════════

    def _bloquear(self):
        val   = self.cb_blq.currentText()
        parts = [p.strip() for p in val.split("↔")]
        if len(parts) == 2:
            par = (parts[0], parts[1])
            if par not in self._bloqueadas:
                self._bloqueadas.append(par)
                self.grafo.bloquear_calle(*par)
                self.lst_blq.addItem(f"{par[0]} ↔ {par[1]}")
                self._canvas.update()

    def _desbloquear(self):
        val   = self.cb_blq.currentText()
        parts = [p.strip() for p in val.split("↔")]
        if len(parts) == 2:
            par = (parts[0], parts[1])
            if par in self._bloqueadas:
                self._bloqueadas.remove(par)
                self.grafo.desbloquear_calle(*par)
                # Actualizar lista visual
                items = [self.lst_blq.item(i).text()
                         for i in range(self.lst_blq.count())]
                self.lst_blq.clear()
                for item in items:
                    if item != f"{par[0]} ↔ {par[1]}":
                        self.lst_blq.addItem(item)
                self._canvas.update()





    def actualizar_mapa_interactivo(self, ruta_nodos_ids=None):
        """Genera un mapa con Folium y lo renderiza de manera interactiva en la UI."""
        # Creamos el mapa centrado en San Sebastián, Cusco (Coordenadas reales de tu proyecto)
        mapa = folium.Map(location=[-13.528, -71.927], zoom_start=14, tiles="OpenStreetMap")
        
        # 1. Pintar un marcador azul para el depósito central
        folium.Marker(
            location=[-13.5222, -71.9392], # Coordenada aproximada del Depósito Av. Cultura
            popup="<b>DEPOSITÓ CENTRAL</b>",
            icon=folium.Icon(color="darkblue", icon="home")
        ).add_to(mapa)

        # 2. Pintar tus pedidos actuales de la tabla como marcadores interactivos
        for pedido in self.pedidos:
            if pedido.nodo_destino in self.grafo.nodos:
                nodo_data = self.grafo.nodos[pedido.nodo_destino]
                # Tu clase Nodo almacena las coordenadas reales en lat y lon
                lat, lon = nodo_data.lat, nodo_data.lon 
                
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>Pedido:</b> {pedido.id}<br><b>Cliente:</b> {pedido.cliente}<br><b>Prioridad:</b> {pedido.prioridad.name}",
                    icon=folium.Icon(color="orange" if pedido.prioridad.value <= 2 else "green", icon="envelope")
                ).add_to(mapa)

        # 3. Si un algoritmo calcula una ruta, la dibujamos encima de las calles exactas de San Sebastián
        if ruta_nodos_ids:
            puntos_calle = []
            for nid in ruta_nodos_ids:
                if nid in self.grafo.nodos:
                    puntos_calle.append([self.grafo.nodos[nid].lat, self.grafo.nodos[nid].lon])
            
            if puntos_calle:
                # Trazamos la polilínea vectorial en azul fluorescente de 5 píxeles de grosor
                folium.PolyLine(
                    locations=puntos_calle,
                    color="#1e90ff",
                    weight=6,
                    opacity=0.85,
                    popup="Ruta de Despacho Óptima"
                ).add_to(mapa)

        # 4. Exportar y leer en memoria
        ruta_html = os.path.abspath("mapa_interactivo_temp.html")
        mapa.save(ruta_html)
        

        with open(ruta_html, 'r', encoding='utf-8') as f:
            html_crudo = f.read()
            
        self.web_view.setHtml(html_crudo)
# ─────────────────────────── Punto de entrada ────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rutas Óptimas — San Sebastián")
    window = App()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    
