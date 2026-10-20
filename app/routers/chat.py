import logging
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import json
import ast
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_community.vectorstores import FAISS
from pymongo.database import Database as SyncDatabase
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent

# --- CONFIGURACIÓN ---
router = APIRouter(prefix="/chat", tags=["Asistente de Chat"])
logger = logging.getLogger(__name__)
SENSITIVE_FIELDS = ["dni", "honorarios", "password", "sueldo", "address", "token"]


# --- MODELOS Y DEPENDENCIAS ---
class ChatRequest(BaseModel):
    query: str = Field(...)
    chat_history: Optional[List[dict]] = Field(default_factory=list)
    user_role: Optional[str] = ""
    user_name: Optional[str] = ""


def get_sync_db(request: Request) -> SyncDatabase:
    logger.info(
        f"🔍 Estado de sync_mongo_db: {hasattr(request.app.state, 'sync_mongo_db')}"
    )
    if hasattr(request.app.state, "sync_mongo_db"):
        logger.info(
            f"🔍 Valor de sync_mongo_db: {request.app.state.sync_mongo_db is not None}"
        )

    if (
        not hasattr(request.app.state, "sync_mongo_db")
        or request.app.state.sync_mongo_db is None
    ):
        logger.error("❌ ERROR: sync_mongo_db no está disponible durante la request")
        raise HTTPException(
            status_code=503,
            detail="Conexión síncrona a la base de datos no está disponible.",
        )
    return request.app.state.sync_mongo_db


def get_vectorstore(request: Request) -> FAISS:
    logger.info(
        f"🔍 Estado de faiss_vectorstore: {hasattr(request.app.state, 'faiss_vectorstore')}"
    )
    if hasattr(request.app.state, "faiss_vectorstore"):
        logger.info(
            f"🔍 Valor de faiss_vectorstore: {request.app.state.faiss_vectorstore is not None}"
        )

    if (
        not hasattr(request.app.state, "faiss_vectorstore")
        or request.app.state.faiss_vectorstore is None
    ):
        logger.error("❌ ERROR: faiss_vectorstore no está disponible")
        # Crear vectorstore vacío on-demand
        try:
            from langchain_openai import OpenAIEmbeddings

            embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
            empty_vectorstore = FAISS.from_texts(
                ["Documentación no disponible"], embeddings_model
            )
            return empty_vectorstore
        except Exception as e:
            logger.error(f"Error creando vectorstore vacío: {e}")
            raise HTTPException(status_code=503, detail="VectorStore no disponible")

    return request.app.state.faiss_vectorstore


# --- SERVICIO DE HERRAMIENTAS GENÉRICAS ---
class AgentToolsService:
    def __init__(self, sync_db: SyncDatabase):
        self.db = sync_db
        self.proposed_action = None

    ROLE_PATTERNS = {
        "fullstack": r"full\s*stack|fullstack|fulltasck|fullstak|full stack developer|desarrollador\s+full\s*stack",
        "frontend": r"front\s*end|frontend|fontend|fronted|fronend|frontend developer|desarrollador\s+front",
        "backend": r"back\s*end|backend|bakend|backed|backend developer|desarrollador\s+back",
        "devops": r"dev\s*ops|devops|sre|cloud engineer",
        "qa": r"qa|tester|testing|quality assurance|analista de calidad",
        "projectmanager": r"project\s*manager|projectmanager|\bpm\b|lider de proyecto|líder de proyecto",
        "uxui": r"ux\s*/?\s*ui|uxui|diseñador|designer",
        "data": r"data\s*(engineer|analyst|scientist)?|datos|cientifico de datos|científico de datos",
    }

    def _role_pattern(self, role: str) -> str:
        normalized = re.sub(r"[^a-z0-9]", "", role.lower())
        typo_aliases = {
            "fullstackdeveloper": "fullstack", "fullstack": "fullstack",
            "fullstak": "fullstack", "fulltasck": "fullstack",
            "frontenddeveloper": "frontend", "frontend": "frontend",
            "fontend": "frontend", "fronted": "frontend", "fronend": "frontend",
            "backenddeveloper": "backend", "backend": "backend",
            "bakend": "backend", "backed": "backend",
            "devopsengineer": "devops", "tester": "qa",
            "projectmanager": "projectmanager", "pm": "projectmanager",
            "uxui": "uxui", "dataengineer": "data", "dataanalyst": "data",
        }
        canonical = typo_aliases.get(normalized, normalized)
        return self.ROLE_PATTERNS.get(canonical, re.escape(role.strip()))

    def count_collaborators_by_role(self, role: str, only_available: bool = False) -> str:
        """Cuenta colaboradores entendiendo sinonimos, variantes y errores del rol."""
        query = {
            "delete_at": None,
            "roles.rol": {"$regex": self._role_pattern(role), "$options": "i"},
        }
        if only_available:
            query["estado"] = {"$regex": "activo|disponible", "$options": "i"}
        people = list(self.db["collaborator"].find(query))
        if only_available:
            people = [person for person in people if sum(float(p.get("horasAsignadas") or 0) for p in person.get("Proyectos", [])) < 40]
        return json.dumps({
            "requested_role": role,
            "matched_pattern": self._role_pattern(role),
            "count": len(people),
            "collaborators": [{"id": str(person.get("_id")), "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(), "roles": person.get("roles", [])} for person in people[:20]],
        }, ensure_ascii=False)

    def propose_create_vacancy(
        self, name: str, hours: int, order_date: str, start_date: str,
        seniority: str, description: str = "", project_id: str = "",
    ) -> str:
        """Prepara una vacante para confirmar sin modificar datos."""
        payload = {
            "vacancieName": name.strip(), "time": hours,
            "orderDate": order_date, "startDate": start_date,
            "seniority": seniority.strip(), "description": description.strip(),
            "status": "Abierta",
        }
        if project_id.strip():
            payload["projectId"] = project_id.strip()
        self.proposed_action = {
            "type": "create_vacancy",
            "title": f"Crear vacante: {name.strip()}",
            "payload": payload,
        }
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def find_available_collaborators(
        self, technology: str, role: str = "", seniority: str = "", limit: int = 5
    ) -> str:
        """Busca colaboradores activos y estima disponibilidad semanal."""
        filters = {
            "delete_at": None,
            "estado": {"$regex": "activo|disponible", "$options": "i"},
            "tecnologias": {"$regex": re.escape(technology.strip()), "$options": "i"},
        }
        if role.strip():
            filters["roles.rol"] = {"$regex": self._role_pattern(role), "$options": "i"}
        if seniority.strip():
            filters["roles.seniority"] = {"$regex": re.escape(seniority.strip()), "$options": "i"}
        results = []
        for person in self.db["collaborator"].find(filters).limit(max(1, min(limit, 10))):
            assigned = sum(float(p.get("horasAsignadas") or 0) for p in person.get("Proyectos", []))
            results.append({
                "id": str(person.get("_id")),
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "technologies": person.get("tecnologias", []),
                "roles": person.get("roles", []),
                "assigned_hours": assigned,
                "estimated_available_hours": max(0, 40 - assigned),
            })
        return json.dumps(results, ensure_ascii=False)

    def find_overdue_projects(self, limit: int = 10) -> str:
        """Lista proyectos cuya fecha final ya paso y no estan finalizados."""
        today = datetime.utcnow()
        query = {
            "delete_at": None,
            "endDate": {"$lt": today},
            "status": {"$not": {"$regex": "finalizado|completado|cerrado", "$options": "i"}},
        }
        docs = list(self.db["projects"].find(query).sort("endDate", 1).limit(max(1, min(limit, 25))))
        return json.dumps(self._sanitize_output(docs), ensure_ascii=False)

    def suggest_team(self, roles: str, technologies: str = "", hours: int = 40) -> str:
        """Sugiere un colaborador disponible por cada rol solicitado."""
        requested_roles = [value.strip() for value in roles.split(",") if value.strip()]
        requested_techs = [value.strip() for value in technologies.split(",") if value.strip()]
        selected_ids = set()
        team = []
        for role in requested_roles:
            query = {"delete_at": None, "estado": {"$regex": "activo|disponible", "$options": "i"}, "roles.rol": {"$regex": re.escape(role), "$options": "i"}}
            if requested_techs:
                query["tecnologias"] = {"$in": [{"$regex": re.escape(tech), "$options": "i"} for tech in requested_techs]}
            candidates = []
            for person in self.db["collaborator"].find(query).limit(20):
                person_id = str(person.get("_id"))
                if person_id in selected_ids:
                    continue
                assigned = sum(float(p.get("horasAsignadas") or 0) for p in person.get("Proyectos", []))
                available = max(0, 40 - assigned)
                techs = [str(t) for t in person.get("tecnologias", [])]
                matches = sum(1 for tech in requested_techs if any(tech.lower() in known.lower() for known in techs))
                candidates.append((available >= hours, matches, available, person))
            candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
            if not candidates:
                team.append({"role": role, "candidate": None, "vacancy_needed": True})
                continue
            _, _, available, person = candidates[0]
            selected_ids.add(str(person.get("_id")))
            team.append({"role": role, "candidate": {"id": str(person.get("_id")), "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(), "technologies": person.get("tecnologias", []), "available_hours": available}, "vacancy_needed": available < hours})
        return json.dumps(team, ensure_ascii=False)

    def propose_create_collaborator(
        self, first_name: str, last_name: str, email: str, dni: str, rol: str,
        seniority: str, jornada: str = "Full Time", tecnologias: str = "",
        start_contrato: str = "", fin_contrato: str = "",
    ) -> str:
        """Prepara el alta de un colaborador para que el usuario la confirme."""
        payload = {
            "first_name": first_name.strip(), "last_name": last_name.strip(),
            "email": email.strip().lower(), "dni": dni.strip(),
            "rol": rol.strip(), "seniority": seniority.strip(),
            "jornada": (jornada or "Full Time").strip(),
            "tecnologias": [t.strip() for t in (tecnologias or "").split(",") if t.strip()],
            "start_contrato": start_contrato.strip(), "fin_contrato": fin_contrato.strip(),
        }
        self.proposed_action = {
            "type": "create_collaborator",
            "title": f"Dar de alta a {payload['first_name']} {payload['last_name']}",
            "payload": payload,
        }
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def propose_create_project(
        self, name: str, client: str, manager_id: str, manager_name: str,
        status: str, project_type: str, start_date: str, end_date: str,
        category: str, description: str = "", budget: float = 0,
    ) -> str:
        payload = {
            "name": name.strip(), "client": client.strip(),
            "managerId": manager_id.strip(), "managerName": manager_name.strip(),
            "managerVisibleInOrgChart": True, "status": status.strip(),
            "projectType": project_type.strip(), "startDate": start_date,
            "endDate": end_date, "category": category.strip(),
            "description": description.strip(), "budget": budget,
            "assignedPersons": [], "ia_generated": True,
        }
        self.proposed_action = {"type": "create_project", "title": f"Crear proyecto: {name.strip()}", "payload": payload}
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def propose_assign_collaborator(
        self, project_id: str, collaborator_id: str, collaborator_name: str,
        role: str, seniority: str, hours: int, technologies: str = "",
    ) -> str:
        payload = {
            "projectId": project_id.strip(), "id": collaborator_id.strip(),
            "name": collaborator_name.strip(), "rol": role.strip(),
            "seniority": seniority.strip(), "horasAsignadas": hours,
            "tecnologias": [item.strip() for item in technologies.split(",") if item.strip()],
        }
        self.proposed_action = {"type": "assign_collaborator", "title": f"Asignar {collaborator_name.strip()} al proyecto", "payload": payload}
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def propose_remove_assignment(self, project_id: str, collaborator_id: str, collaborator_name: str) -> str:
        payload = {"projectId": project_id.strip(), "collaboratorId": collaborator_id.strip(), "name": collaborator_name.strip()}
        self.proposed_action = {"type": "remove_assignment", "title": f"Quitar a {collaborator_name.strip()} del proyecto", "payload": payload}
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def propose_close_vacancy(self, vacancy_id: str, vacancy_name: str) -> str:
        payload = {"vacancyId": vacancy_id.strip(), "name": vacancy_name.strip(), "status": "Finalizada"}
        self.proposed_action = {"type": "close_vacancy", "title": f"Cerrar vacante: {vacancy_name.strip()}", "payload": payload}
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def propose_update_project(
        self, project_id: str, project_name: str, status: str = "",
        end_date: str = "", description: str = "", budget: float = -1,
    ) -> str:
        changes = {}
        if status.strip(): changes["status"] = status.strip()
        if end_date.strip(): changes["endDate"] = end_date.strip()
        if description.strip(): changes["description"] = description.strip()
        if budget >= 0: changes["budget"] = budget
        payload = {"projectId": project_id.strip(), "name": project_name.strip(), "changes": changes}
        self.proposed_action = {"type": "update_project", "title": f"Editar proyecto: {project_name.strip()}", "payload": payload}
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    def propose_notification(self, message: str, recipients: str, alert_level: str = "info", reference_id: str = "jarvis") -> str:
        payload = {"message": message.strip(), "recipients": [value.strip() for value in recipients.split(",") if value.strip()], "alertLevel": alert_level.strip(), "referenceId": reference_id.strip() or "jarvis"}
        self.proposed_action = {"type": "create_notification", "title": "Enviar notificacion interna", "payload": payload}
        return "Accion preparada. El usuario debe revisarla y confirmarla."

    ASSIGNMENT_STATES = {
        "sin_asignacion": "Sin asignación",
        "subasignado": "Subasignado",
        "asignado": "Asignado",
        "sobreasignado": "Sobreasignado",
    }

    def list_collaborators_by_assignment_status(self, estado: str = "") -> str:
        """Clasifica colaboradores activos segun horas semanales asignadas vs capacidad (jornada diaria x 5).
        Usa la misma regla que el dashboard del sistema."""
        key = re.sub(r"[^a-z_]", "", (estado or "").lower().replace(" ", "_").replace("ó", "o"))
        jornadas = {str(j.get("_id")): float(j.get("hours") or 0) for j in self.db["jornadas"].find({})}
        groups = {k: [] for k in self.ASSIGNMENT_STATES}
        for person in self.db["collaborator"].find({"delete_at": None}):
            total = sum(float(p.get("horasAsignadas") or 0) for p in (person.get("Proyectos") or []))
            capacity = jornadas.get(str(person.get("jornadaId")), 8.0) * 5
            if total == 0:
                state = "sin_asignacion"
            elif total > capacity:
                state = "sobreasignado"
            elif total == capacity:
                state = "asignado"
            else:
                state = "subasignado"
            groups[state].append({
                "id": str(person.get("_id")),
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "assigned_hours_per_week": total,
                "weekly_capacity_hours": capacity,
            })
        if key in groups:
            return json.dumps({"estado": self.ASSIGNMENT_STATES[key], "count": len(groups[key]), "collaborators": groups[key]}, ensure_ascii=False)
        return json.dumps({self.ASSIGNMENT_STATES[k]: {"count": len(v), "collaborators": v} for k, v in groups.items()}, ensure_ascii=False)

    def generate_status_report(self) -> str:
        now = datetime.utcnow()
        report = {
            "active_projects": self.db["projects"].count_documents({"delete_at": None, "status": {"$not": {"$regex": "finalizado|completado|cerrado", "$options": "i"}}}),
            "overdue_projects": self.db["projects"].count_documents({"delete_at": None, "endDate": {"$lt": now}, "status": {"$not": {"$regex": "finalizado|completado|cerrado", "$options": "i"}}}),
            "open_vacancies": self.db["vacancie"].count_documents({"delete_at": None, "status": {"$ne": "Finalizada"}}),
            "active_collaborators": self.db["collaborator"].count_documents({"delete_at": None, "estado": {"$regex": "activo|disponible", "$options": "i"}}),
        }
        return json.dumps(report, ensure_ascii=False)

    def _sanitize_output(self, data: any) -> any:
        if isinstance(data, dict):
            return {
                k: self._sanitize_output(v)
                for k, v in data.items()
                if k not in SENSITIVE_FIELDS
            }
        if isinstance(data, list):
            return [self._sanitize_output(item) for item in data]
        if isinstance(data, ObjectId):
            return str(data)
        if isinstance(data, datetime):
            return data.isoformat()
        return data

    def _regex_filter(self, value: str) -> dict:
        return {"$regex": re.escape(value.strip()), "$options": "i"}

    def find_collaborator_by_name(self, full_name: str, limit: int = 5) -> str:
        """Busca colaboradores sin depender del orden entre nombre y apellido."""
        tokens = [token for token in re.split(r"\s+", full_name.strip()) if token]
        if not tokens:
            return "Ingresá al menos una parte del nombre o apellido."

        name_filter = {
            "$and": [
                {
                    "$or": [
                        {"first_name": self._regex_filter(token)},
                        {"last_name": self._regex_filter(token)},
                    ]
                }
                for token in tokens
            ]
        }
        try:
            documents = list(self.db["collaborator"].find(name_filter).limit(limit))
            if not documents:
                return f"No se encontraron colaboradores que coincidan con '{full_name}'."
            return json.dumps(
                self._sanitize_output(documents), ensure_ascii=False, indent=2
            )
        except Exception as e:
            logger.error("Error buscando colaborador por nombre: %s", e)
            return "Error al buscar el colaborador por nombre."

    def _string_filter_value(self, filter_query: dict, field: str) -> Optional[str]:
        value = filter_query.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _build_collaborator_name_fallback_filter(
        self, filter_query: dict
    ) -> Optional[dict]:
        first_name = self._string_filter_value(filter_query, "first_name")
        last_name = self._string_filter_value(filter_query, "last_name")

        if not first_name and not last_name:
            return None

        other_filters = {
            key: value
            for key, value in filter_query.items()
            if key not in {"first_name", "last_name"}
        }

        if first_name and last_name:
            name_filter = {
                "$or": [
                    {
                        "$and": [
                            {"first_name": self._regex_filter(first_name)},
                            {"last_name": self._regex_filter(last_name)},
                        ]
                    },
                    {
                        "$and": [
                            {"first_name": self._regex_filter(last_name)},
                            {"last_name": self._regex_filter(first_name)},
                        ]
                    },
                ]
            }
        else:
            name = first_name or last_name
            name_filter = {
                "$or": [
                    {"first_name": self._regex_filter(name)},
                    {"last_name": self._regex_filter(name)},
                ]
            }

        if other_filters:
            return {"$and": [other_filters, name_filter]}
        return name_filter

    def get_schema(self, collection_names_str: str = "") -> str:
        """Indispensable para ver los nombres exactos de las colecciones y sus campos antes de hacer una consulta."""
        try:
            if not collection_names_str or not collection_names_str.strip():
                collection_names = self.db.list_collection_names()
            else:
                collection_names = [
                    name.strip() for name in collection_names_str.split(",")
                ]

            schema_description = "Esquemas de la Base de Datos:\n"
            for name in collection_names:
                if name.startswith("system."):
                    continue
                sample_doc = self.db[name].find_one({}, {"_id": 0})
                if sample_doc:
                    sanitized_sample = self._sanitize_output(sample_doc)
                    fields = {
                        key: str(type(value).__name__)
                        for key, value in sanitized_sample.items()
                    }
                    schema_description += f"\n--- Colección: '{name}' ---\nCampos: {list(fields.keys())}\n"
            return (
                schema_description
                if len(schema_description) > 50
                else "No se encontraron colecciones con datos."
            )
        except Exception as e:
            return f"Error al obtener el esquema: {str(e)}"

    def count_documents(self, collection_name: str) -> int:
        """Cuenta el número total de documentos en CUALQUIER colección especificada."""
        logger.info(f"Contando documentos en: {collection_name}")
        try:
            return self.db[collection_name].count_documents({})
        except Exception as e:
            logger.error(
                f"Error en count_documents para la colección '{collection_name}': {e}"
            )
            return -1

    def find_documents(
        self, collection_name: str, filter_query_str: str, limit: int = 5
    ) -> str:
        """Busca documentos en CUALQUIER colección usando un filtro. Devuelve una lista de resultados."""
        logger.info(f"Buscando en '{collection_name}' con filtro: {filter_query_str}")
        try:
            filter_query = ast.literal_eval(filter_query_str)
            documents = list(self.db[collection_name].find(filter_query).limit(limit))
            used_fallback = False
            fallback_filter = None

            if (
                not documents
                and collection_name == "collaborator"
                and isinstance(filter_query, dict)
            ):
                fallback_filter = self._build_collaborator_name_fallback_filter(
                    filter_query
                )
                if fallback_filter:
                    logger.info(
                        "Sin resultados exactos. Reintentando busqueda flexible de colaborador con filtro: %s",
                        fallback_filter,
                    )
                    documents = list(
                        self.db[collection_name].find(fallback_filter).limit(limit)
                    )
                    used_fallback = True
            if not documents:
                if fallback_filter:
                    return (
                        f"No se encontraron documentos en la coleccion '{collection_name}' "
                        f"con el filtro {filter_query_str}. Tambien se probo una busqueda "
                        "flexible por first_name/last_name en ambos ordenes."
                    )
                return f"No se encontraron documentos en la colección '{collection_name}' con el filtro {filter_query_str}."
            result = json.dumps(
                self._sanitize_output(documents), ensure_ascii=False, indent=2
            )
            if used_fallback:
                return (
                    "Coincidencias encontradas usando busqueda flexible por "
                    f"nombre/apellido:\n{result}"
                )
            return result
        except Exception as e:
            logger.error(f"Error en find_documents: {e}")
            return "Error al ejecutar la búsqueda. Verifica el nombre de la colección y la sintaxis del filtro."


# --- MODELOS DE ARGUMENTOS ---
class SearchDocsArgs(BaseModel):
    consulta: str = Field(
        description="La pregunta o tema a buscar en la documentación."
    )


class CountArgs(BaseModel):
    collection_name: str = Field(
        description="El nombre exacto de la colección a contar (ej. 'collaborator', 'projects')."
    )


class FindArgs(BaseModel):
    collection_name: str = Field(
        description="El nombre exacto de la colección donde buscar (ej. 'collaborator', 'projects')."
    )
    filter_query_str: str = Field(
        description="Un filtro de MongoDB en formato de string de diccionario Python. Para colaboradores, usa first_name y last_name; si no hay resultado exacto, se prueba una busqueda flexible por nombre/apellido. Ejemplo: \"{'first_name': 'Luciana'}\""
    )
    limit: int = Field(default=5, description="Número máximo de resultados a devolver.")


class CollaboratorNameArgs(BaseModel):
    full_name: str = Field(
        description="Nombre, apellido o nombre completo escrito en cualquier orden."
    )
    limit: int = Field(default=5, description="Número máximo de resultados a devolver.")


class CreateVacancyArgs(BaseModel):
    name: str = Field(description="Nombre de la vacante")
    hours: int = Field(description="Cantidad de horas requeridas")
    order_date: str = Field(description="Fecha del pedido en formato YYYY-MM-DD")
    start_date: str = Field(description="Fecha de inicio en formato YYYY-MM-DD")
    seniority: str = Field(description="Seniority requerido")
    description: str = Field(default="", description="Descripcion opcional")
    project_id: str = Field(default="", description="ID opcional del proyecto")


class AvailableCollaboratorsArgs(BaseModel):
    technology: str
    role: str = ""
    seniority: str = ""
    limit: int = 5


class AssignmentStatusArgs(BaseModel):
    estado: str = Field(
        default="",
        description="Uno de: sin_asignacion, subasignado, asignado, sobreasignado. Vacio = resumen de todos.",
    )


class RoleCountArgs(BaseModel):
    role: str = Field(description="Rol escrito de cualquier manera, incluso abreviado o con errores")
    only_available: bool = Field(default=False, description="Si debe contar solamente personas con horas disponibles")


class OverdueProjectsArgs(BaseModel):
    limit: int = 10


class SuggestTeamArgs(BaseModel):
    roles: str = Field(description="Roles separados por coma")
    technologies: str = Field(default="", description="Tecnologias separadas por coma")
    hours: int = 40


class CreateCollaboratorArgs(BaseModel):
    first_name: str = Field(description="Nombre")
    last_name: str = Field(description="Apellido")
    email: str = Field(description="Email laboral")
    dni: str = Field(description="DNI, solo numeros")
    rol: str = Field(description="Puesto, por ejemplo Backend Developer, QA Engineer, Project Manager")
    seniority: str = Field(description="Trainee, Junior, Semi Senior o Senior")
    jornada: str = Field(default="Full Time", description="Full Time, Part Time o Media Jornada")
    tecnologias: str = Field(default="", description="Tecnologias separadas por coma")
    start_contrato: str = Field(default="", description="Inicio de contrato YYYY-MM-DD")
    fin_contrato: str = Field(default="", description="Fin de contrato YYYY-MM-DD")


class CreateProjectArgs(BaseModel):
    name: str
    client: str
    manager_id: str
    manager_name: str
    status: str
    project_type: str
    start_date: str
    end_date: str
    category: str
    description: str = ""
    budget: float = 0


class AssignCollaboratorArgs(BaseModel):
    project_id: str
    collaborator_id: str
    collaborator_name: str
    role: str
    seniority: str
    hours: int
    technologies: str = ""


class RemoveAssignmentArgs(BaseModel):
    project_id: str
    collaborator_id: str
    collaborator_name: str


class CloseVacancyArgs(BaseModel):
    vacancy_id: str
    vacancy_name: str


class UpdateProjectArgs(BaseModel):
    project_id: str
    project_name: str
    status: str = ""
    end_date: str = ""
    description: str = ""
    budget: float = -1


class NotificationArgs(BaseModel):
    message: str
    recipients: str = Field(description="Emails separados por coma")
    alert_level: str = "info"
    reference_id: str = "jarvis"


# --- ENDPOINT DEL CHAT ---
@router.post("/")
async def chat_endpoint(
    chat_request: ChatRequest,
    sync_db: SyncDatabase = Depends(get_sync_db),
    vectorstore: FAISS = Depends(get_vectorstore),
):
    try:
        logger.info(f"📨 Request recibida en /chat: {chat_request.query}")
        logger.info("✅ Paso 1: Request llegó al endpoint /chat")

        # Verificar dependencias
        if sync_db is None:
            logger.error("❌ sync_db es None")
            return {"answer": "Error: Base de datos no disponible"}

        logger.info("✅ Paso 2: Dependencias verificadas")

        # Inicializar servicio
        try:
            service = AgentToolsService(sync_db)
            logger.info("✅ Paso 3: AgentToolsService creado")
        except Exception as e:
            logger.error(f"❌ Error creando AgentToolsService: {e}", exc_info=True)
            return {"answer": "Error inicializando servicio de herramientas"}

        # Definir función de búsqueda
        def search_docs(consulta: str) -> str:
            try:
                if vectorstore is None:
                    return "La documentación no está disponible en este momento."
                docs = vectorstore.similarity_search(consulta, k=1)
                if not docs:
                    return "No encontré información sobre eso en la documentación."
                return docs[0].page_content
            except Exception as e:
                logger.error(f"❌ Error en search_docs: {e}")
                return f"Ocurrió un error al consultar la documentación: {e}"

        # Crear herramientas
        try:
            tools = [
                StructuredTool.from_function(
                    func=search_docs,
                    name="buscar_en_documentacion",
                    args_schema=SearchDocsArgs,
                    description="Útil para responder preguntas conceptuales sobre el sistema 'Software Team Builder'.",
                ),
                StructuredTool.from_function(
                    func=service.get_schema,
                    name="obtener_esquema_db",
                    description="Indispensable para ver los nombres exactos de las colecciones y sus campos antes de hacer una consulta de datos.",
                ),
                StructuredTool.from_function(
                    func=service.count_documents,
                    name="contar_documentos",
                    args_schema=CountArgs,
                    description="Útil para contar el número total de documentos en una colección (ej. 'collaborator', 'projects').",
                ),
                StructuredTool.from_function(
                    func=service.find_documents,
                    name="buscar_documentos",
                    args_schema=FindArgs,
                    description="Útil para buscar uno o más documentos en una colección usando un filtro.",
                ),
                StructuredTool.from_function(
                    func=service.find_collaborator_by_name,
                    name="buscar_colaborador_por_nombre",
                    args_schema=CollaboratorNameArgs,
                    description="Busca un colaborador por nombre o apellido en cualquier orden. Es la herramienta obligatoria para preguntas como 'quién es Quiroga Martin'.",
                ),
                StructuredTool.from_function(
                    func=service.propose_create_vacancy,
                    name="proponer_creacion_vacante",
                    args_schema=CreateVacancyArgs,
                    description="Prepara una vacante para confirmacion. Usar solo si el usuario pide crearla y dio nombre, horas, fecha de pedido, fecha de inicio y seniority.",
                ),
                StructuredTool.from_function(func=service.find_available_collaborators, name="buscar_colaboradores_disponibles", args_schema=AvailableCollaboratorsArgs, description="Busca colaboradores activos por tecnologia, rol y seniority, mostrando horas disponibles estimadas."),
                StructuredTool.from_function(func=service.count_collaborators_by_role, name="contar_colaboradores_por_rol", args_schema=RoleCountArgs, description="Cuenta colaboradores por rol tolerando sinonimos, nombres parciales y errores como fullstack/full stack/fulltasck o frontend/fontend/fronted."),
                StructuredTool.from_function(func=service.find_overdue_projects, name="buscar_proyectos_atrasados", args_schema=OverdueProjectsArgs, description="Lista proyectos vencidos que aun no estan finalizados."),
                StructuredTool.from_function(func=service.suggest_team, name="armar_equipo", args_schema=SuggestTeamArgs, description="Sugiere un colaborador disponible por cada rol pedido y marca si hace falta una vacante."),
                StructuredTool.from_function(func=service.propose_create_collaborator, name="proponer_alta_colaborador", args_schema=CreateCollaboratorArgs, description="Prepara el alta de un colaborador nuevo para que el usuario la confirme. Usar cuando ya se tienen nombre, apellido, email, DNI, puesto, seniority y jornada."),
                StructuredTool.from_function(func=service.propose_create_project, name="proponer_creacion_proyecto", args_schema=CreateProjectArgs, description="Prepara un proyecto para confirmacion cuando estan todos los datos obligatorios."),
                StructuredTool.from_function(func=service.propose_assign_collaborator, name="proponer_asignacion_colaborador", args_schema=AssignCollaboratorArgs, description="Prepara la asignacion de un colaborador a un proyecto. Primero hay que buscar ambos para obtener IDs reales."),
                StructuredTool.from_function(func=service.propose_remove_assignment, name="proponer_quitar_asignacion", args_schema=RemoveAssignmentArgs, description="Prepara quitar un colaborador de un proyecto usando IDs reales."),
                StructuredTool.from_function(func=service.propose_close_vacancy, name="proponer_cierre_vacante", args_schema=CloseVacancyArgs, description="Prepara el cierre de una vacante encontrada previamente."),
                StructuredTool.from_function(func=service.propose_update_project, name="proponer_edicion_proyecto", args_schema=UpdateProjectArgs, description="Prepara cambios permitidos de un proyecto: estado, fecha final, descripcion o presupuesto."),
                StructuredTool.from_function(func=service.propose_notification, name="proponer_notificacion", args_schema=NotificationArgs, description="Prepara una notificacion interna para emails indicados."),
                StructuredTool.from_function(func=service.list_collaborators_by_assignment_status, name="listar_colaboradores_por_estado_asignacion", args_schema=AssignmentStatusArgs, description="Lista colaboradores sin asignacion, subasignados, asignados o sobreasignados segun sus horas semanales. Usar SIEMPRE para preguntas sobre quien esta libre, sin asignar o sobrecargado."),
                StructuredTool.from_function(func=service.generate_status_report, name="generar_reporte_estado", description="Genera un resumen ejecutivo actual de proyectos, atrasos, vacantes y colaboradores."),
            ]
            logger.info("✅ Paso 4: Tools creadas correctamente")
        except Exception as e:
            logger.error(f"❌ Error creando tools: {e}", exc_info=True)
            return {"answer": "Error configurando herramientas de IA"}

        # Inicializar LLM
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=500)
            logger.info("✅ Paso 5: LLM inicializado (gpt-3.5-turbo)")
        except Exception as e:
            logger.error(f"❌ Error inicializando LLM: {e}", exc_info=True)
            return {"answer": "Error con servicio de OpenAI"}

        # Crear agente
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """Tu nombre es JARVIS. Eres el asistente de IA de Software Team Builder, el sistema desarrollado para esta tesis.
                        Su objetivo es ayudar a gestionar colaboradores y proyectos, analizar perfiles y recomendar
                        equipos de trabajo adecuados según roles, tecnologías, experiencia y presupuesto.
                        **INSTRUCCIONES CRÍTICAS:**
                     1. Para buscar colaboradores/personas, usa SIEMPRE la colección 'collaborator'
                     2. La colección 'people' es de otro sistema y NO contiene datos actuales
                     3. Tu primer paso es SIEMPRE usar 'obtener_esquema_db' para ver la estructura
                     4. Para colaboradores: buscar en colección 'collaborator' con campos 'first_name' y 'last_name'
                     5. Los usuarios pueden escribir "apellido nombre" o solo una parte del nombre; no asumas que el primer token siempre es first_name.
                     6. Si preguntan quién es una persona o buscan un colaborador por nombre, usa PRIMERO 'buscar_colaborador_por_nombre' con el nombre completo tal como lo escribió el usuario.
                     7. Si pide crear una vacante, solicita brevemente los datos obligatorios faltantes. Cuando esten todos, usa 'proponer_creacion_vacante'. Nunca afirmes que fue creada antes de la confirmacion.
                     8. Para disponibilidad usa 'buscar_colaboradores_disponibles'; para atrasos usa 'buscar_proyectos_atrasados'; para sugerir equipos usa 'armar_equipo'.
                     8.0 Para preguntas sobre colaboradores sin asignacion, subasignados, asignados o sobreasignados usa SIEMPRE 'listar_colaboradores_por_estado_asignacion'. Las horas de proyecto son semanales.
                     8.1 Para preguntar cuantos colaboradores hay de un rol usa SIEMPRE 'contar_colaboradores_por_rol'. No construyas filtros literales para roles; la herramienta entiende variantes y errores de escritura.
                     9. Para crear proyectos solicita nombre, cliente, manager con ID, estado, tipo, fechas y categoria. Luego usa 'proponer_creacion_proyecto'.
                     10. Para asignar personas, busca primero el proyecto y colaborador para obtener IDs reales, solicita rol, seniority y horas, y usa 'proponer_asignacion_colaborador'. Toda escritura requiere confirmacion.
                     11. Tambien puedes preparar cierres de vacantes, quitar asignaciones, editar estado/fecha/descripcion/presupuesto de proyectos y enviar notificaciones. Busca primero los IDs y usa la herramienta especifica.
                     12. Para reportes generales usa 'generar_reporte_estado' y presenta los resultados claramente.
                     13. Para dar de alta un colaborador pedi en lenguaje natural: nombre, apellido, email, DNI, puesto, seniority (Trainee, Junior, Semi Senior o Senior), jornada (Full Time, Part Time o Media Jornada), tecnologias y fechas de contrato (opcionales). Con los datos obligatorios usa 'proponer_alta_colaborador'. Solo un administrador puede confirmar altas.
                     14. NUNCA muestres al usuario nombres internos de la base de datos ni de campos (por ejemplo collaborator, projects, first_name, last_name, estado, roles, tecnologias, start_contrato, jornadaId). Habla siempre como una persona: Nombre, Apellido, Puesto, Jornada, Fin de contrato.
                     15. Contexto de la sesion: {user_context}. Si el usuario es manager, recordale amablemente que las altas de colaboradores y proyectos las confirma un administrador, y que solo puede modificar proyectos donde es Project Manager.

                    📋 **Colecciones principales:**
                     - 'collaborator': Colaboradores actuales del sistema
                     - 'projects': Proyectos
                     - 'people': ❌ NO USAR - Datos obsoletos de otro sistema

                     Responde siempre en español, con un tono natural, cercano y conciso. Te basas únicamente en la
                     información que te proporcionan tus herramientas.""",
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("user", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            agent = create_openai_tools_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=6,
                max_execution_time=30,
            )
            logger.info("✅ Paso 6: Agente creado correctamente")

        except Exception as e:
            logger.error(f"❌ Error creando agente: {e}", exc_info=True)
            return {"answer": "Error configurando agente de IA"}

        # Ejecutar agente
        try:
            logger.info("✅ Paso 7: Ejecutando agente...")
            response = await agent_executor.ainvoke(
                {
                    "input": chat_request.query,
                    "chat_history": chat_request.chat_history or [],
                    "user_context": (
                        f"usuario {chat_request.user_name or 'sin nombre'} con rol {chat_request.user_role or 'desconocido'}"
                    ),
                }
            )
            final_answer = response.get("output", "No pude generar una respuesta.")
            logger.info("✅ Paso 8: Agente ejecutado exitosamente")
            return {"answer": final_answer, "action": service.proposed_action}

        except Exception as e:
            logger.error(f"❌ Error ejecutando agente: {e}", exc_info=True)
            return {
                "answer": "Lo siento, tuve un problema al procesar tu pregunta. Por favor intenta de nuevo."
            }

    except Exception as e:
        logger.critical(f"💥 ERROR CRÍTICO NO MANEJADO en /chat: {e}", exc_info=True)
        return {
            "answer": "Error interno del servidor. Por favor contacta al administrador."
        }
