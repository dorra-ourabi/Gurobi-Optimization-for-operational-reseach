from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog,
    QGroupBox, QHeaderView, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush
import csv
import json
from datetime import datetime
import os

class PortefeuilleTab(QWidget):
    
    dossier_ajoute = pyqtSignal(dict)  # Signal pour communication
    
    def __init__(self, optimizer=None):
        super().__init__()
        self.optimizer = optimizer
        self.dossiers = []  
        self.init_ui()
        self.load_portefeuille()  
        print(f"Portefeuille initialisé avec {len(self.dossiers)} dossiers")
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        header_frame = QWidget()
        header_layout = QHBoxLayout(header_frame)
        
        title = QLabel("PORTEFEUILLE DE PRÊTS")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        
        self.status_label = QLabel("0 dossiers")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        layout.addWidget(header_frame)
        stats_group = QGroupBox("STATISTIQUES GLOBALES")
        stats_group.setFont(QFont("Arial", 10, QFont.Bold))
        stats_layout = QHBoxLayout()
        
        self.label_volume = QLabel("Volume total: 0 €")
        self.label_profit = QLabel("Profit estimé: 0 €")
        self.label_taux_moyen = QLabel("Taux moyen: 0.00 %")
        self.label_nb_dossiers = QLabel("Dossiers: 0")
        
        for label in [self.label_volume, self.label_profit, 
                     self.label_taux_moyen, self.label_nb_dossiers]:
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("padding: 5px;")
        
        stats_layout.addWidget(self.label_volume)
        stats_layout.addWidget(self.label_profit)
        stats_layout.addWidget(self.label_taux_moyen)
        stats_layout.addWidget(self.label_nb_dossiers)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        self.table_portefeuille = QTableWidget()
        self.table_portefeuille.setColumnCount(10)  
        self.table_portefeuille.setHorizontalHeaderLabels([
            "ID", "Type", "Montant", "Durée", "Taux %", 
            "Mensualité", "Profit €", "Score", "PD %", "Ratio %"
        ])
        
        header = self.table_portefeuille.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        self.table_portefeuille.setAlternatingRowColors(True)
        self.table_portefeuille.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        layout.addWidget(self.table_portefeuille)
        
        btn_layout = QHBoxLayout()
        
        btn_add_test = QPushButton("Ajouter dossier test")
        btn_add_test.clicked.connect(self.ajouter_dossier_test)
        btn_add_test.setToolTip("Ajouter un dossier de test pour vérification")
        
        btn_export = QPushButton("Exporter CSV")
        btn_export.clicked.connect(self.exporter_csv)
        
        btn_clear = QPushButton("Vider")
        btn_clear.clicked.connect(self.vider_portefeuille)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.actualiser_table)
        
        for btn in [btn_add_test, btn_export, btn_clear, btn_refresh]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        
        btn_add_test.setStyleSheet("background-color: #3498db; color: white;")
        btn_export.setStyleSheet("background-color: #27ae60; color: white;")
        btn_clear.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_refresh.setStyleSheet("background-color: #f39c12; color: white;")
        
        btn_layout.addWidget(btn_add_test)
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.actualiser_statistiques()
    
    def ajouter_dossier(self, resultat, montant, duree, type_pret):
        # if resultat.get('status') != 'ACCEPTE':
        #     return False
        
        try:
            dossier = {
                'id': len(self.dossiers) + 1,
                'type': type_pret,
                'montant': float(montant),
                'duree': float(duree),
                'taux': float(resultat.get('taux_optimal', 0)),
                'mensualite': float(resultat.get('mensualite', 0)),
                'profit': float(resultat.get('profitabilite', {}).get('profit_total_estime', 0)),
                'statut': 'ACCEPTE',
                'date_ajout': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'score_credit': resultat.get('metriques_risque', {}).get('score_credit', 0),
                'PD': resultat.get('probabilite_defaut', 0),
                'ratio_endettement': resultat.get('nouveau_ratio_endettement', 0)
            }
            
            self.dossiers.append(dossier)
            self.actualiser_table()
            self.actualiser_statistiques()
            
            self.save_portefeuille()
            self.dossier_ajoute.emit(dossier)
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def ajouter_dossier_test(self):
        dossier_test = {
            'id': len(self.dossiers) + 1,
            'type': 'automobile',
            'montant': 25000.0,
            'duree': 5.0,
            'taux': 4.85,
            'mensualite': 470.08,
            'profit': 1250.50,
            'statut': 'ACCEPTE',
            'date_ajout': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'score_credit': 720,
            'PD': 1.8,
            'ratio_endettement': 28.5
        }
        
        self.dossiers.append(dossier_test)
        self.actualiser_table()
        self.actualiser_statistiques()
        
        QMessageBox.information(self, "Test", 
            f"Dossier de test ajouté avec succès!\n\n"
            f"Type: {dossier_test['type']}\n"
            f"Montant: {dossier_test['montant']}€\n"
            f"Taux: {dossier_test['taux']}%")
    
    def actualiser_table(self):
        self.table_portefeuille.setRowCount(len(self.dossiers))
        
        for i, dossier in enumerate(self.dossiers):
            self.table_portefeuille.setItem(i, 0, QTableWidgetItem(str(dossier.get('id', i+1))))
            type_item = QTableWidgetItem(dossier.get('type', '').upper())
            type_item.setForeground(QColor('#3498db'))  
            self.table_portefeuille.setItem(i, 1, type_item)
            montant_item = QTableWidgetItem(f"{dossier.get('montant', 0):,.0f} €")
            montant_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_portefeuille.setItem(i, 2, montant_item)
            duree_item = QTableWidgetItem(f"{dossier.get('duree', 0):.1f} ans")
            self.table_portefeuille.setItem(i, 3, duree_item)
            taux = dossier.get('taux', 0)
            taux_item = QTableWidgetItem(f"{taux:.3f} %")
            if taux > 6:
                taux_item.setForeground(QColor('#e74c3c'))  
            elif taux < 3:
                taux_item.setForeground(QColor('#27ae60'))  
            else:
                taux_item.setForeground(QColor('#f39c12'))  
            taux_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_portefeuille.setItem(i, 4, taux_item)
            mensualite_item = QTableWidgetItem(f"{dossier.get('mensualite', 0):.2f} €")
            mensualite_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_portefeuille.setItem(i, 5, mensualite_item)
            profit = dossier.get('profit', 0)
            profit_item = QTableWidgetItem(f"{profit:,.2f} €")
            profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if profit > 1000:
                profit_item.setForeground(QColor('#27ae60'))  
                profit_item.setBackground(QBrush(QColor('#d5f4e6')))
            elif profit < 0:
                profit_item.setForeground(QColor('#e74c3c')) 
                profit_item.setBackground(QBrush(QColor('#fadbd8')))
            self.table_portefeuille.setItem(i, 6, profit_item)
            
            score = dossier.get('score_credit', 0)
            score_item = QTableWidgetItem(str(score))
            if score >= 700:
                score_item.setForeground(QColor('#27ae60'))  
            elif score >= 600:
                score_item.setForeground(QColor('#f39c12')) 
            else:
                score_item.setForeground(QColor('#e74c3c'))  
            self.table_portefeuille.setItem(i, 7, score_item)
            
            pd_item = QTableWidgetItem(f"{dossier.get('PD', 0):.2f} %")
            pd_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_portefeuille.setItem(i, 8, pd_item)
            
            ratio = dossier.get('ratio_endettement', 0)
            ratio_item = QTableWidgetItem(f"{ratio:.1f} %")
            if ratio > 33:
                ratio_item.setForeground(QColor('#e74c3c'))  
            ratio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_portefeuille.setItem(i, 9, ratio_item)
        
        self.table_portefeuille.resizeColumnsToContents()
        
        self.status_label.setText(f"{len(self.dossiers)} dossiers")
    
    def actualiser_statistiques(self):
        if not self.dossiers:
            self.label_volume.setText("Volume total: 0 €")
            self.label_profit.setText("Profit estimé: 0 €")
            self.label_taux_moyen.setText("Taux moyen: 0.00 %")
            self.label_nb_dossiers.setText("Dossiers: 0")
            return
        
        volume_total = sum(d.get('montant', 0) for d in self.dossiers)
        profit_total = sum(d.get('profit', 0) for d in self.dossiers)
        
        taux_moyen = sum(d.get('taux', 0) * d.get('montant', 0) for d in self.dossiers)
        taux_moyen = taux_moyen / volume_total if volume_total > 0 else 0
        
        self.label_volume.setText(f"Volume total: {volume_total:,.0f} €")
        self.label_profit.setText(f"Profit estimé: {profit_total:,.2f} €")
        self.label_taux_moyen.setText(f"Taux moyen: {taux_moyen:.2f} %")
        self.label_nb_dossiers.setText(f"Dossiers: {len(self.dossiers)}")
    
    def exporter_csv(self):
        if not self.dossiers:
            QMessageBox.warning(self, "Portefeuille vide", 
                "Aucun dossier à exporter.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le portefeuille", 
            f"portefeuille_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    f.write("ID;Type;Montant (€);Durée (ans);Taux (%);Mensualité (€);Profit (€);Score;PD (%);Ratio (%);Date\n")
                    
                    for dossier in self.dossiers:
                        ligne = [
                            str(dossier.get('id', '')),
                            dossier.get('type', ''),
                            f"{dossier.get('montant', 0):.2f}",
                            f"{dossier.get('duree', 0):.1f}",
                            f"{dossier.get('taux', 0):.3f}",
                            f"{dossier.get('mensualite', 0):.2f}",
                            f"{dossier.get('profit', 0):.2f}",
                            str(dossier.get('score_credit', '')),
                            f"{dossier.get('PD', 0):.2f}",
                            f"{dossier.get('ratio_endettement', 0):.1f}",
                            dossier.get('date_ajout', '')
                        ]
                        f.write(";".join(ligne) + "\n")
                
                QMessageBox.information(self, "Export réussi", 
                    f"{len(self.dossiers)} dossiers exportés avec succès !\n\n"
                    f"Fichier : {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'export", 
                    f"Erreur lors de l'exportation :\n\n{str(e)}")
    
    def vider_portefeuille(self):
        """Vide le portefeuille"""
        if not self.dossiers:
            QMessageBox.information(self, "Portefeuille vide", 
                "Le portefeuille est déjà vide.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer les {len(self.dossiers)} dossiers ?\n\n"
            "Cette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.dossiers.clear()
            self.actualiser_table()
            self.actualiser_statistiques()
        
            self.delete_portefeuille_file()
            
            QMessageBox.information(self, "Portefeuille vidé", 
                "Tous les dossiers ont été supprimés.")
    
    def save_portefeuille(self):
        try:
            file_path = "portefeuille_save.json"
            save_data = {
                'date_sauvegarde': datetime.now().isoformat(),
                'nombre_dossiers': len(self.dossiers),
                'dossiers': self.dossiers
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erreur sauvegarde portefeuille: {e}")
            return False
    
    def load_portefeuille(self):
        try:
            file_path = "portefeuille_save.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.dossiers = data.get('dossiers', [])
                    print(f"Portefeuille chargé: {len(self.dossiers)} dossiers")
                    return True
                    
        except Exception as e:
            print(f"Erreur chargement portefeuille: {e}")
        
        return False
    
    def delete_portefeuille_file(self):
        """Supprime le fichier de sauvegarde"""
        try:
            file_path = "portefeuille_save.json"
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except:
            pass
        return False