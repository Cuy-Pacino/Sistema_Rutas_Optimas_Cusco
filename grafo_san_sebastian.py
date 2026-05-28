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
    while exp > 0:                            # O(log exp) iteraciones — divide exp a la mitad
        if exp % 2 == 1:          # bit menos significativo = 1  # O(1) — bit check
            resultado *= base                                     # O(1) — multiplicación
        base *= base                                              # O(1) — cuadrado
        exp //= 2                                                 # O(1) — desplazamiento
    return resultado
# --- Análisis Exponenciación Rápida ---
# Cada iteración divide exp entre 2  →  T(e) = T(e/2) + O(1)  →  O(log e)


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
    if len(nodos) <= 1:                                        # O(1) — caso base
        return nodos

    mid = len(nodos) // 2                                     # O(1) — punto medio
    izq = merge_sort_nodos(nodos[:mid],  clave)               # T(n/2) — subproblema izquierdo
    der = merge_sort_nodos(nodos[mid:],  clave)               # T(n/2) — subproblema derecho
    return _merge(izq, der, clave)                            # O(n) — fusión
# T(n) = 2·T(n/2) + O(n)  →  Maestro caso 2  →  O(n log n)


def _merge(izq: list[Nodo], der: list[Nodo],
           clave: str) -> list[Nodo]:
    resultado = []
    i = j = 0

    def val(n: Nodo) -> float:
        return getattr(n, clave)                               # O(1) — acceso a atributo

    while i < len(izq) and j < len(der):                      # O(n) — recorre ambas mitades
        if val(izq[i]) <= val(der[j]):                        # O(1) — comparación
            resultado.append(izq[i]); i += 1
        else:
            resultado.append(der[j]); j += 1
    resultado.extend(izq[i:])                                 # O(restante) — copia sobrantes
    resultado.extend(der[j:])
    return resultado
# _merge: O(|izq| + |der|) = O(n)


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
    for i in range(len(pts)):                                  # O(n) — fila exterior
        for j in range(i + 1, len(pts)):                      # O(n) — fila interior → O(n²)
            d = _dist_euclidea(pts[i], pts[j])                # O(1) — distancia euclidea
            if d < min_d:                                     # O(1) — comparación
                min_d = d
                p1, p2 = pts[i], pts[j]
    return min_d, p1, p2
# Solo se llama con n ≤ 3  →  O(1) prácticamente (caso base constante)


def _closest_franja(franja: list[Nodo], d: float,
                    best_p1: Nodo, best_p2: Nodo
                    ) -> tuple[float, Nodo, Nodo]:
    """Revisa la franja central (ordenada por y) en O(n)."""
    # Merge sort la franja por y
    franja_y = merge_sort_nodos(franja, "y")                  # O(n log n) — sort de franja
    min_d = d

    for i in range(len(franja_y)):                            # O(n) — recorre franja
        j = i + 1
        while j < len(franja_y) and \
              (franja_y[j].y - franja_y[i].y) < min_d:       # máx 7 iteraciones por propiedad geométrica
            dist = _dist_euclidea(franja_y[i], franja_y[j])  # O(1)
            if dist < min_d:                                  # O(1)
                min_d = dist
                best_p1, best_p2 = franja_y[i], franja_y[j]
            j += 1
    return min_d, best_p1, best_p2
# Propiedad clave: cada punto compara con ≤ 7 vecinos  →  bucle interno O(1) amortizado  →  O(n)


def _closest_rec(pts_x: list[Nodo]
                 ) -> tuple[float, Nodo, Nodo]:
    """
    Función recursiva principal del algoritmo.
    pts_x debe estar ordenado por coordenada x (Merge Sort).
    """
    n = len(pts_x)
    if n <= 3:                                                 # O(1) — caso base (≤3 puntos)
        return _closest_fuerza_bruta(pts_x)

    mid = n // 2                                              # O(1) — divide
    mitad_x = pts_x[mid].x

    izq_res = _closest_rec(pts_x[:mid])                      # T(n/2) — mitad izquierda
    der_res = _closest_rec(pts_x[mid:])                      # T(n/2) — mitad derecha

    if izq_res[0] < der_res[0]:                              # O(1) — elige el menor
        d, p1, p2 = izq_res
    else:
        d, p1, p2 = der_res

    # Franja de ancho 2d alrededor de la línea media
    franja = [p for p in pts_x if abs(p.x - mitad_x) < d]   # O(n) — filtra franja
    return _closest_franja(franja, d, p1, p2)
# --- Análisis Par de Puntos Más Cercanos ---
# T(n) = 2·T(n/2) + O(n)  →  O(n log n)  (franja es O(n) por propiedad geométrica)


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
    grados = {v: len(vecinos) for v, vecinos in adyacencia.items()}  # O(V) — grado de cada nodo

    # Quick Sort por grado descendente (implementación propia)
    vertices = _quick_sort_por_grado(list(grados.keys()), grados)    # O(V log V)

    color_asignado: dict[str, int] = {}

    for v in vertices:                                               # O(V) — un color por vértice
        # Colores usados por los vecinos ya coloreados
        vecinos_ids = set(vid for (vid, *_) in adyacencia.get(v, []))   # O(grado(v))
        colores_vecinos = {
            color_asignado[u]
            for u in vecinos_ids
            if u in color_asignado                                   # O(grado(v)) — vecinos coloreados
        }
        # Asignar el menor color no usado
        color = 0
        while color in colores_vecinos:                              # O(Δ) — Δ = grado máximo
            color += 1
        color_asignado[v] = color                                   # O(1) — asignación

    return color_asignado
# --- Análisis Coloreo Welsh-Powell ---
# Sort: O(V log V)  +  bucle: Σ grado(v) = 2E → O(V + E)  +  while color: O(V·Δ) ≤ O(V²)
# Total: O(V log V + V² + E) = O(V² + E)  (dominante V² cuando el grafo es denso)


def _quick_sort_por_grado(vertices: list[str],
                          grados: dict[str, int]) -> list[str]:
    """
    Quick Sort descendente por grado — O(n log n) promedio.
    Pivote: elemento central.
    """
    if len(vertices) <= 1:                                           # O(1) — caso base
        return vertices

    pivot_idx = len(vertices) // 2
    pivot = vertices[pivot_idx]
    pivot_grado = grados[pivot]

    menores  = [v for v in vertices if v != pivot and grados[v] <  pivot_grado]  # O(n)
    iguales  = [v for v in vertices if grados[v] == pivot_grado]                 # O(n)
    mayores  = [v for v in vertices if v != pivot and grados[v] >  pivot_grado]  # O(n)

    # Orden descendente: mayores primero
    return (_quick_sort_por_grado(mayores, grados) +
            iguales +
            _quick_sort_por_grado(menores, grados))
# T(n) = 2·T(n/2) + O(n)  →  O(n log n) promedio (n = V vértices)


# ══════════════════════════════════════════════════════════════
#  NODOS Y ARISTAS DE SAN SEBASTIÁN
# ══════════════════════════════════════════════════════════════

def crear_nodos() -> dict[str, Nodo]:
    datos = [
        # --- EXTREMO IZQUIERDO / ZONA ALTA ---
        ("KARI_GRANDE",       "Kari Grande",                       -13.5200, -71.9320, False),
        ("PRIMER_PARADERO",   "Primer paradero",                   -13.5230, -71.9300, False),
        ("DIEGO_QUISPE",      "Colegio Diego Quispe Tito",                      -13.5260, -71.9310, False),
        
        # --- PARTE ALTA SUPERIOR ---
        ("CAMPINA_ALTA",      "APV Campiña alta",                  -13.5180, -71.9250, False),
        
        # --- SECTOR CENTRAL (EJE PRINCIPAL DE PARADEROS) ---
        ("SEGUNDO_PARADERO",  "Segundo Paradero",                  -13.5240, -71.9260, False),
        ("TERCER_PARADERO",   "Tercer Paradero",                   -13.5245, -71.9220, False),
        ("CUARTO_PARADERO",   "Cuarto Paradero",                   -13.5250, -71.9180, False),
        ("QUINTO_PARADERO",   "Quinto Paradero",                   -13.5252, -71.9140, False),
        ("SEXTO_PARADERO",    "Sexto Paradero",                    -13.5254, -71.9100, False),
        ("SEPTIMO_PARADERO",  "Séptimo Paradero",                  -13.5256, -71.9060, False),
        
        # --- SECTOR CENTRAL INFERIOR (HISTÓRICO / DEPÓSITO) ---
        ("PLAZA_SS",          "Plaza de Armas de San Sebastián",   -13.5280, -71.9280, False),
        ("CEMENTERIO",        "Cementerio Central de San Sebastián",-13.5310, -71.9270, False),
        ("DEPOSITO",          "Depósito Central",                  -13.5270, -71.9200, True),  # Único depósito
        
        # --- SECTOR BAJO / COSTANERA / AEROPUERTO ---
        ("MIRADOR_AVIONES",   "Mirador de Aviones",                -13.5290, -71.9100, False),
        ("AV_COSTANERA",      "Av. Costanera/Los Nogales",        -13.5320, -71.9120, False),
        ("PARADERO_JOYAS",    "Paradero las joyas",                -13.5340, -71.9150, False),
        ("PUENTE_TUPAC",      "Puente Tupac Amaru/Vía de Evitamiento",-13.5350, -71.9050, False),
        
        # --- EXTREMO DERECHO / SALIDA A SAN JERÓNIMO ---
        ("ENACO",             "Enaco",                             -13.5280, -71.9020, False),
        ("URB_TUPAC",         "Urb. Túpac Amaru",                  -13.5330, -71.8990, False),
        ("CACHIMAYO",         "Cachimayo",                         -13.5300, -71.8920, False),
        ]
    nodos = {}
    for id_, nombre, lat, lon, deposito in datos:
        x, y = latlon_a_px(lat, lon)
        nodos[id_] = Nodo(id=id_, nombre=nombre, lat=lat, lon=lon,
                        x=x, y=y, es_deposito=deposito)
    return nodos


def crear_aristas() -> list[Arista]:
    datos = [
        # --- ZONA ALTA / OSTE (Kari Grande / Primer paradero) ---
        ("KARI_GRANDE",       "PRIMER_PARADERO",    500,  3.5, "Acceso Kari Grande"),
        ("PRIMER_PARADERO",   "DIEGO_QUISPE",       350,  2.0, "Av. Diego Quispe"),
        ("PRIMER_PARADERO",   "SEGUNDO_PARADERO",   400,  2.0, "Eje Paraderos Principal"),
        
        # --- CIRCUITO DE CAMPINA ALTA ---
        ("SEGUNDO_PARADERO",  "CAMPINA_ALTA",       600,  4.0, "Subida Campiña"),
        ("CAMPINA_ALTA",      "TERCER_PARADERO",    550,  3.5, "Bajada Campiña"),
        
        # --- CONTINUACIÓN EJE PRINCIPAL DE PARADEROS ---
        ("SEGUNDO_PARADERO",  "TERCER_PARADERO",    350,  1.5, "Eje Paraderos Principal"),
        ("TERCER_PARADERO",   "CUARTO_PARADERO",    350,  1.5, "Eje Paraderos Principal"),
        ("CUARTO_PARADERO",   "QUINTO_PARADERO",    350,  1.5, "Eje Paraderos Principal"),
        ("QUINTO_PARADERO",   "SEXTO_PARADERO",     350,  1.5, "Eje Paraderos Principal"),
        ("SEXTO_PARADERO",    "SEPTIMO_PARADERO",   350,  1.5, "Eje Paraderos Principal"),
        
        # --- CONEXIONES CON PLAZA SAN SEBASTIÁN Y CEMENTERIO ---
        ("DIEGO_QUISPE",      "PLAZA_SS",           450,  2.5, "Prolongación Cusco"),
        ("PLAZA_SS",          "CEMENTERIO",         300,  1.5, "Calle Cementerio"),
        ("PLAZA_SS",          "DEPOSITO",           650,  3.0, "Av. de la Cultura"),
        
        # --- CONEXIONES CON EL DEPÓSITO CENTRAL ---
        ("TERCER_PARADERO",   "DEPOSITO",           500,  2.5, "Acceso Tercer Paradero"),
        ("CUARTO_PARADERO",   "DEPOSITO",           450,  2.5, "Acceso Cuarto Paradero"),
        
        # --- CONEXIONES DEL CIRCUITO DE AVIONES / COSTANERA ---
        ("SEXTO_PARADERO",    "MIRADOR_AVIONES",    400,  2.0, "Bajada Mirador"),
        ("MIRADOR_AVIONES",   "AV_COSTANERA",       450,  2.0, "Av. Costanera"),
        ("PARADERO_JOYAS",    "AV_COSTANERA",       350,  1.5, "Calle Los Nogales"),
        ("PARADERO_JOYAS",    "PUENTE_TUPAC",       750,  3.5, "Av. Costanera Este"),
        ("AV_COSTANERA",      "PUENTE_TUPAC",       600,  3.0, "Eje Costanera"),
        
        # --- EXTREMO ESTE (Enaco, Tupac Amaru, Cachimayo) ---
        ("SEPTIMO_PARADERO",  "ENACO",              500,  2.5, "Av. de la Cultura Este"),
        ("ENACO",             "CACHIMAYO",          700,  3.5, "Carretera Cachimayo"),
        ("PUENTE_TUPAC",    "URB_TUPAC",          450,  2.0, "Av. Tupac Amaru"),
        ("URB_TUPAC",         "CACHIMAYO",          600,  3.0, "Acceso Cachimayo"),
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
    "OESTE": [
        "KARI_GRANDE", 
        "PRIMER_PARADERO", 
        "DIEGO_QUISPE", 
        "CAMPINA_ALTA", 
        "SEGUNDO_PARADERO",
        "PLAZA_SS", 
        "CEMENTERIO"
    ],
    "CENTRO": [
        "TERCER_PARADERO", 
        "CUARTO_PARADERO", 
        "QUINTO_PARADERO", 
        "SEXTO_PARADERO", 
        "DEPOSITO"
    ],
    "ESTE": [
        "MIRADOR_AVIONES", 
        "AV_COSTANERA", 
        "PARADERO_JOYAS", 
        "PUENTE_TUPAC", 
        "ENACO", 
        "URB_TUPAC",
        "SEPTIMO_PARADERO",
        "CACHIMAYO"
    ]
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
        dist   = {n: float("inf") for n in self.nodos}        # O(V) — inicialización
        prev   = {n: None         for n in self.nodos}        # O(V)
        tramos = {n: 0            for n in self.nodos}        # O(V)
        dist[inicio] = 0
        heap = [(0.0, inicio)]                                 # O(1) — heap inicial

        while heap:                                            # O((V+E) log V) total
            costo, u = heapq.heappop(heap)                    # O(log V) — extracción
            if u == fin:                                       # O(1) — destino alcanzado
                break
            if costo > dist[u]:                               # O(1) — nodo obsoleto, poda
                continue
            for vecino, d, t, *_ in self.vecinos(u):         # O(grado(u)) — expande vecinos
                peso_base = t if usar_tiempo else d
                # Penalización exponencial suave por tramos (expo_rapida)
                peso = penalizacion_distancia(peso_base, 1.0001,
                                              tramos[u] + 1)  # O(log tramos) — expo_rapida
                nueva = dist[u] + peso
                if nueva < dist[vecino]:                       # O(1) — relajación
                    dist[vecino]   = nueva
                    prev[vecino]   = u
                    tramos[vecino] = tramos[u] + 1
                    heapq.heappush(heap, (nueva, vecino))     # O(log V) — inserción en heap

        ruta, nodo = [], fin
        while nodo is not None:                               # O(V) — reconstruye camino
            ruta.append(nodo)
            nodo = prev[nodo]
        ruta.reverse()                                        # O(V) — invierte lista
        if not ruta or ruta[0] != inicio:
            return [], float("inf")
        return ruta, dist[fin]
# --- Análisis Dijkstra ---
# Cada arista se relaja una vez: O(E) relajaciones × O(log V) por heappush
# Total: O((V + E) log V)  |  Espacio: O(V) para dist, prev, tramos

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