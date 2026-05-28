"""
grafo_san_sebastian.py
Grafo de calles y puntos de interés — San Sebastián, Cusco.
Programación III — UNSAAC 2026

Algoritmos incorporados:
  • Par de Puntos Más Cercanos  — O(n log n)  divide y vencerás geométrico
  • Coloreo de Grafos           — O(V² + E)   Welsh-Powell (grado descendente)
  • Exponenciación Rápida       — O(log e)    usada en cálculo de pesos
  • Merge Sort                  — O(n log n)  ordenar nodos por coordenada
"""

import math
import heapq
from modelos import Nodo, Arista

# ─────────────────────────── proyección ──────────────────────────────────────
CANVAS_W = 800
CANVAS_H = 600
LAT_MIN, LAT_MAX = -13.565, -13.510
LON_MIN, LON_MAX = -71.975, -71.920


def latlon_a_px(lat: float, lon: float) -> tuple[int, int]:
    margin = 50
    w = CANVAS_W - 2 * margin
    h = CANVAS_H - 2 * margin
    x = int(margin + (lon - LON_MIN) / (LON_MAX - LON_MIN) * w)
    y = int(margin + (1 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * h)
    return x, y


# ══════════════════════════════════════════════════════════════
#  EXPONENCIACIÓN RÁPIDA — O(log e)
#  Usada para calcular potencias de distancias/pesos
#  sin multiplicaciones innecesarias.
# ══════════════════════════════════════════════════════════════

def expo_rapida(base: float, exp: int) -> float:
    """
    Calcula base^exp en O(log exp) multiplicaciones.
    Algoritmo: exponenciación binaria (square-and-multiply).
    Útil para escalar distancias o calcular penalizaciones
    exponenciales en rutas largas.
    """
    resultado = 1.0
    base = float(base)
    while exp > 0:
        if exp % 2 == 1:          # bit menos significativo = 1
            resultado *= base
        base *= base
        exp //= 2
    return resultado


def penalizacion_distancia(distancia_m: float,
                           factor: float = 1.0001,
                           tramos: int = 1) -> float:
    """
    Penalización exponencial para rutas largas:
      penalización = factor ^ tramos
    Multiplica la distancia base por este factor.
    Usa expo_rapida internamente.
    """
    return distancia_m * expo_rapida(factor, tramos)


# ══════════════════════════════════════════════════════════════
#  MERGE SORT — O(n log n)
#  Ordena lista de Nodos por coordenada x o y.
#  Necesario como paso previo al algoritmo
#  de Par de Puntos Más Cercanos.
# ══════════════════════════════════════════════════════════════

def merge_sort_nodos(nodos: list[Nodo],
                     clave: str = "x") -> list[Nodo]:
    """
    Merge Sort estable sobre lista de Nodos.
    clave: 'x' | 'y' | 'lat' | 'lon'
    Complejidad: O(n log n) tiempo, O(n) espacio.
    """
    if len(nodos) <= 1:
        return nodos

    mid = len(nodos) // 2
    izq = merge_sort_nodos(nodos[:mid],  clave)
    der = merge_sort_nodos(nodos[mid:],  clave)
    return _merge(izq, der, clave)


def _merge(izq: list[Nodo], der: list[Nodo],
           clave: str) -> list[Nodo]:
    resultado = []
    i = j = 0

    def val(n: Nodo) -> float:
        return getattr(n, clave)

    while i < len(izq) and j < len(der):
        if val(izq[i]) <= val(der[j]):
            resultado.append(izq[i]); i += 1
        else:
            resultado.append(der[j]); j += 1
    resultado.extend(izq[i:])
    resultado.extend(der[j:])
    return resultado


# ══════════════════════════════════════════════════════════════
#  PAR DE PUNTOS MÁS CERCANOS — O(n log n)
#  Divide y vencerás geométrico sobre los nodos del grafo.
#  Retorna el par de nodos más próximos (útil para asignar
#  el repartidor al pedido/nodo más cercano en O(n log n)
#  en lugar de O(n²) con fuerza bruta).
# ══════════════════════════════════════════════════════════════

def _dist_euclidea(a: Nodo, b: Nodo) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _closest_fuerza_bruta(pts: list[Nodo]) -> tuple[float, Nodo, Nodo]:
    """Fuerza bruta O(n²) para n ≤ 3."""
    min_d = float("inf")
    p1 = p2 = pts[0]
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = _dist_euclidea(pts[i], pts[j])
            if d < min_d:
                min_d = d
                p1, p2 = pts[i], pts[j]
    return min_d, p1, p2


def _closest_franja(franja: list[Nodo], d: float,
                    best_p1: Nodo, best_p2: Nodo
                    ) -> tuple[float, Nodo, Nodo]:
    """Revisa la franja central (ordenada por y) en O(n)."""
    # Merge sort la franja por y
    franja_y = merge_sort_nodos(franja, "y")
    min_d = d

    for i in range(len(franja_y)):
        j = i + 1
        while j < len(franja_y) and \
              (franja_y[j].y - franja_y[i].y) < min_d:
            dist = _dist_euclidea(franja_y[i], franja_y[j])
            if dist < min_d:
                min_d = dist
                best_p1, best_p2 = franja_y[i], franja_y[j]
            j += 1
    return min_d, best_p1, best_p2


def _closest_rec(pts_x: list[Nodo]
                 ) -> tuple[float, Nodo, Nodo]:
    """
    Función recursiva principal del algoritmo.
    pts_x debe estar ordenado por coordenada x (Merge Sort).
    """
    n = len(pts_x)
    if n <= 3:
        return _closest_fuerza_bruta(pts_x)

    mid = n // 2
    mitad_x = pts_x[mid].x

    izq_res = _closest_rec(pts_x[:mid])
    der_res = _closest_rec(pts_x[mid:])

    if izq_res[0] < der_res[0]:
        d, p1, p2 = izq_res
    else:
        d, p1, p2 = der_res

    # Franja de ancho 2d alrededor de la línea media
    franja = [p for p in pts_x if abs(p.x - mitad_x) < d]
    return _closest_franja(franja, d, p1, p2)


def par_mas_cercano(nodos: list[Nodo]
                    ) -> tuple[float, Nodo, Nodo]:
    """
    Algoritmo Par de Puntos Más Cercanos — O(n log n).
    Divide y Vencerás sobre coordenadas pixel (x, y).

    Uso en el sistema:
      Dado un conjunto de nodos-destino con pedidos pendientes,
      encuentra los dos puntos más próximos entre sí para
      optimizar el orden de visita inicial del repartidor.

    Retorna: (distancia_px, nodo_A, nodo_B)
    """
    if len(nodos) < 2:
        raise ValueError("Se necesitan al menos 2 nodos.")
    pts_x = merge_sort_nodos(list(nodos), "x")
    return _closest_rec(pts_x)


# ══════════════════════════════════════════════════════════════
#  COLOREO DE GRAFOS — Welsh-Powell  O(V² + E)
#  Asigna zonas/colores a nodos de modo que nodos adyacentes
#  tengan colores distintos. Útil para:
#    • Visualizar zonas sin conflicto en el canvas
#    • Asignar repartidores a sectores sin solapamiento
# ══════════════════════════════════════════════════════════════

def coloreo_grafos(adyacencia: dict[str, list]) -> dict[str, int]:
    """
    Algoritmo de coloreo Welsh-Powell:
      1. Ordenar vértices por grado descendente  (Quick Sort interno)
      2. Asignar el menor color disponible a cada vértice
         que no choque con sus vecinos ya coloreados.

    Complejidad: O(V² + E) en el peor caso.
    Garantía: usa a lo sumo Δ+1 colores (Δ = grado máximo).

    Retorna: dict {nodo_id → color_int (0-based)}
    """
    # Calcular grados
    grados = {v: len(vecinos) for v, vecinos in adyacencia.items()}

    # Quick Sort por grado descendente (implementación propia)
    vertices = _quick_sort_por_grado(list(grados.keys()), grados)

    color_asignado: dict[str, int] = {}

    for v in vertices:
        # Colores usados por los vecinos ya coloreados
        vecinos_ids = set(vid for (vid, *_) in adyacencia.get(v, []))
        colores_vecinos = {
            color_asignado[u]
            for u in vecinos_ids
            if u in color_asignado
        }
        # Asignar el menor color no usado
        color = 0
        while color in colores_vecinos:
            color += 1
        color_asignado[v] = color

    return color_asignado


def _quick_sort_por_grado(vertices: list[str],
                          grados: dict[str, int]) -> list[str]:
    """
    Quick Sort descendente por grado — O(n log n) promedio.
    Pivote: elemento central.
    """
    if len(vertices) <= 1:
        return vertices

    pivot_idx = len(vertices) // 2
    pivot = vertices[pivot_idx]
    pivot_grado = grados[pivot]

    menores  = [v for v in vertices if v != pivot and grados[v] <  pivot_grado]
    iguales  = [v for v in vertices if grados[v] == pivot_grado]
    mayores  = [v for v in vertices if v != pivot and grados[v] >  pivot_grado]

    # Orden descendente: mayores primero
    return (_quick_sort_por_grado(mayores, grados) +
            iguales +
            _quick_sort_por_grado(menores, grados))


# ══════════════════════════════════════════════════════════════
#  NODOS Y ARISTAS DE SAN SEBASTIÁN
# ══════════════════════════════════════════════════════════════

def crear_nodos() -> dict[str, Nodo]:
    datos = [
        ("DEPOSITO",    "Depósito Central (Av. La Cultura)",   -13.5178, -71.9621, True),
        ("PLAZA_SS",    "Plaza de San Sebastián",              -13.5312, -71.9493, False),
        ("MERCADO",     "Mercado San Sebastián",               -13.5330, -71.9510, False),
        ("HOSP_SS",     "Centro de Salud San Sebastián",       -13.5295, -71.9472, False),
        ("AV_CULTURA",  "Av. La Cultura / Prolongación",       -13.5190, -71.9580, False),
        ("TTIO",        "Terminal Terrestre / Av. Velasco",    -13.5150, -71.9650, False),
        ("LARAPA",      "Urb. Larapa",                         -13.5270, -71.9420, False),
        ("ANGOSTURA",   "Sector Angostura",                    -13.5400, -71.9550, False),
        ("VILLA_SOL",   "Villa El Sol",                        -13.5360, -71.9480, False),
        ("KORIPATA",    "Koripata / Av. Tomasa Tito",          -13.5230, -71.9540, False),
        ("CACHIMAYO",   "Cachimayo",                           -13.5450, -71.9600, False),
        ("SANTA_ANA",   "Santa Ana – San Sebastián",           -13.5350, -71.9430, False),
        ("URB_MAG",     "Urb. Magisterio",                     -13.5210, -71.9510, False),
        ("PASO_SUYO",   "Paso Suyos",                          -13.5480, -71.9520, False),
        ("AV_EJÉRCITO", "Av. del Ejército / Ovalo",            -13.5170, -71.9700, False),
        ("CLORINDA",    "Urb. Clorinda Matto",                 -13.5250, -71.9460, False),
        ("TTIKA",       "Sector Ttica Ttica",                  -13.5300, -71.9560, False),
        ("WIMPILLAY",   "Wimpillay",                           -13.5420, -71.9480, False),
        ("PATA_PATA",   "Pata Pata (altura)",                  -13.5380, -71.9390, False),
        ("KENAJPATA",   "Kenajpata",                           -13.5500, -71.9450, False),
    ]
    nodos = {}
    for id_, nombre, lat, lon, deposito in datos:
        x, y = latlon_a_px(lat, lon)
        nodos[id_] = Nodo(id=id_, nombre=nombre, lat=lat, lon=lon,
                          x=x, y=y, es_deposito=deposito)
    return nodos


def crear_aristas() -> list[Arista]:
    datos = [
        ("DEPOSITO",    "AV_CULTURA",   600,   3.0,  "Av. La Cultura"),
        ("DEPOSITO",    "TTIO",         900,   5.0,  "Av. La Cultura Norte"),
        ("AV_CULTURA",  "KORIPATA",     700,   4.0,  "Prolongación Av. La Cultura"),
        ("AV_CULTURA",  "URB_MAG",      500,   3.0,  "Jr. Los Pinos"),
        ("AV_CULTURA",  "AV_EJÉRCITO",  1200,  6.0,  "Av. La Cultura"),
        ("TTIO",        "AV_EJÉRCITO",  800,   4.5,  "Av. Velasco Astete"),
        ("KORIPATA",    "PLAZA_SS",     900,   5.0,  "Av. San Sebastián"),
        ("KORIPATA",    "TTIKA",        600,   3.5,  "Jr. Ttica Ttica"),
        ("KORIPATA",    "CLORINDA",     550,   3.0,  "Jr. Clorinda Matto"),
        ("URB_MAG",     "CLORINDA",     400,   2.5,  "Jr. Magisterio"),
        ("PLAZA_SS",    "MERCADO",      350,   2.0,  "Jr. del Cementerio"),
        ("PLAZA_SS",    "HOSP_SS",      400,   2.5,  "Jr. Municipalidad"),
        ("PLAZA_SS",    "VILLA_SOL",    700,   4.0,  "Av. Prolongación San Sebastián"),
        ("PLAZA_SS",    "SANTA_ANA",    600,   3.5,  "Jr. Santa Ana"),
        ("MERCADO",     "TTIKA",        500,   3.0,  "Jr. Mercado"),
        ("MERCADO",     "ANGOSTURA",    800,   5.0,  "Camino a Angostura"),
        ("HOSP_SS",     "LARAPA",       700,   4.0,  "Jr. Larapa"),
        ("HOSP_SS",     "CLORINDA",     500,   3.0,  "Jr. Salud"),
        ("VILLA_SOL",   "WIMPILLAY",    600,   3.5,  "Pasaje El Sol"),
        ("VILLA_SOL",   "ANGOSTURA",    700,   4.0,  "Camino Angostura"),
        ("LARAPA",      "PATA_PATA",    900,   5.0,  "Subida Larapa"),
        ("LARAPA",      "SANTA_ANA",    800,   4.5,  "Jr. Larapa Baja"),
        ("ANGOSTURA",   "CACHIMAYO",    1000,  6.0,  "Carretera Cachimayo"),
        ("ANGOSTURA",   "PASO_SUYO",    900,   5.5,  "Camino Paso Suyo"),
        ("WIMPILLAY",   "KENAJPATA",    800,   5.0,  "Camino a Kenajpata"),
        ("WIMPILLAY",   "PASO_SUYO",    700,   4.5,  "Jr. Wimpillay"),
        ("SANTA_ANA",   "PATA_PATA",    700,   4.5,  "Subida Santa Ana"),
        ("CACHIMAYO",   "KENAJPATA",    900,   5.5,  "Camino rural"),
        ("PASO_SUYO",   "KENAJPATA",    700,   4.5,  "Pasaje Sur"),
        ("TTIKA",       "ANGOSTURA",    600,   3.5,  "Jr. Ttica Ttica Sur"),
        ("CLORINDA",    "PLAZA_SS",     700,   4.0,  "Jr. Clorinda"),
        ("PATA_PATA",   "KENAJPATA",    1100,  7.0,  "Camino de altura"),
    ]
    aristas = []
    for origen, destino, dist, tiempo, calle in datos:
        aristas.append(Arista(
            origen=origen, destino=destino,
            distancia=dist, tiempo=tiempo,
            bidireccional=True, nombre_calle=calle
        ))
    return aristas


# ══════════════════════════════════════════════════════════════
#  CLASE PRINCIPAL DEL GRAFO
# ══════════════════════════════════════════════════════════════

ZONAS = {
    "NORTE":  {"DEPOSITO", "AV_CULTURA", "TTIO", "AV_EJÉRCITO", "URB_MAG"},
    "CENTRO": {"PLAZA_SS", "MERCADO", "HOSP_SS", "KORIPATA",
               "CLORINDA", "TTIKA", "LARAPA"},
    "SUR":    {"VILLA_SOL", "ANGOSTURA", "WIMPILLAY", "SANTA_ANA",
               "PATA_PATA", "CACHIMAYO", "PASO_SUYO", "KENAJPATA"},
}


class GrafoSanSebastian:
    """
    Grafo no dirigido ponderado — calles de San Sebastián.
    Incluye:
      • Dijkstra              O((V+E) log V)
      • Par de Puntos Más Cercanos  O(n log n)
      • Coloreo de Grafos     O(V²+E)
      • Merge Sort de nodos   O(n log n)
      • Exponenciación Rápida O(log e)
    """

    def __init__(self):
        self.nodos: dict[str, Nodo] = crear_nodos()
        self._aristas_raw: list[Arista] = crear_aristas()
        self.adyacencia: dict[str, list] = {nid: [] for nid in self.nodos}
        self._construir_adyacencia()

        # Coloreo calculado una vez y cacheado
        self._coloreo: dict[str, int] | None = None

    def _construir_adyacencia(self):
        for a in self._aristas_raw:
            if a.origen in self.adyacencia and a.destino in self.adyacencia:
                self.adyacencia[a.origen].append(
                    (a.destino, a.distancia, a.tiempo, a.nombre_calle, a.bloqueada))
                if a.bidireccional:
                    self.adyacencia[a.destino].append(
                        (a.origen, a.distancia, a.tiempo, a.nombre_calle, a.bloqueada))

    # ── Consultas básicas ──────────────────────────────────────

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

    # ── Bloqueo de calles ──────────────────────────────────────

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

    # ── Dijkstra — O((V+E) log V) ─────────────────────────────

    def dijkstra(self, inicio: str, fin: str,
                 usar_tiempo: bool = False) -> tuple[list[str], float]:
        """
        Dijkstra con min-heap.
        Retorna (ruta_ids, costo_total).
        Integra penalizacion_distancia (expo_rapida) por tramo.
        """
        dist   = {n: float("inf") for n in self.nodos}
        prev   = {n: None         for n in self.nodos}
        tramos = {n: 0            for n in self.nodos}
        dist[inicio] = 0
        heap = [(0.0, inicio)]

        while heap:
            costo, u = heapq.heappop(heap)
            if u == fin:
                break
            if costo > dist[u]:
                continue
            for vecino, d, t, *_ in self.vecinos(u):
                peso_base = t if usar_tiempo else d
                # Penalización exponencial suave por tramos (expo_rapida)
                peso = penalizacion_distancia(peso_base, 1.0001,
                                              tramos[u] + 1)
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

    # ── Par de Puntos Más Cercanos — O(n log n) ───────────────

    def par_nodos_mas_cercanos(self,
                               nodos_ids: list[str] | None = None
                               ) -> tuple[float, str, str]:
        """
        Dado un subconjunto de nodos (o todos si None),
        retorna (distancia_px, id_nodo_A, id_nodo_B).
        Divide y vencerás geométrico O(n log n).
        """
        ids = nodos_ids if nodos_ids else list(self.nodos.keys())
        pts = [self.nodos[i] for i in ids if i in self.nodos]
        if len(pts) < 2:
            raise ValueError("Se necesitan al menos 2 nodos.")
        dist, a, b = par_mas_cercano(pts)
        return dist, a.id, b.id

    # ── Coloreo de Grafos — O(V²+E) ───────────────────────────

    def obtener_coloreo(self, recalcular: bool = False) -> dict[str, int]:
        """
        Welsh-Powell sobre la adyacencia del grafo.
        Cachea el resultado; recalcular=True fuerza nuevo cálculo.
        Retorna {nodo_id → color_int}.
        """
        if self._coloreo is None or recalcular:
            # Construir adyacencia simplificada (solo ids de vecinos)
            ady_simple = {
                nid: [(v, *_) for v, *_ in lst]
                for nid, lst in self.adyacencia.items()
            }
            self._coloreo = coloreo_grafos(ady_simple)
        return self._coloreo

    def nodos_por_color(self) -> dict[int, list[str]]:
        """
        Invierte el coloreo: color → [lista de nodo_ids].
        Útil para asignar repartidores a grupos de nodos
        sin superposición geográfica.
        """
        coloreo = self.obtener_coloreo()
        grupos: dict[int, list[str]] = {}
        for nid, color in coloreo.items():
            grupos.setdefault(color, []).append(nid)
        return grupos

    # ── Nodos ordenados por Merge Sort ────────────────────────

    def nodos_ordenados_por(self, clave: str = "x") -> list[Nodo]:
        """
        Retorna lista de Nodos ordenada por clave (Merge Sort).
        clave: 'x' | 'y' | 'lat' | 'lon'
        """
        return merge_sort_nodos(list(self.nodos.values()), clave)

