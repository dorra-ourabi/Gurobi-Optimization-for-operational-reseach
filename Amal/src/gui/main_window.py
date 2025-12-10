from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QScrollArea, 
                             QFrame, QTabWidget, QMessageBox, QComboBox)
from src.services.optimization_service import GUROBI_AVAILABLE, OptimizationThread
from src.gui.widgets.task_card import TaskCard
from src.gui.widgets.incompatibility_card import IncompatibilityCard
from src.gui.widgets.stat_card import StatCard
from src.gui.widgets.graph_widget import GraphWidget
from src.gui.widgets.bar_chart_widget import BarChartWidget
from src.gui.widgets.pie_chart_widget import PieChartWidget
from src.gui.dialogs.add_incompatibility_dialog import AddIncompatibilityDialog
from src.gui.dialogs.task_capacity_dialog import TaskCapacityDialog
from src.utils.constants import MACHINE_COLORS
from src.utils.styles import Styles
class MachineTaskOptimizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.incompatibilities = []
        self.task_counter = 1
        self.scheduler = None
        self.optimization_thread = None
        self.setWindowTitle("Machine Task Optimizer")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(Styles.get_main_window_style())
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        header = self._create_header()
        main_layout.addWidget(header)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(Styles.get_tab_style())
        self.editor_tab = self.create_editor_tab()
        self.tabs.addTab(self.editor_tab, "Éditeur")
        self.viz_tab = self.create_visualization_tab()
        self.tabs.addTab(self.viz_tab, "Visualisation")
        self.results_tab = self.create_results_tab()
        self.tabs.addTab(self.results_tab, "Résultats")        
        main_layout.addWidget(self.tabs)
    
    def _create_header(self):
        header = QWidget()
        header.setStyleSheet(Styles.get_header_style())
        header_layout = QHBoxLayout(header)
        title_layout = QVBoxLayout()
        title = QLabel("⚡ Machine Task Optimizer")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title_layout.addWidget(title)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        if GUROBI_AVAILABLE:
            status_label = QLabel("✓ Gurobi disponible")
            status_label.setStyleSheet("color: #10b981; font-size: 12px;")
        else:
            status_label = QLabel("⚠ Gurobi non disponible")
            status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
        header_layout.addWidget(status_label)
        return header
    
    def create_editor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Editeur de Graphe")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        subtitle = QLabel("Créez vos tâches et définissez leurs incompatibilités")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        add_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Nom de la tâche...")
        self.task_input.setStyleSheet(Styles.get_input_style())
        self.task_input.returnPressed.connect(self.add_task)
        add_btn = QPushButton("+ Ajouter tâche")
        add_btn.setStyleSheet(Styles.get_button_style("#3b82f6") + """
            QPushButton:hover {
                background-color: #2563eb;
            }""")
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(self.task_input)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
        layout.addSpacing(30)
        tasks_title = QLabel(f"Tâches ({len(self.tasks)})")
        tasks_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(tasks_title)
        self.tasks_title_label = tasks_title
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setSpacing(10)
        scroll.setWidget(self.tasks_container)
        layout.addWidget(scroll, 1)
        layout.addSpacing(20)
        incomp_header = QHBoxLayout()
        incomp_title = QLabel(f"Incompatibilités ({len(self.incompatibilities)})")
        incomp_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.incomp_title_label = incomp_title
        incomp_header.addWidget(incomp_title)
        incomp_header.addStretch()
        add_incomp_btn = QPushButton("+ Ajouter incompatibilité")
        add_incomp_btn.setStyleSheet(Styles.get_button_style("#8b5cf6") + """
            QPushButton {
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }""")
        add_incomp_btn.clicked.connect(self.show_add_incompatibility_dialog)
        incomp_header.addWidget(add_incomp_btn)
        layout.addLayout(incomp_header)
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setStyleSheet("border: none;")
        self.incomp_container = QWidget()
        self.incomp_layout = QVBoxLayout(self.incomp_container)
        self.incomp_layout.setSpacing(10)
        scroll2.setWidget(self.incomp_container)
        layout.addWidget(scroll2, 1)
        return widget
        
    def create_visualization_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0f172a; }")
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Visualisation du Graphe")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        self.viz_subtitle = QLabel("Représentation graphique des tâches et conflits")
        self.viz_subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(title)
        layout.addWidget(self.viz_subtitle)
        layout.addSpacing(20)
        self.graph_widget = GraphWidget(self.tasks, self.incompatibilities)
        self.graph_widget.setMinimumSize(800, 500)
        layout.addWidget(self.graph_widget)
        optimize_layout = QHBoxLayout()
        optimize_layout.addStretch()
        #self.method_combo = QComboBox()
        #self.method_combo.addItem("Modèle d'assignation", "assignment")
        #self.method_combo.addItem("Set Covering", "set_covering")
        #self.method_combo.setStyleSheet(Styles.get_combo_style() + """
         #   QComboBox {
          #      padding: 10px;
           #    min-width: 200px;
           # }""")
        method_label = QLabel("Méthode:")
        method_label.setStyleSheet("color: white; font-size: 14px;")
        optimize_layout.addWidget(method_label)
        #optimize_layout.addWidget(self.method_combo)
        optimize_layout.addSpacing(20)
        self.optimize_btn = QPushButton("🚀 Optimiser")
        self.optimize_btn.setStyleSheet(Styles.get_button_style("#10b981") + """
            QPushButton {
                padding: 12px 30px;
                border-radius: 8px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }""")
        self.optimize_btn.clicked.connect(self.show_capacity_dialog)
        self.optimize_btn.setEnabled(GUROBI_AVAILABLE and len(self.tasks) > 0)
        optimize_layout.addWidget(self.optimize_btn)
        layout.addLayout(optimize_layout)
        layout.addStretch()
        scroll.setWidget(content_widget)
        final_layout = QVBoxLayout(widget)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(scroll)
        return widget
    def create_results_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: #0f172a;")
        content_widget = QWidget()
        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        left_column = QVBoxLayout()
        title = QLabel("Résultats d'Optimisation")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        subtitle = QLabel("Affectation optimale avec contraintes")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")
        left_column.addWidget(title)
        left_column.addWidget(subtitle)
        left_column.addSpacing(20)
        graph_title = QLabel("📊 Graphe de la Solution")
        graph_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        left_column.addWidget(graph_title)
        self.solution_graph_widget = GraphWidget(self.tasks, self.incompatibilities)
        self.solution_graph_widget.setMinimumSize(600, 500)
        self.solution_graph_widget.setMaximumSize(800, 600)
        left_column.addWidget(self.solution_graph_widget)
        self.legend_container = QWidget()
        self.legend_layout = QHBoxLayout(self.legend_container)
        self.legend_layout.setSpacing(15)
        self.legend_container.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 15px;")
        left_column.addWidget(self.legend_container)
        left_column.addStretch()
        main_layout.addLayout(left_column, 2)
        right_column = QVBoxLayout()
        stats_layout = QVBoxLayout()
        self.machines_card = StatCard("Nombre de machines", "0", "#0e7490")
        self.tasks_card = StatCard("Total de tâches", "0", "#7c3aed")
        self.incomp_card = StatCard("Incompatibilités", "0", "#ea580c")
        stats_layout.addWidget(self.machines_card)
        stats_layout.addWidget(self.tasks_card)
        stats_layout.addWidget(self.incomp_card)
        stats_layout.addSpacing(20)
        right_column.addLayout(stats_layout)
        charts_title = QLabel("Distribution des tâches")
        charts_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        right_column.addWidget(charts_title)
        self.bar_chart = BarChartWidget()
        self.bar_chart.setMinimumHeight(250)
        self.bar_chart.setMaximumHeight(300)
        right_column.addWidget(self.bar_chart)
        right_column.addSpacing(15)
        pie_title = QLabel("Proportion par machine")
        pie_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        right_column.addWidget(pie_title)
        self.pie_chart = PieChartWidget()
        self.pie_chart.setMinimumHeight(300)
        self.pie_chart.setMaximumHeight(350)
        right_column.addWidget(self.pie_chart)
        right_column.addSpacing(15)
        detail_title = QLabel("Affectation détaillée")
        detail_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        right_column.addWidget(detail_title)
        self.assignment_container = QWidget()
        self.assignment_layout = QVBoxLayout(self.assignment_container)
        self.assignment_layout.setSpacing(10)
        right_column.addWidget(self.assignment_container)
        right_column.addStretch()
        main_layout.addLayout(right_column, 1)
        scroll.setWidget(content_widget)
        final_layout = QVBoxLayout(widget)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(scroll)
        return widget
        
    def add_task(self):
        task_name = self.task_input.text().strip() or f"Tâche {self.task_counter}"
        task_id = self.task_counter
        self.tasks.append({'id': task_id, 'name': task_name})
        self.task_counter += 1
        card = TaskCard(task_id, task_name, self)
        self.tasks_layout.addWidget(card)
        self.task_input.clear()
        self.update_ui()
        
    def show_add_incompatibility_dialog(self):
        if len(self.tasks) < 2:
            QMessageBox.warning(self, "Erreur", "Vous devez avoir au moins 2 tâches")
            return
        self.dialog = AddIncompatibilityDialog(self.tasks, self)
        self.dialog.move(
            self.x() + (self.width() - self.dialog.width()) // 2,
            self.y() + (self.height() - self.dialog.height()) // 2)
        self.dialog.show()

    def add_incompatibility(self, task1, task2):
        if (task1, task2) in self.incompatibilities or (task2, task1) in self.incompatibilities:
            QMessageBox.warning(self, "Erreur", "Cette incompatibilité existe déjà")
            return
        self.incompatibilities.append((task1, task2))
        self.scheduler = None
        card = IncompatibilityCard(task1, task2, self)
        self.incomp_layout.addWidget(card)
        self.update_ui()
        
    def remove_task(self, task_id):
        self.tasks = [t for t in self.tasks if t['id'] != task_id]
        self.incompatibilities = [(a, b) for a, b in self.incompatibilities 
                                  if a != task_id and b != task_id]
        self.scheduler = None
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for task in self.tasks:
            card = TaskCard(task['id'], task['name'], self)
            self.tasks_layout.addWidget(card)
        self.update_incompatibility_ui()
        self.update_ui()
        
    def remove_incompatibility(self, task1, task2):
        self.incompatibilities = [(a, b) for a, b in self.incompatibilities 
                                  if not ((a == task1 and b == task2) or (a == task2 and b == task1))]
        self.scheduler = None
        self.update_incompatibility_ui()
        self.update_ui()
        
    def update_incompatibility_ui(self):
        while self.incomp_layout.count():
            item = self.incomp_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for task1, task2 in self.incompatibilities:
            card = IncompatibilityCard(task1, task2, self)
            self.incomp_layout.addWidget(card)
            
    def update_ui(self):
        self.tasks_title_label.setText(f"Tâches ({len(self.tasks)})")
        self.incomp_title_label.setText(f"Incompatibilités ({len(self.incompatibilities)})")
        self.graph_widget.tasks = self.tasks
        self.graph_widget.incompatibilities = self.incompatibilities
        self.solution_graph_widget.tasks = self.tasks
        self.solution_graph_widget.incompatibilities = self.incompatibilities
        if self.scheduler and self.scheduler.assignment:
            pass
        else:
            self.graph_widget.set_assignment(None)
            self.solution_graph_widget.set_assignment(None)
            self.viz_subtitle.setText("Représentation graphique des tâches et conflits")
            self.viz_subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")
            while self.legend_layout.count():
                item = self.legend_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        self.graph_widget.update()
        self.solution_graph_widget.update()
        self.optimize_btn.setEnabled(GUROBI_AVAILABLE and len(self.tasks) > 0)
        self.tasks_card.set_value(len(self.tasks))
        self.incomp_card.set_value(len(self.incompatibilities))
    
    def show_capacity_dialog(self):
        if not GUROBI_AVAILABLE:
            QMessageBox.warning(self, "Erreur", "Gurobi n'est pas disponible")
            return
        if not self.tasks:
            QMessageBox.warning(self, "Erreur", "Ajoutez au moins une tâche")
            return
        #if self.method_combo.currentData() != 'assignment':
         #   self.run_optimization_with_settings(None)
          #  return
        self.capacity_dialog = TaskCapacityDialog(self.tasks, self)
        self.capacity_dialog.move(
            self.x() + (self.width() - self.capacity_dialog.width()) // 2,
            self.y() + (self.height() - self.capacity_dialog.height()) // 2)
        self.capacity_dialog.show()
        
    def run_optimization_with_settings(self, settings):
        self.optimize_btn.setEnabled(False)
        self.optimize_btn.setText("⏳ Optimisation en cours...")
        #method = self.method_combo.currentData()
        
        if settings: #and method == 'assignment':
            self.optimization_thread = OptimizationThread(
                self.tasks, 
                self.incompatibilities, 
                method='assignment',
                task_capacities=settings.get('task_capacities'),
                time_capacities=settings.get('time_capacities'),
                durations=settings.get('durations'),
                max_machines_dispo=settings.get('max_machines_dispo'))
        else:
            self.optimization_thread = OptimizationThread(
                self.tasks,
                self.incompatibilities,
                method='assignment')
        self.optimization_thread.finished.connect(self.on_optimization_finished)
        self.optimization_thread.error.connect(self.on_optimization_error)
        self.optimization_thread.start()
        
    def on_optimization_finished(self, scheduler):
        self.scheduler = scheduler
        self.optimize_btn.setEnabled(True)
        self.optimize_btn.setText("🚀 Optimiser")
        if scheduler and scheduler.assignment:
            assignment_ui = {}
            for task_name, machine_id in scheduler.assignment.items():
                task_id = int(task_name[1:])
                assignment_ui[task_id] = machine_id
            self.graph_widget.set_assignment(assignment_ui)
            self.solution_graph_widget.tasks = self.tasks
            self.solution_graph_widget.incompatibilities = self.incompatibilities
            self.solution_graph_widget.set_assignment(assignment_ui)
            self.viz_subtitle.setText(
                f"✓ Solution optimale : {scheduler.n_machines_used} machine(s)"
            )
            self.viz_subtitle.setStyleSheet("color: #10b981; font-size: 14px; font-weight: bold;")
            self.update_results(scheduler, assignment_ui)
            self.tabs.setCurrentIndex(2)
            QMessageBox.information(self, "Succès ✓", 
                f"Optimisation terminée!\n\n✓ Machines: {scheduler.n_machines_used}")
        else:
            QMessageBox.warning(self, "Erreur", "Pas de solution trouvée")
            
    def on_optimization_error(self, error_msg):
        self.optimize_btn.setEnabled(True)
        self.optimize_btn.setText("🚀 Optimiser")
        QMessageBox.critical(self, "Erreur", f"Erreur:\n{error_msg}")
        
    def update_results(self, scheduler, assignment_ui):
        self.machines_card.set_value(scheduler.n_machines_used)
        self.tasks_card.set_value(len(self.tasks))
        self.incomp_card.set_value(len(self.incompatibilities))
        machines = {}
        for task_id, machine_id in assignment_ui.items():
            if machine_id not in machines:
                machines[machine_id] = []
            machines[machine_id].append(task_id)
        machine_counts = {}
        for machine_id, task_list in machines.items():
            machine_counts[machine_id + 1] = len(task_list)        
            self.bar_chart.setData(machine_counts)
            self.pie_chart.setData(machine_counts)
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        legend_title = QLabel("Légende:")
        legend_title.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.legend_layout.addWidget(legend_title)
        
        for machine_id in sorted(machines.keys()):
            color = MACHINE_COLORS[machine_id % len(MACHINE_COLORS)]
            legend_item = QFrame()
            legend_item.setStyleSheet("background-color: transparent; padding: 5px;")
            item_layout = QHBoxLayout(legend_item)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(8)
            color_box = QLabel()
            color_box.setFixedSize(30, 30)
            color_box.setStyleSheet(f"""
                background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                border-radius: 6px;
                border: 2px solid white; """)
            label = QLabel(f"Machine {machine_id + 1}")
            label.setStyleSheet("color: white; font-size: 13px;")
            item_layout.addWidget(color_box)
            item_layout.addWidget(label)
            self.legend_layout.addWidget(legend_item)

        self.legend_layout.addStretch()
        while self.assignment_layout.count():
            item = self.assignment_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for machine_id in sorted(machines.keys()):
            task_ids = sorted(machines[machine_id])
            task_names = [next(t['name'] for t in self.tasks if t['id'] == tid) for tid in task_ids]
            color = MACHINE_COLORS[machine_id % len(MACHINE_COLORS)]
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #1e293b;
                    border-left: 4px solid rgb({color.red()}, {color.green()}, {color.blue()});
                    border-radius: 8px;
                    padding: 15px;
                }}""")
            card_layout = QHBoxLayout(card)
            machine_label = QLabel(f"Machine {machine_id + 1}")
            machine_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            tasks_label = QLabel(", ".join(task_names))
            tasks_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
            count_label = QLabel(f"{len(task_ids)} tâche(s)")
            count_label.setStyleSheet(f"""
                color: rgb({color.red()}, {color.green()}, {color.blue()}); 
                font-size: 12px; 
                padding: 5px 10px; 
                background-color: #334155; 
                border-radius: 4px;
                font-weight: bold;
            """)
            card_layout.addWidget(machine_label)
            card_layout.addWidget(tasks_label)
            card_layout.addStretch()
            card_layout.addWidget(count_label)
            self.assignment_layout.addWidget(card)

