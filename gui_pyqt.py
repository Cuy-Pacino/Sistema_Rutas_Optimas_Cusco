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

import folium
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QListWidget, QMessageBox, QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QObject, pyqtSlot
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel

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

# ─────────────────────────── Bridge Qt <-> JS (QWebChannel) ─────────────────

class _MapBridge(QObject):
    """
    Objeto expuesto al JS del mapa via QWebChannel.
    El JS llama  bridge.onClick(modo, lat, lon)  directamente,
    sin necesidad de HTTP ni fetch cross-origin.
    """
    @pyqtSlot(str, float, float)
    def onClick(self, modo: str, lat: float, lon: float):
        global _app_instance
        if _app_instance:
            QTimer.singleShot(0, lambda: _app_instance._mapa_click(modo, lat, lon))

_app_instance = None

# JavaScript inyectado en el mapa — usa qwebchannel.js nativo de Qt
_JS_CLICK = """
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
(function() {
    var _modo = 'pedido';
    var _bridge = null;

    window._setModoMapa = function(m) { _modo = m; };

    function _attachToMap(mapObj) {
        mapObj.on('click', function(e) {
            if (_bridge) {
                _bridge.onClick(_modo, e.latlng.lat, e.latlng.lng);
            }
        });
    }

    function _findLeafletMaps() {
        var found = false;
        for (var key in window) {
            try {
                var obj = window[key];
                if (obj && typeof obj._leaflet_id !== 'undefined'
                        && typeof obj.on === 'function'
                        && typeof obj.getCenter === 'function') {
                    _attachToMap(obj);
                    found = true;
                }
            } catch(e) {}
        }
        return found;
    }

    function _init() {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            _bridge = channel.objects.bridge;
            function _try(n) {
                if (!_findLeafletMaps() && n > 0) {
                    setTimeout(function() { _try(n - 1); }, 350);
                }
            }
            _try(15);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }
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
        # QWebChannel se configura en _build_ui después de crear el web_view

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
        # Actualizar etiquetas de BT con los nodos por defecto (ya construidas)
        if self._bt_ini_nid:
            n = self.grafo.nodos.get(self._bt_ini_nid)
            if n:
                self.lbl_bt_ini.setText(f"▶ {n.nombre[:35]}")
        if self._bt_fin_nid:
            n = self.grafo.nodos.get(self._bt_fin_nid)
            if n:
                self.lbl_bt_fin.setText(f"⏹ {n.nombre[:35]}")

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

        # ── QWebChannel: comunicación nativa Qt <-> JS ─────────
        self._bridge  = _MapBridge()
        self._channel = QWebChannel(page)
        self._channel.registerObject("bridge", self._bridge)
        page.setWebChannel(self._channel)

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

        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (lbl_txt, ph) in enumerate([
            ("Cliente:", "nombre del cliente"),
            ("Peso kg:", "2.0"),
            ("Vol L:",   "4.0"),
            ("Valor S/.:", "30.0"),
        ]):
            grid.addWidget(_lbl(lbl_txt, 8, False, TEXT_DIM), i, 0)
            e = _entry(ph)
            grid.addWidget(e, i, 1)
        self.e_cli  = grid.itemAtPosition(0, 1).widget()
        self.e_peso = grid.itemAtPosition(1, 1).widget()
        self.e_vol  = grid.itemAtPosition(2, 1).widget()
        self.e_val  = grid.itemAtPosition(3, 1).widget()

        grid.addWidget(_lbl("Prioridad:", 8, False, TEXT_DIM), 4, 0)
        self.cb_pri = _combo(["URGENTE", "ALTA", "NORMAL", "BAJA"])
        self.cb_pri.setCurrentIndex(2)
        grid.addWidget(self.cb_pri, 4, 1)
        lay.addLayout(grid)

        # ── Picker de destino ──────────────────────────────────
        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Destino de Entrega ──", 9, True, ACCENT))
        lay.addWidget(_lbl(
            "Activa el picker y haz clic sobre el mapa\n"
            "para seleccionar la ubicación de entrega.", 7, False, TEXT_DIM))

        picker_row = QHBoxLayout()
        self.btn_picker_ped = _btn("🖱 Seleccionar en mapa", ACCENT2, 30)
        self.btn_picker_ped.setCheckable(True)
        self.btn_picker_ped.clicked.connect(self._toggle_picker_pedido)
        picker_row.addWidget(self.btn_picker_ped)
        lay.addLayout(picker_row)

        self.lbl_dest_clic = _lbl("📍 Sin destino seleccionado", 8, False, TEXT_DIM)
        lay.addWidget(self.lbl_dest_clic)
        self._pedido_dest_nid: str | None = None  # nid seleccionado con picker

        bf = QHBoxLayout()
        b_add = _btn("➕ Agregar Pedido", ACCENT, 30)
        b_cls = _btn("🗑 Limpiar Todo",   RED_VIF, 30)
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
        rep_row = QHBoxLayout()
        self.cb_rep = _combo([f"{r.id} – {r.nombre}" for r in self.repartidores])
        b_add_rep = _btn("➕ Nuevo", ACCENT2, 26)
        b_add_rep.clicked.connect(self._agregar_repartidor)
        rep_row.addWidget(self.cb_rep, stretch=1)
        rep_row.addWidget(b_add_rep)
        lay.addLayout(rep_row)

        dep_row = QHBoxLayout()
        dep_row.addWidget(_lbl("Depósito:", 8, False, TEXT_DIM))
        self.btn_picker_dep = _btn("🏭 Fijar Depósito en mapa", ACCENT, 26)
        self.btn_picker_dep.setCheckable(True)
        self.btn_picker_dep.clicked.connect(self._toggle_picker_deposito)
        dep_row.addWidget(self.btn_picker_dep, stretch=1)
        lay.addLayout(dep_row)
        self.lbl_dep_actual = _lbl("", 7, False, TEXT_DIM)
        dep = next((n for n in self.grafo.nodos.values() if n.es_deposito), None)
        if dep:
            self.lbl_dep_actual.setText(f"📍 {dep.nombre[:40]}")
        lay.addWidget(self.lbl_dep_actual)

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
        self.e_bcli = _entry("nombre del cliente...")
        b_cli = _btn("🔍 Lineal O(n)", ACCENT2, 28)
        b_cli.clicked.connect(self._buscar_lineal_cli)
        r2.addWidget(self.e_bcli); r2.addWidget(b_cli)
        lay.addLayout(r2)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Búsqueda por Zona (Divide y Vencerás) ──",
                           9, True, ACCENT))
        lay.addWidget(_lbl(
            "Selecciona una zona para listar sus pedidos.\n"
            "La zona se resaltará en el mapa.", 7, False, TEXT_DIM))
        r3 = QHBoxLayout()
        self.cb_sec = _combo(["OESTE", "CENTRO", "ESTE"])
        b_sec = _btn("🔍 Buscar Zona", PURPLE, 28)
        b_vis = _btn("🗺 Ver Zona", BLUE, 28)
        b_sec.clicked.connect(self._buscar_por_zona)
        b_vis.clicked.connect(self._visualizar_zona)
        r3.addWidget(self.cb_sec); r3.addWidget(b_sec); r3.addWidget(b_vis)
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
            ("📍 Par de Puntos Más Cercanos",  ACCENT2, self._run_par_cercano),
            ("📊 Merge Sort — Nodos Activos",  PURPLE,  self._run_merge_nodos),
        ]
        for txt, col, fn in botones:
            b = _btn(txt, col, 32); b.clicked.connect(fn)
            lay.addWidget(b)


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
        lay.addWidget(_lbl(
            "Activa el picker y haz clic en DOS puntos del mapa\n"
            "para seleccionar el tramo a bloquear.", 7, False, TEXT_DIM))

        blq_row = QHBoxLayout()
        self.btn_picker_blq = _btn("🚧 Seleccionar tramo", RED_VIF, 28)
        self.btn_picker_blq.setCheckable(True)
        self.btn_picker_blq.clicked.connect(self._toggle_picker_bloqueo)
        self.lbl_blq_estado = _lbl("Sin selección", 7, False, TEXT_DIM)
        blq_row.addWidget(self.btn_picker_blq)
        blq_row.addWidget(self.lbl_blq_estado, stretch=1)
        lay.addLayout(blq_row)

        b_des_sel = _btn("✅ Desbloquear seleccionado", GREEN_VIF, 26)
        b_des_sel.clicked.connect(self._desbloquear_seleccionado)
        lay.addWidget(b_des_sel)

        lay.addWidget(_lbl("Calles bloqueadas:", 8, False, TEXT_DIM))
        self.lst_blq = QListWidget()
        self.lst_blq.setMaximumHeight(90)
        lay.addWidget(self.lst_blq)

        lay.addWidget(_sep())
        lay.addWidget(_lbl("── Backtracking — Origen y Destino ──",
                           9, True, ACCENT))
        lay.addWidget(_lbl(
            "Usa los pickers o los botones de la barra del mapa.", 7, False, TEXT_DIM))

        # Picker inicio BT
        ini_row = QHBoxLayout()
        ini_row.addWidget(_lbl("Desde:", 8, False, TEXT_DIM))
        self.btn_picker_bt_ini = _btn("▶ Picker inicio", BLUE, 26)
        self.btn_picker_bt_ini.setCheckable(True)
        self.btn_picker_bt_ini.clicked.connect(
            lambda: self._toggle_picker_bt("bt_ini"))
        ini_row.addWidget(self.btn_picker_bt_ini, stretch=1)
        lay.addLayout(ini_row)
        self.lbl_bt_ini = _lbl("No seleccionado", 7, False, BLUE)
        lay.addWidget(self.lbl_bt_ini)

        # Picker destino BT
        fin_row = QHBoxLayout()
        fin_row.addWidget(_lbl("Hasta:", 8, False, TEXT_DIM))
        self.btn_picker_bt_fin = _btn("⏹ Picker destino", RED_VIF, 26)
        self.btn_picker_bt_fin.setCheckable(True)
        self.btn_picker_bt_fin.clicked.connect(
            lambda: self._toggle_picker_bt("bt_fin"))
        fin_row.addWidget(self.btn_picker_bt_fin, stretch=1)
        lay.addLayout(fin_row)
        self.lbl_bt_fin = _lbl("No seleccionado", 7, False, RED_VIF)
        lay.addWidget(self.lbl_bt_fin)

        # Estado interno para los BT pickers (nid seleccionado)
        # Valores por defecto: depósito → nodo más cercano a Urb. Túpac Amaru
        dep_node = next((n for n in self.grafo.nodos.values() if n.es_deposito), None)
        self._bt_ini_nid: str | None = dep_node.id if dep_node else None

        # Túpac Amaru está al este de San Sebastián (~-13.530, -71.923)
        # Búsqueda lineal directa para evitar dependencia de scikit-learn
        _TUPAC_LAT, _TUPAC_LON = -13.5305, -71.9230
        tupac_nid = min(
            self.grafo.nodos,
            key=lambda nid: (self.grafo.nodos[nid].lat - _TUPAC_LAT)**2
                          + (self.grafo.nodos[nid].lon - _TUPAC_LON)**2
        )
        self._bt_fin_nid: str | None = tupac_nid

        self._blq_paso: int = 0      # 0=libre, 1=esperando 1er clic, 2=esperando 2do
        self._blq_nid1: str | None = None

        lay.addWidget(_sep())
        st = self.grafo.stats()
        info = (f"Fuente: OSM  |  {st.get('nodos',0)} nodos  |  "
                f"{st.get('aristas','?')} aristas\n"
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
        self.web_view.page().runJavaScript(
            f"if(typeof window._setModoMapa==='function') window._setModoMapa('{modo}');")
        modos_label = {
            "pedido":   "📦 Haz clic en el mapa para añadir un pedido",
            "deposito": "🏭 Haz clic para fijar el depósito",
            "bt_ini":   "▶ Haz clic para fijar el INICIO del Backtracking",
            "bt_fin":   "⏹ Haz clic para fijar el DESTINO del Backtracking",
            "bloqueo1": "🚧 [1/2] Haz clic en el PRIMER punto del tramo a bloquear",
            "bloqueo2": "🚧 [2/2] Haz clic en el SEGUNDO punto del tramo a bloquear",
        }
        self._write(self.txt_res, modos_label.get(modo, ""))
        # Cambiar cursor: cruz de mira cuando hay picker activo, normal si no
        picker_activo = modo != "pedido"
        cursor = Qt.CursorShape.CrossCursor if picker_activo else Qt.CursorShape.ArrowCursor
        self.web_view.setCursor(cursor)

    # ── Toggles de pickers ───────────────────────────────────

    def _toggle_picker_pedido(self):
        self._cambiar_modo_mapa("pedido")
        for k, b in self._modo_btns.items():
            b.setChecked(k == "pedido")

    def _toggle_picker_deposito(self):
        if self.btn_picker_dep.isChecked():
            self._cambiar_modo_mapa("deposito")
            # marcar también el botón de la barra
            for k, b in self._modo_btns.items():
                b.setChecked(k == "deposito")
        else:
            self._cambiar_modo_mapa("pedido")

    def _toggle_picker_bloqueo(self):
        if self.btn_picker_blq.isChecked():
            self._blq_paso  = 1
            self._blq_nid1  = None
            self._cambiar_modo_mapa("bloqueo1")
            self.lbl_blq_estado.setText("Clic en punto 1…")
        else:
            self._blq_paso = 0
            self._cambiar_modo_mapa("pedido")
            self.lbl_blq_estado.setText("Sin selección")

    def _toggle_picker_bt(self, cual: str):
        btn = self.btn_picker_bt_ini if cual == "bt_ini" else self.btn_picker_bt_fin
        if btn.isChecked():
            self._cambiar_modo_mapa(cual)
            for k, b in self._modo_btns.items():
                b.setChecked(k == cual)
        else:
            self._cambiar_modo_mapa("pedido")

    # ── Acción al hacer clic en el mapa ──────────────────────

    def _mapa_click(self, accion: str, lat: float, lon: float):
        nid  = self.grafo.nodo_mas_cercano_a(lat, lon)
        nodo = self.grafo.nodos.get(nid)
        if not nodo:
            return

        modo = self._modo_mapa

        # ── Añadir pedido ─────────────────────────────────────
        if modo == "pedido":
            self._pedido_dest_nid = nid
            nombre_corto = nodo.nombre[:45]
            self.lbl_dest_clic.setText(f"📍 {nombre_corto}")
            self.lbl_dest_clic.setStyleSheet(
                f"color:{ACCENT2}; font-family:'Courier New'; font-size:8pt;")
            self._write(self.txt_res,
                        f"📍 Destino seleccionado:\n  {nid}\n  {nodo.nombre}\n"
                        f"  ({nodo.lat:.5f}, {nodo.lon:.5f})\n\n"
                        f"  Completa los datos del pedido y pulsa ➕ Agregar.")

        # ── Fijar depósito ────────────────────────────────────
        elif modo == "deposito":
            for n in self.grafo.nodos.values():
                object.__setattr__(n, "es_deposito", False)
            object.__setattr__(nodo, "es_deposito", True)
            for r in self.repartidores:
                r.nodo_actual = nid
            if hasattr(self, "lbl_dep_actual"):
                self.lbl_dep_actual.setText(f"📍 {nodo.nombre[:40]}")
            # Desactivar picker
            if hasattr(self, "btn_picker_dep"):
                self.btn_picker_dep.setChecked(False)
            self._cambiar_modo_mapa("pedido")
            self._write(self.txt_res,
                        f"✅ Depósito fijado en:\n  {nid}\n  {nodo.nombre}\n"
                        f"  ({nodo.lat:.5f}, {nodo.lon:.5f})")
            self.actualizar_mapa_interactivo()

        # ── Bloqueo de calle — paso 1 ─────────────────────────
        elif modo == "bloqueo1":
            self._blq_nid1 = nid
            self._cambiar_modo_mapa("bloqueo2")
            self.lbl_blq_estado.setText(
                f"Punto 1: {nodo.nombre[:25]}  → clic en punto 2")

        # ── Bloqueo de calle — paso 2 ─────────────────────────
        elif modo == "bloqueo2":
            nid1 = self._blq_nid1
            nid2 = nid
            self._blq_paso = 0
            self._blq_nid1 = None
            if hasattr(self, "btn_picker_blq"):
                self.btn_picker_blq.setChecked(False)
            self._cambiar_modo_mapa("pedido")
            if nid1 and nid1 != nid2:
                par = (nid1, nid2)
                if par not in self._bloqueadas:
                    self._bloqueadas.append(par)
                    self.grafo.bloquear_calle(*par)
                    n1 = self.grafo.nodos.get(nid1)
                    n1_nom = n1.nombre[:20] if n1 else nid1
                    n2_nom = nodo.nombre[:20]
                    self.lst_blq.addItem(f"{n1_nom} ↔ {n2_nom}")
                    self.lbl_blq_estado.setText(
                        f"🚧 Bloqueado: {n1_nom} ↔ {n2_nom}")
                    self.actualizar_mapa_interactivo()
            else:
                self.lbl_blq_estado.setText("⚠ Mismo punto, cancelado")

        # ── Backtracking inicio ───────────────────────────────
        elif modo == "bt_ini":
            self._bt_ini_nid = nid
            if hasattr(self, "lbl_bt_ini"):
                self.lbl_bt_ini.setText(f"▶ {nodo.nombre[:35]}")
            if hasattr(self, "btn_picker_bt_ini"):
                self.btn_picker_bt_ini.setChecked(False)
            self._cambiar_modo_mapa("pedido")
            self._write(self.txt_res, f"▶ Inicio BT: {nodo.nombre}\n  ({nid})")

        # ── Backtracking destino ──────────────────────────────
        elif modo == "bt_fin":
            self._bt_fin_nid = nid
            if hasattr(self, "lbl_bt_fin"):
                self.lbl_bt_fin.setText(f"⏹ {nodo.nombre[:35]}")
            if hasattr(self, "btn_picker_bt_fin"):
                self.btn_picker_bt_fin.setChecked(False)
            self._cambiar_modo_mapa("pedido")
            self._write(self.txt_res, f"⏹ Destino BT: {nodo.nombre}\n  ({nid})")

    # ══ MAPA FOLIUM ══════════════════════════════════════════

    def actualizar_mapa_interactivo(self, rutas=None, coloreo=None,
                                     par_cercano=None, zona_resaltada=None):
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

        # ── Zona resaltada ────────────────────────────────────
        if zona_resaltada:
            zona_nombre, nids_zona, zona_color = zona_resaltada
            for nid in nids_zona:
                nodo = self.grafo.nodos.get(nid)
                if nodo:
                    folium.CircleMarker(
                        location=[nodo.lat, nodo.lon],
                        radius=5,
                        color=zona_color,
                        fill=True,
                        fill_color=zona_color,
                        fill_opacity=0.35,
                        weight=1,
                        tooltip=f"Zona {zona_nombre}",
                    ).add_to(mapa)

        # ── Calles bloqueadas ─────────────────────────────────
        for par in self._bloqueadas:
            n1 = self.grafo.nodos.get(par[0])
            n2 = self.grafo.nodos.get(par[1])
            if n1 and n2:
                folium.PolyLine(
                    locations=[[n1.lat, n1.lon], [n2.lat, n2.lon]],
                    color="#e74c3c",
                    weight=5,
                    opacity=0.9,
                    dash_array="10",
                    tooltip=f"🚧 Bloqueado: {n1.nombre[:20]} ↔ {n2.nombre[:20]}",
                ).add_to(mapa)
        # ── Coloreo de nodos ─────────────────────────────────
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
        if not self._pedido_dest_nid:
            QMessageBox.warning(self, "Destino requerido",
                                "Activa '🖱 Seleccionar en mapa' y haz clic\n"
                                "en el mapa para elegir el destino.")
            return
        try:
            cli  = self.e_cli.text().strip() or f"Cliente {self._id_counter}"
            peso = float(self.e_peso.text() or "2")
            vol  = float(self.e_vol.text()  or "4")
            val  = float(self.e_val.text()  or "30")
        except ValueError:
            QMessageBox.critical(self, "Error",
                                 "Peso, Volumen y Valor deben ser números.")
            return
        pri  = Prioridad[self.cb_pri.currentText()]
        pid  = f"P{self._id_counter:03d}"
        self._id_counter += 1
        self.pedidos.append(Pedido(
            id=pid, cliente=cli, nodo_destino=self._pedido_dest_nid,
            peso=peso, volumen=vol, valor=val,
            prioridad=pri, hora_registro=time.time()
        ))
        self._pedido_dest_nid = None
        self.lbl_dest_clic.setText("📍 Sin destino seleccionado")
        self.lbl_dest_clic.setStyleSheet(
            f"color:{TEXT_DIM}; font-family:'Courier New'; font-size:8pt;")
        self._actualizar_tabla()
        self.actualizar_mapa_interactivo()
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
        """Lanza fn() en _Worker. Si hay uno corriendo, lo cancela y lanza el nuevo."""
        if self._worker and self._worker.isRunning():
            # Desconectar señales del worker anterior y dejar que termine en background
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except Exception:
                pass
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
        ini = getattr(self, "_bt_ini_nid", None)
        fin = getattr(self, "_bt_fin_nid", None)
        if not ini or not fin:
            QMessageBox.warning(self, "Selecciona puntos",
                                "Usa los pickers de Backtracking en la pestaña\n"
                                "Config (▶ y ⏹) o los botones de la barra del mapa\n"
                                "para fijar el inicio y destino.")
            return
        if ini == fin:
            return QMessageBox.warning(self, "", "Inicio y destino deben ser distintos.")
        bloq = list(self._bloqueadas)
        self._write(self.txt_res,
                    f"⏳ Backtracking en ejecución…\n"
                    f"  Desde : {self.grafo.nodos[ini].nombre}\n"
                    f"  Hasta : {self.grafo.nodos[fin].nombre}\n"
                    f"  Calles bloqueadas: {len(bloq)}\n\n"
                    f"  (Usando poda Dijkstra para garantizar que termine)")
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
        ini_bt = (self._bt_ini_nid or "DEPOSITO")
        fin_bt = (self._bt_fin_nid
                  or (destinos[0] if destinos else list(self.grafo.nodos.keys())[2]))
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
        # kept for compatibility — delegates to new method
        self._buscar_por_zona()

    def _buscar_por_zona(self):
        zona = self.cb_sec.currentText()
        nids_zona = self.grafo.nodos_en_zona(zona)
        pedidos_zona = [p for p in self.pedidos if p.nodo_destino in nids_zona]
        txt = (f"🗺 Búsqueda por Zona — {zona}  (Divide y Vencerás)\n"
               f"Nodos en zona: {len(nids_zona)} | "
               f"Pedidos en zona: {len(pedidos_zona)}\n"
               f"{'─'*50}\n")
        if pedidos_zona:
            for p in pedidos_zona:
                nd = self.grafo.nodos.get(p.nodo_destino)
                loc = nd.nombre[:30] if nd else p.nodo_destino
                txt += (f"  • {p.id} | {p.cliente} | "
                        f"{PRIORIDAD_LABEL[p.prioridad]} | "
                        f"S/.{p.valor} | {loc}\n")
        else:
            txt += "  Sin pedidos en esta zona.\n"
        self._write(self.txt_bus, txt)

    def _visualizar_zona(self):
        zona = self.cb_sec.currentText()
        ZONA_COLORES = {"OESTE": "#3498db", "CENTRO": "#2ecc71", "ESTE": "#e67e22"}
        color = ZONA_COLORES.get(zona, "#aaaaaa")
        nids_zona = self.grafo.nodos_en_zona(zona)
        self.actualizar_mapa_interactivo(zona_resaltada=(zona, nids_zona, color))
        self._write(self.txt_bus,
                    f"🗺 Zona {zona} resaltada en el mapa\n"
                    f"Nodos: {len(nids_zona)}")

    def _desbloquear_seleccionado(self):
        item = self.lst_blq.currentItem()
        if not item:
            QMessageBox.information(self, "", "Selecciona una calle de la lista primero.")
            return
        row = self.lst_blq.currentRow()
        if 0 <= row < len(self._bloqueadas):
            par = self._bloqueadas[row]
            self.grafo.desbloquear_calle(*par)
            self._bloqueadas.pop(row)
            self.lst_blq.takeItem(row)
            self.actualizar_mapa_interactivo()

    def _agregar_repartidor(self):
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("Nuevo Repartidor")
        dlg.setStyleSheet(f"background:{BG_PANEL}; color:{TEXT_MAIN};")
        dlg.setFixedWidth(300)
        form = QFormLayout(dlg)
        e_nom = _entry("Nombre"); e_cap = _entry("30.0"); e_vol = _entry("60.0")
        form.addRow(_lbl("Nombre:", 9, False, TEXT_DIM), e_nom)
        form.addRow(_lbl("Cap. peso kg:", 9, False, TEXT_DIM), e_cap)
        form.addRow(_lbl("Cap. vol L:", 9, False, TEXT_DIM), e_vol)
        bbs = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        bbs.accepted.connect(dlg.accept)
        bbs.rejected.connect(dlg.reject)
        bbs.setStyleSheet(f"color:{TEXT_MAIN};")
        form.addRow(bbs)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        nombre = e_nom.text().strip() or "Repartidor"
        try:
            cap_p = float(e_cap.text() or "30")
            cap_v = float(e_vol.text() or "60")
        except ValueError:
            cap_p, cap_v = 30.0, 60.0
        dep = next((n for n in self.grafo.nodos.values() if n.es_deposito), None)
        nid_dep = dep.id if dep else list(self.grafo.nodos.keys())[0]
        rid = f"R{len(self.repartidores)+1}"
        self.repartidores.append(
            Repartidor(rid, nombre, nid_dep, cap_p, cap_v, 25.0))
        self.cb_rep.addItem(f"{rid} – {nombre}")

    def _run_huffman(self):
        txt = self.e_huf.text().strip()
        if not txt:
            return
        self._write(self.txt_bus, demo_huffman(txt))

    # ══ ACCIONES GRAFO ═══════════════════════════════════════

    def _run_par_cercano(self):
        """Par más cercano solo entre nodos con pedidos activos + depósito."""
        nids_activos = list({p.nodo_destino for p in self.pedidos
                             if p.nodo_destino in self.grafo.nodos})
        dep = next((n.id for n in self.grafo.nodos.values() if n.es_deposito), None)
        if dep:
            nids_activos.append(dep)
        nids_activos = list(set(nids_activos))
        if len(nids_activos) < 2:
            self._write(self.txt_grafo,
                        "⚠ Necesitas al menos 2 pedidos para calcular el par más cercano.")
            return
        self._write(self.txt_grafo,
                    f"⏳ Calculando par más cercano entre {len(nids_activos)} nodos activos…")
        def _fn():
            return self.grafo.par_nodos_mas_cercanos(nids_activos)
        def _on_done(res):
            dist, a, b = res
            na, nb = self.grafo.nodos[a], self.grafo.nodos[b]
            self._write(self.txt_grafo,
                        f"✅ Par de Puntos Más Cercanos — O(n log n)\n"
                        f"Solo considera nodos con pedidos activos + depósito.\n\n"
                        f"Nodo A : {na.nombre}\n"
                        f"Nodo B : {nb.nombre}\n"
                        f"Distancia px: {dist:.1f}")
            self.actualizar_mapa_interactivo(par_cercano=(a, b))
        self._run_en_hilo(_fn, _on_done)

    def _run_merge_nodos(self):
        """Merge Sort solo sobre nodos presentes (depósito + destinos de pedidos)."""
        nids_activos = list({p.nodo_destino for p in self.pedidos
                             if p.nodo_destino in self.grafo.nodos})
        dep = next((n for n in self.grafo.nodos.values() if n.es_deposito), None)
        nodos_act = [self.grafo.nodos[n] for n in nids_activos]
        if dep and dep.id not in nids_activos:
            nodos_act.append(dep)
        from grafo_osm import merge_sort_nodos
        nodos_ord = merge_sort_nodos(nodos_act, "x")
        lineas = [f"✅ Merge Sort nodos activos por X — O(n log n)",
                  f"Mostrando {len(nodos_ord)} nodo(s) presentes:", ""]
        for n in nodos_ord:
            tag = "🏭" if n.es_deposito else "📦"
            lineas.append(f"  {tag} {n.nombre[:35]}")
            lineas.append(f"     lat={n.lat:.5f}, lon={n.lon:.5f}")
        self._write(self.txt_grafo, "\n".join(lineas))

    # ══ ACCIONES CONFIG ══════════════════════════════════════

    # ── fin acciones config ───────────────────────────────────


# ─────────────────────────── Entry point ─────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rutas Óptimas — San Sebastián")
    window = App()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()