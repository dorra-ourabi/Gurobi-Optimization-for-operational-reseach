
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def check_dependencies():

    """Vérifie que toutes les dépendances sont installées"""

    missing = []

   

    try:
        import gurobipy
    except ImportError:
        missing.append("gurobipy")
    try:

        from PyQt5 import QtCore
    except ImportError:
        missing.append("PyQt5")
    try:

        import numpy
    except ImportError:
        missing.append("numpy")
    if missing:
        print(f"\n Dépendances manquantes: {', '.join(missing)}")
        print("\nInstaller avec:")
        print(f"pip install {' '.join(missing)}")
        return False
    return True
def main():
    if not check_dependencies():
        input("\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)
    app = QApplication(sys.argv)
    app.setApplicationName("Tarification Optimale")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    try:
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

       

    except ImportError as e:

        QMessageBox.critical(
            None, "Erreur d'import",
            f"Erreur lors de l'import des modules:\n\n{str(e)}\n\n"
            "Vérifiez que tous les fichiers sont présents."

        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None, "Erreur",
            f"Erreur lors du démarrage:\n\n{str(e)}"
        )

        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":

    main() 