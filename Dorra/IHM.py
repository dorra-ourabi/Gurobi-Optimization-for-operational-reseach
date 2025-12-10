import sys
from qtpy.QtWidgets import *


from qtpy.QtCore import Qt, QThread, Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx

from Dorra.EnergiePl import ModeleGaz  # ton modèle enrichi

# --- Thread de résolution ---
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
            if "Erreur" in resultats.get('statut_text','') or "IRRÉALISABLE" in resultats.get('statut_text',''):
                self.error_signal.emit(resultats['statut_text'])
            else:
                self.result_ready.emit(resultats)
        except Exception as e:
            self.error_signal.emit(f"Erreur inattendue : {str(e)}")

# --- IHM principale ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation Réseau Gaz")
        self.setGeometry(50, 50, 1600, 900)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.btn_solve = QPushButton("🚀 Lancer l'optimisation")
        self.btn_solve.setFixedHeight(50)
        self.btn_solve.clicked.connect(self.lancer_resolution)
        self.layout.addWidget(self.btn_solve)

        self.setup_config_tab()
        self.setup_data_tab()
        self.setup_results_tab()

        self.worker = None

        # --- Pré-remplissage pour test ---
        self.input_nodes.setText("3")
        self.input_arcs.setText("3")
        self.generate_tables()
        # Nœuds
        self.node_table.setItem(0,1,QTableWidgetItem("50"))
        self.node_table.setItem(1,1,QTableWidgetItem("-30"))
        self.node_table.setItem(2,1,QTableWidgetItem("-20"))
        # Arcs
        self.arc_table.setItem(0,0,QTableWidgetItem("N1"))
        self.arc_table.setItem(0,1,QTableWidgetItem("N2"))
        self.arc_table.setItem(0,2,QTableWidgetItem("50"))
        self.arc_table.setItem(0,3,QTableWidgetItem("1"))
        self.arc_table.setItem(1,0,QTableWidgetItem("N1"))
        self.arc_table.setItem(1,1,QTableWidgetItem("N3"))
        self.arc_table.setItem(1,2,QTableWidgetItem("50"))
        self.arc_table.setItem(1,3,QTableWidgetItem("1"))
        self.arc_table.setItem(2,0,QTableWidgetItem("N2"))
        self.arc_table.setItem(2,1,QTableWidgetItem("N3"))
        self.arc_table.setItem(2,2,QTableWidgetItem("30"))
        self.arc_table.setItem(2,3,QTableWidgetItem("1"))

    # --- Onglet Configuration ---
    def setup_config_tab(self):
        self.config_tab = QWidget()
        self.tabs.addTab(self.config_tab, "⚙️ Configuration")
        layout = QVBoxLayout(self.config_tab)

        group = QGroupBox("Fonctionnalités Avancées")
        g_layout = QVBoxLayout()

        self.cb_fixed = QCheckBox("Coûts fixes")
        self.cb_mincap = QCheckBox("Capacités minimales")
        self.cb_press = QCheckBox("Pressions min/max")
        self.cb_losses = QCheckBox("Pertes de charge")
        self.cb_diam = QCheckBox("Diamètre / vitesse")
        self.cb_red = QCheckBox("Redondance nœuds critiques")

        for cb in [self.cb_fixed,self.cb_mincap,self.cb_press,self.cb_losses,self.cb_diam,self.cb_red]:
            g_layout.addWidget(cb)

        group.setLayout(g_layout)
        layout.addWidget(group)

        # Vitesse max globale
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Vitesse maximale (m/s) :"))
        self.input_vmax = QLineEdit("20.0")
        hbox.addWidget(self.input_vmax)
        layout.addLayout(hbox)
        layout.addStretch()

    # --- Onglet Données ---
    def setup_data_tab(self):
        self.data_tab = QWidget()
        self.tabs.addTab(self.data_tab, "📊 Données réseau")
        layout = QVBoxLayout(self.data_tab)

        # Nombre de noeuds/arcs
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Nombre de nœuds :"))
        self.input_nodes = QLineEdit("3")
        hbox.addWidget(self.input_nodes)
        hbox.addWidget(QLabel("Nombre d'arcs :"))
        self.input_arcs = QLineEdit("3")
        hbox.addWidget(self.input_arcs)
        self.btn_generate = QPushButton("Générer tables")
        self.btn_generate.clicked.connect(self.generate_tables)
        hbox.addWidget(self.btn_generate)
        layout.addLayout(hbox)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

    # Génération des tableaux dynamiques
    def generate_tables(self):
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        try:
            self.num_nodes = int(self.input_nodes.text())
            self.num_arcs = int(self.input_arcs.text())
        except:
            QMessageBox.critical(self,"Erreur","Nombre de nœuds/arcs invalide")
            return

        # --- Tableau nœuds ---
        node_cols = ["Nom","Bilan"]
        if self.cb_press.isChecked():
            node_cols += ["P_min","P_max"]
        if self.cb_red.isChecked():
            node_cols += ["Critique"]

        self.node_table = QTableWidget(self.num_nodes,len(node_cols))
        self.node_table.setHorizontalHeaderLabels(node_cols)
        self.node_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r in range(self.num_nodes):
            self.node_table.setItem(r,0,QTableWidgetItem(f"N{r+1}"))
            self.node_table.setItem(r,1,QTableWidgetItem("0"))
            col=2
            if self.cb_press.isChecked():
                self.node_table.setItem(r,col,QTableWidgetItem("2.0"))
                self.node_table.setItem(r,col+1,QTableWidgetItem("8.0"))
                col+=2
            if self.cb_red.isChecked():
                self.node_table.setItem(r,col,QTableWidgetItem("0"))
        self.scroll_layout.addWidget(QLabel("Nœuds et bilans"))
        self.scroll_layout.addWidget(self.node_table)

        # --- Tableau arcs ---
        arc_cols = ["Départ","Arrivée","Capacité","Cout_var"]
        self.arc_table = QTableWidget(self.num_arcs,len(arc_cols))
        self.arc_table.setHorizontalHeaderLabels(arc_cols)
        self.arc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r in range(self.num_arcs):
            self.arc_table.setItem(r,0,QTableWidgetItem("N1"))
            self.arc_table.setItem(r,1,QTableWidgetItem("N2"))
            self.arc_table.setItem(r,2,QTableWidgetItem("100"))
            self.arc_table.setItem(r,3,QTableWidgetItem("1.0"))
        self.scroll_layout.addWidget(QLabel("Arcs"))
        self.scroll_layout.addWidget(self.arc_table)

        # --- Paramètres avancés arcs ---
        adv_cols=[]
        if self.cb_fixed.isChecked(): adv_cols.append("Cout fixe")
        if self.cb_mincap.isChecked(): adv_cols.append("Capacité min")
        if self.cb_losses.isChecked(): adv_cols += ["Longueur","Perte"]
        if self.cb_diam.isChecked(): adv_cols.append("Diamètre")
        if adv_cols:
            self.adv_table = QTableWidget(self.num_arcs,len(adv_cols))
            self.adv_table.setHorizontalHeaderLabels(adv_cols)
            self.adv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for r in range(self.num_arcs):
                for c in range(len(adv_cols)):
                    self.adv_table.setItem(r,c,QTableWidgetItem("0"))
                    if adv_cols[c]=="Diamètre": self.adv_table.setItem(r,c,QTableWidgetItem("0.5"))
                    if adv_cols[c]=="Longueur": self.adv_table.setItem(r,c,QTableWidgetItem("10"))
                    if adv_cols[c]=="Perte": self.adv_table.setItem(r,c,QTableWidgetItem("0.01"))
            self.scroll_layout.addWidget(QLabel("Paramètres avancés"))
            self.scroll_layout.addWidget(self.adv_table)

    # --- Onglet Résultats ---
    def setup_results_tab(self):
        self.results_tab = QWidget()
        self.tabs.addTab(self.results_tab,"📈 Résultats")
        layout = QVBoxLayout(self.results_tab)
        self.label_status = QLabel("Statut : en attente")
        layout.addWidget(self.label_status)
        self.label_cost = QLabel("")
        layout.addWidget(self.label_cost)
        self.results_table = QTableWidget(0,4)
        self.results_table.setHorizontalHeaderLabels(["Arc","Debit","Etat","Cout"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)

        # Graphe du réseau
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

    # --- Collecte des données ---
    def collecter_donnees(self):
        try:
            Arcs,Cout_Var,Capacite={}, {}, {}
            Cout_Fixe,Cap_Min={}, {}
            Longueur,Perte={}, {}
            Diametre={}
            Noeuds,Bilan=[], {}
            Pression_Min,Pression_Max={}, {}
            Noeuds_Critiques=[]

            # arcs
            for r in range(self.arc_table.rowCount()):
                u=self.arc_table.item(r,0).text().strip()
                v=self.arc_table.item(r,1).text().strip()
                cap=float(self.arc_table.item(r,2).text())
                cost=float(self.arc_table.item(r,3).text())
                Arcs[(u,v)]=(u,v)
                Capacite[(u,v)]=cap
                Cout_Var[(u,v)]=cost
                Cout_Fixe[(u,v)]=0
                Cap_Min[(u,v)]=0
                Longueur[(u,v)]=10
                Perte[(u,v)]=0
                Diametre[(u,v)]=0.5

            # avancés
            if hasattr(self,'adv_table'):
                for r in range(self.adv_table.rowCount()):
                    c=0
                    if self.cb_fixed.isChecked():
                        Cout_Fixe[list(Arcs.keys())[r]]=float(self.adv_table.item(r,c).text());c+=1
                    if self.cb_mincap.isChecked():
                        Cap_Min[list(Arcs.keys())[r]]=float(self.adv_table.item(r,c).text());c+=1
                    if self.cb_losses.isChecked():
                        Longueur[list(Arcs.keys())[r]]=float(self.adv_table.item(r,c).text());c+=1
                        Perte[list(Arcs.keys())[r]]=float(self.adv_table.item(r,c).text());c+=1
                    if self.cb_diam.isChecked():
                        Diametre[list(Arcs.keys())[r]]=float(self.adv_table.item(r,c).text())

            # noeuds
            for r in range(self.node_table.rowCount()):
                n=self.node_table.item(r,0).text().strip()
                Bilan[n]=float(self.node_table.item(r,1).text())
                Noeuds.append(n)
                c=2
                if self.cb_press.isChecked():
                    Pression_Min[n]=float(self.node_table.item(r,c).text());c+=1
                    Pression_Max[n]=float(self.node_table.item(r,c).text());c+=1
                if self.cb_red.isChecked():
                    crit=int(self.node_table.item(r,c).text());c+=1
                    if crit>0: Noeuds_Critiques.append(n)

            # dictionnaire final
            donnees={'Noeuds':Noeuds,'Arcs':list(Arcs.keys()),'Bilan':Bilan,
                     'Cout_Var':Cout_Var,'Capacite':Capacite}
            if self.cb_fixed.isChecked(): donnees['Cout_Fixe']=Cout_Fixe
            if self.cb_mincap.isChecked(): donnees['Capacite_Min']=Cap_Min
            if self.cb_press.isChecked():
                donnees['Pression_Min']=Pression_Min
                donnees['Pression_Max']=Pression_Max
            if self.cb_losses.isChecked():
                donnees['Longueur']=Longueur
                donnees['Perte_Charge']=Perte
            if self.cb_diam.isChecked():
                donnees['Diametre']=Diametre
                donnees['Vitesse_Max']=float(self.input_vmax.text())
            if self.cb_red.isChecked():
                donnees['Contrainte_Redondance']=True
                donnees['Noeuds_Critiques']=Noeuds_Critiques

            return donnees
        except Exception as e:
            QMessageBox.critical(self,"Erreur","Données invalides: "+str(e))
            return None

    # --- Lancer résolution ---
    def lancer_resolution(self):
        donnees = self.collecter_donnees()
        if not donnees: return
        self.btn_solve.setEnabled(False)
        self.label_status.setText("Statut : Résolution en cours...")
        self.worker = SolverWorker(donnees)
        self.worker.result_ready.connect(self.afficher_resultats)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.start()

    def handle_error(self,msg):
        QMessageBox.critical(self,"Erreur",msg)
        self.label_status.setText("Statut : ERREUR")
        self.btn_solve.setEnabled(True)

    # --- Affichage résultats ---
    def afficher_resultats(self,res):
        self.btn_solve.setEnabled(True)
        self.label_status.setText(f"Statut : {res.get('statut_text')}")
        if 'cout_total' in res:
            self.label_cost.setText(f"Coût total : {res['cout_total']:.2f} €")

        debits=res.get('debits_optimaux',{})
        arcs_act=res.get('arcs_actifs',{})
        self.results_table.setRowCount(len(debits))
        for r,(arc,val) in enumerate(debits.items()):
            self.results_table.setItem(r,0,QTableWidgetItem(f"{arc[0]}→{arc[1]}"))
            self.results_table.setItem(r,1,QTableWidgetItem(f"{val:.2f}"))
            etat="✓" if (arc in arcs_act and arcs_act[arc]>0.5) else "✗"
            self.results_table.setItem(r,2,QTableWidgetItem(etat))
            cout = val*self.collecter_donnees()['Cout_Var'][arc]
            if arc in arcs_act and arcs_act[arc]>0.5:
                cout += self.collecter_donnees().get('Cout_Fixe',{}).get(arc,0)
            self.results_table.setItem(r,3,QTableWidgetItem(f"{cout:.2f}"))

        # --- Graphe ---
        self.ax.clear()
        G=nx.DiGraph()
        for n in self.collecter_donnees()['Noeuds']:
            G.add_node(n)
        for arc in debits:
            G.add_edge(arc[0],arc[1])
        colors=['green' if (arc in arcs_act and arcs_act[arc]>0.5) else 'red' for arc in debits]
        pos=nx.spring_layout(G)
        nx.draw(G,pos,ax=self.ax,node_color='lightblue',with_labels=True,arrows=True,edge_color=colors,arrowstyle='-|>',arrowsize=20)
        self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()