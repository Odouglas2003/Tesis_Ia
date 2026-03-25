# software-team-builder/app/recommendation_engine.py

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import spacy
import logging
import re
from typing import Dict, List, Any, Set, Optional
from pymongo.database import Database

# --- Configuración y Carga de Modelos ---
AppConfig_global = None
try:
    import sys
    import os

    PROJECT_ROOT_FOR_ENGINE_CONFIG = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    if PROJECT_ROOT_FOR_ENGINE_CONFIG not in sys.path:
        sys.path.insert(0, PROJECT_ROOT_FOR_ENGINE_CONFIG)
    from config import Config as AppConfig_imported

    AppConfig_global = AppConfig_imported
except ImportError:

    class ConfigDummy:
        DEBUG_MODE = True
        NLP_MODEL_NAME = "es_core_news_sm"
        MAX_CANDIDATES_PER_ROLE = 3
        W_TECH_SCORE = 40.0
        W_SENIORITY_MATCH_BONUS = 25.0
        W_PERFORMANCE_SCORE = 20.0
        W_AVAILABILITY_SCORE = 15.0
        W_SUGGESTED_CANDIDATE_BONUS = 10.0

    AppConfig_global = ConfigDummy()

logging.basicConfig(
    level=logging.INFO if not AppConfig_global.DEBUG_MODE else logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)


class SoftwareTeamRecommender:
    def __init__(
        self, df_collaborators: pd.DataFrame, df_projects: Optional[pd.DataFrame] = None
    ):
        logger.info("Initializing SoftwareTeamRecommender (Position-based)...")
        if df_collaborators is None or df_collaborators.empty:
            raise ValueError("DataFrame de colaboradores no puede estar vacío.")

        self.nlp = None
        try:
            logger.info(
                f"Cargando modelo spaCy '{AppConfig_global.NLP_MODEL_NAME}' para esta instancia..."
            )
            self.nlp = spacy.load(AppConfig_global.NLP_MODEL_NAME)
            logger.info("Modelo spaCy cargado exitosamente para esta instancia.")
        except Exception as e:
            logger.exception(
                f"Error crítico al cargar modelo spaCy para esta instancia: {e}"
            )
            raise e

        self.config = AppConfig_global
        self.tech_mapping = self._initialize_tech_mapping()
        self.seniority_map = {
            "trainee": {"tech_exp_factor": 0.2},
            "junior": {"tech_exp_factor": 0.4},
            "junior advanced": {"tech_exp_factor": 0.5},
            "semi senior": {"tech_exp_factor": 0.7},
            "ssr": {"tech_exp_factor": 0.7},
            "senior": {"tech_exp_factor": 0.9},
            "sr": {"tech_exp_factor": 0.9},
            "expert": {"tech_exp_factor": 0.95},
            "lead": {"tech_exp_factor": 0.9},
            "project manager": {"tech_exp_factor": 0.5},
            "manager": {"tech_exp_factor": 0.4},
            "desconocido": {"tech_exp_factor": 0.1},
            "no especificado": {"tech_exp_factor": 0.1},
        }
        self.role_keywords_map = {
            "backend": [
                "backend",
                "back end",
                "dev. back end",
                "backend developer",
                "desarrollador backend",
                "dev.backend",
            ],
            "frontend": [
                "frontend",
                "front end",
                "dev. font end",
                "frontend developer",
                "desarrollador frontend",
            ],
            "fullstack": [
                "fullstack",
                "full stack",
                "dev. full stack",
                "desarrollador",
                "dev.full stack",
            ],
            "devops": ["devops", "devops engineer", "sre", "cloud engineer"],
            "qa": [
                "qa",
                "analista de calidad",
                "analista calidad (qa)",
                "tester",
                "qa analyst",
                "quality assurance",
            ],
            "project manager": [
                "project manager",
                "pm",
                "líder de proyecto",
                "lider de proyecto",
            ],
            "analista funcional": ["analista funcional", "functional analyst"],
            "diseñador ux/ui": [
                "diseñador ux/ui",
                "ux/ui",
                "diseñador",
                "ux designer",
                "ui designer",
            ],
            "arquitecto": ["arquitecto", "architect"],
            "data": [
                "data scientist",
                "científico de datos",
                "cientifico de datos",
                "data analyst",
                "data engineer",
                "data",
            ],
            "scrum master": ["scrum master"],
            "rrhh": ["rrhh", "analista rrhh", "manager rrhh", "recursos humanos"],
            "marketing": ["marketing", "analista de marketing", "comunicacion"],
            "administrativo": [
                "administracion",
                "manager administración y finananzas",
                "analista administración",
                "administrativo",
            ],
            "ceo": ["ceo", "directorio"],
        }

        self.df_projects = pd.DataFrame()
        self.df_employees_original_numeric_values = pd.DataFrame()
        self.df_employees = pd.DataFrame()

        self._process_all_data(df_collaborators, df_projects)

        if not self.df_employees.empty:
            logger.info("Motor inicializado y datos procesados exitosamente.")
        else:
            logger.error(
                "Motor no pudo ser inicializado porque los datos de empleados quedaron vacíos."
            )

    def _process_all_data(
        self, df_collaborators: pd.DataFrame, df_projects: Optional[pd.DataFrame] = None
    ):
        logger.info("Iniciando procesamiento completo de datos...")
        self.df_projects = (
            df_projects.copy() if df_projects is not None else pd.DataFrame()
        )
        self.df_employees_original_numeric_values = pd.DataFrame()
        self.df_employees = self._preprocess_data(df_collaborators.copy())

        if not self.df_employees.empty:
            self._normalize_numeric_values()
            logger.info("Procesamiento de datos completado exitosamente.")
        else:
            logger.warning(
                "El DataFrame de empleados quedó vacío después del preprocesamiento."
            )

    def _initialize_tech_mapping(self) -> Dict[str, List[str]]:
        mapping = {
            "python": ["python", "python3"],
            "java": ["java"],
            "javascript": ["javascript", "js"],
            "react": ["react", "react.js", "reactjs"],
            "react native": ["react native", "reactnative"],
            "angular": ["angular", "angular.js", "angularjs"],
            "vue": ["vue", "vue.js", "vuejs"],
            "node.js": ["node.js", "node", "nodejs"],
            "dotnetcore": [".net core", "dotnet core", ".netcore", "net core"],
            "dotnetframework": [
                ".net framework",
                "dotnet framework",
                ".netframework",
                "net framework",
            ],
            "csharp": ["c#", "csharp"],
            "mongodb": ["mongodb", "mongo"],
            "postgresql": ["postgresql", "postgres", "pgsql"],
            "mysql": ["mysql"],
            "sqlserver": ["sql server", "sqlserver", "mssql"],
            "docker": ["docker"],
            "kubernetes": ["kubernetes", "k8s"],
            "aws": ["aws", "amazon web services"],
            "azure": ["azure", "microsoft azure"],
            "gcp": ["gcp", "google cloud platform"],
            "git": ["git"],
            "jenkins": ["jenkins"],
            "selenium": ["selenium"],
            "figma": ["figma"],
            "html": ["html", "html5"],
            "css": ["css", "css3"],
            "flutter": ["flutter"],
            "typescript": ["typescript", "ts"],
            "db relacionales": ["db relacionales", "sql"],
            "uml": ["uml"],
            "mockups": ["mockups"],
            "jira": ["jira"],
            "microservicios": ["microservicios", "microservices"],
            "kafka": ["kafka"],
            "spring": ["spring", "spring boot"],
            "ansible": ["ansible"],
            "terraform": ["terraform"],
            "pandas": ["pandas"],
            "numpy": ["numpy"],
            "tensorflow": ["tensorflow", "tf"],
            "pytorch": ["pytorch", "torch"],
            "scikit-learn": ["scikit-learn", "sklearn"],
            "next.js": ["next.js", "nextjs"],
        }
        for k, v_list in mapping.items():
            mapping[k] = list(set(v for v in v_list if v != "html / css"))
        return mapping

    def _normalize_tech_name(self, tech_name: str) -> Optional[str]:
        if (
            not isinstance(tech_name, str)
            or pd.isna(tech_name)
            or not tech_name.strip()
        ):
            return None
        tech_lower = tech_name.strip().lower()
        for standard, variants in self.tech_mapping.items():
            if tech_lower in variants:
                return standard
        return tech_lower

    def _get_standard_tech_col_name(self, std_name: str, suffix: str) -> str:
        if not std_name:
            return f"invalid_tech{suffix}"
        if std_name == "node.js":
            base_name = "node.js"
        else:
            base_name = re.sub(r"[^\w.-]+", "_", std_name.strip()).strip("_")
        return f"{base_name}{suffix}"

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Preprocessing data from Collaborator DataFrame...")
        if "_id" in df.columns:
            df["id_col"] = df["_id"].astype(str)
        else:
            df["id_col"] = df.index.astype(str)

        df.set_index("id_col", inplace=True)

        df["nombre_completo"] = (
            df["first_name"].fillna("") + " " + df["last_name"].fillna("")
        ).str.strip()
        df["eval_desempeno"] = pd.to_numeric(df.get("eval_desempeno"), errors="coerce")
        df["sueldo"] = pd.to_numeric(df.get("sueldo"), errors="coerce")
        df["horasAsignadas"] = pd.to_numeric(
            df.get("horasAsignadas"), errors="coerce"
        ).fillna(0)
        df["rol_asignado"] = df["roles"].apply(
            lambda r: (
                self._map_role(r[0].get("rol"))
                if isinstance(r, list) and r and isinstance(r[0], dict)
                else None
            )
        )
        df["seniority_normalizado"] = df["roles"].apply(
            lambda r: (
                self._get_seniority_from_mongo(r)
                if isinstance(r, list)
                else "desconocido"
            )
        )
        df["tech_exp_factor"] = df["seniority_normalizado"].map(
            lambda s: self.seniority_map.get(s, {"tech_exp_factor": 0.1})[
                "tech_exp_factor"
            ]
        )
        for tech_std_name in self.tech_mapping.keys():
            df[self._get_standard_tech_col_name(tech_std_name, "_exp")] = 0.0
        for index, row in df.iterrows():
            tecnologias_list = row.get("tecnologias", [])
            if isinstance(tecnologias_list, list):
                for tech_item in tecnologias_list:
                    norm_tech = self._normalize_tech_name(tech_item)
                    if norm_tech and norm_tech in self.tech_mapping:
                        df.loc[
                            index, self._get_standard_tech_col_name(norm_tech, "_exp")
                        ] = row.get("tech_exp_factor", 0.1)

        numeric_cols = ["eval_desempeno", "sueldo", "horasAsignadas"] + [
            c for c in df.columns if c.endswith("_exp")
        ]
        valid_orig_cols = [c for c in numeric_cols if c in df.columns]

        for col in valid_orig_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        self.df_employees_original_numeric_values = df[valid_orig_cols].copy()

        logger.info(f"Preprocesamiento completado. DataFrame tiene {len(df)} filas.")
        return df

    def _normalize_numeric_values(self):
        if self.df_employees.empty:
            return
        cols_to_normalize = [
            col for col in self.df_employees_original_numeric_values.columns
        ]
        if not cols_to_normalize:
            return

        scaler = MinMaxScaler()
        self.df_employees[cols_to_normalize] = scaler.fit_transform(
            self.df_employees_original_numeric_values.fillna(0)
        )
        logger.info("Valores numéricos normalizados.")

    def _map_role(self, text_to_search: Optional[str]) -> Optional[str]:
        if (
            not text_to_search
            or not isinstance(text_to_search, str)
            or text_to_search.lower() == "n/a"
        ):
            return None
        text_to_search_lower = text_to_search.lower().strip()
        for standard_role, keywords in self.role_keywords_map.items():
            if any(keyword in text_to_search_lower for keyword in keywords):
                return standard_role
        if text_to_search_lower in self.role_keywords_map:
            return text_to_search_lower
        return None

    def _get_seniority_from_mongo(
        self, roles_array: Optional[List[Dict[str, str]]]
    ) -> str:
        if not roles_array or not isinstance(roles_array, list) or not roles_array:
            return "desconocido"
        first_role_obj = roles_array[0]
        if isinstance(first_role_obj, dict):
            seniority_str = first_role_obj.get("seniority", "desconocido")
            cleaned_seniority = (
                seniority_str.lower().strip()
                if isinstance(seniority_str, str)
                else "desconocido"
            )
            return (
                "desconocido"
                if cleaned_seniority in ["-", "no especificado", "nan", ""]
                else cleaned_seniority
            )
        return "desconocido"

    def calculate_position_score(
        self,
        candidate_row: pd.Series,
        required_techs: Set[str],
        required_seniority: str,
        assigned_hours_needed: int,
        is_suggested: bool,
    ) -> tuple[Dict[str, Any], List[str], str]:
        # El método ahora devuelve un diccionario con el desglose del score
        score_details = {}
        missing_data_warnings = []

        if required_techs:
            num_techs_matched = sum(
                1
                for tech in required_techs
                if candidate_row.get(
                    self._get_standard_tech_col_name(tech, "_exp"), 0.0
                )
                > 0
            )
            score_details["tech_score"] = (
                (num_techs_matched / len(required_techs)) * self.config.W_TECH_SCORE
                if len(required_techs) > 0
                else self.config.W_TECH_SCORE
            )
        else:
            score_details["tech_score"] = self.config.W_TECH_SCORE

        score_details["seniority_score"] = (
            self.config.W_SENIORITY_MATCH_BONUS
            if candidate_row.get("seniority_normalizado") == required_seniority
            else 0.0
        )

        original_values_row = self.df_employees_original_numeric_values.loc[
            candidate_row.name
        ]
        eval_desempeno = original_values_row.get("eval_desempeno")
        if pd.notna(eval_desempeno) and eval_desempeno > 0:
            score_details["performance_score"] = (
                (eval_desempeno - 1) / 4
            ) * self.config.W_PERFORMANCE_SCORE
        else:
            score_details["performance_score"] = 0.0
            missing_data_warnings.append("evaluacion_de_desempeno")

        horas_asignadas_actual = original_values_row.get("horasAsignadas", 0)
        horas_disponibles = max(0, 160 - horas_asignadas_actual)

        # El score de disponibilidad ya se filtra antes, así que aquí solo se calcula para informar
        if assigned_hours_needed > 0:
            score_details["availability_score"] = self.config.W_AVAILABILITY_SCORE
            availability_message = f"Disponible ({int(horas_disponibles)}h libres)"
        else:
            score_details["availability_score"] = self.config.W_AVAILABILITY_SCORE
            availability_message = "Disponible (0h requeridas)"

        score_details["suggestion_bonus"] = (
            self.config.W_SUGGESTED_CANDIDATE_BONUS
            if is_suggested
            and (score_details["tech_score"] > 0 or not required_techs)
            and score_details["seniority_score"] > 0
            else 0.0
        )

        score_details["total_score"] = sum(score_details.values())
        return score_details, missing_data_warnings, availability_message

    def analyze_suggested_candidate(
        self, candidate_row: pd.Series, pos_req: Any
    ) -> str:
        # (Sin cambios en esta función)
        analysis_points = []
        mapped_role_req = self._map_role(pos_req.role)
        required_seniority = pos_req.seniority.lower().strip()
        if candidate_row.get("rol_asignado") != mapped_role_req:
            analysis_points.append(
                f"No coincide con el rol solicitado ('{pos_req.role}'). Su rol es '{candidate_row.get('rol_asignado', 'N/A')}'."
            )
        if candidate_row.get("seniority_normalizado") != required_seniority:
            analysis_points.append(
                f"No coincide con el seniority solicitado ('{pos_req.seniority}'). Su seniority es '{candidate_row.get('seniority_normalizado', 'N/A')}'."
            )
        required_techs = {
            self._normalize_tech_name(t)
            for t in pos_req.technologies
            if self._normalize_tech_name(t) in self.tech_mapping
        }
        if required_techs:
            candidate_techs = {
                t.replace("_exp", "")
                for t in self.df_employees.columns
                if t.endswith("_exp") and candidate_row.get(t, 0) > 0
            }
            missing_techs = required_techs.difference(candidate_techs)
            if missing_techs:
                analysis_points.append(
                    f"Le faltan las siguientes tecnologías requeridas: {', '.join(missing_techs)}."
                )
        return (
            "El candidato sugerido es una opción viable y cumple con los requisitos principales de rol, seniority y tecnologías."
            if not analysis_points
            else "Análisis del candidato sugerido: " + " ".join(analysis_points)
        )

    def recommend_for_positions_v2(
        self,
        positions_requested: List[Any],
        budget: float,
        project_description: Optional[str] = None,
        db: Optional[Database] = None,
    ) -> Dict[str, Any]:
        logger.info(
            f"Iniciando recomendación v2 para {len(positions_requested)} posiciones."
        )
        if self.df_employees is None or self.df_employees.empty:
            raise ValueError(
                "No hay datos de colaboradores procesados para realizar recomendaciones."
            )

        position_responses = []

        for pos_req in positions_requested:
            technologies_requested_list = pos_req.technologies or []
            mapped_role = self._map_role(pos_req.role)

            if mapped_role is None:
                position_responses.append(
                    {
                        "position_id": pos_req.position_id,
                        "role_requested": pos_req.role,
                        "seniority_requested": pos_req.seniority,
                        "technologies_requested": technologies_requested_list,
                        "candidates": [],
                        "vacancy_needed": True,
                        "vacancy_message": f"Rol '{pos_req.role}' no reconocido.",
                    }
                )
                continue

            candidates_df_by_role = self.df_employees[
                self.df_employees["rol_asignado"] == mapped_role
            ].copy()

            # --- NUEVO: FILTRO DURO POR DISPONIBILIDAD ---
            final_candidates_df = candidates_df_by_role
            if pos_req.assigned_hours_needed > 0 and not final_candidates_df.empty:
                horas_disponibles = (
                    160
                    - self.df_employees_original_numeric_values.loc[
                        final_candidates_df.index
                    ]["horasAsignadas"]
                )
                final_candidates_df = final_candidates_df[
                    horas_disponibles >= pos_req.assigned_hours_needed
                ]
                logger.info(
                    f"Rol '{pos_req.role}': {len(candidates_df_by_role)} -> {len(final_candidates_df)} candidatos después de filtrar por disponibilidad."
                )

            scored_candidates = []
            if not final_candidates_df.empty:
                required_seniority = pos_req.seniority.lower().strip()
                required_techs = {
                    self._normalize_tech_name(t)
                    for t in (pos_req.technologies or [])
                    if self._normalize_tech_name(t) in self.tech_mapping
                }

                for _, cand_row in final_candidates_df.iterrows():
                    is_suggested = (
                        pos_req.suggestedId is not None
                        and cand_row.name == pos_req.suggestedId
                    )

                    score_details, warnings, availability = (
                        self.calculate_position_score(
                            cand_row,
                            required_techs,
                            required_seniority,
                            pos_req.assigned_hours_needed,
                            is_suggested,
                        )
                    )
                    analysis = (
                        self.analyze_suggested_candidate(cand_row, pos_req)
                        if is_suggested
                        else None
                    )

                    original_values_row = self.df_employees_original_numeric_values.loc[
                        cand_row.name
                    ]
                    sueldo = original_values_row.get("sueldo")
                    if not pd.notna(sueldo) or sueldo == 0:
                        warnings.append("sueldo")

                    known_techs = sorted(
                        [
                            self.tech_mapping[std_tech][0].title()
                            for std_tech in self.tech_mapping
                            if cand_row.get(
                                self._get_standard_tech_col_name(std_tech, "_exp"), 0
                            )
                            > 0
                        ]
                    )

                    scored_candidates.append(
                        {
                            "id": cand_row.name,
                            "name": cand_row["nombre_completo"],
                            "score": score_details["total_score"],
                            "score_details": score_details,  # <-- CAMPO AÑADIDO CON EL DESGLOSE
                            "sueldo": sueldo if pd.notna(sueldo) else 0,
                            "missing_data_warnings": warnings,
                            "availability_message": availability,
                            "is_user_suggestion": is_suggested,
                            "suggestion_analysis": analysis,
                            "known_technologies": known_techs,
                        }
                    )

            scored_candidates.sort(key=lambda x: x["score"], reverse=True)

            final_proposals = []
            user_suggested_candidate = next(
                (c for c in scored_candidates if c.get("is_user_suggestion")), None
            )
            if user_suggested_candidate:
                final_proposals.append(user_suggested_candidate)

            alternatives = [
                c for c in scored_candidates if not c.get("is_user_suggestion")
            ]
            num_alternatives_to_add = self.config.MAX_CANDIDATES_PER_ROLE - len(
                final_proposals
            )
            if num_alternatives_to_add > 0:
                final_proposals.extend(alternatives[:num_alternatives_to_add])

            if final_proposals:
                final_proposals.sort(key=lambda x: x["score"], reverse=True)
                if not final_proposals[0]["is_user_suggestion"]:
                    final_proposals[0]["suggested_by_ia"] = True

            # Preparamos la respuesta final para el frontend
            candidate_responses = []
            for c in final_proposals:
                # Preparamos el desglose del score para que sea legible
                score_breakdown = {
                    "Puntos por Habilidad Técnica": round(
                        c["score_details"].get("tech_score", 0), 2
                    ),
                    "Bonus por Seniority": round(
                        c["score_details"].get("seniority_score", 0), 2
                    ),
                    "Puntos por Desempeño": round(
                        c["score_details"].get("performance_score", 0), 2
                    ),
                    "Puntos por Disponibilidad": round(
                        c["score_details"].get("availability_score", 0), 2
                    ),
                    "Bonus por Sugerencia del Usuario": round(
                        c["score_details"].get("suggestion_bonus", 0), 2
                    ),
                }
                candidate_responses.append(
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "score": round(c.get("score", 0.0), 2),
                        "score_details": score_breakdown,  # <-- CAMPO AÑADIDO Y FORMATEADO
                        "is_user_suggestion": c.get("is_user_suggestion", False),
                        "suggestion_analysis": c.get("suggestion_analysis"),
                        "suggested_by_ia": c.get("suggested_by_ia", False),
                        "availability_message": c["availability_message"],
                        "known_technologies": c.get("known_technologies", []),
                        "missing_data_warnings": c["missing_data_warnings"],
                    }
                )

            num_aptos_total = len(scored_candidates)
            vacancy_needed = num_aptos_total < pos_req.quantity
            vacancy_message = ""
            if num_aptos_total == 0:
                vacancy_message = f"No se encontraron candidatos disponibles para '{pos_req.role} {pos_req.seniority}'. Se necesitan {pos_req.quantity} vacante(s)."
            elif vacancy_needed:
                vacancy_message = f"Solo se encontraron {num_aptos_total} candidato(s) disponible(s) y apto(s). Se necesitan {pos_req.quantity - num_aptos_total} vacante(s) adicionales."
            else:
                vacancy_message = f"Se encontraron {num_aptos_total} candidatos disponibles y aptos. Se proponen los {len(candidate_responses)} mejores."

            position_responses.append(
                {
                    "position_id": pos_req.position_id,
                    "role_requested": pos_req.role,
                    "seniority_requested": pos_req.seniority,
                    "technologies_requested": technologies_requested_list,
                    "candidates": candidate_responses,
                    "vacancy_needed": vacancy_needed,
                    "vacancy_message": vacancy_message,
                }
            )

        budget_details = {
            "total_requested": budget,
            "total_assigned": 0.0,
            "remaining": budget,
        }
        return {"budget_details": budget_details, "positions": position_responses}
