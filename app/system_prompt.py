import openai
from fastapi import FastAPI, Request
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()


MONGO_DB_CONNECTION = os.getenv("MONGO_DB_CONNECTION_STRING")


mongo_client = MongoClient(MONGO_DB_CONNECTION)
db = mongo_client["Rubik"]


SYSTEM_PROMPT = """
Tu eres un asistente experto que convierte preguntas en lenguaje natural a filtros de MongoDB.
Responde SIEMPRE y ÚNICAMENTE con un objeto JSON. No añadas explicaciones.

El JSON de respuesta debe tener la siguiente estructura:
{
  "collection": "nombre_de_la_coleccion",
  "filter": { ...objeto de filtro de MongoDB... }
}

Las colecciones disponibles son: "projects", "collaborator", "vacancie".

### Reglas para la colección "projects":
- El campo de categoría es `category` (valores: "Privado", "Público").
- El campo de estado es `status` (valores: "En curso", "Finalizado", "A iniciar").
- La fecha de inicio es `startDate`.
- Las personas asignadas están en el array `assignedPersons`, que contiene objetos con un campo `rol`.
- Para buscar por año de inicio, usa: `{"$expr": {"$eq": [{"$year": {"$toDate": "$startDate"}}, AÑO]}}`

### Reglas para la colección "collaborator":
- El rol está en `roles.rol`.
- La seniority está en `roles.seniority`.
- Las tecnologías son un array de strings en `tecnologias`.
- La fecha de ingreso es `start_contrato`.

Ejemplos:
- User: "proyectos privados con rol de qa"
- Assistant: { "collection": "projects", "filter": { "$and": [ { "category": { "$regex": "^Privado$", "$options": "i" } }, { "assignedPersons.rol": { "$regex": "QA", "$options": "i" } } ] } }

- User: "colaboradores senior que sepan node"
- Assistant: { "collection": "collaborator", "filter": { "$and": [ { "roles.seniority": { "$regex": "Senior", "$options": "i" } }, { "tecnologias": { "$regex": "Node", "$options": "i" } } ] } }
"""


def generate_mongo_filter_from_query(user_query: str) -> dict:
    """
    Usa la API de OpenAI para convertir una pregunta en un filtro de MongoDB.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ],
            response_format={"type": "json_object"},
        )

        json_response_str = response.choices[0].message["content"]

        import json

        return json.loads(json_response_str)

    except Exception as e:

        print(f"Error al contactar OpenAI: {e}")
        return None


@app.post("/analytics/query")
async def handle_analytics_query(request: Request):
    body = await request.json()
    query = body.get("query")

    if not query:

        return {"error": "No se proporcionó la consulta."}

    mongo_spec = generate_mongo_filter_from_query(query)

    if not mongo_spec:

        return {"error": "No se pudo generar el filtro con la IA."}

    collection_name = mongo_spec.get("collection")
    db_filter = mongo_spec.get("filter")

    results = db[collection_name].find(db_filter)

    results = list(results)
    return {
        "intent": "find",
        "collection": collection_name,
        "filter": db_filter,
        "results": list(results),
    }
