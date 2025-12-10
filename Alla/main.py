# main.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QTableWidgetItem, QHeaderView)
from ui.ui_placement import Ui_MainWindow
from data.parser import parse_table_sites, parse_table_zones
from model.optimizer import optimize_placement


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #configuration des tableaux
        self.setup_tables()

        #connexion des signaux
        self.connect_signals()

        #charger des données exemples
        self.load_example_data()

        #message de bienvenue dans la barre de statut
        self.statusBar().showMessage("Prêt à optimiser le placement des ambulances")

    def setup_tables(self):
        #table Sites
        self.ui.tableSites.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableSites.setAlternatingRowColors(True)
        self.ui.tableSites.verticalHeader().setVisible(True)

        #table Zones
        self.ui.tableZones.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableZones.setAlternatingRowColors(True)
        self.ui.tableZones.verticalHeader().setVisible(True)

        #zone de resultats en lecture seule
        self.ui.textResults.setReadOnly(True)

    def connect_signals(self):
        """Connecte tous les signaux aux slots"""
        #bouton d'optimisation
        self.ui.btnOptimize.clicked.connect(self.run_optimizer)

        #boutons pour les sites
        self.ui.btnAddSite.clicked.connect(self.add_site_row)
        self.ui.btnRemoveSite.clicked.connect(self.remove_site_row)

        #boutons pour les zones
        self.ui.btnAddZone.clicked.connect(self.add_zone_row)
        self.ui.btnRemoveZone.clicked.connect(self.remove_zone_row)

    def add_site_row(self):
        """Ajoute une nouvelle ligne dans le tableau des sites"""
        row_count = self.ui.tableSites.rowCount()
        self.ui.tableSites.insertRow(row_count)

        #initialiser les cellules avec des valeurs par défaut
        self.ui.tableSites.setItem(row_count, 0, QTableWidgetItem(f"Site_{row_count + 1}"))
        self.ui.tableSites.setItem(row_count, 1, QTableWidgetItem("0"))
        self.ui.tableSites.setItem(row_count, 2, QTableWidgetItem("0"))
        self.ui.tableSites.setItem(row_count, 3, QTableWidgetItem(""))

        self.statusBar().showMessage(f"Site ajouté (ligne {row_count + 1})", 3000)

    def remove_site_row(self):
        """Supprime la ligne sélectionnée dans le tableau des sites"""
        current_row = self.ui.tableSites.currentRow()
        if current_row >= 0:
            self.ui.tableSites.removeRow(current_row)
            self.statusBar().showMessage(f"Site supprimé", 3000)
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une ligne à supprimer")

    def add_zone_row(self):
        """Ajoute une nouvelle ligne dans le tableau des zones"""
        row_count = self.ui.tableZones.rowCount()
        self.ui.tableZones.insertRow(row_count)

        #initialiser les cellules avec des valeurs par défaut
        self.ui.tableZones.setItem(row_count, 0, QTableWidgetItem(f"Zone_{row_count + 1}"))
        self.ui.tableZones.setItem(row_count, 1, QTableWidgetItem("0"))
        self.ui.tableZones.setItem(row_count, 2, QTableWidgetItem("0"))
        self.ui.tableZones.setItem(row_count, 3, QTableWidgetItem("1000"))
        self.ui.tableZones.setItem(row_count, 4, QTableWidgetItem("1"))

        self.statusBar().showMessage(f" Zone ajoutée (ligne {row_count + 1})", 3000)

    def remove_zone_row(self):
        """Supprime la ligne sélectionnée dans le tableau des zones"""
        current_row = self.ui.tableZones.currentRow()
        if current_row >= 0:
            self.ui.tableZones.removeRow(current_row)
            self.statusBar().showMessage(f"Zone supprimée", 3000)
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une ligne à supprimer")

    def load_example_data(self):
        """Charge des données d'exemple pour faciliter les tests"""
        # Exemple 1 : - Hôpital Centre couvre TOUTES les zones (5km max) et Base Est couvre B et E (zones peuplées)
        sites_data = [
            ("🏥 Hôpital Centre", 5.0, 5.0, "3"),
            ("🚒 Caserne Nord", 2.0, 8.0, "2"),
            ("🏢 Station Sud", 8.0, 2.0, "2"),
            ("🏭 Base Est", 10.0, 5.0, "3"),
        ]
        zones_data = [
            ("🏘️ Quartier A", 3.0, 6.0, "5000", "1"),
            ("🏘️ Quartier B", 7.0, 7.0, "8000", "2"),
            ("🏘️ Quartier C", 6.0, 3.0, "6000", "1"),
            ("🏘️ Quartier D", 1.0, 2.0, "4000", "3"),
            ("🏘️ Quartier E", 9.0, 8.0, "7000", "1"),
        ]
        #2 Exemple 2 : CAS "ZONE ISOLÉE" : Quartier D loin de tout
        """sites_data = [
            ("🏥 Hôpital Centre", 5.0, 5.0, "3"),
            ("🚒 Caserne Nord", 2.0, 8.0, "2"),
            ("🏢 Station Sud", 8.0, 2.0, "2"),
            ("🏭 Base Est", 10.0, 5.0, "3"),
        ]
        # Mêmes sites
        zones_data = [
            ("🏘️ Quartier A", 3.0, 6.0, "5000", "1"),
            ("🏘️ Quartier B", 7.0, 7.0, "8000", "2"),
            ("🏘️ Quartier C", 6.0, 3.0, "6000", "1"),
            ("🏘️ Quartier D", 15.0, 15.0, "4000", "3"),  # TRÈS LOIN !
            ("🏘️ Quartier E", 9.0, 8.0, "7000", "1"),
        ]"""
        # Exemple 3 : D devient le plus prioritaire !! donc A et D auront la mm imprtance
        """sites_data = [
            ("🏥 Hôpital Centre", 5.0, 5.0, "3"),
            ("🚒 Caserne Nord", 2.0, 8.0, "2"),
            ("🏢 Station Sud", 8.0, 2.0, "2"),
            ("🏭 Base Est", 10.0, 5.0, "3"),
        ]
        # Mêmes sites
        zones_data = [
            ("🏘️ Quartier A", 3.0, 6.0, "5000", "1"),
            ("🏘️ Quartier B", 7.0, 7.0, "8000", "2"),
            ("🏘️ Quartier C", 6.0, 3.0, "6000", "1"),
            ("🏘️ Quartier D", 1, 2, "5000", "5"),  # TRÈS PRIORITAIRE!
            ("🏘️ Quartier E", 9.0, 8.0, "7000", "1"),
        ]"""
        #exemple 4: mm que exemple 1 mais rayon 3



        self.ui.tableSites.setRowCount(len(sites_data))
        for i, (name, x, y, cap) in enumerate(sites_data):
            self.ui.tableSites.setItem(i, 0, QTableWidgetItem(name))
            self.ui.tableSites.setItem(i, 1, QTableWidgetItem(str(x)))
            self.ui.tableSites.setItem(i, 2, QTableWidgetItem(str(y)))
            self.ui.tableSites.setItem(i, 3, QTableWidgetItem(cap))

        # Exemple de zones


        self.ui.tableZones.setRowCount(len(zones_data))
        for i, (name, x, y, pop, prio) in enumerate(zones_data):
            self.ui.tableZones.setItem(i, 0, QTableWidgetItem(name))
            self.ui.tableZones.setItem(i, 1, QTableWidgetItem(str(x)))
            self.ui.tableZones.setItem(i, 2, QTableWidgetItem(str(y)))
            self.ui.tableZones.setItem(i, 3, QTableWidgetItem(pop))
            self.ui.tableZones.setItem(i, 4, QTableWidgetItem(prio))

        # Paramètres par défaut
        self.ui.spinTotalAmbulances.setValue(6)
        self.ui.spinMaxDistance.setValue(5.0)

    def run_optimizer(self):
        """Lance l'optimisation et affiche les résultats"""
        try:
            #récupération des données
            sites = parse_table_sites(self.ui.tableSites)
            zones = parse_table_zones(self.ui.tableZones)
            total_ambulances = self.ui.spinTotalAmbulances.value()
            max_distance = self.ui.spinMaxDistance.value()

            #déterminer le mode
            mode_text = self.ui.comboModeDecision.currentText()
            if 'Binaire' in mode_text or 'binaire' in mode_text:
                mode = 'binaire'
            else:
                mode = 'entier'

            # Validation
            if not sites:
                QMessageBox.warning(self, "⚠Erreur", "Veuillez ajouter au moins un site")
                return

            if not zones:
                QMessageBox.warning(self, "⚠Erreur", "Veuillez ajouter au moins une zone")
                return

            #message de progression
            self.ui.textResults.setText("Optimisation en cours...\n\nCalcul du placement optimal...")
            self.statusBar().showMessage("Optimisation en cours...")
            QApplication.processEvents()  # Forcer la mise à jour de l'interface

            #lancer l'optimisation
            placement, stats = optimize_placement(sites, zones, total_ambulances,
                                                  max_distance, mode)

            #vérifier les erreurs
            if 'error' in stats:
                QMessageBox.critical(self, " Erreur d'optimisation", stats['error'])
                self.ui.textResults.setText(f" ERREUR\n\n{stats['error']}")
                self.statusBar().showMessage("Erreur d'optimisation", 5000)
                return

            #afficher les résultats
            self.display_results(placement, stats, mode, max_distance, total_ambulances)
            self.statusBar().showMessage("Optimisation terminée avec succès!", 5000)

        except Exception as e:
            error_msg = f"Une erreur s'est produite:\n{str(e)}"
            QMessageBox.critical(self, "Erreur", error_msg)
            self.ui.textResults.setText(f"ERREUR\n\n{str(e)}")
            self.statusBar().showMessage("Erreur", 5000)

    def display_results(self, placement, stats, mode, max_distance, total_ambulances):
        """Affichage moderne, clair et professionnel avec les vraies probabilités"""

        lines = []
        add = lines.append

        # === EN-TÊTE ===
        add("RÉSULTATS DE L'OPTIMISATION PROBABILISTE")
        add("────────────────────────────────────────────────────────────────")
        add(f"  Mode               : {mode.capitalize()}")
        add(f"  Distance maximale  : {max_distance:.1f} km")
        add(f"  Budget ambulances  : {total_ambulances}")
        add("")

        # === PLACEMENT ===
        add("PLACEMENT OPTIMAL DES AMBULANCES")
        add("────────────────────────────────────────────────────────────────")
        if placement:
            for site, nb in sorted(placement.items(), key=lambda x: -x[1]):
                if nb > 0:
                    add(f"  {site:<35} → {nb} ambulance{'s' if nb > 1 else ' '}")
            add("")
            add(f"  Total utilisé : {stats['total_ambulances_placed']} / {total_ambulances} ambulances")
        else:
            add("  Aucune ambulance placée")
        add("")

        # === COUVERTURE PROBABILISTE (le vrai truc impressionnant) ===
        add("COUVERTURE RÉELLE ATTENDUE (ambulances parfois occupées)")
        add("────────────────────────────────────────────────────────────────")

        # Taux global
        add(f"  Couverture moyenne attendue : {stats['coverage_percentage']}%")
        add("")

        # Détail par zone (les 10 plus importantes + résumé)
        add("Détail par zone (ambulances couvrantes → probabilité de sauvetage)")
        add("────────────────────────────────────────────────────────────────")

        # Tri par contribution décroissante
        sorted_zones = sorted(stats['details_zones'], key=lambda x: x['contribution'], reverse=True)

        for zone in sorted_zones[:12]:  # les 12 plus importantes
            nom = zone['nom']
            pop = f"{zone['population']:,}".replace(",", " ")
            amb = zone['ambulances']
            proba = zone['probabilite_%']
            add(f"  {nom:<30} ({pop} hab.) → {amb} amb. → {proba}% de chance d’être sauvé")

        if len(sorted_zones) > 12:
            add(f"  ... et {len(sorted_zones) - 12} autres zones")
        add("")

        # === RÉSUMÉ FINAL ===
        add("RÉSUMÉ")
        add("────────────────────────────────────────────────────────────────")
        add(f"  Population sauvée en moyenne : {stats['population_covered']:,} habitants")
        add(f"  Probabilité moyenne de sauvetage : {stats['coverage_percentage']:.1f} %")
        add("")
        add("Modèle basé sur une disponibilité réelle de 60 % (ambulances parfois en intervention)")

        # Affichage final
        result_text = "\n".join(lines)
        self.ui.textResults.setPlainText(result_text)
        self.ui.textResults.setFont(self.ui.textResults.font())  # police propre


def main():
    """point d'entrée de l'application"""
    app = QApplication(sys.argv)

    #style de l'application
    app.setStyle('Fusion')

    #créer et afficher la fenêtre
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()