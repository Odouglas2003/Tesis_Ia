# app/services/query_parser.py
import re
from typing import Dict, Any, Optional

SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def parse_user_query(query: str) -> Optional[Dict[str, Any]]:
    text = query.lower().strip()

    # --- Prioridad 1: Colaboradores por Proyecto (Pipeline) ---
    m = re.search(r"colaboradores del proyecto (.+)", text)
    if m:
        project_name = m.group(1).strip()
        return {
            "collection": "collaborator",
            "pipeline": [
                {
                    "$lookup": {
                        "from": "projects",
                        "let": {"collaborator_id_str": {"$toString": "$_id"}},
                        "pipeline": [
                            {
                                "$match": {
                                    "name": {"$regex": project_name, "$options": "i"},
                                    "$expr": {
                                        "$in": [
                                            "$$collaborator_id_str",
                                            "$assignedPersons.id",
                                        ]
                                    },
                                }
                            }
                        ],
                        "as": "assigned_project",
                    }
                },
                {"$match": {"assigned_project": {"$ne": []}}},
                {"$project": {"assigned_project": 0}},
            ],
        }

    # --- Lógica de Disponibilidad (Pipeline) ---
    if "disponibles" in text or "libres" in text:
        rol_match = re.search(r"\b(qa|dev|ux|ui|pm|project manager)\b", text, re.I)
        rol_filter = {}
        if rol_match:
            rol = rol_match.group(1).strip()
            if rol.lower() == "dev":
                rol = "Dev."
            rol_filter = {"roles.rol": {"$regex": rol, "$options": "i"}}

        return {
            "collection": "collaborator",
            "pipeline": [
                {"$match": rol_filter},
                {
                    "$addFields": {
                        "totalHorasAsignadasEnProyectos": {
                            "$ifNull": [{"$sum": "$Proyectos.horasAsignadas"}, 0]
                        },
                        "jornada_obj_id": {
                            "$cond": {
                                "if": {
                                    "$and": [
                                        {"$ne": ["$jornadaId", None]},
                                        {"$ne": ["$jornadaId", ""]},
                                    ]
                                },
                                "then": {"$toObjectId": "$jornadaId"},
                                "else": None,
                            }
                        },
                    }
                },
                {
                    "$lookup": {
                        "from": "jornadas",
                        "localField": "jornada_obj_id",
                        "foreignField": "_id",
                        "as": "jornada_details",
                    }
                },
                {
                    "$unwind": {
                        "path": "$jornada_details",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$addFields": {
                        "horasJornadaMensual": {
                            "$ifNull": [{"$multiply": [{"$toInt": "$jornada_details.hours"}, 5]}, 40]
                        }
                    }
                },
                {
                    "$match": {
                        "$expr": {
                            "$lt": [
                                "$totalHorasAsignadasEnProyectos",
                                "$horasJornadaMensual",
                            ]
                        }
                    }
                },
                {
                    "$project": {
                        "jornada_details": 0,
                        "horasJornadaMensual": 0,
                        "jornada_obj_id": 0,
                        "totalHorasAsignadasEnProyectos": 0,
                    }
                },
            ],
        }

    # --- Lógica General de Filtros Simples y Combinados ---
    all_filters = []

    collection = "collaborator"
    if "proyecto" in text:
        collection = "projects"

    if "senior" in text:
        all_filters.append({"roles.seniority": {"$regex": "Senior", "$options": "i"}})
    if "junior" in text:
        all_filters.append({"roles.seniority": {"$regex": "Junior", "$options": "i"}})

    if "node" in text:
        all_filters.append({"tecnologias": {"$regex": "node", "$options": "i"}})
    if "react" in text:
        all_filters.append({"tecnologias": {"$regex": "react", "$options": "i"}})

    if "privado" in text:
        all_filters.append({"category": "Privado"})

    date_match = re.search(
        r"(ingresaron|finalizan|terminan|empiezan|inician).*(?:en|del)?\s*([a-záéíóú]+)?\s*(\d{4})",
        text,
    )
    if date_match:
        verb, mes_txt, year_str = date_match.groups()
        year = int(year_str)
        date_field = (
            "start_contrato"
            if verb == "ingresaron"
            else ("startDate" if verb in ["empiezan", "inician"] else "endDate")
        )

        date_filter_expr = {"$eq": [{"$year": {"$toDate": f"${date_field}"}}, year]}
        if mes_txt and mes_txt in SPANISH_MONTHS:
            mes = SPANISH_MONTHS[mes_txt]
            date_filter_expr = {
                "$and": [
                    date_filter_expr,
                    {"$eq": [{"$month": {"$toDate": f"${date_field}"}}, mes]},
                ]
            }

        all_filters.append({"$expr": date_filter_expr})

    if not all_filters:
        # Manejar caso "todos los colaboradores"
        if text == "todos los colaboradores":
            return {"collection": "collaborator", "filter": {}}
        return None

    final_mongo_filter = (
        {"$and": all_filters} if len(all_filters) > 1 else all_filters[0]
    )
    return {"collection": collection, "filter": final_mongo_filter}
