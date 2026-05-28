"""
algoritmos.py
Los cuatro enfoques algorítmicos del sistema + algoritmos de apoyo.
Zona: San Sebastián, Cusco — Programación III UNSAAC 2026

Algoritmos incorporados:
  • Mochila Fraccionaria      — O(n log n)   repartidor (obligatorio)
  • Selección de Actividades  — O(n log n)   franjas horarias sin solapamiento
  • Quick Sort                — O(n log n)   ordenar pedidos por ratio valor/peso
  • Heap Sort                 — O(n log n)   cola de prioridad de pedidos
  • Radix Sort                — O(n·k)       ordenar pedidos por valor entero
  • Subset Sum                — O(n·W) DP    verificar combinaciones de carga exacta
  • Greedy vecino más cercano — O(n²)
  • Divide y Vencerás zonal   — O(n log n)
  • Backtracking rutas        — O(n!)
"""

import time
import heapq
import math
from typing import Optional
from modelos import (Pedido, Repartidor, ResultadoAlgoritmo, Prioridad,
                     bubble_sort, shell_sort, counting_sort_prioridad)
from grafo_san_sebastian import GrafoSanSebastian, ZONAS


# ══════════════════════════════════════════════════════════════
#  QUICK SORT — O(n log n) promedio
#  Ordena pedidos por ratio valor/peso (eficiencia de carga).
# ══════════════════════════════════════════════════════════════

def quick_sort_pedidos(pedidos: list[Pedido],
                       clave: str = "ratio") -> list[Pedido]:
    """
    Quick Sort in-place sobre lista de pedidos.
    clave:
      'ratio'    → valor / peso  (desc)  — eficiencia de carga
      'prioridad'→ prioridad.value (asc)
      'valor'    → valor (desc)
    Complejidad: O(n log n) promedio, O(n²) peor caso.
    """
    arr = list(pedidos)
    _qs(arr, 0, len(arr) - 1, clave)
    return arr


def _ks_key(p: Pedido, clave: str) -> float:
    if clave == "ratio":
        return -(p.valor / p.peso) if p.peso > 0 else 0.0   # O(1) — aritmética simple
    if clave == "prioridad":
        return float(p.prioridad.value)                       # O(1) — acceso a atributo
    if clave == "valor":
        return -p.valor                                       # O(1) — negación
    return 0.0


def _qs(arr: list, lo: int, hi: int, clave: str):
    if lo < hi:                                               # O(1) — comparación de índices
        p = _particion(arr, lo, hi, clave)                   # O(n) cada llamada
        _qs(arr, lo,     p - 1, clave)                       # T(k)   subproblema izquierdo
        _qs(arr, p + 1,  hi,    clave)                       # T(n-k) subproblema derecho


def _particion(arr: list, lo: int, hi: int, clave: str) -> int:
    """Pivote = elemento central (mediana de 3 implícita)."""
    mid = (lo + hi) // 2
    arr[mid], arr[hi] = arr[hi], arr[mid]                    # O(1) — intercambio
    pivot = _ks_key(arr[hi], clave)
    i = lo - 1
    for j in range(lo, hi):                                  # O(n) — recorre el subarreglo
        if _ks_key(arr[j], clave) <= pivot:                  # O(1) — comparación
            i += 1
            arr[i], arr[j] = arr[j], arr[i]                 # O(1) — intercambio
    arr[i + 1], arr[hi] = arr[hi], arr[i + 1]               # O(1) — coloca pivote final
    return i + 1
# --- Análisis Quick Sort ---
# T(n) = 2·T(n/2) + O(n)  →  Maestro caso 2  →  O(n log n) promedio
# Peor caso (pivote mínimo/máximo siempre): T(n) = T(n-1) + O(n)  →  O(n²)


# ══════════════════════════════════════════════════════════════
#  HEAP SORT — O(n log n)
#  Cola de prioridad de pedidos: extrae siempre el menos urgente.
# ══════════════════════════════════════════════════════════════

def heap_sort_pedidos(pedidos: list[Pedido]) -> list[Pedido]:
    """
    Heap Sort: construye max-heap por urgencia y extrae ordenado.
    Prioridad compuesta: (prioridad.value ASC, hora_registro ASC).
    Complejidad: O(n log n) tiempo, O(n) espacio.
    """
    arr = list(pedidos)
    n = len(arr)

    # Construir max-heap (usamos negativo para simular min → menos urgente primero)
    def clave(p: Pedido) -> tuple:
        return (-p.prioridad.value, -p.hora_registro)

    # heapify manual
    heap: list[tuple] = [(clave(p), i, p) for i, p in enumerate(arr)]  # O(n) — construye lista
    heapq.heapify(heap)                                                  # O(n) — heapify lineal

    resultado = []
    while heap:                                                          # n iteraciones
        _, _, pedido = heapq.heappop(heap)                              # O(log n) — extracción
        resultado.append(pedido)

    return resultado
# --- Análisis Heap Sort ---
# heapify: O(n)  +  n × heappop: O(log n)  →  O(n) + O(n log n)  =  O(n log n)


# ══════════════════════════════════════════════════════════════
#  RADIX SORT — O(n·k)
#  Ordena pedidos por valor entero (soles) sin comparaciones.
#  k = número de dígitos del valor máximo.
# ══════════════════════════════════════════════════════════════

def radix_sort_por_valor(pedidos: list[Pedido]) -> list[Pedido]:
    """
    Radix Sort LSD (dígito menos significativo primero).
    Los valores se multiplican ×10 para trabajar con enteros.
    Complejidad: O(n·k) donde k = dígitos del valor máximo.
    Retorna lista ordenada de MAYOR a MENOR valor.
    """
    if not pedidos:
        return []

    arr = list(pedidos)
    # Convertir a enteros (×10 para 1 decimal)
    max_val = int(max(p.valor * 10 for p in arr)) + 1      # O(n) — recorre para hallar máximo

    exp = 1
    while max_val // exp > 0:                               # k iteraciones (k = dígitos de max_val)
        arr = _counting_pass(arr, exp)                      # O(n) por pasada
        exp *= 10

    return arr[::-1]      # invertir → mayor primero       # O(n) — copia inversa
# --- Análisis Radix Sort ---
# k pasadas × O(n) por pasada  →  O(n·k), k = ⌊log₁₀(max_val)⌋ + 1  ≈  constante pequeña


def _counting_pass(arr: list[Pedido], exp: int) -> list[Pedido]:
    """Un paso de counting sort por el dígito en posición exp."""
    n = len(arr)
    salida  = [None] * n
    conteo  = [0] * 10                                      # O(1) — tamaño fijo (base 10)

    for p in arr:                                           # O(n) — cuenta frecuencias
        digito = (int(p.valor * 10) // exp) % 10
        conteo[digito] += 1

    for i in range(1, 10):                                  # O(1) — acumulado, solo 10 cubetas
        conteo[i] += conteo[i - 1]

    for p in reversed(arr):                                 # O(n) — coloca elementos estable
        digito = (int(p.valor * 10) // exp) % 10
        conteo[digito] -= 1
        salida[conteo[digito]] = p

    return salida
# _counting_pass: O(n + 10) = O(n) por pasada


# ══════════════════════════════════════════════════════════════
#  SELECCIÓN DE ACTIVIDADES — O(n log n)
#  Dado un conjunto de ventanas de entrega (inicio, fin),
#  seleccionar la mayor cantidad de pedidos compatibles
#  (sin solapamiento de horario).
# ══════════════════════════════════════════════════════════════

def seleccion_actividades(pedidos: list[Pedido],
                          ventanas: list[tuple[str, float, float]]
                          ) -> list[Pedido]:
    """
    Algoritmo Greedy de Selección de Actividades.
    ventanas: [(pedido_id, hora_inicio, hora_fin), ...]
              hora en formato decimal (ej: 8.5 = 8:30 am)

    Estrategia: ordenar por hora de FIN ascendente,
    seleccionar la siguiente actividad que no solape
    con la última seleccionada.

    Complejidad: O(n log n) por el ordenamiento inicial.
    Garantía: solución óptima (máximo número de actividades).

    Retorna: lista de Pedido seleccionados (compatibles).
    """
    if not ventanas or not pedidos:
        return []

    # Mapeo id → pedido
    mapa = {p.id: p for p in pedidos}                       # O(n) — construye diccionario

    # Ordenar por hora de finalización (Quick Sort)
    act_sorted = quick_sort_actividades(list(ventanas))      # O(n log n) — Quick Sort

    seleccionados: list[Pedido] = []
    ultimo_fin = -1.0

    for pid, inicio, fin in act_sorted:                      # O(n) — recorrido lineal
        if inicio >= ultimo_fin:          # no hay solapamiento  # O(1) — comparación
            if pid in mapa:                                  # O(1) — lookup en dict
                seleccionados.append(mapa[pid])
                ultimo_fin = fin

    return seleccionados
# --- Análisis Selección de Actividades ---
# O(n) dict + O(n log n) sort + O(n) barrido  →  dominante: O(n log n)


def quick_sort_actividades(acts: list[tuple]) -> list[tuple]:
    """Quick Sort de actividades por hora de fin (índice 2)."""
    if len(acts) <= 1:                                       # O(1) — caso base
        return acts
    pivot = acts[len(acts) // 2][2]
    menores = [a for a in acts if a[2] <  pivot]            # O(n) — partición con comprensión
    iguales = [a for a in acts if a[2] == pivot]            # O(n)
    mayores = [a for a in acts if a[2] >  pivot]            # O(n)
    return (quick_sort_actividades(menores) +
            iguales +
            quick_sort_actividades(mayores))
# T(n) = 2·T(n/2) + O(n)  →  O(n log n) promedio


# ══════════════════════════════════════════════════════════════
#  MOCHILA FRACCIONARIA — O(n log n)  ← OBLIGATORIO
#  Maximiza el valor de carga del repartidor permitiendo
#  fracciones de pedidos (p.ej. parte de un paquete grande).
#  Más eficiente que la 0/1 para restricciones de peso.
# ══════════════════════════════════════════════════════════════

def mochila_fraccionaria(repartidor: Repartidor,
                         pedidos: list[Pedido],
                         grafo: GrafoSanSebastian
                         ) -> ResultadoAlgoritmo:
    """
    Mochila Fraccionaria Greedy.

    Pasos:
      1. Calcular ratio valor/peso para cada pedido.
      2. Ordenar de mayor a menor ratio (Quick Sort).
      3. Tomar pedidos completos mientras quede capacidad;
         si no cabe entero, tomar fracción del último.
      4. Calcular ruta con Dijkstra para los pedidos seleccionados.

    Complejidad: O(n log n) por Quick Sort + O(n) de selección.
    Ventaja frente a Knapsack 0/1: no requiere tabla DP O(n·W).

    Nota académica:
      La mochila fraccionaria permite dividir un pedido,
      lo cual es válido cuando la carga es divisible
      (ej: sacos de harina, líquidos, paquetes múltiples).
    """
    t0 = time.perf_counter()

    disponibles = [p for p in pedidos if not p.entregado]
    if not disponibles:
        return ResultadoAlgoritmo(
            nombre_algoritmo="Mochila Fraccionaria",
            ruta=[], distancia_total=0, tiempo_total=0,
            pedidos_incluidos=[], valor_total=0,
            tiempo_computo=time.perf_counter() - t0,
            notas="Sin pedidos disponibles."
        )

    # 1. Calcular ratios y ordenar de mayor a menor (Quick Sort)
    ordenados = quick_sort_pedidos(disponibles, clave="ratio")  # O(n log n)

    # 2. Llenar la mochila
    capacidad_restante = repartidor.capacidad_disponible_peso
    seleccionados: list[Pedido]      = []
    fracciones:    list[float]       = []   # 1.0 = completo, 0.3 = 30%
    valor_total = 0.0

    for pedido in ordenados:                                    # O(n) — recorrido lineal
        if capacidad_restante <= 0:                             # O(1) — comparación
            break
        if pedido.peso <= capacidad_restante:                   # O(1) — comparación
            seleccionados.append(pedido)
            fracciones.append(1.0)
            valor_total           += pedido.valor
            capacidad_restante    -= pedido.peso
        else:
            # Fracción
            fraccion = capacidad_restante / pedido.peso         # O(1) — división
            seleccionados.append(pedido)
            fracciones.append(fraccion)
            valor_total        += pedido.valor * fraccion
            capacidad_restante  = 0

    # 3. Construir ruta Dijkstra para pedidos completos
    #    (los fraccionados se incluyen si fracción > 0.5)
    pedidos_ruta = [p for p, f in zip(seleccionados, fracciones) if f > 0.0]  # O(n)
    # Ordenar por prioridad antes de trazar la ruta
    pedidos_ruta = counting_sort_prioridad(pedidos_ruta)        # O(n) — counting sort

    pos = repartidor.nodo_actual
    ruta_nodos  = [pos]
    dist_total  = 0.0
    tiempo_total = 0.0

    for pedido in pedidos_ruta:                                 # O(n) iteraciones
        r, d = grafo.dijkstra(pos, pedido.nodo_destino)        # O((V+E) log V) por llamada
        if r:
            ruta_nodos.extend(r[1:])
            dist_total   += d
            tiempo_total += d / 416.0
            pos = pedido.nodo_destino
# --- Análisis Mochila Fraccionaria ---
# O(n log n) sort + O(n) selección + O(n·(V+E) log V) Dijkstra
# Dominante: O(n·(V+E) log V) si el grafo es grande; O(n log n) sin rutas

    if pos != "DEPOSITO":
        r_ret, d_ret = grafo.dijkstra(pos, "DEPOSITO")
        if r_ret:
            ruta_nodos.extend(r_ret[1:])
            dist_total   += d_ret
            tiempo_total += d_ret / 416.0

    t1 = time.perf_counter()

    # Resumen de fracciones
    detalle_frac = "; ".join(
        f"{p.id}={f*100:.0f}%"
        for p, f in zip(seleccionados, fracciones)
    )

    return ResultadoAlgoritmo(
        nombre_algoritmo="Mochila Fraccionaria",
        ruta=ruta_nodos,
        distancia_total=dist_total,
        tiempo_total=tiempo_total,
        pedidos_incluidos=pedidos_ruta,
        valor_total=valor_total,
        tiempo_computo=t1 - t0,
        notas=(
            f"Capacidad: {repartidor.capacidad_peso} kg | "
            f"Cargado: {repartidor.capacidad_peso - capacidad_restante:.1f} kg | "
            f"Pedidos: {len(seleccionados)} | "
            f"Valor optimizado: S/. {valor_total:.2f} | "
            f"Fracciones: {detalle_frac}"
        )
    )


# ══════════════════════════════════════════════════════════════
#  SUBSET SUM (Programación Dinámica) — O(n·W)
#  Verifica si existe un subconjunto de pedidos cuyo peso
#  total sea exactamente igual a la capacidad del repartidor
#  (carga perfecta sin desperdicio).
# ══════════════════════════════════════════════════════════════

def subset_sum_carga_exacta(pedidos: list[Pedido],
                            capacidad: float) -> tuple[bool, list[Pedido]]:
    """
    Problema Subset Sum: ¿hay subconjunto de pedidos con peso == capacidad?
    Usa programación dinámica tabla booleana O(n·W).

    capacidad: peso objetivo en kg (multiplicado ×10 para enteros).
    Retorna: (encontrado: bool, pedidos_del_subconjunto: list)
    """
    FACTOR = 10
    W = int(capacidad * FACTOR)
    pesos = [int(p.peso * FACTOR) for p in pedidos]
    n = len(pedidos)

    # dp[i][w] = True si con los primeros i pedidos se puede alcanzar peso w
    dp = [[False] * (W + 1) for _ in range(n + 1)]             # O(n·W) — tabla DP
    dp[0][0] = True

    for i in range(1, n + 1):                                   # n filas
        wi = pesos[i - 1]
        for w in range(W + 1):                                  # W+1 columnas → O(n·W) total
            dp[i][w] = dp[i - 1][w]                             # O(1) — sin tomar el item
            if wi <= w:
                dp[i][w] = dp[i][w] or dp[i - 1][w - wi]       # O(1) — tomando el item

    if not dp[n][W]:
        return False, []

    # Reconstruir subconjunto
    subconjunto = []
    w = W
    for i in range(n, 0, -1):                                   # O(n) — traza hacia atrás
        if not dp[i - 1][w]:
            subconjunto.append(pedidos[i - 1])
            w -= pesos[i - 1]

    return True, subconjunto
# --- Análisis Subset Sum DP ---
# Llenado tabla: O(n·W)  |  Reconstrucción: O(n)  |  Espacio: O(n·W)
# W = capacidad × FACTOR; si W es grande, puede ser costoso (pseudo-polinomial)


# ══════════════════════════════════════════════════════════════
#  GREEDY VECINO MÁS CERCANO — O(n²)
# ══════════════════════════════════════════════════════════════

def greedy_vecino_cercano(grafo: GrafoSanSebastian,
                          repartidor: Repartidor,
                          pedidos: list[Pedido]) -> ResultadoAlgoritmo:
    """
    Greedy: siempre ir al pedido pendiente más cercano.
    Ordena primero con Heap Sort (pedidos más urgentes primero).
    Complejidad: O(n²) por la búsqueda del mínimo en cada paso.
    """
    t0 = time.perf_counter()

    # Heap Sort para atender urgentes primero
    pendientes = heap_sort_pedidos(
        [p for p in pedidos if not p.entregado and repartidor.puede_tomar(p)]
    )                                                            # O(n log n) — Heap Sort

    ruta_nodos    = [repartidor.nodo_actual]
    pedidos_ruta  = []
    dist_total    = 0.0
    tiempo_total  = 0.0
    pos           = repartidor.nodo_actual
    visitados     = set()

    while pendientes:                                            # n iteraciones externas
        mejor       = None
        mejor_dist  = float("inf")
        mejor_tramo = []

        for pedido in pendientes:                               # O(n) — busca el más cercano
            if pedido.nodo_destino in visitados:                # O(1) — lookup en set
                continue
            ruta_p, dist_p = grafo.dijkstra(pos, pedido.nodo_destino)  # O((V+E) log V)
            if dist_p < mejor_dist:                             # O(1) — comparación
                mejor_dist  = dist_p
                mejor       = pedido
                mejor_tramo = ruta_p

        if mejor is None:
            break

        ruta_nodos.extend(mejor_tramo[1:])
        tiempo_total += mejor_dist / 416.0
        dist_total   += mejor_dist
        pedidos_ruta.append(mejor)
        visitados.add(mejor.nodo_destino)
        pos = mejor.nodo_destino
        pendientes.remove(mejor)                                # O(n) — lista sin indexar
# --- Análisis Greedy Vecino Más Cercano ---
# n iteraciones × O(n) búsqueda de mínimo  →  O(n²) sin contar Dijkstra
# Con Dijkstra: O(n² · (V+E) log V); sin grafo complejo se simplifica a O(n²)

    if pos != "DEPOSITO":
        r_ret, d_ret = grafo.dijkstra(pos, "DEPOSITO")
        if r_ret:
            ruta_nodos.extend(r_ret[1:])
            dist_total   += d_ret
            tiempo_total += d_ret / 416.0

    t1 = time.perf_counter()

    return ResultadoAlgoritmo(
        nombre_algoritmo="Greedy Vecino Más Cercano",
        ruta=ruta_nodos,
        distancia_total=dist_total,
        tiempo_total=tiempo_total,
        pedidos_incluidos=pedidos_ruta,
        valor_total=sum(p.valor for p in pedidos_ruta),
        tiempo_computo=t1 - t0,
        notas=(
            f"Ordena con Heap Sort antes de recorrer. "
            f"Sin visión global — puede no ser óptimo. "
            f"Pedidos: {len(pedidos_ruta)}/{len(pedidos)}"
        )
    )


# ══════════════════════════════════════════════════════════════
#  DIVIDE Y VENCERÁS — Segmentación zonal O(n log n)
# ══════════════════════════════════════════════════════════════

def _asignar_zona(nodo_id: str) -> str:
    for zona, nids in ZONAS.items():
        if nodo_id in nids:
            return zona
    return "CENTRO"


def _resolver_zona(grafo: GrafoSanSebastian,
                   inicio: str,
                   pedidos_zona: list[Pedido]
                   ) -> tuple[list[str], float, float]:
    """Greedy local para una sub-zona."""
    if not pedidos_zona:
        return [inicio], 0.0, 0.0

    ruta, pos       = [inicio], inicio
    dist_total      = 0.0
    tiempo_total    = 0.0
    pendientes      = list(pedidos_zona)

    while pendientes:
        mejor, mejor_dist, mejor_tramo = None, float("inf"), []
        for p in pendientes:
            r, d = grafo.dijkstra(pos, p.nodo_destino)
            if d < mejor_dist:
                mejor_dist  = d
                mejor       = p
                mejor_tramo = r
        if mejor is None:
            break
        ruta.extend(mejor_tramo[1:])
        dist_total   += mejor_dist
        tiempo_total += mejor_dist / 416.0
        pos = mejor.nodo_destino
        pendientes.remove(mejor)

    return ruta, dist_total, tiempo_total


def divide_y_venceras(grafo: GrafoSanSebastian,
                      repartidores: list[Repartidor],
                      pedidos: list[Pedido]) -> list[ResultadoAlgoritmo]:
    """
    Divide el mapa en 3 zonas (Norte, Centro, Sur) y resuelve
    cada sub-problema independientemente.
    Usa Shell Sort para ordenar pedidos dentro de cada zona.
    Complejidad: O(n log n) división + O(k²) por zona.
    """
    t0 = time.perf_counter()

    pedidos_por_zona: dict[str, list[Pedido]] = {z: [] for z in ZONAS}
    for pedido in pedidos:                                      # O(n) — clasifica cada pedido
        pedidos_por_zona[_asignar_zona(pedido.nodo_destino)].append(pedido)  # O(|zona|) lookup

    resultados = []
    for i, zona in enumerate(ZONAS):                           # O(Z) zonas, Z constante
        if not pedidos_por_zona[zona]:
            continue
        rep   = repartidores[i % len(repartidores)]
        t_z0  = time.perf_counter()

        # Shell Sort dentro de cada zona por prioridad
        zona_ordenada = shell_sort(pedidos_por_zona[zona], "prioridad")  # O(k log²k), k = pedidos zona
        ruta, dist, tiempo = _resolver_zona(grafo, "DEPOSITO", zona_ordenada)  # O(k²) greedy local
# --- Análisis Divide y Vencerás ---
# División: O(n)  |  Por zona: O(k log²k) sort + O(k² · (V+E) log V) Dijkstra
# Total: O(n) + Z · O(k²) = O(n log n) asintótico si k ≈ n/Z  →  O(n log n)

        if ruta[-1] != "DEPOSITO":
            r_ret, d_ret = grafo.dijkstra(ruta[-1], "DEPOSITO")
            if r_ret:
                ruta.extend(r_ret[1:])
                dist   += d_ret
                tiempo += d_ret / 416.0

        t_z1 = time.perf_counter()
        resultados.append(ResultadoAlgoritmo(
            nombre_algoritmo="Divide y Vencerás",
            ruta=ruta,
            distancia_total=dist,
            tiempo_total=tiempo,
            pedidos_incluidos=pedidos_por_zona[zona],
            valor_total=sum(p.valor for p in pedidos_por_zona[zona]),
            tiempo_computo=t_z1 - t_z0,
            notas=(
                f"Zona: {zona} | Rep: {rep.nombre} | "
                f"Pedidos: {len(pedidos_por_zona[zona])} | "
                f"Ordenados con Shell Sort antes de recorrer."
            )
        ))

    if resultados:
        resultados[0].tiempo_computo = time.perf_counter() - t0
    return resultados


# ══════════════════════════════════════════════════════════════
#  BACKTRACKING — Rutas con restricciones O(n!)
# ══════════════════════════════════════════════════════════════

def backtracking_rutas_restringidas(grafo: GrafoSanSebastian,
                                    inicio: str,
                                    fin: str,
                                    calles_bloqueadas: list[tuple[str, str]],
                                    max_rutas: int = 20
                                    ) -> ResultadoAlgoritmo:
    """
    Encuentra TODAS las rutas posibles de inicio a fin
    evitando calles bloqueadas, retorna la más corta.
    Poda: abandona ramas cuya distancia supera 150% del mejor hallado.
    Complejidad: O(V!) peor caso, O(ramificación^profundidad) con poda.
    """
    t0 = time.perf_counter()

    for o, d in calles_bloqueadas:
        grafo.bloquear_calle(o, d)

    todas_rutas: list[list[str]]  = []
    todas_dists: list[float]      = []

    def backtrack(nodo: str, ruta: list[str],
                  dist_acum: float, visitados: set[str]):
        if len(todas_rutas) >= max_rutas:                       # O(1) — límite de exploración
            return
        if nodo == fin:                                         # O(1) — caso base
            todas_rutas.append(list(ruta))
            todas_dists.append(dist_acum)
            return
        # Poda por distancia
        if todas_dists and dist_acum >= min(todas_dists) * 1.5: # O(rutas) — poda de rama
            return
        for vecino, dist, _, _ in grafo.vecinos(nodo):         # O(grado) — expansión de vecinos
            if vecino not in visitados:                         # O(1) — lookup en set
                visitados.add(vecino)
                ruta.append(vecino)
                backtrack(vecino, ruta, dist_acum + dist, visitados)  # recursión
                ruta.pop()
                visitados.remove(vecino)
# --- Análisis Backtracking ---
# Sin poda: O(V!) — explora todas las permutaciones de nodos
# Con poda 1.5×mejor: O(b^d), b = factor ramificación, d = profundidad media
# En la práctica mucho menor que O(V!) gracias al límite max_rutas y la poda

    backtrack(inicio, [inicio], 0.0, {inicio})

    for o, d in calles_bloqueadas:
        grafo.desbloquear_calle(o, d)

    t1 = time.perf_counter()

    if not todas_rutas:
        return ResultadoAlgoritmo(
            nombre_algoritmo="Backtracking",
            ruta=[], distancia_total=float("inf"),
            tiempo_total=float("inf"),
            pedidos_incluidos=[], valor_total=0,
            tiempo_computo=t1 - t0,
            notas=f"❌ Sin ruta posible de {inicio} a {fin}."
        )

    idx     = todas_dists.index(min(todas_dists))
    ruta_op = todas_rutas[idx]
    dist_op = todas_dists[idx]

    return ResultadoAlgoritmo(
        nombre_algoritmo="Backtracking",
        ruta=ruta_op,
        distancia_total=dist_op,
        tiempo_total=dist_op / 416.0,
        pedidos_incluidos=[],
        valor_total=0,
        tiempo_computo=t1 - t0,
        notas=(
            f"Rutas exploradas: {len(todas_rutas)} | "
            f"Nodos en ruta óptima: {len(ruta_op)} | "
            f"Bloqueadas: {[(o+chr(8596)+d) for o,d in calles_bloqueadas] or 'ninguna'}"
        )
    )


# ══════════════════════════════════════════════════════════════
#  COMPARADOR
# ══════════════════════════════════════════════════════════════

def comparar_algoritmos(resultados: list[ResultadoAlgoritmo]) -> str:
    if not resultados:
        return "Sin resultados para comparar."

    lineas = ["=" * 62, "   COMPARATIVA DE ALGORITMOS — SAN SEBASTIÁN, CUSCO",
              "=" * 62]

    for r in resultados:
        lineas += [
            f"\n🔷 {r.nombre_algoritmo}",
            f"   Big-O          : {r.complejidad_big_o}",
            f"   Distancia total: {r.distancia_total:.0f} m",
            f"   Tiempo viaje   : {r.tiempo_total:.1f} min",
            f"   Pedidos        : {len(r.pedidos_incluidos)}",
            f"   Valor total    : S/. {r.valor_total:.2f}",
            f"   T. cómputo     : {r.tiempo_computo*1000:.2f} ms",
            f"   Notas          : {r.notas}",
        ]

    lineas.append("\n" + "=" * 62)

    if len(resultados) >= 2:
        validos = [r for r in resultados if r.distancia_total < float("inf")]
        if validos:
            mejor_dist  = min(validos, key=lambda r: r.distancia_total)
            mejor_valor = max(validos, key=lambda r: r.valor_total)
            lineas += [
                "\n📌 RECOMENDACIONES:",
                f"  • Menor distancia  → {mejor_dist.nombre_algoritmo}  "
                f"({mejor_dist.distancia_total:.0f} m)",
                f"  • Mayor valor      → {mejor_valor.nombre_algoritmo}  "
                f"(S/. {mejor_valor.valor_total:.2f})",
                "",
                "📚 ANÁLISIS BIG-O:",
                "  • Greedy          O(n²)      — rápido, no garantiza óptimo",
                "  • Mochila Fracc.  O(n log n) — óptimo para carga divisible",
                "  • Divide y Venc.  O(n log n) — escala bien con más zonas",
                "  • Backtracking    O(n!)       — exhaustivo, usar con poda",
            ]

    return "\n".join(lineas)