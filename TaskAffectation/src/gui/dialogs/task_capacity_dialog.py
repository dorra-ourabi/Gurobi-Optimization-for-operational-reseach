from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
                             QSpinBox, QDoubleSpinBox, QScrollArea, QGridLayout, QFrame)
from PyQt5.QtCore import Qt

class TaskCapacityDialog(QWidget):
    """Dialog pour définir les capacités des machines et durées des tâches"""
    def __init__(self, tasks, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.tasks = tasks
        
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.setWindowTitle("Configuration des Capacités")
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
            }
            QLabel {
                color: white;
            }
        """)
        self.setMinimumSize(600, 700)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Title
        title = QLabel("⚙️ Configuration Avancée")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(20)
        
        # --- SECTION NOMBRE DE MACHINES (MODIFIÉE) ---
        max_machines_group = QGroupBox("Nombre Maximum de Machines Disponibles")
        max_machines_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 2px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
        """)
        max_machines_layout = QVBoxLayout()
        
        label_info = QLabel("Définit la limite de machines et génère les configurations ci-dessous :")
        label_info.setStyleSheet("color: #94a3b8; font-style: italic; margin-bottom: 5px;")
        
        self.max_machines_spin = QSpinBox()
        self.max_machines_spin.setRange(1, 50)
        self.max_machines_spin.setValue(5) # Valeur par défaut
        self.max_machines_spin.setStyleSheet(self.get_spinbox_style())
        
        # CONNECTION DIRECTE : Changer la limite met à jour la liste des machines
        self.max_machines_spin.valueChanged.connect(self.update_machine_capacities)
        
        max_machines_layout.addWidget(label_info)
        max_machines_layout.addWidget(self.max_machines_spin)
        max_machines_group.setLayout(max_machines_layout)
        layout.addWidget(max_machines_group)
        layout.addSpacing(15)
        
        # Durées des tâches
        durations_group = QGroupBox("Durées des Tâches")
        durations_group.setStyleSheet(self.get_groupbox_style())
        durations_layout = QVBoxLayout()
        
        self.duration_inputs = {}
        for task in tasks:
            task_layout = QHBoxLayout()
            label = QLabel(f"{task['name']} (ID: {task['id']}):")
            label.setStyleSheet("color: #94a3b8; font-weight: normal;")
            label.setMinimumWidth(150)
            
            spin = QDoubleSpinBox()
            spin.setRange(0.1, 999.9)
            spin.setValue(1.0)
            spin.setSuffix(" h")
            spin.setStyleSheet(self.get_spinbox_style())
            
            self.duration_inputs[task['id']] = spin
            task_layout.addWidget(label)
            task_layout.addWidget(spin)
            task_layout.addStretch()
            durations_layout.addLayout(task_layout)
        
        durations_group.setLayout(durations_layout)
        layout.addWidget(durations_group)
        layout.addSpacing(15)
        
        # Capacités des machines
        capacities_group = QGroupBox("Capacités Individuelles des Machines")
        capacities_group.setStyleSheet(self.get_groupbox_style())
        capacities_layout = QVBoxLayout()
        
        self.machine_capacities_container = QWidget()
        self.machine_capacities_layout = QVBoxLayout(self.machine_capacities_container)
        self.machine_capacities_layout.setSpacing(10)
        
        self.task_capacity_inputs = {}
        self.time_capacity_inputs = {}
        
        capacities_layout.addWidget(self.machine_capacities_container)
        capacities_group.setLayout(capacities_layout)
        layout.addWidget(capacities_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setStyleSheet(self.get_button_style("#334155", "#475569"))
        
        apply_btn = QPushButton("Appliquer et Optimiser")
        apply_btn.clicked.connect(self.apply_settings)
        apply_btn.setStyleSheet(self.get_button_style("#10b981", "#059669"))
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(apply_btn)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        self.update_machine_capacities() # Initial call
    
    def get_groupbox_style(self):
        return """
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 2px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """

    def get_spinbox_style(self):
        return """
            QSpinBox, QDoubleSpinBox {
                background-color: #1e293b;
                color: white;
                border: 1px solid #334155;
                padding: 8px;
                border-radius: 6px;
                min-width: 100px;
            }
        """

    def get_button_style(self, bg, hover):
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """

    def update_machine_capacities(self):
        # On vide le layout actuel
        while self.machine_capacities_layout.count():
            item = self.machine_capacities_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.task_capacity_inputs.clear()
        self.time_capacity_inputs.clear()
        
        # Le nombre de machines à configurer est ÉGAL au nombre max choisi
        num_machines = self.max_machines_spin.value()
        
        for m in range(num_machines):
            machine_frame = QFrame()
            machine_frame.setStyleSheet("background-color: #1e293b; border-radius: 6px; padding: 10px;")
            machine_layout = QGridLayout(machine_frame)
            
            title = QLabel(f"Machine {m + 1}")
            title.setStyleSheet("color: #06b6d4; font-weight: bold;")
            machine_layout.addWidget(title, 0, 0, 1, 2)
            
            # Capacité Tâches
            machine_layout.addWidget(QLabel("Max tâches:"), 1, 0)
            task_cap = QSpinBox()
            task_cap.setRange(1, len(self.tasks))
            task_cap.setValue(len(self.tasks))
            task_cap.setStyleSheet(self.get_spinbox_style())
            self.task_capacity_inputs[m] = task_cap
            machine_layout.addWidget(task_cap, 1, 1)
            
            # Capacité Temps
            machine_layout.addWidget(QLabel("Temps max:"), 2, 0)
            time_cap = QDoubleSpinBox()
            time_cap.setRange(0.1, 9999.9)
            time_cap.setValue(100.0)
            time_cap.setSuffix(" h")
            time_cap.setStyleSheet(self.get_spinbox_style())
            self.time_capacity_inputs[m] = time_cap
            machine_layout.addWidget(time_cap, 2, 1)
            
            self.machine_capacities_layout.addWidget(machine_frame)
    
    def apply_settings(self):
        settings = {
            # On envoie toujours la valeur du spinbox car le check a disparu
            'max_machines_dispo': self.max_machines_spin.value(),
            'durations': {tid: spin.value() for tid, spin in self.duration_inputs.items()},
            'task_capacities': {m: spin.value() for m, spin in self.task_capacity_inputs.items()},
            'time_capacities': {m: spin.value() for m, spin in self.time_capacity_inputs.items()}
        }
        self.parent_widget.run_optimization_with_settings(settings)
        self.close()