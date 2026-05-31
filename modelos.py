"""
modelos.py
Clases base del Sistema de Gestión de Rutas Óptimas
Zona: San Sebastián, Cusco — Programación III UNSAAC 2026

Algoritmos incorporados en este módulo:
  • Bubble Sort         — ordenar pedidos por prioridad/valor/peso
  • Shell Sort          — ordenar pedidos (gap sequence de Knuth)
  • Counting Sort       — ordenar por prioridad (valores discretos 1-4)
  • Búsqueda Lineal     — buscar pedido por cliente o sector
  • Búsqueda Binaria    — buscar pedido por ID (iterativa)
  • Codificación Huffman— comprimir/descomprimir nombres de clientes
"""

import math
import time
import heapq
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import Counter


# ══════════════════════════════════════════════════════════════
#  ENUMERACIONES Y CONSTANTES
# ══════════════════════════════════════════════════════════════

class Prioridad(Enum):
    URGENTE = 1
    ALTA    = 2
    NORMAL  = 3
    BAJA    = 4


PRIORIDAD_LABEL = {
    Prioridad.URGENTE: "🔴 Urgente",
    Prioridad.ALTA:    "🟠 Alta",
    Prioridad.NORMAL:  "🟡 Normal",
    Prioridad.BAJA:    "🟢 Baja",
}


# ══════════════════════════════════════════════════════════════
#  DATACLASSES DEL DOMINIO
# ══════════════════════════════════════════════════════════════

@dataclass
class Nodo:
    id: str
    nombre: str
    lat: float
    lon: float
    x: float
    y: float
    es_deposito: bool = False

    def distancia_a(self, otro: "Nodo") -> float:
        dlat = self.lat - otro.lat
        dlon = self.lon - otro.lon
        return math.sqrt((dlat * 111_000) ** 2 + (dlon * 90_000) ** 2)

    def distancia_px(self, otro: "Nodo") -> float:
        return math.sqrt((self.x - otro.x) ** 2 + (self.y - otro.y) ** 2)

    def __repr__(self):
        return f"Nodo({self.id}: {self.nombre})"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Nodo) and self.id == other.id


@dataclass
class Arista:
    origen: str
    destino: str
    distancia: float
    tiempo: float
    bidireccional: bool = True
    nombre_calle: str = ""
    bloqueada: bool = False


@dataclass
class Pedido:
    id: str
    cliente: str
    nodo_destino: str
    peso: float
    volumen: float
    valor: float
    prioridad: Prioridad = Prioridad.NORMAL
    hora_registro: float = field(default_factory=time.time)
    entregado: bool = False
    repartidor_asignado: Optional[str] = None

    def __lt__(self, other):
        if self.prioridad.value != other.prioridad.value:
            return self.prioridad.value < other.prioridad.value
        return self.hora_registro < other.hora_registro


@dataclass
class Repartidor:
    id: str
    nombre: str
    nodo_actual: str
    capacidad_peso: float
    capacidad_vol: float
    velocidad_kmh: float = 25.0
    activo: bool = True
    pedidos_asignados: list = field(default_factory=list)
    ruta_actual: list = field(default_factory=list)

    @property
    def carga_actual_peso(self) -> float:
        return sum(p.peso for p in self.pedidos_asignados if not p.entregado)

    @property
    def carga_actual_vol(self) -> float:
        return sum(p.volumen for p in self.pedidos_asignados if not p.entregado)

    @property
    def capacidad_disponible_peso(self) -> float:
        return self.capacidad_peso - self.carga_actual_peso

    @property
    def capacidad_disponible_vol(self) -> float:
        return self.capacidad_vol - self.carga_actual_vol

    def puede_tomar(self, pedido: Pedido) -> bool:
        return (pedido.peso   <= self.capacidad_disponible_peso and
                pedido.volumen <= self.capacidad_disponible_vol)


@dataclass
class ResultadoAlgoritmo:
    nombre_algoritmo: str
    ruta: list
    distancia_total: float
    tiempo_total: float
    pedidos_incluidos: list
    valor_total: float
    tiempo_computo: float
    notas: str = ""

    @property
    def complejidad_big_o(self) -> str:
        tabla = {
            "Greedy Vecino Más Cercano":            "O(n²)",
            "Mochila Fraccionaria":                 "O(n log n)",
            "Divide y Vencerás":                    "O(n log n)",
            "Programación Dinámica (Knapsack 0/1)": "O(n·W)",
            "Backtracking":                         "O(n!)",
            "Coloreo de Grafos (Welsh-Powell)":     "O(V² + E)",
            "Par de Puntos Más Cercanos":           "O(n log n)",
        }
        return tabla.get(self.nombre_algoritmo, "O(?)")


# ══════════════════════════════════════════════════════════════
#  1. BUBBLE SORT — O(n²)
#     Ordena lista de pedidos in-place según clave elegida.
# ══════════════════════════════════════════════════════════════

def bubble_sort(pedidos: list[Pedido], clave: str = "prioridad") -> list[Pedido]:
    """
    Ordenamiento por burbuja.
    clave: 'prioridad' | 'valor' | 'peso' | 'volumen'
    Complejidad: O(n²) tiempo, O(1) espacio extra.
    """
    def key(p: Pedido):
        if clave == "prioridad": return p.prioridad.value
        if clave == "valor":     return -p.valor        # desc
        if clave == "peso":      return p.peso
        if clave == "volumen":   return p.volumen
        return p.prioridad.value

    arr = list(pedidos)
    n = len(arr)
    for i in range(n):                                          # n pasadas externas
        intercambiado = False
        for j in range(0, n - i - 1):                          # O(n-i) comparaciones
            if key(arr[j]) > key(arr[j + 1]):                  # O(1) — comparación de claves
                arr[j], arr[j + 1] = arr[j + 1], arr[j]       # O(1) — intercambio
                intercambiado = True
        if not intercambiado:       # optimización: ya ordenado # O(1) — corta si no hubo cambios
            break
    return arr
# --- Análisis Bubble Sort ---
# Σ(i=0..n-1) (n-i-1) = n(n-1)/2 comparaciones  →  O(n²)
# Mejor caso (ya ordenado, con flag): O(n)  |  Espacio: O(1)


# ══════════════════════════════════════════════════════════════
#  2. SHELL SORT — O(n log² n) promedio
#     Mejora Bubble Sort usando saltos (gap sequence de Knuth).
# ══════════════════════════════════════════════════════════════

def shell_sort(pedidos: list[Pedido], clave: str = "prioridad") -> list[Pedido]:
    """
    Shell Sort con secuencia de Knuth: h = 1, 4, 13, 40, …
    Complejidad: O(n log² n) promedio, O(1) espacio extra.
    """
    def key(p: Pedido):
        if clave == "prioridad": return p.prioridad.value
        if clave == "valor":     return -p.valor
        if clave == "peso":      return p.peso
        return p.prioridad.value

    arr = list(pedidos)
    n = len(arr)

    # Calcular gap inicial de Knuth
    gap = 1
    while gap < n // 3:                                        # O(log₃ n) — halla gap inicial
        gap = gap * 3 + 1

    while gap >= 1:                                            # O(log₃ n) valores de gap
        for i in range(gap, n):                                # O(n) — barrido por gap
            temp = arr[i]
            j = i
            while j >= gap and key(arr[j - gap]) > key(temp): # O(n/gap) desplazamientos
                arr[j] = arr[j - gap]                          # O(1) — desplazamiento
                j -= gap
            arr[j] = temp                                      # O(1) — inserción final
        gap //= 3
    return arr
# --- Análisis Shell Sort (secuencia Knuth) ---
# Número de gaps: O(log n)  ×  trabajo por gap: O(n · n/gap)
# Suma sobre todos los gaps  →  O(n log² n) promedio
# Peor caso conocido con Knuth: O(n^(3/2))  |  Espacio: O(1)


# ══════════════════════════════════════════════════════════════
#  3. COUNTING SORT — O(n + k)
#     Ideal para prioridades (dominio discreto k=4).
# ══════════════════════════════════════════════════════════════

def counting_sort_prioridad(pedidos: list[Pedido]) -> list[Pedido]:
    """
    Counting Sort por prioridad (valores 1–4).
    Complejidad: O(n + k) con k=4 → efectivamente O(n).
    Estable: conserva orden de registro dentro de cada prioridad.
    """
    if not pedidos:
        return []

    k = 4   # Prioridad.URGENTE=1 … Prioridad.BAJA=4
    conteo = [[] for _ in range(k + 1)]   # índices 0..4       # O(k) — k=4, constante

    for p in pedidos:                                           # O(n) — distribuye en cubetas
        conteo[p.prioridad.value].append(p)                    # O(1) — append amortizado

    resultado = []
    for bucket in conteo[1:]:             # de prioridad 1 a 4 # O(k) = O(1) — k fijo
        resultado.extend(bucket)                                # O(n) total al juntar todo
    return resultado
# --- Análisis Counting Sort ---
# O(n) distribución + O(k) acumulado + O(n) concatenación  →  O(n + k)
# Con k=4 constante  →  O(n)  |  Estable  |  Espacio: O(n + k)


# ══════════════════════════════════════════════════════════════
#  4. BÚSQUEDA LINEAL — O(n)
#     Busca pedidos por nombre de cliente o nodo destino.
# ══════════════════════════════════════════════════════════════

def busqueda_lineal_cliente(pedidos: list[Pedido],
                            termino: str) -> list[Pedido]:
    """
    Búsqueda lineal: recorre todos los pedidos comparando
    el término contra el nombre del cliente (case-insensitive).
    Complejidad: O(n).
    """
    termino_lower = termino.lower()
    encontrados = []
    for p in pedidos:                          # recorre 1 a 1  # O(n) — sin acceso directo
        if termino_lower in p.cliente.lower():                  # O(|cliente|) ≈ O(1) strings cortos
            encontrados.append(p)
    return encontrados
# --- Análisis Búsqueda Lineal ---
# Peor caso (no encontrado): visita n elementos  →  O(n)
# Mejor caso (primer elemento): O(1)  |  Espacio: O(resultado) ≤ O(n)


def busqueda_lineal_sector(pedidos: list[Pedido],
                           nodo_id: str) -> list[Pedido]:
    """
    Búsqueda lineal por sector/nodo destino exacto.
    Complejidad: O(n).
    """
    return [p for p in pedidos if p.nodo_destino == nodo_id]   # O(n) — comprensión de lista
# O(n) — compara nodo_destino de cada pedido; sin estructura auxiliar


# ══════════════════════════════════════════════════════════════
#  5. BÚSQUEDA BINARIA ITERATIVA — O(log n)
#     Requiere lista previamente ordenada por ID.
# ══════════════════════════════════════════════════════════════

def busqueda_binaria_id(pedidos: list[Pedido],
                        id_buscado: str) -> Optional[Pedido]:
    """
    Búsqueda binaria iterativa sobre lista ordenada por ID.
    Complejidad: O(log n).
    Nota: ordena internamente — si se llama muchas veces,
          pre-ordenar externamente para mayor eficiencia.
    """
    arr = sorted(pedidos, key=lambda p: p.id)                  # O(n log n) — sort previo
    izq, der = 0, len(arr) - 1

    while izq <= der:                          # iterativa (no recursiva)  # O(log n) iteraciones
        mid = (izq + der) // 2                                 # O(1) — punto medio
        if arr[mid].id == id_buscado:                          # O(1) — comparación de strings cortos
            return arr[mid]
        elif arr[mid].id < id_buscado:                         # O(1)
            izq = mid + 1                                      # descarta mitad izquierda
        else:
            der = mid - 1                                      # descarta mitad derecha
    return None
# --- Análisis Búsqueda Binaria ---
# Cada iteración divide el espacio a la mitad: T(n) = T(n/2) + O(1)  →  O(log n)
# Incluye sort interno: O(n log n) + O(log n) = O(n log n) total si lista no está pre-ordenada


# ══════════════════════════════════════════════════════════════
#  6. CODIFICACIÓN DE HUFFMAN — O(n log n)
#     Comprime / descomprime strings (ej: nombres de clientes).
# ══════════════════════════════════════════════════════════════

class _NodoHuffman:
    """Nodo interno del árbol de Huffman."""
    __slots__ = ("freq", "char", "izq", "der")

    def __init__(self, freq: int, char: str = "",
                 izq=None, der=None):
        self.freq = freq
        self.char = char
        self.izq  = izq
        self.der  = der

    # Para heapq: compara por frecuencia
    def __lt__(self, other):
        return self.freq < other.freq


def huffman_codigos(texto: str) -> dict[str, str]:
    """
    Construye el árbol de Huffman y retorna el mapa
    carácter → código binario.
    Complejidad: O(n log n) donde n = caracteres únicos.
    """
    if not texto:
        return {}

    freq = Counter(texto)                                       # O(n) — cuenta frecuencias

    # Caso especial: texto de un solo carácter único
    if len(freq) == 1:
        char = next(iter(freq))
        return {char: "0"}

    heap = [_NodoHuffman(f, c) for c, f in freq.items()]      # O(k) — k = chars únicos
    heapq.heapify(heap)                                        # O(k) — heapify lineal

    while len(heap) > 1:                                       # k-1 fusiones
        izq = heapq.heappop(heap)                              # O(log k) — extracción
        der = heapq.heappop(heap)                              # O(log k)
        padre = _NodoHuffman(izq.freq + der.freq, izq=izq, der=der)
        heapq.heappush(heap, padre)                            # O(log k) — inserción

    raiz = heap[0]
    codigos: dict[str, str] = {}

    def _recorrer(nodo: _NodoHuffman, prefijo: str):
        if nodo.char:                          # hoja           # O(1) — nodo hoja
            codigos[nodo.char] = prefijo
        else:
            if nodo.izq: _recorrer(nodo.izq, prefijo + "0")   # recorre subárbol izquierdo
            if nodo.der: _recorrer(nodo.der, prefijo + "1")   # recorre subárbol derecho
    # _recorrer visita los 2k-1 nodos del árbol  →  O(k)

    _recorrer(raiz, "")
    return codigos
# --- Análisis Huffman ---
# O(n) frecuencias + O(k) heapify + O(k log k) fusiones + O(k) recorrido
# k = chars únicos ≤ n  →  dominante: O(k log k) ≤ O(n log n)


def huffman_comprimir(texto: str) -> tuple[str, dict[str, str]]:
    """
    Comprime texto usando Huffman.
    Retorna (bits_string, tabla_codigos).
    """
    codigos = huffman_codigos(texto)
    comprimido = "".join(codigos[c] for c in texto)
    return comprimido, codigos


def huffman_descomprimir(bits: str, codigos: dict[str, str]) -> str:
    """
    Descomprime string de bits usando la tabla de códigos.
    """
    inverso = {v: k for k, v in codigos.items()}               # O(k) — invierte tabla
    resultado = []
    buffer = ""
    for bit in bits:                                            # O(b) — b = longitud en bits
        buffer += bit
        if buffer in inverso:                                   # O(|buffer|) lookup en dict
            resultado.append(inverso[buffer])
            buffer = ""
    return "".join(resultado)
# --- Análisis descompresión ---
# O(b) recorrido de bits; b = longitud comprimida ≤ n·log₂k  →  O(n log k) ≤ O(n log n)


def demo_huffman(texto: str) -> str:
    """
    Retorna un string con el resumen de la compresión Huffman.
    Útil para mostrar en la GUI.
    """
    if not texto:
        return "Texto vacío."
    bits, codigos = huffman_comprimir(texto)
    original_bits  = len(texto) * 8
    comprimido_bits = len(bits)
    ratio = (1 - comprimido_bits / original_bits) * 100 if original_bits else 0
    lineas = [
        f"Texto original   : {texto!r}  ({len(texto)} chars, {original_bits} bits)",
        f"Bits comprimidos : {comprimido_bits} bits",
        f"Ratio compresión : {ratio:.1f}%",
        "",
        "Tabla de códigos Huffman:",
    ]
    for char, cod in sorted(codigos.items(), key=lambda x: len(x[1])):
        display = repr(char) if char == " " else char
        lineas.append(f"  '{display}'  →  {cod}  (freq {Counter(texto)[char]})")
    return "\n".join(lineas)