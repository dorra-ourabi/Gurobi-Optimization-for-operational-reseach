import sys
from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QFont, QIcon
from Ghaida.ui import MainWindow, apply_light_palette


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 11))
    apply_light_palette(app)
    app.setWindowIcon(QIcon("icon.png"))
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
