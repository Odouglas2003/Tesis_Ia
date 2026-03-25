from __future__ import annotations
import re
from typing import Any, Dict, Optional

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


def build_projects_spec(query: str) -> Optional[Dict[str, Any]]:
    text = query.lower()
    if "proyecto" not in text:
        return None

    m = re.search(
        r"(finalizan|terminan|empiezan|inician).*(?:en|del)?\s*([a-záéíóú]+)?\s*(\d{4})",
        text,
    )
    if m:
        verb, mes_txt, year_str = m.groups()
        year = int(year_str)
        date_field = "startDate" if verb in ["empiezan", "inician"] else "endDate"

        if mes_txt and mes_txt in SPANISH_MONTHS:
            mes = SPANISH_MONTHS[mes_txt]
            return {
                "collection": "projects",
                "filter": {
                    "$expr": {
                        "$and": [
                            {"$eq": [{"$year": {"$toDate": f"${date_field}"}}, year]},
                            {"$eq": [{"$month": {"$toDate": f"${date_field}"}}, mes]},
                        ]
                    }
                },
            }

        else:
            return {
                "collection": "projects",
                "filter": {
                    "$expr": {"$eq": [{"$year": {"$toDate": f"${date_field}"}}, year]}
                },
            }

    if "privado" in text:
        return {
            "collection": "projects",
            "filter": {"category": {"$regex": "privado", "$options": "i"}},
        }
    if "público" in text:
        return {
            "collection": "projects",
            "filter": {"category": {"$regex": "público", "$options": "i"}},
        }

    return None
