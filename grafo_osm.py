"""
grafo_osm.py
Grafo real de calles — San Sebastián, Cusco.
Basado exclusivamente en OpenStreetMap via OSMnx + NetworkX.
Programación III — UNSAAC 2026

Algoritmos propios incorporados:
  • Dijkstra propio          — O((V+E) log V)
  • Par de Puntos Más Cercanos — O(n log n)   divide y vencerás geométrico
  • Coloreo Welsh-Powell     — O(V²+E)
  • Merge Sort               — O(n log n)     ordenar nodos por coordenada
  • Exponenciación Rápida    — O(log e)       penalización por tramos
"""

from __future__ import annotations

import math
import heapq
import time
import os
import pickle
from typing import Optional

import networkx as nx
import osmnx as ox

from modelos import Nodo, Arista

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

_PLACE_QUERY = "San Sebastián, Cusco, Peru"

ox.settings.log_console   = False
ox.settings.use_cache     = True
ox.settings.timeout       = 90

_CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache_osm")
_CACHE_FILE = os.path.join(_CACHE_DIR, "san_sebastian_v3.pkl")

CANVAS_W = 900
CANVAS_H = 650

# Umbrales de longitud para dividir en 3 zonas (San Sebastián: ~-71.975 → -71.920)
_LON_OESTE_LIM = -71.960
_LON_ESTE_LIM  = -71.935

# Depósito por defecto: cruce Av. La Cultura con límite de San Sebastián
_DEPOSITO_LAT =  -13.5178
_DEPOSITO_LON =  -71.9490


def _zona_de_lon(lon: float) -> str:
    if lon < _LON_OESTE_LIM:
        return "OESTE"
    if lon > _LON_ESTE_LIM:
        return "ESTE"
    return "CENTRO"

# ─────────────────────────────────────────────────────────────────────────────
#  EXPONENCIACIÓN RÁPIDA — O(log e)
# ─────────────────────────────────────────────────────────────────────────────

def expo_rapida(base: float, exp: int) -> float:
    resultado = 1.0
    base = float(base)
    while exp > 0:
        if exp % 2 == 1:
            resultado *= base
        base *= base
        exp >>= 1
    return resultado


def penalizacion_distancia(distancia_m: float,
                           factor: float = 1.0001,
                           tramos: int = 1) -> float:
    return distancia_m * expo_rapida(factor, tramos)

# ─────────────────────────────────────────────────────────────────────────────
#  MERGE SORT DE NODOS — O(n log n)
# ─────────────────────────────────────────────────────────────────────────────

def merge_sort_nodos(nodos: list[Nodo], clave: str = "x") -> list[Nodo]:
    if len(nodos) <= 1:
        return nodos
    mid = len(nodos) // 2
    izq = merge_sort_nodos(nodos[:mid],  clave)
    der = merge_sort_nodos(nodos[mid:],  clave)
    return _merge(izq, der, clave)


def _merge(izq: list[Nodo], der: list[Nodo], clave: str) -> list[Nodo]:
    resultado, i, j = [], 0, 0
    while i < len(izq) and j < len(der):
        if getattr(izq[i], clave) <= getattr(der[j], clave):
            resultado.append(izq[i]); i += 1
        else:
            resultado.append(der[j]); j += 1
    resultado.extend(izq[i:])
    resultado.extend(der[j:])
    return resultado

# ─────────────────────────────────────────────────────────────────────────────
#  PAR DE PUNTOS MÁS CERCANOS — O(n log n)
# ─────────────────────────────────────────────────────────────────────────────

def _dist_euclidea(a: Nodo, b: Nodo) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _closest_fuerza_bruta(pts: list[Nodo]) -> tuple[float, Nodo, Nodo]:
    min_d, p1, p2 = float("inf"), pts[0], pts[0]
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = _dist_euclidea(pts[i], pts[j])
            if d < min_d:
                min_d, p1, p2 = d, pts[i], pts[j]
    return min_d, p1, p2


def _closest_franja(franja: list[Nodo], d: float,
                    p1: Nodo, p2: Nodo) -> tuple[float, Nodo, Nodo]:
    franja_y = merge_sort_nodos(franja, "y")
    min_d = d
    for i in range(len(franja_y)):
        j = i + 1
        while j < len(franja_y) and (franja_y[j].y - franja_y[i].y) < min_d:
            dist = _dist_euclidea(franja_y[i], franja_y[j])
            if dist < min_d:
                min_d, p1, p2 = dist, franja_y[i], franja_y[j]
            j += 1
    return min_d, p1, p2


def _closest_rec(pts_x: list[Nodo]) -> tuple[float, Nodo, Nodo]:
    n = len(pts_x)
    if n <= 3:
        return _closest_fuerza_bruta(pts_x)
    mid   = n // 2
    mid_x = pts_x[mid].x
    izq   = _closest_rec(pts_x[:mid])
    der   = _closest_rec(pts_x[mid:])
    d, p1, p2 = izq if izq[0] < der[0] else der
    franja = [p for p in pts_x if abs(p.x - mid_x) < d]
    return _closest_franja(franja, d, p1, p2)


def par_mas_cercano(nodos: list[Nodo]) -> tuple[float, Nodo, Nodo]:
    """Par de Puntos Más Cercanos — O(n log n)."""
    if len(nodos) < 2:
        raise ValueError("Se necesitan al menos 2 nodos.")
    return _closest_rec(merge_sort_nodos(list(nodos), "x"))

# ─────────────────────────────────────────────────────────────────────────────
#  COLOREO DE GRAFOS — Welsh-Powell  O(V²+E)
# ─────────────────────────────────────────────────────────────────────────────

def coloreo_grafos(adyacencia: dict[str, list]) -> dict[str, int]:
    grados = {v: len(vecinos) for v, vecinos in adyacencia.items()}
    vertices = list(grados.keys())
    _qs_grados(vertices, 0, len(vertices) - 1, grados)
    colores: dict[str, int] = {}
    for v in vertices:
        vecinos_colores = {
            colores[w] for w in adyacencia.get(v, [])
            if isinstance(w, str) and w in colores
        }
        c = 0
        while c in vecinos_colores:
            c += 1
        colores[v] = c
    return colores


def _qs_grados(arr, lo, hi, grados):
    if lo < hi:
        p = _part_grados(arr, lo, hi, grados)
        _qs_grados(arr, lo, p - 1, grados)
        _qs_grados(arr, p + 1, hi, grados)


def _part_grados(arr, lo, hi, grados):
    pivot = grados[arr[(lo + hi) // 2]]
    arr[(lo + hi) // 2], arr[hi] = arr[hi], arr[(lo + hi) // 2]
    i = lo - 1
    for j in range(lo, hi):
        if grados[arr[j]] >= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
    return i + 1

# ─────────────────────────────────────────────────────────────────────────────
#  UTILIDADES DE CONVERSIÓN
# ─────────────────────────────────────────────────────────────────────────────

def _latlon_a_px(lat, lon, lat_min, lat_max, lon_min, lon_max, margin=50):
    w = CANVAS_W - 2 * margin
    h = CANVAS_H - 2 * margin
    x = int(margin + (lon - lon_min) / max(lon_max - lon_min, 1e-9) * w)
    y = int(margin + (1 - (lat - lat_min) / max(lat_max - lat_min, 1e-9)) * h)
    return x, y


def _nombre_calle_osm(datos: dict) -> str:
    name = datos.get("name", "")
    if isinstance(name, list):
        name = name[0]
    return name or datos.get("highway", "calle")


def _velocidad_kmh(datos: dict) -> float:
    highway = datos.get("highway", "residential")
    if isinstance(highway, list):
        highway = highway[0]
    tabla = {
        "motorway": 80, "trunk": 60, "primary": 50,
        "secondary": 40, "tertiary": 30,
        "residential": 20, "living_street": 10,
        "service": 15, "unclassified": 20,
    }
    return tabla.get(highway, 20)

# ─────────────────────────────────────────────────────────────────────────────
#  ZONAS PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────

ZONAS: dict[str, set] = {"OESTE": set(), "CENTRO": set(), "ESTE": set()}

# ─────────────────────────────────────────────────────────────────────────────
#  DESCARGA / CACHÉ DEL GRAFO OSMnx
# ─────────────────────────────────────────────────────────────────────────────

def _descargar_o_cargar_grafo():
    """
    Devuelve (nodos, aristas, zonas, G_utm, G_geo).
    G_utm  — MultiDiGraph proyectado a UTM (para cálculos de longitud).
    G_geo  — MultiDiGraph en EPSG:4326 (lat/lon) para coordenadas reales.
    Ambos tienen los mismos osmids como nodos.
    """
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "rb") as f:
                c = pickle.load(f)
            print(f"  [OSM] Grafo cargado desde caché.")
            return c["nodos"], c["aristas"], c["zonas"], c["G_utm"], c["G_geo"]
        except Exception as e:
            print(f"  [OSM] Caché inválida ({e}), re-descargando…")

    print(f"  [OSM] Descargando '{_PLACE_QUERY}' desde OpenStreetMap…")

    # 1. Descargar en CRS geográfico (EPSG:4326)
    G_geo = ox.graph_from_place(
        _PLACE_QUERY,
        network_type="drive",
        simplify=True,
        retain_all=False,
    )
    G_geo = ox.truncate.largest_component(G_geo, strongly=True)

    # 2. Proyectar a UTM para cálculos de distancia/velocidad precisos
    G_utm = ox.project_graph(G_geo)
    G_utm = ox.routing.add_edge_speeds(G_utm)
    G_utm = ox.routing.add_edge_travel_times(G_utm)

    # 3. Pasar travel_time y speed_kph al grafo geo (mismos osmids)
    for u, v, k, data in G_utm.edges(keys=True, data=True):
        if G_geo.has_edge(u, v, k):
            G_geo[u][v][k]["travel_time"] = data.get("travel_time", 0)
            G_geo[u][v][k]["speed_kph"]   = data.get("speed_kph",   20)

    nodos, aristas, zonas = _procesar_grafo(G_geo)

    os.makedirs(_CACHE_DIR, exist_ok=True)
    with open(_CACHE_FILE, "wb") as f:
        pickle.dump({"nodos": nodos, "aristas": aristas,
                     "zonas": zonas, "G_utm": G_utm, "G_geo": G_geo}, f)
    print(f"  [OSM] Caché guardada.")
    return nodos, aristas, zonas, G_utm, G_geo


def _procesar_grafo(G_geo: nx.MultiDiGraph):
    """
    Convierte G_geo (EPSG:4326) en las estructuras internas Nodo/Arista.
    En EPSG:4326 los atributos de nodo son  y=lat, x=lon.
    """
    lat_by_id = {n: d["y"] for n, d in G_geo.nodes(data=True)}
    lon_by_id = {n: d["x"] for n, d in G_geo.nodes(data=True)}

    lats = list(lat_by_id.values())
    lons = list(lon_by_id.values())
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    # Depósito: nodo más cercano a coordenada de referencia
    deposito_osmid = min(
        lat_by_id,
        key=lambda n: (lat_by_id[n] - _DEPOSITO_LAT)**2
                    + (lon_by_id[n] - _DEPOSITO_LON)**2
    )

    # Conservar sólo nodos con degree ≥ 2 (intersecciones reales)
    relevantes = {n for n, d in G_geo.degree() if d >= 2}
    relevantes.add(deposito_osmid)

    # Nombres de calle por nodo
    nombres: dict[int, str] = {}
    for u, v, data in G_geo.edges(data=True):
        name = _nombre_calle_osm(data)
        if name:
            nombres.setdefault(u, name)
            nombres.setdefault(v, name)

    # Mapa osmid → nid interno
    id_map: dict[int, str] = {deposito_osmid: "DEPOSITO"}
    for osmid in relevantes:
        if osmid != deposito_osmid:
            id_map[osmid] = f"N{osmid}"

    # Construir nodos
    nodos: dict[str, Nodo] = {}
    for osmid in relevantes:
        nid    = id_map[osmid]
        lat    = lat_by_id[osmid]
        lon    = lon_by_id[osmid]
        nombre = "Depósito — Av. La Cultura" if osmid == deposito_osmid \
                 else nombres.get(osmid, f"Intersección {nid}")
        x, y   = _latlon_a_px(lat, lon, lat_min, lat_max, lon_min, lon_max)
        nodos[nid] = Nodo(id=nid, nombre=nombre, lat=lat, lon=lon,
                          x=x, y=y, es_deposito=(osmid == deposito_osmid))

    # Construir aristas (sin duplicar)
    aristas: list[Arista] = []
    vistas: set[tuple] = set()
    for u, v, data in G_geo.edges(data=True):
        nu, nv = id_map.get(u), id_map.get(v)
        if not nu or not nv or nu not in nodos or nv not in nodos:
            continue
        par = (min(nu, nv), max(nu, nv))
        if par in vistas:
            continue
        vistas.add(par)
        dist_m = float(data.get("length", 0) or 0)
        vel    = float(data.get("speed_kph", _velocidad_kmh(data)) or 20)
        t_min  = float(data.get("travel_time", 0) or 0) / 60.0
        if t_min == 0 and dist_m > 0:
            t_min = (dist_m / 1000.0) / vel * 60.0
        aristas.append(Arista(
            origen=nu, destino=nv,
            distancia=dist_m, tiempo=t_min,
            bidireccional=True,
            nombre_calle=_nombre_calle_osm(data),
            bloqueada=False,
        ))

    # Zonas por longitud
    zonas: dict[str, set] = {"OESTE": set(), "CENTRO": set(), "ESTE": set()}
    for nid, nodo in nodos.items():
        zonas[_zona_de_lon(nodo.lon)].add(nid)

    return nodos, aristas, zonas

# ─────────────────────────────────────────────────────────────────────────────
#  CLASE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class GrafoOSM:
    """
    Grafo de San Sebastián basado en OpenStreetMap (OSMnx + NetworkX).
    Interfaz pública compatible con algoritmos.py.

    Atributos extra:
      G_utm  — MultiDiGraph UTM (NetworkX nativo, para algoritmos nx)
      G_geo  — MultiDiGraph EPSG:4326 (lat/lon) para dibujar en Folium
      zonas  — dict zona → set de nodo_ids
      fuente — "osm"
    """

    def __init__(self, forzar_descarga: bool = False):
        print("  [GrafoOSM] Inicializando…")
        t0 = time.perf_counter()

        if forzar_descarga and os.path.exists(_CACHE_FILE):
            os.remove(_CACHE_FILE)

        self.nodos: dict[str, Nodo]
        self._aristas_raw: list[Arista]
        self.zonas: dict[str, set]
        self.G_utm: nx.MultiDiGraph
        self.G_geo: nx.MultiDiGraph

        (self.nodos, self._aristas_raw, self.zonas,
         self.G_utm, self.G_geo) = _descargar_o_cargar_grafo()

        self.fuente = "osm"

        # Mapa osmid ↔ nid (para traducir rutas NetworkX ↔ nuestros IDs)
        self._nid_a_osmid: dict[str, int] = {}
        self._osmid_a_nid: dict[int, str] = {}
        for osmid in self.G_geo.nodes():
            nid = f"N{osmid}"
            if nid in self.nodos:
                self._nid_a_osmid[nid]   = osmid
                self._osmid_a_nid[osmid] = nid
        # DEPOSITO especial
        dep = next((n for n in self.nodos.values() if n.es_deposito), None)
        if dep:
            osmid_dep = next(
                (n for n in self.G_geo.nodes()
                 if abs(self.G_geo.nodes[n].get("y",0) - dep.lat) < 0.00005
                 and abs(self.G_geo.nodes[n].get("x",0) - dep.lon) < 0.00005),
                None
            )
            if osmid_dep:
                self._nid_a_osmid["DEPOSITO"]    = osmid_dep
                self._osmid_a_nid[osmid_dep]     = "DEPOSITO"

        # Actualizar ZONAS global
        ZONAS.clear()
        ZONAS.update(self.zonas)

        # Adyacencia propia
        self.adyacencia: dict[str, list] = {nid: [] for nid in self.nodos}
        self._construir_adyacencia()

        self._coloreo: dict[str, int] | None = None

        t1 = time.perf_counter()
        print(f"  [GrafoOSM] Listo — {len(self.nodos)} nodos, "
              f"{sum(len(v) for v in self.adyacencia.values())//2} aristas "
              f"en {t1-t0:.2f}s")

    # ── Construcción de adyacencia ────────────────────────────

    def _construir_adyacencia(self):
        for a in self._aristas_raw:
            if a.origen in self.adyacencia and a.destino in self.adyacencia:
                self.adyacencia[a.origen].append(
                    (a.destino, a.distancia, a.tiempo, a.nombre_calle, a.bloqueada))
                if a.bidireccional:
                    self.adyacencia[a.destino].append(
                        (a.origen, a.distancia, a.tiempo, a.nombre_calle, a.bloqueada))

    # ── API básica ────────────────────────────────────────────

    def vecinos(self, nodo_id: str,
                ignorar_bloqueadas: bool = True) -> list[tuple]:
        return [
            (v, d, t, c) for v, d, t, c, bloq
            in self.adyacencia.get(nodo_id, [])
            if not (ignorar_bloqueadas and bloq)
        ]

    def nodo(self, nid: str) -> Nodo:
        return self.nodos[nid]

    def todos_los_nodos_ids(self) -> list[str]:
        return list(self.nodos.keys())

    def distancia_directa(self, a: str, b: str) -> float:
        return self.nodos[a].distancia_a(self.nodos[b])

    # ── Nodo más cercano a coordenadas (lat, lon) ─────────────

    def nodo_mas_cercano_a(self, lat: float, lon: float) -> str:
        """Devuelve el nid más cercano a las coordenadas dadas."""
        osmid = ox.distance.nearest_nodes(self.G_geo, lon, lat)
        nid = self._osmid_a_nid.get(osmid)
        if nid:
            return nid
        # Fallback: búsqueda lineal sobre nuestros nodos
        return min(self.nodos,
                   key=lambda n: (self.nodos[n].lat - lat)**2
                               + (self.nodos[n].lon - lon)**2)

    # ── Bloqueo de calles ─────────────────────────────────────

    def bloquear_calle(self, origen: str, destino: str):
        self._set_bloqueo(origen, destino, True)

    def desbloquear_calle(self, origen: str, destino: str):
        self._set_bloqueo(origen, destino, False)

    def _set_bloqueo(self, origen: str, destino: str, estado: bool):
        for nid, vid in [(origen, destino), (destino, origen)]:
            lst = self.adyacencia.get(nid, [])
            for i, (v, d, t, c, _) in enumerate(lst):
                if v == vid:
                    lst[i] = (v, d, t, c, estado)
        for a in self._aristas_raw:
            if (a.origen == origen and a.destino == destino) or \
               (a.bidireccional and a.origen == destino and a.destino == origen):
                a.bloqueada = estado

    # ── Dijkstra PROPIO — O((V+E) log V) ─────────────────────

    def dijkstra(self, inicio: str, fin: str,
                 usar_tiempo: bool = False) -> tuple[list[str], float]:
        if inicio not in self.nodos or fin not in self.nodos:
            return [], float("inf")

        dist   = {n: float("inf") for n in self.nodos}
        prev   = {n: None         for n in self.nodos}
        tramos = {n: 0            for n in self.nodos}
        dist[inicio] = 0.0
        heap = [(0.0, inicio)]

        while heap:
            costo, u = heapq.heappop(heap)
            if u == fin:
                break
            if costo > dist[u]:
                continue
            for vecino, d, t, *_ in self.vecinos(u):
                peso_base = t if usar_tiempo else d
                peso = penalizacion_distancia(peso_base, 1.0001, tramos[u] + 1)
                nueva = dist[u] + peso
                if nueva < dist[vecino]:
                    dist[vecino]   = nueva
                    prev[vecino]   = u
                    tramos[vecino] = tramos[u] + 1
                    heapq.heappush(heap, (nueva, vecino))

        ruta, nodo = [], fin
        while nodo is not None:
            ruta.append(nodo)
            nodo = prev[nodo]
        ruta.reverse()
        if not ruta or ruta[0] != inicio:
            return [], float("inf")
        return ruta, dist[fin]

    # ── Ruta con curvas reales usando NetworkX + G_geo ────────

    def ruta_como_coordenadas(self, nids: list[str]) -> list[list[float]]:
        """
        Convierte una lista de nids en pares [lat, lon] siguiendo la
        geometría real de las calles almacenada en G_geo.
        """
        puntos: list[list[float]] = []
        for i in range(len(nids) - 1):
            u_nid, v_nid = nids[i], nids[i + 1]
            u_osm = self._nid_a_osmid.get(u_nid)
            v_osm = self._nid_a_osmid.get(v_nid)

            dibujado = False
            if u_osm is not None and v_osm is not None:
                # Intentar obtener geometría de la arista en G_geo
                if self.G_geo.has_edge(u_osm, v_osm):
                    datos = self.G_geo.get_edge_data(u_osm, v_osm)
                    datos = datos[0] if 0 in datos else next(iter(datos.values()))
                    geom = datos.get("geometry")
                    if geom is not None:
                        for coord in geom.coords:
                            puntos.append([coord[1], coord[0]])  # lon,lat → lat,lon
                        dibujado = True
                elif self.G_geo.has_edge(v_osm, u_osm):
                    datos = self.G_geo.get_edge_data(v_osm, u_osm)
                    datos = datos[0] if 0 in datos else next(iter(datos.values()))
                    geom = datos.get("geometry")
                    if geom is not None:
                        for coord in reversed(list(geom.coords)):
                            puntos.append([coord[1], coord[0]])
                        dibujado = True

            if not dibujado:
                # Fallback: línea recta
                n1 = self.nodos.get(u_nid)
                n2 = self.nodos.get(v_nid)
                if n1:
                    puntos.append([n1.lat, n1.lon])
                if n2:
                    puntos.append([n2.lat, n2.lon])

        return puntos

    # ── Dijkstra NetworkX (validación / comparación) ──────────

    def nx_shortest_path(self, ini_nid: str, fin_nid: str,
                         weight: str = "length") -> tuple[list[str], float]:
        u = self._nid_a_osmid.get(ini_nid)
        v = self._nid_a_osmid.get(fin_nid)
        if u is None or v is None:
            return self.dijkstra(ini_nid, fin_nid)
        try:
            ruta_osm = nx.shortest_path(self.G_geo, u, v, weight=weight)
            costo    = nx.shortest_path_length(self.G_geo, u, v, weight=weight)
            ruta_nid = [self._osmid_a_nid.get(n, f"N{n}") for n in ruta_osm]
            return ruta_nid, float(costo)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return self.dijkstra(ini_nid, fin_nid)

    # ── Par de Puntos Más Cercanos ────────────────────────────

    def par_nodos_mas_cercanos(self, nodos_ids=None) -> tuple[float, str, str]:
        ids = nodos_ids or list(self.nodos.keys())
        pts = [self.nodos[i] for i in ids if i in self.nodos]
        if len(pts) < 2:
            raise ValueError("Se necesitan al menos 2 nodos.")
        dist, a, b = par_mas_cercano(pts)
        return dist, a.id, b.id

    # ── Coloreo Welsh-Powell ──────────────────────────────────

    def obtener_coloreo(self, recalcular: bool = False) -> dict[str, int]:
        if self._coloreo is None or recalcular:
            ady_simple = {nid: [v for v, *_ in lst]
                          for nid, lst in self.adyacencia.items()}
            self._coloreo = coloreo_grafos(ady_simple)
        return self._coloreo

    def nodos_por_color(self) -> dict[int, list[str]]:
        coloreo = self.obtener_coloreo()
        grupos: dict[int, list[str]] = {}
        for nid, color in coloreo.items():
            grupos.setdefault(color, []).append(nid)
        return grupos

    # ── Merge Sort ────────────────────────────────────────────

    def nodos_ordenados_por(self, clave: str = "x") -> list[Nodo]:
        return merge_sort_nodos(list(self.nodos.values()), clave)

    # ── Utilidades de zona ────────────────────────────────────

    def nodos_en_zona(self, zona: str) -> list[str]:
        return list(self.zonas.get(zona, set()))

    def zona_de_nodo(self, nid: str) -> str:
        if nid not in self.nodos:
            return "CENTRO"
        return _zona_de_lon(self.nodos[nid].lon)

    def stats(self) -> dict:
        total_aristas = sum(len(v) for v in self.adyacencia.values()) // 2
        return {
            "nodos":   len(self.nodos),
            "aristas": total_aristas,
            "zonas":   {z: len(ids) for z, ids in self.zonas.items()},
            "fuente":  self.fuente,
            "place":   _PLACE_QUERY,
        }

    def invalidar_cache(self):
        if os.path.exists(_CACHE_FILE):
            os.remove(_CACHE_FILE)
            print(f"  [GrafoOSM] Caché eliminada.")


# Alias de compatibilidad con algoritmos.py
GrafoSanSebastian = GrafoOSM
