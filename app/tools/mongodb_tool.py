import logging
from langchain.tools import Tool
from pymongo import MongoClient
from config import Config
import json
from bson import ObjectId  # Importante para manejar los _id de MongoDB

logger = logging.getLogger(__name__)


# --- Clase para convertir los resultados de MongoDB a un JSON legible ---
class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


# --- Conexión a MongoDB ---
try:
    client = MongoClient(Config.MONGO_DB_CONNECTION_STRING)
    db = client[Config.MONGO_DB_NAME]
    logger.info("Conexión a MongoDB para la herramienta establecida correctamente.")
except Exception as e:
    logger.critical(f"No se pudo conectar a MongoDB para la herramienta: {e}")
    client = None
    db = None


def run_mongodb_query(query: str) -> str:
    """
    Ejecuta una consulta de solo lectura en MongoDB y devuelve el resultado como un string JSON.
    """
    if not db:
        return "Error: No hay conexión a la base de datos."

    try:
        logger.info(f"Ejecutando consulta de agente en MongoDB: {query}")

        local_namespace = {"db": db, "list": list, "ObjectId": ObjectId}
        result = eval(query, {"__builtins__": {}}, local_namespace)

        if result is None:
            return "La consulta no devolvió ningún resultado."

        # Usamos nuestro Encoder personalizado para manejar tipos de MongoDB como ObjectId
        return json.dumps(result, cls=MongoEncoder, indent=2)

    except Exception as e:
        logger.error(f"Error al ejecutar la consulta del agente: {e}")
        return f"Error de sintaxis o ejecución en la consulta: {str(e)}"


# --- DESCRIPCIÓN MEJORADA DE LA HERRAMIENTA ---
# Esta es la parte más importante. Le damos al LLM un "mapa" de la base de datos.
tool_description = """
Herramienta indispensable para responder preguntas sobre los datos de la aplicación 'Software Team Builder'.
La entrada debe ser una consulta de PyMongo de solo lectura, como una única cadena de texto.

**Esquema de Colecciones Disponibles:**

1.  **`db.collaborator`**: Información principal de los colaboradores.
    -   Campos clave: `name`, `lastName`, `rol`, `technologies` (array), `projects` (array), `seniority`.
    -   Útil para preguntas como "¿Quiénes son los desarrolladores senior?" o "¿Qué tecnologías conoce Juan Pérez?".
    -   Ejemplo de consulta: `list(db.collaborator.find({{'seniority': 'Senior'}}, {{'name': 1, 'lastName': 1, '_id': 0}}))`

2.  **`db.projects`**: Detalles de los proyectos.
    -   Campos clave: `name`, `description`, `technologies` (array), `state` (ej. 'Activo', 'Finalizado'), `vacancies` (array).
    -   Útil para preguntas como "¿Cuántos proyectos activos hay?" o "¿Qué tecnologías se usan en un proyecto?".
    -   Ejemplo de consulta: `db.projects.count_documents({{'state': 'Activo'}})`

3.  **`db.vacancie`**: Puestos de trabajo o vacantes abiertas.
    -   Campos clave: `title`, `description`, `required_technologies` (array), `role`, `project_id`.
    -   Útil para preguntas como "¿Hay vacantes para un rol de QA?" o "¿Qué vacantes tiene el proyecto SIRHU?".
    -   Ejemplo de consulta: `list(db.vacancie.find({{'role': 'QA'}}, {{'title': 1, '_id': 0}}))`
    4.  **`db.technologies`**: Lista de todas las tecnologías disponibles en el sistema.
    -   Campos clave: `name`.
    -   Útil para preguntas como "¿Qué tecnologías de backend manejamos?".
    -   Ejemplo de consulta: `list(db.technologies.find({{}}, {{'name': 1, '_id': 0}}))`

5.  **Otras colecciones relevantes:** `user` (datos de usuarios de la app), `notifications`, `roles`.

**Instrucciones para el Agente:**
-   Usa `count_documents` para contar.
-   Usa `.find()` para buscar múltiples documentos. **SIEMPRE** envuelve `.find()` en `list()` para ver los resultados. Ejemplo: `list(db.collection.find())`.
-   Usa `.find_one()` para obtener un solo documento.
-   Usa proyecciones para pedir solo los campos que necesitas. Ejemplo: `{{'name': 1, '_id': 0}}`.
-   Para buscar por ID, usa `ObjectId`. Ejemplo: `db.projects.find_one({{"_id": ObjectId("60d5ecb...")}})`
"""


mongodb_query_tool = Tool(
    name="MongoDB_Database_Query_Tool",
    func=run_mongodb_query,
    description=tool_description,
)
