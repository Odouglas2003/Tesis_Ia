from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

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


def is_count_query(text: str) -> bool:
    t = text.lower()
    return "cuántos" in t or "cuantos" in t


def _expr_month_eq_anyfield(fields: List[str], month: int) -> Dict[str, Any]:
    return {
        "$or": [
            {"$expr": {"$eq": [{"$month": {"$toDate": f"${f}"}}, month]}}
            for f in fields
        ]
    }


def _expr_year_eq_anyfield(fields: List[str], year: int) -> Dict[str, Any]:
    return {
        "$or": [
            {"$expr": {"$eq": [{"$year": {"$toDate": f"${f}"}}, year]}} for f in fields
        ]
    }


ROLE_TOKENS = {
    "dev",
    "qa",
    "ux",
    "ui",
    "backend",
    "front",
    "frontend",
    "backend",
    "full",
    "fullstack",
    "scrum",
    "pm",
    "data",
    "designer",
    "arquitecto",
    "back",
    "front end",
    "back end",
}


def build_vacancies_spec(query: str) -> Optional[Dict[str, Any]]:
    if not query:
        return None

    text = query.strip().lower()
    intent = "count" if is_count_query(text) else "find"

    m = re.search(
        r"(?:vacantes?|puestos?).*(?:del\s+proyecto|proyecto)\s+([a-z0-9\.\-_\s]+)",
        text,
        re.I,
    )
    if m:
        proj_txt = m.group(1).strip()
        regex_proj = re.escape(proj_txt).replace(r"\ ", r"\s+")
        return {
            "intent": intent,
            "collection": "vacancie",
            "pipeline": [
                {
                    "$lookup": {
                        "from": "projects",
                        "localField": "projectId",
                        "foreignField": "_id",
                        "as": "proj",
                    }
                },
                {"$match": {"proj.name": {"$regex": regex_proj, "$options": "i"}}},
                {"$project": {"proj": 0}},
            ],
        }

    m = re.search(r"(?:más|mas)\s+de\s+(\d+)\s+horas", text, re.I)
    if m:
        horas = int(m.group(1))
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"time": {"$gt": horas}},
        }

    m = re.search(r">=\s*(\d+)\s*horas?", text)
    if m:
        horas = int(m.group(1))
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"time": {"$gte": horas}},
        }

    m = re.search(r"(?:al\s+menos|mínimo|minimo)\s+(\d+)\s+horas?", text, re.I)
    if m:
        horas = int(m.group(1))
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"time": {"$gte": horas}},
        }

    if re.search(r"\b(editado|modificado|editad[ao]s?)\b", text, re.I):
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"last_edited_on": {"$exists": True}},
        }

    if re.search(r"\b(abierta|abiertas|abierto)\b", text, re.I):
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {
                "$or": [
                    {"delete_at": {"$exists": False}},
                    {"delete_at": None},
                    {"delete_at": ""},
                ]
            },
        }

    if re.search(r"\b(cerrada|cerradas|cerrado)\b", text, re.I):
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"delete_at": {"$nin": [None, ""]}},
        }

    s_txt = None

    m = re.search(
        r"(?:seniority|señority|senoridad|señoridad|nivel)\s+(?:requerido|solicitado)?\s*([a-z\.\s]+)",
        text,
        re.I,
    )
    if m:
        s_txt = m.group(1).strip()
    else:

        m2 = re.search(
            r"\bvacantes?\b.*\b(junior|semi\s*senior|semi\s*sr|ssr|sr|senior|jr)\b",
            text,
            re.I,
        )
        if m2:
            s_txt = m2.group(1).strip()

    if s_txt:
        key = re.sub(r"\s+", " ", s_txt.lower())
        alias = {
            "jr": "Junior",
            "sr": "Senior",
            "ssr": "Semi Senior",
            "semi sr": "Semi Senior",
            "semi senior": "Semi Senior",
        }
        canon = alias.get(key, s_txt)
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {
                "seniority": {"$regex": f"^{re.escape(canon)}$", "$options": "i"}
            },
        }

    m = re.search(
        r"\b(?:rol|puesto|vacante|vacantes?|puestos?)\b.*?\b(?:de|para)\s+([a-z0-9\.\-/\s]+)$",
        text,
        re.I,
    )
    if m:
        term = m.group(1).strip()

    ROLE_HINTS = r"(dev|desarrollador|backend|front\s*end|frontend|full\s*stack|qa|tester|data|analista|arquitect|pm|po|ux|ui|mobile|android|ios|\.net|dotnet|java|node|python|golang|go|php|ruby|sap|sr|ssr|jr)"
    if not re.search(ROLE_HINTS, term, re.I):

        pass
    else:
        term_low = term.lower()
        if "dev" in term_low and "back" in term_low and "end" in term_low:
            regex_rol = r"dev\.?\s*back\s*end"
        elif "dev" in term_low and "front" in term_low and "end" in term_low:
            regex_rol = r"dev\.?\s*front\s*end"
        else:
            regex_rol = re.escape(term).replace(r"\ ", r"\s+")
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"vacancieName": {"$regex": regex_rol, "$options": "i"}},
        }

    m = re.search(
        r"(?:vacantes?|puestos?|b[uú]squedas?|busquedas?)\s+(?!del\s+proyecto)(?:de|del)\s+([a-záéíóúñ\s]+)",
        text,
        re.I,
    )
    if m:
        nombre = m.group(1).strip()
        regex_nombre = re.escape(nombre).replace(r"\ ", r"\s+")
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"manager_name": {"$regex": regex_nombre, "$options": "i"}},
        }

    m = re.search(r"(?:pedido|solicitad[ao]|cread[ao]).*en\s+(\d{4})", text, re.I)
    if m:
        year = int(m.group(1))
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": _expr_year_eq_anyfield(["orderDate", "created_at"], year),
        }

    m = re.search(r"(?:inicio|comienzan?|empiezan?).*en\s+(\d{4})", text, re.I)
    if m:
        year = int(m.group(1))
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": _expr_year_eq_anyfield(["startDate"], year),
        }

    m = re.search(
        r"(?:tecnolog[ií]as?|skills?).*(?:de|para)?\s*([a-z0-9\.\-_\s]+)", text, re.I
    )
    if m:
        tech = m.group(1).strip()
        regex_tech = re.escape(tech).replace(r"\ ", r"\s+")
        return {
            "intent": intent,
            "collection": "vacancie",
            "filter": {"tecnologias": {"$regex": regex_tech, "$options": "i"}},
        }

    return None
