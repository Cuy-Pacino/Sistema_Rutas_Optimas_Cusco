"""
main.py
Punto de entrada — Sistema de Gestión de Rutas Óptimas
Zona: San Sebastián, Cusco
Programación III — UNSAAC 2026
Docentes: M.Sc. Hector E. Ugarte R. & M.Sc. Boris Chullo Llave
"""

import sys
import os

# Asegura que Python encuentre los módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verificar_dependencias():
    """Comprueba que las librerías necesarias estén disponibles."""
    faltantes = []
    try:
        import tkinter
    except ImportError:
        faltantes.append("tkinter")

    if faltantes:
        print("❌ Faltan dependencias:")
        for lib in faltantes:
            print(f"   • {lib}")
        print("\nInstala con:  pip install", " ".join(faltantes))
        sys.exit(1)


def splash():
    """Muestra información de inicio en consola."""
    banner = r"""
  ╔══════════════════════════════════════════════════════════════╗
  ║    SISTEMA DE GESTIÓN DE RUTAS ÓPTIMAS — SAN SEBASTIÁN      ║
  ║                  Cusco, Perú  |  2026                        ║
  ║──────────────────────────────────────────────────────────────║
  ║  Algoritmos implementados:                                   ║
  ║    • Greedy        — Vecino Más Cercano    O(n²)             ║
  ║    • Divide & C.   — Segmentación Zonal    O(n log n)        ║
  ║    • Prog. Din.    — Knapsack 0/1          O(n·W)            ║
  ║    • Backtracking  — Rutas Restringidas    O(n!)             ║
  ║──────────────────────────────────────────────────────────────║
  ║  Programación III — UNSAAC                                   ║
  ║  M.Sc. Hector E. Ugarte R.  &  M.Sc. Boris Chullo Llave     ║
  ╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    verificar_dependencias()
    splash()

    print("  ▶ Cargando grafo de San Sebastián…")
    from grafo_san_sebastian import GrafoSanSebastian
    grafo = GrafoSanSebastian()
    print(f"    ✔ {len(grafo.nodos)} nodos cargados")
    print(f"    ✔ {sum(len(v) for v in grafo.adyacencia.values())//2} aristas cargadas")

    print("  ▶ Iniciando interfaz gráfica…\n")
    from gui import App
    app = App()
    app.mainloop()
    print("\n  Aplicación cerrada. ¡Hasta pronto!")


if __name__ == "__main__":
    main()
