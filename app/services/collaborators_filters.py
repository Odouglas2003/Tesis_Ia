from __future__ import annotations
import re
from typing import Any, Dict, Optional


def build_collaborators_spec(query: str) -> Optional[Dict[str, Any]]:
    text = query.lower()
    if not any(
        word in text
        for word in [
            "colaborador",
            "empleado",
            "persona",
            "qa",
            "dev",
            "senior",
            "junior",
        ]
    ):
        return None

    m = re.search(r"(?:rol|puesto)\s+([a-z\.\s/]+)", text)
    if m:
        rol = m.group(1).strip()
        return {
            "collection": "collaborator",
            "filter": {"roles.rol": {"$regex": rol, "$options": "i"}},
        }

    m = re.search(r"(senior|semi senior|junior)\b", text)
    if m:
        seniority = m.group(1).strip()
        return {
            "collection": "collaborator",
            "filter": {"roles.seniority": {"$regex": seniority, "$options": "i"}},
        }

    return None
