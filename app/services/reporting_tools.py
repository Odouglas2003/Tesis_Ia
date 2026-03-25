from pymongo.database import Database
from datetime import datetime
import calendar
from typing import List, Dict, Optional, Any
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class ReportingTools:
    def __init__(self, db: Database):
        self.db = db

    def find_collaborators_by_availability(self, month: int, year: int) -> List[Dict]:
        """
        Útil para encontrar colaboradores que terminan sus asignaciones en un mes y año específicos.
        'month' es un número del 1 (Enero) al 12 (Diciembre).
        'year' es el año, por ejemplo, 2025.
        """
        if not (1 <= month <= 12):
            return [{"error": "Mes inválido. Debe ser entre 1 y 12."}]

        _, last_day = calendar.monthrange(year, month)
        start_of_month = datetime(year, month, 1)
        end_of_month = datetime(year, month, last_day, 23, 59, 59)

        logger.info(
            f"Buscando proyectos que terminan entre {start_of_month} y {end_of_month}"
        )

        projects_ending = list(
            self.db.projects.find(
                {"end_date": {"$gte": start_of_month, "$lte": end_of_month}}
            )
        )

        if not projects_ending:
            return []

        collaborator_ids = [
            str(id)
            for proj in projects_ending
            for id in proj.get("assigned_collaborators", [])
        ]
        unique_ids = list(set(collaborator_ids))

        available_collaborators = list(
            self.db.collaborator.find({"_id": {"$in": unique_ids}})
        )

        results = [
            {
                "id": str(c["_id"]),
                "name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                "role": c.get("roles", [{}])[0].get("rol", "N/A"),
                "seniority": c.get("roles", [{}])[0].get("seniority", "N/A"),
                "technologies": c.get("tecnologias", []),
            }
            for c in available_collaborators
        ]

        return results

    def generate_project_status_report(self) -> List[Dict]:
        """
        Útil para generar un reporte completo que muestra todos los proyectos
        y qué colaboradores están asignados a cada uno, con sus roles y tecnologías.
        No necesita parámetros.
        """
        logger.info("Generando reporte de estado de proyectos...")

        projects = list(self.db.projects.find({}))
        collaborators = list(self.db.collaborator.find({}))

        collaborator_map = {str(c["_id"]): c for c in collaborators}

        report_data = []
        for project in projects:
            project_info = {
                "organization_name": project.get("name", "Proyecto sin nombre"),
                "collaborators": [],
            }

            for collab_id in [
                str(id) for id in project.get("assigned_collaborators", [])
            ]:
                collab = collaborator_map.get(collab_id)
                if collab:
                    project_info["collaborators"].append(
                        {
                            "employee_name": f"{collab.get('first_name', '')} {collab.get('last_name', '')}".strip(),
                            "role": collab.get("roles", [{}])[0].get("rol", "N/A"),
                            "seniority": collab.get("roles", [{}])[0].get(
                                "seniority", "N/A"
                            ),
                            "technologies": ", ".join(collab.get("tecnologias", [])),
                            "assigned_hours": collab.get("horasAsignadas", 0),
                        }
                    )

            report_data.append(project_info)

        return report_data

    def top_technologies(self, top: int = 10):
        """Ranking simple de tecnologías por cantidad de colaboradores que las declaran."""
        collabs = self.db.collaborator.find({}, {"tecnologias": 1})
        c = Counter()
        for cdb in collabs:
            for tech in cdb.get("tecnologias", []) or []:
                c[tech] += 1
        return sorted(
            ({"technology": k, "count": v} for k, v in c.items()),
            key=lambda x: (-x["count"], x["technology"]),
        )[:top]

    def collaborator_load(
        self, role: Optional[str] = None, seniority: Optional[str] = None
    ):
        """Carga por colaborador (horasAsignadas), con filtros opcionales por rol/seniority."""
        match: Dict[str, Any] = {}
        if role:
            match["roles.rol"] = role
        if seniority:
            match["roles.seniority"] = seniority
        fields = {"first_name": 1, "last_name": 1, "horasAsignadas": 1, "roles": 1}
        cur = self.db.collaborator.find(match, fields)
        out = []
        for x in cur:
            out.append(
                {
                    "employee_name": f"{x.get('first_name','')} {x.get('last_name','')}",
                    "role": (x.get("roles") or [{}])[0].get("rol", "N/A"),
                    "seniority": (x.get("roles") or [{}])[0].get("seniority", "N/A"),
                    "assigned_hours": x.get("horasAsignadas", 0),
                }
            )
        return out
