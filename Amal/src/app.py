import sys
from PyQt5.QtWidgets import QApplication
from Amal.src.gui.main_window import MachineTaskOptimizer
from Amal.src.gui.widgets.task_card import TaskCard

def main():
    app = QApplication(sys.argv)
    window = MachineTaskOptimizer()
    # Initialiser avec des données de test (optionnel)
    window.tasks = [
        {'id': 1, 'name': 'Tâche 1'},
        {'id': 2, 'name': 'Tâche 2'},
        {'id': 3, 'name': 'Tâche 3'}]
    window.task_counter = 4
    window.incompatibilities = [(2, 3), (1, 3)]
    # Créer les cartes de tâches
    for task in window.tasks:
        card = TaskCard(task['id'], task['name'], window)
        window.tasks_layout.addWidget(card)
    # Mettre à jour l'interface
    window.update_incompatibility_ui()
    window.update_ui()
    # Afficher la fenêtre
    window.show()
    # Lancer la boucle d'événements
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()