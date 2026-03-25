# process_readmes.py
import os
import json
import re
import logging

try:
    from config import Config
except ImportError:
    print("ERROR: No se pudo importar 'Config' desde 'config.py'.")
    exit(1)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_and_generate_knowledge_base():
    """
    Lee los archivos README, los divide en trozos inteligentes basados en títulos y párrafos,
    y los guarda en un archivo JSON que servirá como base de conocimiento.
    """
    logger.info("--- Iniciando el procesamiento de archivos README ---")

    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    DOCS_DIR = os.path.join(PROJECT_ROOT, Config.DOCS_SUBDIR)
    DATA_DIR = os.path.join(PROJECT_ROOT, Config.DATA_SUBDIR)
    OUTPUT_FILE = os.path.join(DATA_DIR, Config.KNOWLEDGE_BASE_FILE_NAME)

    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.isdir(DOCS_DIR):
        logger.error(f"La carpeta de documentos '{DOCS_DIR}' no existe.")
        return

    knowledge_entries = []
    MAX_CHUNK_SIZE = 1500  # Tamaño máximo de un trozo en caracteres

    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".md"):
            file_path = os.path.join(DOCS_DIR, filename)
            logger.info(f"Procesando archivo: {filename}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Dividir por títulos principales (##, ###)
                    chunks_by_title = re.split(r"(?m)^\s*#{2,}\s+.*", content)
                    titles = re.findall(r"(?m)^\s*#{2,}\s+(.*)", content)

                    if (
                        not titles
                    ):  # Si no hay títulos, procesar el archivo como un solo bloque
                        titles = ["General"]
                    else:
                        # Añadir un título para el contenido que viene antes del primer título
                        titles.insert(0, "General")

                    for i, chunk in enumerate(chunks_by_title):
                        title = titles[i].strip() if i < len(titles) else "Continuación"

                        # Si un trozo es demasiado grande, lo subdividimos por párrafos
                        if len(chunk) > MAX_CHUNK_SIZE:
                            logger.info(
                                f"  -> Trozo '{title}' es muy largo, subdividiendo..."
                            )
                            sub_chunks = re.split(r"\n\s*\n", chunk)
                            for sub_chunk in sub_chunks:
                                cleaned_sub_chunk = sub_chunk.strip()
                                if 50 < len(cleaned_sub_chunk):
                                    entry = {
                                        "source": filename,
                                        "text": f"Contexto: {title}\n\n{cleaned_sub_chunk}",
                                    }
                                    knowledge_entries.append(entry)
                        else:
                            cleaned_chunk = chunk.strip()
                            if len(cleaned_chunk) > 50:
                                entry = {
                                    "source": filename,
                                    "text": f"Contexto: {title}\n\n{cleaned_chunk}",
                                }
                                knowledge_entries.append(entry)

                logger.info(
                    f"  -> Se extrajeron {len(knowledge_entries)} trozos contextuales hasta ahora."
                )

            except Exception as e:
                logger.error(f"Error procesando {file_path}: {e}")

    if knowledge_entries:
        logger.info(
            f"Guardando {len(knowledge_entries)} entradas de conocimiento en {OUTPUT_FILE}"
        )
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(knowledge_entries, f, indent=2, ensure_ascii=False)
        logger.info("--- Procesamiento de READMEs completado. ---")
    else:
        logger.warning("No se generó ninguna entrada de conocimiento.")


if __name__ == "__main__":
    process_and_generate_knowledge_base()
