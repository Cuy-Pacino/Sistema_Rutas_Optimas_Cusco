"""
main.py
Punto de entrada — Sistema de Gestión de Rutas Óptimas
Zona: San Sebastián, Cusco
Programación III — UNSAAC 2026
Docentes: M.Sc. Hector E. Ugarte R. & M.Sc. Boris Chullo Llave
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from gui_pyqt import App




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


def main():
    print("Iniciando Sistema Logístico Profesional Avanzado...")
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()