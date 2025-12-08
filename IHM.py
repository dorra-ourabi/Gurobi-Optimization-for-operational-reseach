# ihm_app.py
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox, QHeaderView, QLineEdit, QApplication,
    QTableWidget
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QColor

# Assurez-vous que modele_gaz.py est dans le même répertoire
from EnergiePl import ModeleGaz


# --- THREAD DE RÉSOLUTION ---
class SolverWorker(QThread):
    result_ready = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, donnees):
        super().__init__()
        self.donnees = donnees

    def run(self):
        try:
            modele = ModeleGaz(self.donnees)
            resultats = modele.resoudre()
            if 'Erreur' in resultats.get('statut_text', '') or "Gurobi" in resultats.get('statut_text', ''):
                self.error_signal.emit(resultats['statut_text'])
            else:
                self.result_ready.emit(resultats)
        except Exception as e:
            self.error_signal.emit(f"Erreur de résolution inattendue : {str(e)}")


# --- FENÊTRE PRINCIPALE (IHM) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projet RO - Flux à Coût Minimum (PL)")
        self.setGeometry(100, 100, 1100, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.num_nodes = 0
        self.num_arcs = 0

        self.init_ui()
        self.worker = None

    def init_ui(self):
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.btn_solve = QPushButton("LANCER L'OPTIMISATION (Gurobi)")
        self.btn_solve.setFixedHeight(50)
        self.btn_solve.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16pt; font-weight: bold;")
        self.btn_solve.clicked.connect(self.lancer_resolution)
        self.btn_solve.setEnabled(False)
        self.layout.addWidget(self.btn_solve)

        self.data_tab = QWidget()
        self.tabs.addTab(self.data_tab, "1. Saisie des Données")
        self.setup_data_tab()

        self.results_tab = QWidget()
        self.tabs.addTab(self.results_tab, "2. Résultats et Analyse")
        self.setup_results_tab()

    def setup_data_tab(self):
        data_layout = QVBoxLayout(self.data_tab)
        size_group = QWidget()
        size_layout = QHBoxLayout(size_group)
        size_layout.addWidget(QLabel("Nombre de Nœuds :"))
        self.input_nodes = QLineEdit("3")
        size_layout.addWidget(self.input_nodes)
        size_layout.addWidget(QLabel("Nombre d'Arcs :"))
        self.input_arcs = QLineEdit("3")
        size_layout.addWidget(self.input_arcs)

        self.btn_generate = QPushButton("Générer les Tableaux de Saisie")
        self.btn_generate.clicked.connect(self.generate_tables)
        size_layout.addWidget(self.btn_generate)
        data_layout.addWidget(size_group)

        self.tables_container = QWidget()
        self.tables_layout = QVBoxLayout(self.tables_container)
        data_layout.addWidget(self.tables_container)

        self.generate_tables()

    def generate_tables(self):
        while self.tables_layout.count():
            item = self.tables_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        try:
            self.num_nodes = int(self.input_nodes.text())
            self.num_arcs = int(self.input_arcs.text())
            if self.num_nodes <= 0 or self.num_arcs <= 0:
                raise ValueError("Les nombres de nœuds et d'arcs doivent être > 0.")
        except ValueError as e:
            QMessageBox.critical(self, "Erreur de Saisie", f"Veuillez entrer des nombres entiers valides. {str(e)}")
            self.btn_solve.setEnabled(False)
            return

        self.tables_layout.addWidget(QLabel("<h2>1. Nœuds et Bilans</h2>"))
        self.node_table = QTableWidget(self.num_nodes, 2)
        self.node_table.setHorizontalHeaderLabels(["Nom du Nœud", "Bilan net (b_i)"])
        self.node_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tables_layout.addWidget(self.node_table)

        self.tables_layout.addWidget(QLabel("<h2>2. Arcs et Paramètres</h2>"))
        self.arc_table = QTableWidget(self.num_arcs, 4)
        self.arc_table.setHorizontalHeaderLabels(
            ["Nœud Départ (i)", "Nœud Arrivée (j)", "Capacité max (u_ij)", "Coût Unitaire (c_ij)"])
        self.arc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tables_layout.addWidget(self.arc_table)

        self.btn_solve.setEnabled(True)

    def setup_results_tab(self):
        results_layout = QVBoxLayout(self.results_tab)

        # Titre général
        results_layout.addWidget(QLabel("<h2>Résultats de l'Optimisation</h2>"))

        # Coût Total et Statut (Couleur de texte par défaut: Blanc)
        self.cost_label = QLabel("Statut : En attente de lancement...")
        self.cost_label.setStyleSheet("font-size: 14pt; color: white;")
        results_layout.addWidget(self.cost_label)

        # Acheminement Optimal (Gardé et stylisé en blanc sans fond bleu)
        results_layout.addWidget(QLabel("<h3>Acheminement Optimal (Arcs Actifs)</h3>"))
        self.path_label = QLabel("Aucun flux calculé.")
        self.path_label.setWordWrap(True)

        # Style : Texte blanc, suppression du fond bleu, et conservation du cadre.
        self.path_label.setStyleSheet(
            "font-size: 12pt; font-weight: bold; padding: 5px; background-color: none; border: 1px solid #c0d0e0; color: white;")
        results_layout.addWidget(self.path_label)

        # Les sections "Plan de Débit Optimal" et "Visualisation Graphique" ont été supprimées.
        self.debit_table = None

    def collecter_donnees(self):
        # La logique de collecte est conservée pour l'envoi des données à Gurobi
        try:
            Arcs, Cout_Var, Capacite = [], {}, {}

            for row in range(self.arc_table.rowCount()):
                items = [self.arc_table.item(row, col) for col in range(4)]
                if not all(items) or any(item.text().strip() == "" for item in items):
                    raise ValueError(f"Ligne d'arc {row + 1} incomplète. Toutes les cellules doivent être remplies.")
                u, v = items[0].text(), items[1].text()
                cap = float(items[2].text().replace(',', '.'))
                cost_var = float(items[3].text().replace(',', '.'))
                if cap <= 0 or cost_var < 0:
                    raise ValueError(f"Capacité doit être > 0 et Coût >= 0 (Ligne d'arc {row + 1}).")
                arc = (u, v)
                Arcs.append(arc)
                Capacite[arc] = cap
                Cout_Var[arc] = cost_var

            Noeuds, Bilan = [], {}
            for row in range(self.node_table.rowCount()):
                node_item = self.node_table.item(row, 0)
                bilan_item = self.node_table.item(row, 1)
                if not node_item or not bilan_item or node_item.text().strip() == "" or bilan_item.text().strip() == "":
                    raise ValueError(f"Ligne de nœud {row + 1} incomplète. Le nom et le bilan doivent être remplis.")
                node = node_item.text()
                bilan_val = float(bilan_item.text().replace(',', '.'))
                Noeuds.append(node)
                Bilan[node] = bilan_val

            for u, v in Arcs:
                if u not in Noeuds or v not in Noeuds:
                    raise ValueError(f"Un nœud de l'arc ({u} -> {v}) n'est pas défini dans la liste des Nœuds.")

            somme_bilan = sum(Bilan.values())
            if abs(somme_bilan) > 1e-6:
                raise ValueError(f"Déséquilibre de Flux : Bilan net non nul : {somme_bilan:,.2f}. IRRÉALISABLE.")

            return {
                'Noeuds': Noeuds, 'Arcs': Arcs, 'Bilan': Bilan,
                'Cout_Var': Cout_Var, 'Capacite': Capacite,
            }

        except ValueError as e:
            QMessageBox.critical(self, "Erreur de Données", str(e))
            return None
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inattendue", f"Veuillez d'abord générer les tableaux. {str(e)}")
            return None

    def lancer_resolution(self):
        donnees = self.collecter_donnees()
        if donnees is None: return

        self.btn_solve.setEnabled(False)
        self.btn_solve.setText("Résolution en cours...")
        self.cost_label.setText("Statut : Résolution en cours par Gurobi...")
        self.path_label.setText("Calcul des chemins...")
        self.tabs.setCurrentIndex(1)

        self.worker = SolverWorker(donnees)
        self.worker.result_ready.connect(self.afficher_resultats)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.start()

    def handle_error(self, message):
        QMessageBox.critical(self, "Erreur Critique", message)
        self.btn_solve.setEnabled(True)
        self.btn_solve.setText("LANCER L'OPTIMISATION (Gurobi)")
        self.cost_label.setText(f"Statut : ERREUR (Voir fenêtre d'erreur)")
        self.path_label.setText("Calcul échoué.")

    def afficher_resultats(self, resultats):
        self.btn_solve.setEnabled(True)
        self.btn_solve.setText("LANCER L'OPTIMISATION (Gurobi)")

        statut_text = resultats.get('statut_text')

        if statut_text == "OPTIMAL":
            cout_total = resultats.get('cout_total', 0.0)

            # Statut OPTIMAL : Coût affiché en BLANC
            self.cost_label.setText(
                f"Statut : 🟢 OPTIMAL | Coût Total Minimal: <span style='color: white; font-weight: bold;'>{cout_total:,.2f} €</span>"
            )

            debits = resultats['debits_optimaux']

            # --- CALCUL ET AFFICHAGE DES CHEMINS ACTIFS ---
            active_paths = []
            routing_map = {}

            for (u, v), debit in debits.items():
                if debit > 1e-6:
                    if u not in routing_map:
                        routing_map[u] = []
                    # Formatage: Nœud Départ -> Nœud Arrivée (Débit)
                    routing_map[u].append(f"-> {v} ({debit:,.2f})")

            if routing_map:
                for u, destinations in routing_map.items():
                    active_paths.append(f"De {u} :{' '.join(destinations)}")
                path_text = "<br>".join(active_paths)
                self.path_label.setText(path_text)
            else:
                self.path_label.setText("Le modèle est optimal, mais le flux total requis est nul.")
            # ---------------------------------------------------------

        elif "IRRÉALISABLE" in statut_text or "INFEASIBLE" in statut_text:
            # Statut IRRÉALISABLE : Message affiché en BLANC
            self.cost_label.setText(
                f"Statut : <span style='color: white;'> IRRÉALISABLE (Vérifiez les capacités ou les bilans).</span>"
            )
            self.path_label.setText("Réseau irréalisable. Aucun chemin valide trouvé.")
        else:
            self.cost_label.setText(f"Statut :  ÉCHEC ({statut_text}).")
            self.path_label.setText("Erreur de calcul Gurobi.")



# Vérifie si le script est exécuté directement
if __name__ == '__main__':
    # 1. Crée l'instance de l'application PySide6
    app = QApplication(sys.argv)

    # 2. Crée une instance de la fenêtre principale (IHM)
    window = MainWindow()

    # 3. Affiche la fenêtre à l'écran
    window.show()

    # 4. Lance la boucle d'événements de l'application
    sys.exit(app.exec())