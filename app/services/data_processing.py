import pandas as pd
import numpy as np
import faiss
import spacy
import logging
from typing import List, Any, Optional, TYPE_CHECKING

# Esta importación especial previene errores de importación circular
# permitiendo a los type checkers (como Pylance) ver el tipo
# sin ejecutar la importación en runtime.
if TYPE_CHECKING:
    from ..recommendation_engine import SoftwareTeamRecommender

logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(
        self,
        processed_dataframe: pd.DataFrame,
        recommender_instance: Optional["SoftwareTeamRecommender"] = None,
    ):
        if processed_dataframe is None or processed_dataframe.empty:
            logger.error("DataProcessor recibió un DataFrame vacío o None.")
            raise ValueError("El DataFrame preprocesado no puede estar vacío.")

        self.df: pd.DataFrame = processed_dataframe
        self.recommender: Optional["SoftwareTeamRecommender"] = recommender_instance

        # --- REEMPLAZO DE SENTENCE TRANSFORMER POR SPACY ---
        try:
            # Reutiliza la instancia de spaCy del motor de recomendación si existe
            if (
                self.recommender
                and hasattr(self.recommender, "nlp")
                and self.recommender.nlp is not None
            ):
                self.nlp = self.recommender.nlp
                logger.info(
                    "Usando la instancia de spaCy del Recommender en DataProcessor."
                )
            else:
                # Como fallback, carga una nueva instancia (no debería ocurrir en el flujo normal con Singleton)
                from config import Config

                logger.warning(
                    "DataProcessor está cargando una nueva instancia de spaCy (fallback)."
                )
                self.nlp = spacy.load(Config.NLP_MODEL_NAME)

            # Verificamos que el modelo cargado tenga vectores para generar embeddings
            if not self.nlp.vocab.vectors.length:
                model_name = self.nlp.meta.get("name", "desconocido")
                raise RuntimeError(
                    f"El modelo de spaCy '{model_name}' no incluye vectores de palabras. "
                    "No se pueden generar embeddings. Considera usar un modelo 'md' o 'lg'."
                )

        except Exception as e:
            logger.exception(
                "Error al inicializar el embedder de spaCy en DataProcessor:"
            )
            raise RuntimeError(
                "No se pudo cargar el modelo de embeddings en DataProcessor."
            ) from e
        # --- FIN DEL REEMPLAZO ---

    def generate_text_descriptions(self) -> list:
        if self.df is None or self.df.empty:
            logger.error("DataFrame no cargado/vacío en generate_text_descriptions.")
            return []
        logger.info("Generando descripciones textuales para los perfiles...")
        try:
            descriptions_series = self.df.apply(
                self._create_description_from_processed_data, axis=1
            )
            descriptions_list = descriptions_series.tolist()
            logger.info(
                f"Se generaron {len(descriptions_list)} descripciones textuales."
            )
            return descriptions_list
        except Exception as e:
            logger.exception("Error generando descripciones textuales:", e)
            return []

    def generate_faiss_index(self, descriptions: list, save_path: str) -> Any:
        if not descriptions:
            logger.warning("No hay descripciones para generar el índice FAISS.")
            return None
        try:
            logger.info(
                f"Generando embeddings para {len(descriptions)} descripciones usando spaCy..."
            )

            # --- LÓGICA DE EMBEDDINGS ACTUALIZADA PARA SPACY ---
            # nlp.pipe es la forma más eficiente de procesar múltiples textos
            docs = self.nlp.pipe(descriptions)
            # El .vector de un Doc en spaCy es el embedding promedio de sus tokens
            embeddings = np.array([doc.vector for doc in docs])
            # --- FIN DE LA ACTUALIZACIÓN ---

            if not isinstance(embeddings, np.ndarray) or embeddings.ndim != 2:
                logger.error(
                    f"Los embeddings generados no son un array 2D de NumPy. Forma obtenida: {embeddings.shape}"
                )
                return None

            logger.info(f"Embeddings generados con forma: {embeddings.shape}")

            dimension = embeddings.shape[1]
            if dimension == 0:
                raise ValueError(
                    "La dimensión de los embeddings es 0. El modelo de spaCy no tiene vectores válidos."
                )

            index = faiss.IndexFlatIP(dimension)

            embeddings_float32 = embeddings.astype(np.float32)
            faiss.normalize_L2(embeddings_float32)
            index.add(embeddings_float32)

            logger.info(f"Índice FAISS creado con {index.ntotal} vectores.")
            faiss.write_index(index, save_path)
            logger.info(f"Índice FAISS guardado en: {save_path}")
            return index
        except Exception as e:
            logger.exception(
                f"Error generando o guardando el índice FAISS en '{save_path}':", e
            )
        return None

    def _create_description_from_processed_data(self, row: pd.Series) -> str:
        description_parts: List[str] = []
        rol = row.get("rol_asignado", "Rol no especificado")
        seniority_display = row.get(
            "seniority_original_mongo_display", row.get("seniority_normalizado", "N/A")
        )
        description_parts.append(
            f"Perfil: {rol.replace('_',' ').title()} ({seniority_display.title()})."
        )

        anos_exp_real = "N/A"
        if self.recommender and hasattr(
            self.recommender, "df_employees_original_numeric_values"
        ):
            if not isinstance(self.recommender, type(None)) and hasattr(
                self.recommender, "df_employees_original_numeric_values"
            ):
                if (
                    row.name
                    in self.recommender.df_employees_original_numeric_values.index
                ):
                    anos_exp_real_val = (
                        self.recommender.df_employees_original_numeric_values.loc[
                            row.name
                        ].get("anos_experiencia")
                    )
                    if pd.notna(anos_exp_real_val):
                        anos_exp_real = str(int(anos_exp_real_val))
        if anos_exp_real != "N/A":
            description_parts.append(f"Experiencia general: {anos_exp_real} años.")

        tech_skills: List[str] = []
        if self.recommender and hasattr(self.recommender, "tech_mapping"):
            if not isinstance(self.recommender, type(None)) and hasattr(
                self.recommender, "tech_mapping"
            ):
                for tech_std_name in self.recommender.tech_mapping.keys():
                    exp_col_name = self.recommender._get_standard_tech_col_name(
                        tech_std_name, "_exp"
                    )
                    exp_value_norm = row.get(exp_col_name, 0.0)
                    is_principal_col_name = (
                        self.recommender._get_standard_tech_col_name(
                            tech_std_name, "_principal"
                        )
                    )
                    is_principal = row.get(is_principal_col_name, False)
                    if exp_value_norm > 0.05 or is_principal:
                        tech_display_name = self.recommender.tech_mapping[
                            tech_std_name
                        ][0].title()
                        tech_skills.append(tech_display_name)
        elif "tecnologias" in row and isinstance(row.get("tecnologias"), list):
            tech_skills.extend(row["tecnologias"])

        if tech_skills:
            description_parts.append(
                f"Habilidades técnicas: {', '.join(sorted(list(set(tech_skills))))}."
            )
        else:
            description_parts.append("Habilidades técnicas: No especificadas.")

        estado = row.get("estado", "Estado no especificado")
        description_parts.append(f"Estado actual: {estado}.")

        if "fin_contrato" in row and pd.notna(row.get("fin_contrato")):
            try:
                fin_contrato_dt = pd.to_datetime(row["fin_contrato"], errors="coerce")
                if pd.notna(fin_contrato_dt):
                    description_parts.append(
                        f"Disponible hasta: {fin_contrato_dt.strftime('%d/%m/%Y')}."
                    )
            except Exception:
                pass

        horas_orig = "N/A"
        if self.recommender and hasattr(
            self.recommender, "df_employees_original_numeric_values"
        ):
            if not isinstance(self.recommender, type(None)) and hasattr(
                self.recommender, "df_employees_original_numeric_values"
            ):
                if (
                    row.name
                    in self.recommender.df_employees_original_numeric_values.index
                ):
                    horas_val = (
                        self.recommender.df_employees_original_numeric_values.loc[
                            row.name
                        ].get("horas_capacitacion")
                    )
                    if pd.notna(horas_val):
                        horas_orig = str(int(horas_val))
        if horas_orig != "N/A" and horas_orig != "0":
            description_parts.append(f"Dedicación estimada: {horas_orig} horas.")

        final_description = " ".join(
            part for part in description_parts if part and part.strip() != "."
        )
        return final_description.strip()
