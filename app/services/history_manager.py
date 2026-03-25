import json
import os
from datetime import datetime
from typing import List, Dict


class HistoryManager:
    def __init__(self, file_path: str = "data/history.json"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def save_request(self, request_data: Dict, response_data: Dict):
        """Guarda una solicitud y su respuesta en el historial"""
        history = self._load_history()

        entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request_data,
            "response": response_data,
        }

        history.append(entry)
        self._save_history(history)

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Obtiene el historial de solicitudes"""
        history = self._load_history()
        return history[-limit:]

    def get_last_request(self) -> Dict:
        """Obtiene la última solicitud"""
        history = self._load_history()
        return history[-1] if history else None

    def _load_history(self) -> List[Dict]:
        """Carga el historial desde el archivo"""
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _save_history(self, history: List[Dict]):
        """Guarda el historial en el archivo"""
        with open(self.file_path, "w") as f:
            json.dump(history, f, indent=2)
