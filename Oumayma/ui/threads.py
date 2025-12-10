from PyQt5.QtCore import QThread, pyqtSignal
import traceback

class OptimizationThread(QThread):
    """Thread pour l'optimisation"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, optimizer, client, pret):
        super().__init__()
        self.optimizer = optimizer
        self.client = client
        self.pret = pret
    
    def run(self):
        try:
            self.progress.emit(30)
            result = self.optimizer.optimiser_taux(self.client, self.pret)
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class BatchOptimizationThread(QThread):
    """Thread pour optimisation par lots"""
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    result_ready = pyqtSignal(dict)  # Pour résultats intermédiaires
    
    def __init__(self, optimizer, clients_data, loans_data):
        super().__init__()
        self.optimizer = optimizer
        self.clients_data = clients_data
        self.loans_data = loans_data
        self.results = []
    
    def run(self):
        self.results = []
        total = len(self.clients_data)
        
        for i, (client, loan) in enumerate(zip(self.clients_data, self.loans_data)):
            progress = int((i / total) * 100)
            self.progress.emit(progress)
            
            try:
                result = self.optimizer.optimiser_taux(client, loan)
                self.results.append(result)
                self.result_ready.emit(result)
            except Exception as e:
                error_result = {
                    'status': 'ERROR',
                    'raison': str(e),
                    'client': getattr(client, 'score_credit', 'N/A'),
                    'pret': getattr(loan, 'montant', 'N/A')
                }
                self.results.append(error_result)
        
        self.progress.emit(100)
        self.finished.emit(self.results)