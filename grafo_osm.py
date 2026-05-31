"""
grafo_osm.py
Grafo real de calles — San Sebastián, Cusco.
Basado en OpenStreetMap via OSMnx + NetworkX.
Programación III — UNSAAC 2026

Reemplaza a grafo_san_sebastian.py manteniendo la misma interfaz
pública para que algoritmos.py y gui.py funcionen sin modificación.

Dependencias:
    pip install osmnx networkx shapely

Algoritmos propios incorporados (igual que el original):
  • Dijkstra propio          — O((V+E) log V)   sobre el grafo OSM
  • Par de Puntos Más Cercanos — O(n log n)      divide y vencerás geométrico
  • Coloreo Welsh-Powell     — O(V²+E)           sobre adyacencia OSM
  • Merge Sort               — O(n log n)        ordenar nodos por coordenada
  • Exponenciación Rápida    — O(log e)          penalización por tramos
"""

from __future__ import annotations

import math
import heapq
import time
import os
import pickle
import logging
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx

# OSMnx es la única dependencia nueva; se importa con manejo de error claro.
try:
    import osmnx as ox
    _OSMNX_OK = True
except ImportError:
    _OSMNX_OK = False

from modelos import Nodo, Arista

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────

# Lugar a consultar en OpenStreetMap. Puedes cambiarlo si necesitas otra zona.
_PLACE_QUERY = "San Sebastián, Cusco, Peru"

# OSMnx configuración recomendada
if _OSMNX_OK:
    ox.settings.log_console = False
    ox.settings.use_cache   = True           # cachea en disco automáticamente
    ox.settings.timeout     = 60

# Caché local adicional (grafo procesado → .pkl) para no re-procesar en cada run.
_CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache_osm")
_CACHE_FILE = os.path.join(_CACHE_DIR, "san_sebastian_grafo.pkl")

# Proyección canvas — se recalcula dinámicamente según el bounding box del grafo.
CANVAS_W = 900
CANVAS_H = 650

# ─────────────────────────────────────────────────────────────────────────────
#  ZONAS GEOGRÁFICAS (latitudes/longitudes aproximadas de San Sebastián)
#  Los nodos se asignan automáticamente según su longitud.
# ─────────────────────────────────────────────────────────────────────────────

# Umbral de longitud para dividir Oeste / Centro / Este
# San Sebastián se extiende aprox. entre lon -71.975 y -71.920
_LON_OESTE_LIM  = -71.960   # más al oeste que esto → OESTE
_LON_ESTE_LIM   = -71.935   # más al este que esto  → ESTE
# entre _LON_OESTE_LIM y _LON_ESTE_LIM → CENTRO

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
    """
    Calcula base^exp en O(log exp) multiplicaciones.
    Algoritmo square-and-multiply.
    """
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
    """Penalización suave por número de tramos recorridos."""
    return distancia_m * expo_rapida(factor, tramos)


# ─────────────────────────────────────────────────────────────────────────────
#  MERGE SORT DE NODOS — O(n log n)
# ─────────────────────────────────────────────────────────────────────────────

def merge_sort_nodos(nodos: list[Nodo], clave: str = "x") -> list[Nodo]:
    """Merge Sort estable sobre Nodos. clave: 'x'|'y'|'lat'|'lon'"""
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
    """Fuerza bruta O(n²) para n ≤ 3."""
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
    """Par de Puntos Más Cercanos — O(n log n). Retorna (dist_px, nodo_A, nodo_B)."""
    if len(nodos) < 2:
        raise ValueError("Se necesitan al menos 2 nodos.")
    return _closest_rec(merge_sort_nodos(list(nodos), "x"))


# ─────────────────────────────────────────────────────────────────────────────
#  COLOREO DE GRAFOS — Welsh-Powell  O(V²+E)
# ─────────────────────────────────────────────────────────────────────────────

def coloreo_grafos(adyacencia: dict[str, list]) -> dict[str, int]:
    """
    Welsh-Powell:
      1. Quick Sort de vértices por grado descendente.
      2. Asignar el menor color disponible que no colisione con vecinos.
    Retorna {nodo_id → color_int (0-based)}.
    """
    # Calcular grados
    grados = {v: len(vecinos) for v, vecinos in adyacencia.items()}

    # Quick Sort por grado descendente (propio)
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


def _qs_grados(arr: list[str], lo: int, hi: int,
               grados: dict[str, int]):
    """Quick Sort in-place descendente por grado."""
    if lo < hi:
        p = _part_grados(arr, lo, hi, grados)
        _qs_grados(arr, lo, p - 1, grados)
        _qs_grados(arr, p + 1, hi, grados)


def _part_grados(arr: list[str], lo: int, hi: int,
                 grados: dict[str, int]) -> int:
    pivot = grados[arr[(lo + hi) // 2]]
    arr[(lo + hi) // 2], arr[hi] = arr[hi], arr[(lo + hi) // 2]
    i = lo - 1
    for j in range(lo, hi):
        if grados[arr[j]] >= pivot:   # descendente
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
    return i + 1


# ─────────────────────────────────────────────────────────────────────────────
#  UTILIDADES DE CONVERSIÓN OSMnx ↔ Nodo/Arista propio
# ─────────────────────────────────────────────────────────────────────────────

def _nodo_id_from_osmid(osmid: int) -> str:
    """Convierte el osmid numérico en string corto para la GUI."""
    return f"N{osmid}"


def _latlon_a_px(lat: float, lon: float,
                 lat_min: float, lat_max: float,
                 lon_min: float, lon_max: float,
                 margin: int = 50) -> tuple[int, int]:
    """Proyecta lat/lon a coordenadas pixel del canvas."""
    w = CANVAS_W - 2 * margin
    h = CANVAS_H - 2 * margin
    x = int(margin + (lon - lon_min) / max(lon_max - lon_min, 1e-9) * w)
    y = int(margin + (1 - (lat - lat_min) / max(lat_max - lat_min, 1e-9)) * h)
    return x, y


def _nombre_calle_osm(datos: dict) -> str:
    """Extrae el nombre de la calle de los atributos de la arista OSM."""
    name = datos.get("name", "")
    if isinstance(name, list):
        name = name[0]
    return name or datos.get("highway", "calle")


def _distancia_m(datos: dict) -> float:
    """Longitud de la arista en metros."""
    length = datos.get("length", 0.0)
    return float(length) if length else 0.0


def _velocidad_kmh(datos: dict) -> float:
    """
    Velocidad estimada según tipo de vía (highway).
    Se usa para calcular tiempo de recorrido.
    """
    highway = datos.get("highway", "residential")
    if isinstance(highway, list):
        highway = highway[0]
    tabla = {
        "motorway": 80, "trunk": 60, "primary": 50,
        "secondary": 40, "tertiary": 30,
        "residential": 20, "living_street": 10,
        "service": 15, "unclassified": 20,
        "footway": 5, "path": 5, "cycleway": 15,
    }
    return tabla.get(highway, 20)


def _tiempo_min(distancia_m: float, velocidad_kmh: float) -> float:
    """Tiempo de recorrido en minutos."""
    if velocidad_kmh <= 0:
        return distancia_m / 416.0   # fallback: ~25 km/h en m/min
    return (distancia_m / 1000.0) / velocidad_kmh * 60.0


# ─────────────────────────────────────────────────────────────────────────────
#  GRAFO FALLBACK (sin OSMnx) — nodos manuales de San Sebastián
#  Se usa cuando osmnx no está instalado o la descarga falla.
# ─────────────────────────────────────────────────────────────────────────────

_FALLBACK_NODOS = [
    # (id_str, nombre, lat, lon, es_deposito)
    ("DEPOSITO",    "Depósito Central (Av. La Cultura)",    -13.5178, -71.9490, True),
    ("PLAZA_SS",    "Plaza Principal San Sebastián",         -13.5312, -71.9493, False),
    ("MERCADO",     "Mercado San Sebastián",                 -13.5330, -71.9510, False),
    ("HOSP_SS",     "Centro de Salud San Sebastián",         -13.5295, -71.9472, False),
    ("IGLESIA_SS",  "Iglesia San Sebastián",                 -13.5308, -71.9498, False),
    ("TTIKA",       "Sector Ttica Ttica",                    -13.5300, -71.9560, False),
    ("CLORINDA",    "Urb. Clorinda Matto de Turner",         -13.5250, -71.9460, False),
    ("AV_CULTURA",  "Av. La Cultura (cruce San Sebastián)",  -13.5190, -71.9580, False),
    ("URB_MAG",     "Urb. Magisterio",                       -13.5210, -71.9510, False),
    ("PROLONGACION","Prolongación Av. La Cultura",           -13.5230, -71.9540, False),
    ("MANUEL_P",    "Av. Manuel Prado (ingreso oeste)",      -13.5260, -71.9600, False),
    ("LARAPA",      "Urb. Larapa",                           -13.5270, -71.9420, False),
    ("LARAPA_GR",   "Larapa Grande",                         -13.5255, -71.9385, False),
    ("VILLA_SOL",   "Villa El Sol",                          -13.5360, -71.9480, False),
    ("SANTA_ANA",   "Santa Ana – San Sebastián",             -13.5350, -71.9430, False),
    ("PATA_PATA",   "Pata Pata (zona alta este)",            -13.5380, -71.9390, False),
    ("WIMPILLAY",   "Wimpillay",                             -13.5420, -71.9480, False),
    ("ANGOSTURA",   "Angostura",                             -13.5400, -71.9550, False),
    ("KENAJPATA",   "Kenajpata",                             -13.5500, -71.9450, False),
    ("PASO_SUYO",   "Paso Suyos",                            -13.5480, -71.9520, False),
]

_FALLBACK_ARISTAS = [
    ("DEPOSITO","AV_CULTURA",600,3.0,"Av. La Cultura"),
    ("DEPOSITO","URB_MAG",700,3.5,"Av. La Cultura"),
    ("DEPOSITO","PROLONGACION",800,4.0,"Prolongación Av. La Cultura"),
    ("AV_CULTURA","URB_MAG",500,3.0,"Jr. Los Pinos"),
    ("AV_CULTURA","MANUEL_P",600,3.5,"Av. Manuel Prado"),
    ("AV_CULTURA","PROLONGACION",400,2.5,"Prolongación La Cultura"),
    ("URB_MAG","CLORINDA",400,2.5,"Jr. Magisterio"),
    ("PROLONGACION","PLAZA_SS",700,4.0,"Av. San Sebastián"),
    ("PROLONGACION","TTIKA",600,3.5,"Jr. Ttica Ttica"),
    ("MANUEL_P","PLAZA_SS",500,3.0,"Jr. Manuel Prado"),
    ("PLAZA_SS","MERCADO",350,2.0,"Jr. del Cementerio"),
    ("PLAZA_SS","HOSP_SS",400,2.5,"Jr. Municipalidad"),
    ("PLAZA_SS","IGLESIA_SS",150,1.0,"Jr. frente Iglesia"),
    ("PLAZA_SS","CLORINDA",500,3.0,"Jr. Clorinda"),
    ("IGLESIA_SS","MERCADO",300,2.0,"Jr. del Mercado"),
    ("HOSP_SS","CLORINDA",500,3.0,"Jr. Salud"),
    ("TTIKA","MERCADO",500,3.0,"Jr. Mercado"),
    ("HOSP_SS","LARAPA",700,4.0,"Jr. Larapa"),
    ("MERCADO","VILLA_SOL",700,4.0,"Av. Prol. San Sebastián"),
    ("PLAZA_SS","SANTA_ANA",600,3.5,"Jr. Santa Ana"),
    ("CLORINDA","LARAPA",550,3.0,"Camino a Larapa"),
    ("LARAPA","LARAPA_GR",500,3.0,"Camino Larapa Grande"),
    ("LARAPA","SANTA_ANA",800,4.5,"Jr. Larapa Baja"),
    ("LARAPA","PATA_PATA",900,5.0,"Subida Larapa"),
    ("LARAPA_GR","PATA_PATA",700,4.0,"Subida Larapa Grande"),
    ("VILLA_SOL","WIMPILLAY",600,3.5,"Pasaje El Sol"),
    ("VILLA_SOL","ANGOSTURA",700,4.0,"Camino Angostura"),
    ("SANTA_ANA","PATA_PATA",700,4.5,"Subida Santa Ana"),
    ("SANTA_ANA","WIMPILLAY",650,4.0,"Jr. Santa Ana Sur"),
    ("ANGOSTURA","PASO_SUYO",900,5.5,"Camino Paso Suyo"),
    ("WIMPILLAY","KENAJPATA",800,5.0,"Camino a Kenajpata"),
    ("WIMPILLAY","PASO_SUYO",700,4.5,"Jr. Wimpillay"),
    ("PASO_SUYO","KENAJPATA",700,4.5,"Pasaje Sur"),
    ("PATA_PATA","KENAJPATA",1100,7.0,"Camino de altura"),
    ("TTIKA","ANGOSTURA",600,3.5,"Jr. Ttica Ttica Sur"),
]


def _construir_fallback() -> tuple[dict[str, Nodo], list[Arista], dict[str, set]]:
    """Construye el grafo manual cuando OSMnx no está disponible."""
    lats = [r[2] for r in _FALLBACK_NODOS]
    lons = [r[3] for r in _FALLBACK_NODOS]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    nodos: dict[str, Nodo] = {}
    for id_, nombre, lat, lon, dep in _FALLBACK_NODOS:
        x, y = _latlon_a_px(lat, lon, lat_min, lat_max, lon_min, lon_max)
        nodos[id_] = Nodo(id=id_, nombre=nombre, lat=lat, lon=lon,
                          x=x, y=y, es_deposito=dep)

    aristas = [
        Arista(origen=o, destino=d, distancia=dist, tiempo=t,
               bidireccional=True, nombre_calle=c)
        for o, d, dist, t, c in _FALLBACK_ARISTAS
    ]

    zonas: dict[str, set] = {"OESTE": set(), "CENTRO": set(), "ESTE": set()}
    for nid, nodo in nodos.items():
        zonas[_zona_de_lon(nodo.lon)].add(nid)

    return nodos, aristas, zonas


# ─────────────────────────────────────────────────────────────────────────────
#  DESCARGA Y PROCESAMIENTO DEL GRAFO OSMnx
# ─────────────────────────────────────────────────────────────────────────────

def _descargar_o_cargar_grafo() -> tuple[dict[str, Nodo], list[Arista], dict[str, set], nx.MultiDiGraph | None]:
    """
    Intenta cargar desde caché local primero, luego descarga de OSMnx.
    Retorna (nodos, aristas, zonas, G_nx) donde G_nx puede ser None en fallback.
    """
    # ── Caché local ───────────────────────────────────────────
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "rb") as f:
                cached = pickle.load(f)
            print(f"  [OSM] Grafo cargado desde caché: {_CACHE_FILE}")
            return cached["nodos"], cached["aristas"], cached["zonas"], cached["G_nx"]
        except Exception as e:
            print(f"  [OSM] Caché inválida, re-descargando: {e}")

    # ── Sin OSMnx → fallback ──────────────────────────────────
    if not _OSMNX_OK:
        print("  [OSM] osmnx no instalado → usando grafo manual de respaldo.")
        nodos, aristas, zonas = _construir_fallback()
        return nodos, aristas, zonas, None

    # ── Descarga desde OpenStreetMap ──────────────────────────
    print(f"  [OSM] Descargando grafo de '{_PLACE_QUERY}' desde OpenStreetMap…")
    try:
        G_raw = ox.graph_from_place(
            _PLACE_QUERY,
            network_type="drive",
            simplify=True,
            retain_all=False,
        )
        
        # --- EL FILTRO BRUTAL PARA QUE NO SE LAGEE ---
        vias_importantes = ['primary', 'secondary', 'tertiary', 'residential', 'trunk']
        aristas_filtradas = [
            (u, v, k, d) for u, v, k, d in G_raw.edges(keys=True, data=True)
            if d.get('highway') in vias_importantes
        ]
        
        G = nx.MultiDiGraph()
        for u, v, k, d in aristas_filtradas:
            G.add_node(u, **G_raw.nodes[u])
            G.add_node(v, **G_raw.nodes[v])
            G.add_edge(u, v, key=k, **d)
        # ---------------------------------------------

        # Proyectar a UTM para tener distancias en metros exactas
        G = ox.project_graph(G)
        # Agregar atributo 'speed_kph' y 'travel_time' a todas las aristas
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)

    except Exception as e:
        print(f"  [OSM] Error al descargar: {e}\n  → Usando grafo manual de respaldo.")
        nodos, aristas, zonas = _construir_fallback()
        return nodos, aristas, zonas, None


def _procesar_grafo_osm(G: nx.MultiDiGraph) -> tuple[dict[str, Nodo], list[Arista], dict[str, set]]:
    """
    Convierte el MultiDiGraph de OSMnx a nodos/aristas del sistema.

    Estrategia de simplificación de IDs:
      - osmid (entero) → "N{osmid}" como string
      - El depósito se asigna al nodo más cercano a la Av. La Cultura
        en los límites de San Sebastián.
    """
    # ── Bounding box para proyección pixel ───────────────────
    lats = [data["lat"] for _, data in G.nodes(data=True) if "lat" in data]
    lons = [data["lon"] for _, data in G.nodes(data=True) if "lon" in data]

    # Si el grafo fue proyectado a UTM, recuperar lat/lon originales
    if not lats:
        G_latlon = ox.project_graph(G, to_crs="EPSG:4326")
        lats = [data.get("y", 0) for _, data in G_latlon.nodes(data=True)]
        lons = [data.get("x", 0) for _, data in G_latlon.nodes(data=True)]
        lat_by_id  = {n: data.get("y", 0) for n, data in G_latlon.nodes(data=True)}
        lon_by_id  = {n: data.get("x", 0) for n, data in G_latlon.nodes(data=True)}
    else:
        lat_by_id = {n: data["lat"] for n, data in G.nodes(data=True)}
        lon_by_id = {n: data["lon"] for n, data in G.nodes(data=True)}

    # Obtener lat/lon del grafo original (antes de proyectar a UTM)
    G_geo = ox.project_graph(G, to_crs="EPSG:4326")
    lat_by_id = {n: data.get("y", 0) for n, data in G_geo.nodes(data=True)}
    lon_by_id = {n: data.get("x", 0) for n, data in G_geo.nodes(data=True)}

    lats = list(lat_by_id.values())
    lons = list(lon_by_id.values())
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)

    # ── Nodos ─────────────────────────────────────────────────
    nodos: dict[str, Nodo] = {}

    # Nodo de depósito: el más cercano a la coord de Av. La Cultura
    DEPOSITO_LAT, DEPOSITO_LON = -13.5178, -71.9490
    deposito_osmid = min(
        lat_by_id.keys(),
        key=lambda n: (lat_by_id[n] - DEPOSITO_LAT)**2 + (lon_by_id[n] - DEPOSITO_LON)**2
    )

    # Limitar a los N nodos más "conectados" para no saturar la GUI.
    # OSMnx puede devolver cientos de nodos; mantenemos los que tienen
    # grado ≥ 2 (intersecciones reales) más el depósito.
    nodos_relevantes = [
        n for n, deg in dict(G.degree()).items() if deg >= 2
    ]
    if deposito_osmid not in nodos_relevantes:
        nodos_relevantes.append(deposito_osmid)

    # Para los nodos relevantes, obtener nombres de calles cercanas
    street_names_by_node: dict[int, str] = {}
    for u, v, data in G.edges(data=True):
        name = _nombre_calle_osm(data)
        if name and u in nodos_relevantes:
            street_names_by_node.setdefault(u, name)
        if name and v in nodos_relevantes:
            street_names_by_node.setdefault(v, name)

    for osmid in nodos_relevantes:
        nid     = _nodo_id_from_osmid(osmid)
        lat     = lat_by_id.get(osmid, 0)
        lon     = lon_by_id.get(osmid, 0)
        nombre  = street_names_by_node.get(osmid, f"Nodo {osmid}")
        x, y    = _latlon_a_px(lat, lon, lat_min, lat_max, lon_min, lon_max)
        es_dep  = (osmid == deposito_osmid)
        nodos[nid] = Nodo(id=nid, nombre=nombre, lat=lat, lon=lon,
                          x=x, y=y, es_deposito=es_dep)

    # Asegurar que "DEPOSITO" siempre exista con ese ID fijo
    dep_nid = _nodo_id_from_osmid(deposito_osmid)
    if dep_nid in nodos:
        dep_copy = nodos.pop(dep_nid)
        dep_nuevo = Nodo(id="DEPOSITO", nombre="Depósito — Av. La Cultura",
                         lat=dep_copy.lat, lon=dep_copy.lon,
                         x=dep_copy.x, y=dep_copy.y, es_deposito=True)
        nodos["DEPOSITO"] = dep_nuevo
        _id_map = {deposito_osmid: "DEPOSITO"}
    else:
        _id_map = {deposito_osmid: "DEPOSITO"}

    _id_map.update({
        osmid: _nodo_id_from_osmid(osmid)
        for osmid in nodos_relevantes
        if osmid != deposito_osmid
    })

    # ── Aristas ───────────────────────────────────────────────
    aristas: list[Arista] = []
    vistas: set[tuple[str, str]] = set()

    for u, v, data in G.edges(data=True):
        nid_u = _id_map.get(u)
        nid_v = _id_map.get(v)
        if nid_u is None or nid_v is None:
            continue
        if nid_u not in nodos or nid_v not in nodos:
            continue

        par = (min(nid_u, nid_v), max(nid_u, nid_v))
        if par in vistas:
            continue
        vistas.add(par)

        dist_m  = _distancia_m(data)
        vel_kmh = data.get("speed_kph", _velocidad_kmh(data))
        t_min   = data.get("travel_time", _tiempo_min(dist_m, vel_kmh)) / 60.0
        calle   = _nombre_calle_osm(data)

        aristas.append(Arista(
            origen=nid_u, destino=nid_v,
            distancia=dist_m,
            tiempo=t_min,
            bidireccional=True,
            nombre_calle=calle,
            bloqueada=False,
        ))

    # ── Zonas (automáticas por longitud) ─────────────────────
    zonas: dict[str, set] = {"OESTE": set(), "CENTRO": set(), "ESTE": set()}
    for nid, nodo in nodos.items():
        zonas[_zona_de_lon(nodo.lon)].add(nid)

    return nodos, aristas, zonas


# ─────────────────────────────────────────────────────────────────────────────
#  ZONAS (variable pública usada por algoritmos.py)
# ─────────────────────────────────────────────────────────────────────────────

# Se inicializa con el fallback para que los imports de módulo no fallen;
# GrafoOSM.zonas contiene el valor real después de construir el grafo.
ZONAS: dict[str, set] = {
    "OESTE":  set(),
    "CENTRO": set(),
    "ESTE":   set(),
}


# ─────────────────────────────────────────────────────────────────────────────
#  CLASE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class GrafoOSM:
    """
    Grafo de San Sebastián basado en OpenStreetMap (OSMnx + NetworkX).

    Interfaz pública idéntica a GrafoSanSebastian para compatibilidad
    con algoritmos.py y gui.py sin modificaciones.

    Agrega:
      • self.G_nx      — MultiDiGraph de NetworkX (None en fallback)
      • self.zonas     — dict zona → set de nodo_ids
      • self.fuente    — "osm" | "fallback"
      • nx_shortest_path() — atajo a NetworkX para distancias exactas
    """

    def __init__(self, forzar_descarga: bool = False):
        print("  [GrafoOSM] Inicializando…")
        t0 = time.perf_counter()

        if forzar_descarga and os.path.exists(_CACHE_FILE):
            os.remove(_CACHE_FILE)

        self.nodos: dict[str, Nodo]
        self._aristas_raw: list[Arista]
        self.zonas: dict[str, set]
        self.G_nx: nx.MultiDiGraph | None

        self.nodos, self._aristas_raw, self.zonas, self.G_nx = \
            _descargar_o_cargar_grafo()

        self.fuente = "osm" if self.G_nx is not None else "fallback"

        # Actualizar ZONAS global (usado por algoritmos.py)
        ZONAS.clear()
        ZONAS.update(self.zonas)

        # Construir adyacencia propia (misma estructura que el original)
        self.adyacencia: dict[str, list] = {nid: [] for nid in self.nodos}
        self._construir_adyacencia()

        # Coloreo cacheado
        self._coloreo: dict[str, int] | None = None

        t1 = time.perf_counter()
        print(f"  [GrafoOSM] Listo — {len(self.nodos)} nodos, "
              f"{sum(len(v) for v in self.adyacencia.values())//2} aristas "
              f"({self.fuente}) en {t1-t0:.2f}s")

    # ── Construcción de adyacencia ────────────────────────────

    def _construir_adyacencia(self):
        for a in self._aristas_raw:
            if a.origen in self.adyacencia and a.destino in self.adyacencia:
                self.adyacencia[a.origen].append(
                    (a.destino, a.distancia, a.tiempo, a.nombre_calle, a.bloqueada))
                if a.bidireccional:
                    self.adyacencia[a.destino].append(
                        (a.origen, a.distancia, a.tiempo, a.nombre_calle, a.bloqueada))

    # ── API básica (misma que GrafoSanSebastian) ──────────────

    def vecinos(self, nodo_id: str,
                ignorar_bloqueadas: bool = True) -> list[tuple]:
        resultado = []
        for v, d, t, c, bloq in self.adyacencia.get(nodo_id, []):
            if ignorar_bloqueadas and bloq:
                continue
            resultado.append((v, d, t, c))
        return resultado

    def nodo(self, nid: str) -> Nodo:
        return self.nodos[nid]

    def todos_los_nodos_ids(self) -> list[str]:
        return list(self.nodos.keys())

    def distancia_directa(self, a: str, b: str) -> float:
        return self.nodos[a].distancia_a(self.nodos[b])

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
        # También marcar en aristas raw para persistencia
        for a in self._aristas_raw:
            if (a.origen == origen and a.destino == destino) or \
               (a.bidireccional and a.origen == destino and a.destino == origen):
                a.bloqueada = estado

    # ── Dijkstra PROPIO — O((V+E) log V) ─────────────────────

    def dijkstra(self, inicio: str, fin: str,
                 usar_tiempo: bool = False) -> tuple[list[str], float]:
        """
        Dijkstra con min-heap sobre la adyacencia propia.
        Incorpora penalizacion_distancia (expo_rapida) por tramo.
        Retorna (ruta_ids, costo_total).
        """
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

    # ── Dijkstra via NetworkX (opcional, más preciso con OSMnx) ──

    def nx_shortest_path(self, inicio_nid: str, fin_nid: str,
                         weight: str = "length") -> tuple[list[str], float]:
        """
        Camino mínimo usando nx.shortest_path sobre el grafo OSMnx original.
        Solo disponible cuando self.G_nx is not None.
        Útil para comparar contra el Dijkstra propio.
        """
        if self.G_nx is None:
            return self.dijkstra(inicio_nid, fin_nid)

        # Convertir nid → osmid
        nid_a_osmid = {v: k for k, v in
                       {n: f"N{n}" for n in self.G_nx.nodes()}.items()}
        nid_a_osmid["DEPOSITO"] = next(
            (n for n in self.G_nx.nodes()
             if self.nodos.get("DEPOSITO") and
             abs(self.G_nx.nodes[n].get("y", 0) - self.nodos["DEPOSITO"].lat) < 0.0001),
            None
        )

        osmid_i = nid_a_osmid.get(inicio_nid)
        osmid_f = nid_a_osmid.get(fin_nid)
        if osmid_i is None or osmid_f is None:
            return self.dijkstra(inicio_nid, fin_nid)

        try:
            ruta_osm  = nx.shortest_path(self.G_nx, osmid_i, osmid_f, weight=weight)
            costo     = nx.shortest_path_length(self.G_nx, osmid_i, osmid_f, weight=weight)
            osmid_a_nid = {v: k for k, v in nid_a_osmid.items() if v is not None}
            ruta_nids = [osmid_a_nid.get(n, f"N{n}") for n in ruta_osm]
            return ruta_nids, float(costo)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return self.dijkstra(inicio_nid, fin_nid)

    # ── Par de Puntos Más Cercanos — O(n log n) ───────────────

    def par_nodos_mas_cercanos(self,
                               nodos_ids: list[str] | None = None
                               ) -> tuple[float, str, str]:
        """
        Divide y Vencerás geométrico.
        Retorna (distancia_px, id_nodo_A, id_nodo_B).
        """
        ids = nodos_ids if nodos_ids else list(self.nodos.keys())
        pts = [self.nodos[i] for i in ids if i in self.nodos]
        if len(pts) < 2:
            raise ValueError("Se necesitan al menos 2 nodos.")
        dist, a, b = par_mas_cercano(pts)
        return dist, a.id, b.id

    # ── Coloreo de Grafos — Welsh-Powell O(V²+E) ─────────────

    def obtener_coloreo(self, recalcular: bool = False) -> dict[str, int]:
        """
        Welsh-Powell sobre la adyacencia. Cachea el resultado.
        Retorna {nodo_id → color_int}.
        """
        if self._coloreo is None or recalcular:
            ady_simple = {
                nid: [v for v, *_ in lst]
                for nid, lst in self.adyacencia.items()
            }
            self._coloreo = coloreo_grafos(ady_simple)
        return self._coloreo

    def nodos_por_color(self) -> dict[int, list[str]]:
        """Invierte el coloreo: color → [lista de nodo_ids]."""
        coloreo = self.obtener_coloreo()
        grupos: dict[int, list[str]] = {}
        for nid, color in coloreo.items():
            grupos.setdefault(color, []).append(nid)
        return grupos

    # ── Nodos ordenados por Merge Sort ────────────────────────

    def nodos_ordenados_por(self, clave: str = "x") -> list[Nodo]:
        """Merge Sort sobre nodos. clave: 'x'|'y'|'lat'|'lon'"""
        return merge_sort_nodos(list(self.nodos.values()), clave)

    # ── Utilidades extra (no estaban en el original) ──────────

    def nodos_en_zona(self, zona: str) -> list[str]:
        """Lista de nodo_ids en la zona dada ('OESTE'|'CENTRO'|'ESTE')."""
        return list(self.zonas.get(zona, set()))

    def zona_de_nodo(self, nid: str) -> str:
        """Retorna la zona a la que pertenece el nodo."""
        if nid not in self.nodos:
            return "CENTRO"
        return _zona_de_lon(self.nodos[nid].lon)

    def stats(self) -> dict:
        """Estadísticas del grafo para mostrar en la GUI."""
        total_aristas = sum(len(v) for v in self.adyacencia.values()) // 2
        return {
            "nodos":   len(self.nodos),
            "aristas": total_aristas,
            "zonas":   {z: len(ids) for z, ids in self.zonas.items()},
            "fuente":  self.fuente,
            "place":   _PLACE_QUERY,
        }

    def invalidar_cache(self):
        """Elimina el caché para forzar nueva descarga en el próximo inicio."""
        if os.path.exists(_CACHE_FILE):
            os.remove(_CACHE_FILE)
            print(f"  [GrafoOSM] Caché eliminada: {_CACHE_FILE}")


# ─────────────────────────────────────────────────────────────────────────────
#  ALIAS DE COMPATIBILIDAD
#  algoritmos.py importa "GrafoSanSebastian" — este alias lo resuelve
#  sin tocar ningún otro archivo.
# ─────────────────────────────────────────────────────────────────────────────
GrafoSanSebastian = GrafoOSM