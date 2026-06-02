"""
gui_pyqt.py — Interfaz Gráfica PyQt6
Sistema de Gestión de Rutas Óptimas — San Sebastián, Cusco
Programación III — UNSAAC 2026
"""

import os
import sys
import time
import math
import traceback
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import folium
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QListWidget, QMessageBox, QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

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

# ─────────────────────────── Paleta ──────────────────────────────────────────
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

ALGO_COLORES = {
    "Greedy Vecino Más Cercano": "#f5a623",
    "Mochila Fraccionaria":      "#1abc9c",
    "Divide y Vencerás":         "#4ecdc4",
    "Backtracking":              "#e74c3c",
}

GLOBAL_STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {BG_DARK}; color: {TEXT_MAIN};
}}
QTabWidget::pane {{ border: none; background: {BG_PANEL}; }}
QTabBar::tab {{
    background: {BG_CARD}; color: {TEXT_DIM};
    font-family: 'Courier New'; font-size: 8pt; font-weight: bold;
    padding: 5px 10px; border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    background: {BG_DARK}; color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{ color: {TEXT_MAIN}; }}
QScrollBar:vertical {{
    background: {BG_CARD}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #3d4460; border-radius: 4px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QTableWidget {{
    background: {BG_CARD}; color: {TEXT_MAIN};
    gridline-color: #2d3748; border: none;
    font-family: 'Courier New'; font-size: 8pt;
}}
QTableWidget::item:selected {{ background: {ACCENT}; color: {BG_DARK}; }}
QHeaderView::section {{
    background: {BG_DARK}; color: {ACCENT};
    font-family: 'Courier New'; font-size: 8pt; font-weight: bold;
    padding: 4px; border: none; border-bottom: 1px solid #2d3748;
}}
QListWidget {{
    background: {BG_CARD}; color: {RED_VIF};
    border: none; font-family: 'Courier New'; font-size: 8pt;
}}
QCheckBox {{
    color: {TEXT_MAIN}; font-family: 'Courier New'; font-size: 8pt;
}}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid #3d4460; border-radius: 2px; background: {BG_CARD};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QSplitter::handle {{ background: {BG_CARD}; width: 3px; height: 3px; }}
"""

# ─────────────────────────── Widget helpers ───────────────────────────────────

def _btn(text, color=ACCENT, min_h=30):
    b = QPushButton(text)
    b.setMinimumHeight(min_h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {color}; color: {BG_DARK};
            border: none; border-radius: 4px; padding: 4px 10px;
            font-family: 'Courier New'; font-size: 9pt; font-weight: bold;
        }}
        QPushButton:hover {{ background: #aabbcc; color: #111; }}
        QPushButton:pressed {{ background: {color}; opacity: 0.7; }}
    """)
    return b

def _lbl(text, size=9, bold=False, color=TEXT_MAIN):
    l = QLabel(text)
    l.setStyleSheet(
        f"color:{color}; font-family:'Courier New'; font-size:{size}pt;"
        f"{'font-weight:bold;' if bold else ''} background:transparent;"
    )
    return l

def _entry(ph=""):
    e = QLineEdit()
    e.setPlaceholderText(ph)
    e.setStyleSheet(f"""
        QLineEdit {{
            background:{BG_CARD}; color:{TEXT_MAIN};
            border:1px solid #2d3748; border-radius:3px;
            padding:4px 6px; font-family:'Courier New'; font-size:9pt;
        }}
        QLineEdit:focus {{ border:1px solid {ACCENT}; }}
    """)
    return e

def _combo(items):
    c = QComboBox()
    c.addItems(items)
    c.setStyleSheet(f"""
        QComboBox {{
            background:{BG_CARD}; color:{TEXT_MAIN};
            border:1px solid #2d3748; border-radius:3px;
            padding:3px 6px; font-family:'Courier New'; font-size:8pt;
        }}
        QComboBox::drop-down {{ border:none; }}
        QComboBox QAbstractItemView {{
            background:{BG_CARD}; color:{TEXT_MAIN};
            selection-background-color:{ACCENT}; selection-color:{BG_DARK};
        }}
    """)
    return c

def _textedit():
    t = QTextEdit()
    t.setReadOnly(True)
    t.setFont(QFont("Courier New", 8))
    t.setStyleSheet(f"""
        QTextEdit {{
            background:{BG_CARD}; color:{TEXT_MAIN};
            border:none; border-radius:4px; padding:6px;
        }}
    """)
    return t

def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color:{BG_CARD}; margin:4px 0;")
    return f

# ─────────────────────────── Worker thread ───────────────────────────────────

class _Worker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.finished.emit(self._fn())
        except Exception:
            self.error.emit(traceback.format_exc())

# ─────────────────────────── Servidor HTTP para clics del mapa ───────────────

_app_instance = None

class _MapHandler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")

        if not _app_instance:
            return

        accion = parsed.path          # /set_deposito | /add_pedido | /set_bt_ini | /set_bt_fin
        lat_s  = params.get("lat", [None])[0]
        lon_s  = params.get("lon", [None])[0]
        if lat_s is None or lon_s is None:
            return

        lat = float(lat_s)
        lon = float(lon_s)
        QTimer.singleShot(0, lambda: _app_instance._mapa_click(accion, lat, lon))


def _iniciar_servidor_mapa():
    try:
        srv = HTTPServer(("localhost", 9999), _MapHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
    except OSError:
        pass   # puerto ya en uso


# JavaScript que inyectamos en el mapa para capturar clics
_JS_CLICK = """
<script>
(function() {
    var _modo = 'pedido';   // modo por defecto
    window._setModoMapa = function(m) { _modo = m; };

    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            // Encontrar el objeto mapa de Leaflet
            for (var key in window) {
                try {
                    var obj = window[key];
                    if (obj && typeof obj.on === 'function' && obj._container) {
                        obj.on('click', function(e) {
                            var lat = e.latlng.lat.toFixed(7);
                            var lon = e.latlng.lng.toFixed(7);
                            var url = 'http://localhost:9999/' + _modo
                                    + '?lat=' + lat + '&lon=' + lon;
                            fetch(url).catch(function(){});
                        });
                    }
                } catch(err) {}
            }
        }, 1000);
    });
})();
</script>
"""

# ─────────────────────────── Página Web con interceptor ──────────────────────

class _WebPage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def javaScriptConsoleMessage(self, level, msg, line, src):
        pass   # silenciar errores JS en consola


# ─────────────────────────── Ventana principal ───────────────────────────────

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rutas Óptimas — San Sebastián, Cusco  |  UNSAAC 2026")
        self.showMaximized()

        # Datos
        self.grafo         = GrafoSanSebastian()
        self.pedidos: list[Pedido]          = []
        self.repartidores: list[Repartidor] = self._crear_repartidores()
        self._id_counter   = 1
        self._bloqueadas: list[tuple[str, str]] = []
        self._coloreo_on   = False
        self._modo_mapa    = "pedido"   # pedido | deposito | bt_ini | bt_fin
        self._worker       = None

        global _app_instance
        _app_instance = self
        _iniciar_servidor_mapa()

        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._build_ui()
        self._cargar_demo()
        # El mapa se carga en _build_ui → actualizar_mapa_interactivo()

    # ── Datos iniciales ──────────────────────────────────────

    def _crear_repartidores(self):
        dep = next((n for n in self.grafo.nodos.values() if n.es_deposito), None)
        nid_dep = dep.id if dep else list(self.grafo.nodos.keys())[0]
        return [
            Repartidor("R1", "Carlos Quispe", nid_dep, 30.0, 60.0, 25.0),
            Repartidor("R2", "Ana Huanca",    nid_dep, 25.0, 50.0, 25.0),
            Repartidor("R3", "Luis Ccopa",    nid_dep, 20.0, 40.0, 20.0),
        ]

    def _cargar_demo(self):
        import random
        nids = [n for n in self.grafo.nodos if not self.grafo.nodos[n].es_deposito]
        if not nids:
            return
        demos = [
            ("P001", "Farmacia San Sebastián",  random.choice(nids), 1.5,  3.0,  45.0, Prioridad.URGENTE),
            ("P002", "Abastos Central",          random.choice(nids), 3.0,  8.0,  30.0, Prioridad.ALTA),
            ("P003", "Accesorios Cachimayo",     random.choice(nids), 8.0,  15.0, 80.0, Prioridad.NORMAL),
            ("P004", "Vivanderas Enaco",         random.choice(nids), 2.0,  5.0,  25.0, Prioridad.NORMAL),
            ("P005", "Urb. Túpac Amaru",         random.choice(nids), 5.0,  10.0, 60.0, Prioridad.BAJA),
        ]
        for id_, cli, nodo, peso, vol, val, pri in demos:
            self.pedidos.append(Pedido(
                id=id_, cliente=cli, nodo_destino=nodo,
                peso=peso, volumen=vol, valor=val,
                prioridad=pri, hora_registro=time.time()
            ))
        self._actualizar_tabla()

    # ── Layout principal ─────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        root.addWidget(splitter)

        # Panel izquierdo (sidebar)
        sidebar = QWidget()
        sidebar.setFixedWidth(420)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"#sidebar {{ background:{BG_PANEL}; border-radius:6px; }}")
        splitter.addWidget(sidebar)
        self._build_sidebar(sidebar)

        # Panel derecho (mapa + resultados)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        splitter.addWidget(right)

        # ── Mapa Folium ────────────────────────────────────────
        self.web_view = QWebEngineView()
        page = _WebPage(self.web_view)
        self.web_view.setPage(page)
        s = self.web_view.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        right_layout.addWidget(self.web_view, stretch=3)

        # ── Barra de modo de clic ──────────────────────────────
        modo_bar = QWidget()
        modo_bar.setStyleSheet(f"background:{BG_PANEL}; border-radius:4px; padding:2px;")
        mb_lay = QHBoxLayout(modo_bar)
        mb_lay.setContentsMargins(6, 4, 6, 4)
        mb_lay.addWidget(_lbl("🖱 Clic en mapa:", 8, True, ACCENT))
        self._modo_btns = {}
        for clave, label, color in [
            ("pedido",   "📦 Añadir Pedido",   ACCENT2),
            ("deposito", "🏭 Fijar Depósito",  ACCENT),
            ("bt_ini",   "▶ Inicio BT",        BLUE),
            ("bt_fin",   "⏹ Destino BT",       RED_VIF),
        ]:
            b = _btn(label, color, 24)
            b.setCheckable(True)
            b.clicked.connect(lambda checked, k=clave: self._cambiar_modo_mapa(k))
            self._modo_btns[clave] = b
            mb_lay.addWidget(b)
        mb_lay.addStretch()
        right_layout.addWidget(modo_bar)

        # ── Panel resultados ───────────────────────────────────
        res_frame = QWidget()
        res_frame.setStyleSheet(f"background:{BG_PANEL}; border-radius:6px;")
        res_layout = QVBoxLayout(res_frame)
        res_layout.setContentsMargins(8, 6, 8, 6)
        res_layout.addWidget(_lbl("📋  Resultados y Análisis Big-O", 10, True, ACCENT))
        self.txt_res = _textedit()
        res_layout.addWidget(self.txt_res)
        right_layout.addWidget(res_frame, stretch=2)

        splitter.setSizes([420, 900])

        # Ahora que txt_res ya existe, activar modo inicial y cargar mapa
        self._cambiar_modo_mapa("pedido")
        self.actualizar_mapa_interactivo()

    # ── Sidebar ──────────────────────────────────────────────

    def _build_sidebar(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = QWidget()
        header.setStyleSheet(f"background:{BG_DARK}; border-radius:4px; padding:4px;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(8, 6, 8, 6)
        t = _lbl("🚚  RUTAS ÓPTIMAS", 13, True, ACCENT)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(t)
        s = _lbl("San Sebastián · Cusco · UNSAAC 2026", 8, False, TEXT_DIM)
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(s)
        layout.addWidget(header)

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
        lay.addWidget(_lbl(
            "💡 Haz clic en el mapa con modo '📦 Añadir Pedido' para\n"
            "   asignar la ubicación, o elige el destino manualmente.",
            7, False, TEXT_DIM))

        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (lbl_txt, ph) in enumerate([
            ("Cliente:", ""), ("Peso kg:", "2.0"),
            ("Vol L:",   "4.0"), ("Valor S/.:", "30.0")
        ]):
            grid.addWidget(_lbl(lbl_txt, 8, False, TEXT_DIM), i, 0)
            e = _entry(ph)
            grid.addWidget(e, i, 1)
        self.e_cli  = grid.itemAtPosition(0,1).widget()
        self.e_peso = grid.itemAtPosition(1,1).widget()
        self.e_vol  = grid.itemAtPosition(2,1).widget()
        self.e_val  = grid.itemAtPosition(3,1).widget()

        nids = [n for n in self.grafo.nodos if not self.grafo.nodos[n].es_deposito]
        grid.addWidget(_lbl("Destino:", 8, False, TEXT_DIM), 4, 0)
        self.cb_dest = _combo(
            [f"{n} | {self.grafo.nodos[n].nombre[:30]}" for n in nids])
        grid.addWidget(self.cb_dest, 4, 1)

        grid.addWidget(_lbl("Prioridad:", 8, False, TEXT_DIM), 5, 0)
        self.cb_pri = _combo(["URGENTE", "ALTA", "NORMAL", "BAJA"])
        self.cb_pri.setCurrentIndex(2)
        grid.addWidget(self.cb_pri, 5, 1)
        lay.addLayout(grid)

        # Destino desde clic (label de estado)
        self.lbl_dest_clic = _lbl("", 7, False, ACCENT2)
        lay.addWidget(self.lbl_dest_clic)

        bf = QHBoxLayout()
        b_add = _btn("➕ Agregar", ACCENT)
        b_cls = _btn("🗑 Limpiar", RED_VIF)
        b_add.clicked.connect(self._agregar_pedido)
        b_cls.clicked.connect(self._limpiar_pedidos)
        bf.addWidget(b_add); bf.addWidget(b_cls)
        lay.addLayout(bf)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Ordenar Pedidos ──", 9, True, ACCENT))

        sort_grid = QGridLayout()
        sort_grid.setSpacing(3)
        sorts = [
            ("Bubble O(n²)",     ACCENT2, lambda: self._ordenar("bubble")),
            ("Shell O(n log²n)", PURPLE,  lambda: self._ordenar("shell")),
            ("Counting O(n+k)",  ACCENT2, lambda: self._ordenar("counting")),
            ("Quick O(n log n)", PURPLE,  lambda: self._ordenar("quick")),
            ("Heap O(n log n)",  ACCENT2, lambda: self._ordenar("heap")),
            ("Radix O(n·k)",     PURPLE,  lambda: self._ordenar("radix")),
        ]
        for i, (txt, col, fn) in enumerate(sorts):
            b = _btn(txt, col, 26); b.clicked.connect(fn)
            sort_grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(sort_grid)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Lista de Pedidos ──", 9, True, ACCENT))
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Cliente", "Destino", "Prior.", "Peso", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, stretch=1)

    # ══ TAB ALGORITMOS ═══════════════════════════════════════

    def _build_tab_algoritmos(self):
        lay = QVBoxLayout(self.tab_alg)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        lay.addWidget(_lbl("── Repartidor ──", 9, True, ACCENT))
        self.cb_rep = _combo([f"{r.id} – {r.nombre}" for r in self.repartidores])
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
            b = _btn(txt, col, 32); b.clicked.connect(fn)
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
        r1.addWidget(self.e_bid); r1.addWidget(b_bin)
        lay.addLayout(r1)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Búsqueda Lineal por Cliente ──", 9, True, ACCENT))
        r2 = QHBoxLayout()
        self.e_bcli = _entry("nombre...")
        b_cli = _btn("🔍 Lineal O(n)", ACCENT2, 28)
        b_cli.clicked.connect(self._buscar_lineal_cli)
        r2.addWidget(self.e_bcli); r2.addWidget(b_cli)
        lay.addLayout(r2)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Búsqueda por Sector ──", 9, True, ACCENT))
        r3 = QHBoxLayout()
        self.cb_sec = _combo(list(self.grafo.nodos.keys()))
        b_sec = _btn("🔍 Sector O(n)", PURPLE, 28)
        b_sec.clicked.connect(self._buscar_lineal_sec)
        r3.addWidget(self.cb_sec); r3.addWidget(b_sec)
        lay.addLayout(r3)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Huffman — Comprimir Texto ──", 9, True, ACCENT))
        r4 = QHBoxLayout()
        self.e_huf = _entry("texto a comprimir…")
        b_huf = _btn("⚡ Comprimir", ACCENT, 28)
        b_huf.clicked.connect(self._run_huffman)
        r4.addWidget(self.e_huf, stretch=1); r4.addWidget(b_huf)
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
            b = _btn(txt, col, 32); b.clicked.connect(fn)
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
        b_blq = _btn("🚧 Bloquear", RED_VIF)
        b_des = _btn("✅ Desbloquear", GREEN_VIF)
        b_blq.clicked.connect(self._bloquear)
        b_des.clicked.connect(self._desbloquear)
        bf.addWidget(b_blq); bf.addWidget(b_des)
        lay.addLayout(bf)

        lay.addWidget(_lbl("Calles bloqueadas:", 8, False, TEXT_DIM))
        self.lst_blq = QListWidget()
        self.lst_blq.setMaximumHeight(80)
        lay.addWidget(self.lst_blq)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Backtracking — Origen/Destino ──", 9, True, ACCENT))
        lay.addWidget(_lbl(
            "💡 También puedes usar los botones '▶ Inicio BT' y '⏹ Destino BT'\n"
            "   haciendo clic directamente en el mapa.", 7, False, TEXT_DIM))

        nids = list(self.grafo.nodos.keys())
        bt_grid = QGridLayout()
        bt_grid.addWidget(_lbl("Desde:", 8, False, TEXT_DIM), 0, 0)
        self.cb_bt_ini = _combo(nids)
        bt_grid.addWidget(self.cb_bt_ini, 0, 1)
        bt_grid.addWidget(_lbl("Hasta:", 8, False, TEXT_DIM), 1, 0)
        self.cb_bt_fin = _combo(nids)
        self.cb_bt_fin.setCurrentIndex(min(2, len(nids)-1))
        bt_grid.addWidget(self.cb_bt_fin, 1, 1)
        lay.addLayout(bt_grid)

        lay.addWidget(_sep())
        st = self.grafo.stats()
        info = (f"Fuente: {st.get('fuente','?').upper()}  |  "
                f"{st.get('nodos',0)} nodos  |  {st.get('aristas','?')} aristas\n"
                f"Zona: San Sebastián, Cusco")
        lay.addWidget(_lbl(info, 8, False, TEXT_DIM))
        lay.addStretch()

    # ══ HELPERS ══════════════════════════════════════════════

    def _rep(self) -> Repartidor:
        return self.repartidores[self.cb_rep.currentIndex()]

    def _write(self, widget, text):
        widget.setPlainText(text)

    def _mostrar(self, r):
        noms = " → ".join(
            self.grafo.nodos[n].nombre.split("(")[0].strip()[:14]
            for n in r.ruta if n in self.grafo.nodos
        )
        pids = ", ".join(p.id for p in r.pedidos_incluidos) or "N/A"
        txt = (
            f"{'='*52}\n  {r.nombre_algoritmo.upper()}\n{'='*52}\n"
            f"  Big-O           : {r.complejidad_big_o}\n"
            f"  Distancia total : {r.distancia_total:.0f} m\n"
            f"  Tiempo de viaje : {r.tiempo_total:.1f} min\n"
            f"  Pedidos         : {pids}\n"
            f"  Valor total     : S/. {r.valor_total:.2f}\n"
            f"  T. cómputo      : {r.tiempo_computo*1000:.2f} ms\n"
            f"\n  Ruta ({len(r.ruta)} nodos):\n  {noms}\n"
            f"\n  Notas:\n  {r.notas}\n{'='*52}\n"
        )
        self._write(self.txt_res, txt)
        self._write(self.txt_resumen,
                    f"{r.nombre_algoritmo}\n"
                    f"Dist: {r.distancia_total:.0f}m | "
                    f"Tiempo: {r.tiempo_total:.1f}min | Big-O: {r.complejidad_big_o}")

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

    def _cambiar_modo_mapa(self, modo: str):
        self._modo_mapa = modo
        for k, b in self._modo_btns.items():
            b.setChecked(k == modo)
        # Inyectar JS al mapa para que sepa el modo actual
        self.web_view.page().runJavaScript(
            f"if(typeof window._setModoMapa==='function') window._setModoMapa('{modo}');")
        modos_label = {
            "pedido":   "📦 Clic en el mapa para añadir pedido",
            "deposito": "🏭 Clic en el mapa para fijar depósito",
            "bt_ini":   "▶ Clic en el mapa para fijar inicio Backtracking",
            "bt_fin":   "⏹ Clic en el mapa para fijar destino Backtracking",
        }
        self._write(self.txt_res, modos_label.get(modo, ""))

    # ── Acción al hacer clic en el mapa ──────────────────────

    def _mapa_click(self, accion: str, lat: float, lon: float):
        nid = self.grafo.nodo_mas_cercano_a(lat, lon)
        nodo = self.grafo.nodos.get(nid)
        if not nodo:
            return

        if accion == "/set_deposito" or accion == "/deposito":
            # Actualizar depósito
            for n in self.grafo.nodos.values():
                object.__setattr__(n, "es_deposito", False)
            object.__setattr__(nodo, "es_deposito", True)
            for r in self.repartidores:
                r.nodo_actual = nid
            self._write(self.txt_res,
                        f"✅ Depósito fijado en:\n  {nid}\n  {nodo.nombre}\n"
                        f"  ({nodo.lat:.5f}, {nodo.lon:.5f})")
            self.actualizar_mapa_interactivo()

        elif accion == "/add_pedido" or accion == "/pedido":
            # Pre-seleccionar destino en el combo
            for i in range(self.cb_dest.count()):
                if self.cb_dest.itemText(i).startswith(nid):
                    self.cb_dest.setCurrentIndex(i)
                    break
            self.lbl_dest_clic.setText(
                f"📍 Destino seleccionado: {nid} — {nodo.nombre[:35]}")
            self._write(self.txt_res,
                        f"📍 Nodo seleccionado como destino:\n  {nid}\n  {nodo.nombre}\n"
                        f"  Completa los datos y pulsa ➕ Agregar.")

        elif accion == "/bt_ini" or accion == "/set_bt_ini":
            idx = self.cb_bt_ini.findText(nid)
            if idx >= 0:
                self.cb_bt_ini.setCurrentIndex(idx)
            self._write(self.txt_res, f"▶ Inicio Backtracking: {nid}\n  {nodo.nombre}")

        elif accion == "/bt_fin" or accion == "/set_bt_fin":
            idx = self.cb_bt_fin.findText(nid)
            if idx >= 0:
                self.cb_bt_fin.setCurrentIndex(idx)
            self._write(self.txt_res, f"⏹ Destino Backtracking: {nid}\n  {nodo.nombre}")

    # ══ MAPA FOLIUM ══════════════════════════════════════════

    def actualizar_mapa_interactivo(self, rutas=None, coloreo=None,
                                     par_cercano=None):
        """Genera el mapa Folium con todos los elementos y lo carga en QWebEngineView."""
        # Centro del mapa en el depósito
        dep = next((n for n in self.grafo.nodos.values() if n.es_deposito), None)
        centro = [dep.lat, dep.lon] if dep else [-13.528, -71.927]

        mapa = folium.Map(
            location=centro,
            zoom_start=14,
            tiles="OpenStreetMap",
        )

        # ── Depósito ─────────────────────────────────────────
        if dep:
            folium.Marker(
                location=[dep.lat, dep.lon],
                popup=folium.Popup(
                    f"<b>🏭 DEPÓSITO</b><br>{dep.nombre}", max_width=200),
                icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
                tooltip="🏭 Depósito",
            ).add_to(mapa)

        # ── Pedidos ───────────────────────────────────────────
        for p in self.pedidos:
            nd = self.grafo.nodos.get(p.nodo_destino)
            if nd:
                color_p = "red" if p.prioridad.value <= 2 else "orange"
                folium.Marker(
                    location=[nd.lat, nd.lon],
                    popup=folium.Popup(
                        f"<b>📦 {p.id}</b><br>"
                        f"Cliente: {p.cliente}<br>"
                        f"Prioridad: {p.prioridad.name}<br>"
                        f"Peso: {p.peso} kg | S/. {p.valor}",
                        max_width=220),
                    tooltip=f"{p.id} — {p.cliente[:18]}",
                    icon=folium.Icon(color=color_p, icon="envelope", prefix="fa"),
                ).add_to(mapa)

        # ── Rutas de algoritmos ───────────────────────────────
        if rutas:
            for item in rutas:
                if isinstance(item, tuple):
                    nids_ruta, color_hex = item
                else:
                    nids_ruta, color_hex = item, "#1e90ff"

                if len(nids_ruta) < 2:
                    continue

                # Obtener coordenadas reales siguiendo las calles (G_geo + geometría)
                puntos = self.grafo.ruta_como_coordenadas(nids_ruta)

                if len(puntos) >= 2:
                    folium.PolyLine(
                        locations=puntos,
                        color=color_hex,
                        weight=6,
                        opacity=0.85,
                        tooltip="Ruta óptima",
                    ).add_to(mapa)
                    # Marcador en el origen
                    folium.CircleMarker(
                        location=puntos[0],
                        radius=8, color="white", fill=True,
                        fill_color=color_hex, fill_opacity=1.0,
                        tooltip="Inicio de ruta",
                    ).add_to(mapa)
                    # Bandera en el destino
                    folium.Marker(
                        location=puntos[-1],
                        icon=folium.DivIcon(
                            html='<div style="font-size:22px;margin-top:-10px">🏁</div>',
                            icon_size=(28, 28),
                        ),
                        tooltip="Fin de ruta",
                    ).add_to(mapa)

        # ── Par de puntos más cercanos ────────────────────────
        if par_cercano:
            a, b = par_cercano
            na, nb = self.grafo.nodos.get(a), self.grafo.nodos.get(b)
            if na and nb:
                folium.PolyLine(
                    locations=[[na.lat, na.lon], [nb.lat, nb.lon]],
                    color="#e74c3c", weight=4, dash_array="8",
                    tooltip=f"Par más cercano: {a} ↔ {b}",
                ).add_to(mapa)
                for nd, lbl in [(na, a), (nb, b)]:
                    folium.CircleMarker(
                        location=[nd.lat, nd.lon],
                        radius=7, color="#e74c3c", fill=True,
                        fill_color="#e74c3c", fill_opacity=0.9,
                        tooltip=lbl,
                    ).add_to(mapa)

        # ── Coloreo de nodos ──────────────────────────────────
        if coloreo:
            _pal = ["red", "blue", "green", "orange", "purple",
                    "cadetblue", "darkred", "darkgreen"]
            for nid, color_idx in coloreo.items():
                nodo = self.grafo.nodos.get(nid)
                if nodo and not nodo.es_deposito:
                    folium.CircleMarker(
                        location=[nodo.lat, nodo.lon],
                        radius=5,
                        color=_pal[color_idx % len(_pal)],
                        fill=True,
                        fill_color=_pal[color_idx % len(_pal)],
                        fill_opacity=0.85,
                        tooltip=f"{nid} — color {color_idx}",
                    ).add_to(mapa)

        # ── Guardar HTML + inyectar JS de clic ───────────────
        ruta_html = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "mapa_interactivo_temp.html"
        )
        mapa.save(ruta_html)

        with open(ruta_html, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("</body>", _JS_CLICK + "</body>")
        with open(ruta_html, "w", encoding="utf-8") as f:
            f.write(html)

        self.web_view.setUrl(QUrl.fromLocalFile(ruta_html))

        # Re-aplicar modo de clic tras cargar el mapa
        QTimer.singleShot(1500, lambda: self.web_view.page().runJavaScript(
            f"if(typeof window._setModoMapa==='function') "
            f"window._setModoMapa('{self._modo_mapa}');"))

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
        self.actualizar_mapa_interactivo()
        for e in (self.e_cli, self.e_peso, self.e_vol, self.e_val):
            e.clear()
        self.lbl_dest_clic.setText("")

    def _limpiar_pedidos(self):
        if QMessageBox.question(
            self, "Confirmar", "¿Limpiar todos los pedidos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.pedidos.clear()
            self._actualizar_tabla()
            self.actualizar_mapa_interactivo()

    def _ordenar(self, metodo):
        antes = [p.id for p in self.pedidos]
        tabla = {
            "bubble":   (lambda: bubble_sort(self.pedidos, "prioridad"),       "O(n²)"),
            "shell":    (lambda: shell_sort(self.pedidos, "prioridad"),         "O(n log² n)"),
            "counting": (lambda: counting_sort_prioridad(self.pedidos),         "O(n + k)"),
            "quick":    (lambda: quick_sort_pedidos(self.pedidos, "prioridad"), "O(n log n)"),
            "heap":     (lambda: heap_sort_pedidos(self.pedidos),               "O(n log n)"),
            "radix":    (lambda: radix_sort_por_valor(self.pedidos),            "O(n·k)"),
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

    def _run_en_hilo(self, fn, on_done, on_error_msg="❌ Error en el algoritmo"):
        """Lanza fn() en _Worker, llama on_done(result) al terminar."""
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Espera",
                                "Ya hay un algoritmo en ejecución.")
            return
        self._worker = _Worker(fn)
        self._worker.finished.connect(on_done)
        self._worker.error.connect(
            lambda e: self._write(self.txt_res, f"{on_error_msg}\n\n{e}"))
        self._worker.start()

    def _run_greedy(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        rep = self._rep()
        self._write(self.txt_res, "⏳ Ejecutando Greedy…")
        self._run_en_hilo(
            lambda: greedy_vecino_cercano(self.grafo, rep, self.pedidos),
            lambda r: (
                self._mostrar(r),
                self.actualizar_mapa_interactivo(
                    rutas=[(r.ruta, ALGO_COLORES["Greedy Vecino Más Cercano"])])
            ),
        )

    def _run_mochila_frac(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        rep = self._rep()
        self._write(self.txt_res, "⏳ Ejecutando Mochila Fraccionaria…")
        self._run_en_hilo(
            lambda: mochila_fraccionaria(rep, self.pedidos, self.grafo),
            lambda r: (
                self._mostrar(r),
                self.actualizar_mapa_interactivo(
                    rutas=[(r.ruta, ALGO_COLORES["Mochila Fraccionaria"])])
            ),
        )

    def _run_dyv(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        reps = self.repartidores
        peds = list(self.pedidos)
        self._write(self.txt_res, "⏳ Ejecutando Divide y Vencerás…")
        def _on_done(rs):
            self._write(self.txt_res, comparar_algoritmos(rs))
            self._write(self.txt_resumen,
                        f"D&V — {len(rs)} zona(s) | "
                        f"{sum(len(r.pedidos_incluidos) for r in rs)} pedidos")
            self.actualizar_mapa_interactivo(
                rutas=[(r.ruta, ALGO_COLORES["Divide y Vencerás"])
                       for r in rs if r.ruta])
        self._run_en_hilo(
            lambda: divide_y_venceras(self.grafo, reps, peds), _on_done)

    def _run_backtracking(self):
        ini = self.cb_bt_ini.currentText()
        fin = self.cb_bt_fin.currentText()
        if ini == fin:
            return QMessageBox.warning(self, "", "Inicio y destino deben ser distintos.")
        bloq = list(self._bloqueadas)
        self._write(self.txt_res, f"⏳ Backtracking {ini} → {fin}…")
        def _on_done(r):
            self._mostrar(r)
            self.actualizar_mapa_interactivo(
                rutas=[(r.ruta, ALGO_COLORES["Backtracking"])])
        self._run_en_hilo(
            lambda: backtracking_rutas_restringidas(
                self.grafo, ini, fin, bloq, 30),
            _on_done,
        )

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
            f"Seleccionados : {len(sel)}", "", "Pedidos seleccionados:"
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

    def _comparar(self):
        if not self.pedidos:
            return QMessageBox.warning(self, "", "Agrega pedidos primero.")
        rep  = self._rep()
        reps = self.repartidores
        peds = list(self.pedidos)
        bloq = list(self._bloqueadas)
        destinos = [p.nodo_destino for p in peds if not p.entregado]
        fin_bt = (self.cb_bt_fin.currentText()
                  or (destinos[0] if destinos else list(self.grafo.nodos.keys())[2]))
        ini_bt = self.cb_bt_ini.currentText() or "DEPOSITO"
        self._write(self.txt_res, "⏳ Comparando todos los algoritmos…")

        def _fn():
            r_g  = greedy_vecino_cercano(self.grafo, rep, peds)
            r_f  = mochila_fraccionaria(rep, peds, self.grafo)
            r_d  = divide_y_venceras(self.grafo, reps, peds)
            r_bt = backtracking_rutas_restringidas(
                self.grafo, ini_bt, fin_bt, bloq, 20)
            return [r_g, r_f] + r_d + [r_bt]

        def _on_done(todos):
            self._write(self.txt_res, comparar_algoritmos(todos))
            self._write(self.txt_resumen, "✅ Comparación completa")
            self.actualizar_mapa_interactivo(
                rutas=[(r.ruta, ALGO_COLORES.get(r.nombre_algoritmo, ACCENT))
                       for r in todos if r.ruta])

        self._run_en_hilo(_fn, _on_done)

    # ══ ACCIONES BÚSQUEDA ════════════════════════════════════

    def _buscar_binaria(self):
        pid = self.e_bid.text().strip()
        r   = busqueda_binaria_id(self.pedidos, pid)
        if r:
            txt = (f"✅ Búsqueda Binaria — O(log n)\n\n"
                   f"  ID       : {r.id}\n  Cliente  : {r.cliente}\n"
                   f"  Destino  : {r.nodo_destino}\n"
                   f"  Prioridad: {PRIORIDAD_LABEL[r.prioridad]}\n"
                   f"  Peso     : {r.peso} kg\n  Valor    : S/. {r.valor}\n")
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
        ) if rs else "❌ Sin resultados para este sector."
        self._write(self.txt_bus, txt)

    def _run_huffman(self):
        txt = self.e_huf.text().strip()
        if not txt:
            return
        self._write(self.txt_bus, demo_huffman(txt))

    # ══ ACCIONES GRAFO ═══════════════════════════════════════

    def _run_coloreo(self):
        self._write(self.txt_grafo, "⏳ Calculando coloreo…")
        def _fn():
            return self.grafo.obtener_coloreo(recalcular=True)
        def _on_done(coloreo):
            n_colores = max(coloreo.values()) + 1 if coloreo else 0
            self._write(self.txt_grafo,
                        f"✅ Coloreo Welsh-Powell — O(V²+E)\n"
                        f"Colores usados: {n_colores}\n"
                        f"Nodos coloreados: {len(coloreo)}")
            if self._coloreo_on:
                self.actualizar_mapa_interactivo(coloreo=coloreo)
        self._run_en_hilo(_fn, _on_done)

    def _toggle_coloreo(self, state):
        self._coloreo_on = bool(state)
        if self._coloreo_on:
            coloreo = self.grafo.obtener_coloreo()
            self.actualizar_mapa_interactivo(coloreo=coloreo)
        else:
            self.actualizar_mapa_interactivo()

    def _run_par_cercano(self):
        self._write(self.txt_grafo, "⏳ Calculando par más cercano…")
        def _fn():
            return self.grafo.par_nodos_mas_cercanos()
        def _on_done(res):
            dist, a, b = res
            na, nb = self.grafo.nodos[a], self.grafo.nodos[b]
            self._write(self.txt_grafo,
                        f"✅ Par de Puntos Más Cercanos — O(n log n)\n"
                        f"Nodo A : {a} — {na.nombre}\n"
                        f"Nodo B : {b} — {nb.nombre}\n"
                        f"Distancia px: {dist:.1f}")
            self.actualizar_mapa_interactivo(par_cercano=(a, b))
        self._run_en_hilo(_fn, _on_done)

    def _run_merge_nodos(self):
        nodos_ord = self.grafo.nodos_ordenados_por("x")
        lineas = [f"✅ Merge Sort nodos por X — O(n log n)",
                  f"Total: {len(nodos_ord)} nodos", ""]
        for n in nodos_ord[:15]:
            lineas.append(f"  {n.id:<20} x={n.x:>4}  lat={n.lat:.5f}")
        if len(nodos_ord) > 15:
            lineas.append(f"  … ({len(nodos_ord)-15} más)")
        self._write(self.txt_grafo, "\n".join(lineas))

    def _run_expo(self):
        from grafo_osm import expo_rapida
        lineas = ["✅ Exponenciación Rápida — O(log e)", ""]
        for base, exp in [(2, 10), (1.5, 20), (1.0001, 500)]:
            res = expo_rapida(base, exp)
            lineas.append(f"  {base}^{exp} = {res:.6f}")
        self._write(self.txt_grafo, "\n".join(lineas))

    # ══ ACCIONES CONFIG ══════════════════════════════════════

    def _bloquear(self):
        val   = self.cb_blq.currentText()
        parts = [p.strip() for p in val.split("↔")]
        if len(parts) == 2:
            par = (parts[0], parts[1])
            if par not in self._bloqueadas:
                self._bloqueadas.append(par)
                self.grafo.bloquear_calle(*par)
                self.lst_blq.addItem(f"{par[0]} ↔ {par[1]}")
                self.actualizar_mapa_interactivo()

    def _desbloquear(self):
        val   = self.cb_blq.currentText()
        parts = [p.strip() for p in val.split("↔")]
        if len(parts) == 2:
            par = (parts[0], parts[1])
            if par in self._bloqueadas:
                self._bloqueadas.remove(par)
                self.grafo.desbloquear_calle(*par)
                items = [self.lst_blq.item(i).text()
                         for i in range(self.lst_blq.count())]
                self.lst_blq.clear()
                for item in items:
                    if item != f"{par[0]} ↔ {par[1]}":
                        self.lst_blq.addItem(item)
                self.actualizar_mapa_interactivo()


# ─────────────────────────── Entry point ─────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rutas Óptimas — San Sebastián")
    window = App()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()