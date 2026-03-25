from typing import List, Dict, Any


class ChatProcessor:
    def __init__(self):
        self.chat_history = []

    def process_message(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Procesa un mensaje del usuario y genera una respuesta

        Args:
            user_input: Mensaje del usuario
            context: Contexto adicional (proyecto actual, equipo, etc.)

        Returns:
            Respuesta generada
        """
        # Analizar intención (simplificado)
        intent = self._detect_intent(user_input)

        if intent == "greeting":
            response = "¡Hola! Soy tu asistente para formación de equipos técnicos. ¿En qué puedo ayudarte?"
        elif intent == "team_request":
            response = self._handle_team_request(user_input, context)
        else:
            response = "No estoy seguro de cómo ayudarte con eso. ¿Podrías reformular tu pregunta?"

        # Actualizar historial
        self._update_chat_history(user_input, response)

        return response

    def _detect_intent(self, text: str) -> str:
        """Detección básica de intención"""
        text = text.lower()

        if any(word in text for word in ["hola", "hi", "saludos"]):
            return "greeting"
        elif any(word in text for word in ["equipo", "team", "necesito", "formar"]):
            return "team_request"
        else:
            return "unknown"

    def _handle_team_request(self, text: str, context: Dict) -> str:
        """Maneja solicitudes relacionadas con formación de equipos"""
        # Extraer parámetros básicos (en una implementación real usaríamos NLP)
        params = {
            "technologies": self._extract_technologies(text),
            "team_size": self._extract_team_size(text),
            "budget": self._extract_budget(text),
        }

        return f"Entendido. Voy a buscar un equipo con estas características: {params}"

    def _extract_technologies(self, text: str) -> List[str]:
        """Extrae tecnologías mencionadas (simplificado)"""
        tech_keywords = ["react", "python", "node", "angular", "java"]
        return [tech for tech in tech_keywords if tech in text.lower()]

    def _extract_team_size(self, text: str) -> int:
        """Extrae tamaño del equipo mencionado (simplificado)"""
        # Implementar lógica más sofisticada en producción
        return 5  # Valor por defecto

    def _extract_budget(self, text: str) -> float:
        """Extrae presupuesto mencionado (simplificado)"""
        # Implementar lógica más sofisticada en producción
        return 50000.0  # Valor por defecto

    def _update_chat_history(self, user_input: str, ai_response: str):
        """Actualiza el historial de chat"""
        self.chat_history.append({"user": user_input, "ai": ai_response})

        # Mantener un límite de historial
        if len(self.chat_history) > 10:
            self.chat_history.pop(0)
