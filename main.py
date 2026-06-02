"""
main.py
Punto de entrada — Sistema de Gestión de Rutas Óptimas
Zona: San Sebastián, Cusco
Programación III — UNSAAC 2026
"""
import sys
from PyQt6.QtWidgets import QApplication
from gui_pyqt import App

def main():
    print("Iniciando Sistema Logístico — San Sebastián, Cusco...")
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
