from PyQt5.QtCore import  QThread, pyqtSignal

# Import du scheduler Gurobi
GUROBI_AVAILABLE = False
MachineScheduler = None

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("machine_scheduler", "src/machine_scheduler.py")
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        MachineScheduler = module.MachineScheduler
        GUROBI_AVAILABLE = True
        print("✓ Gurobi et machine_scheduler.py chargés avec succès")
except Exception as e:
    print(f"⚠ Gurobi non disponible: {e}")
    print("L'application fonctionnera en mode visualisation uniquement")

class OptimizationThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    def __init__(self, tasks, incompatibilities, method='assignment', 
                 task_capacities=None, time_capacities=None, 
                 durations=None, max_machines_dispo=None):
        super().__init__()
        self.tasks = tasks
        self.incompatibilities = incompatibilities
        self.method = method
        self.task_capacities = task_capacities
        self.time_capacities = time_capacities
        self.durations = durations
        self.max_machines_dispo = max_machines_dispo
        
    def run(self):
        try:
            task_names = [f"T{t['id']}" for t in self.tasks]
            conflicts = [(f"T{t1}", f"T{t2}") for t1, t2 in self.incompatibilities]
            scheduler = MachineScheduler(task_names, conflicts)
            #if self.method == 'assignment':
                # Convertir les durées avec les bons noms de tâches
            durations_converted = None
            if self.durations:
                  durations_converted = {f"T{tid}": dur for tid, dur in self.durations.items()}
            scheduler.solve_assignment_model(
                task_capacities=self.task_capacities,
                time_capacities=self.time_capacities,
                durations=durations_converted,
                max_machines_dispo=self.max_machines_dispo,
                time_limit=60 )
            #else:
             #   scheduler.solve_set_covering_model(time_limit=60)
            self.finished.emit(scheduler)
        except Exception as e:
            self.error.emit(str(e))