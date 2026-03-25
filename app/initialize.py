# software-team-builder/app/initialize.py
import pandas as pd
import os
import logging
import sys
from pymongo import MongoClient  # Para MongoDB
from typing import Optional  # Tipos necesarios

# --- Añadir la raíz del proyecto a sys.path ---
# Esto es crucial para que la importación explícita de 'config' funcione consistentemente.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Importación explícita de config.py desde la raíz del proyecto ---
Config_class_from_root = (
    None  # Inicializar para asegurar que está definido en el scope global del script
)
config_module_loaded_successfully = False  # Bandera para verificar la carga
try:
    import importlib.util

    # Construir la ruta completa al archivo config.py en la raíz del proyecto
    config_file_path = os.path.join(PROJECT_ROOT, "config.py")
    # print(f"DEBUG [initialize.py]: Intentando cargar config desde: {config_file_path}") # Log de depuración

    if not os.path.exists(config_file_path):
        # Este error debería detener el script antes si config.py no existe
        raise ImportError(
            f"El archivo config.py no se encuentra en la ruta esperada: {config_file_path}"
        )

    # Crear una especificación de módulo desde la ruta del archivo
    # Usar un nombre de módulo único para esta carga para evitar conflictos si 'config' ya está en sys.modules
    spec = importlib.util.spec_from_file_location(
        "config_module_for_initialize_script", config_file_path
    )

    if spec and spec.loader:  # Verificar que spec y spec.loader no sean None
        config_module = importlib.util.module_from_spec(spec)
        # Añadir el módulo a sys.modules ANTES de ejecutarlo para que las importaciones dentro de config.py (si las tuviera) funcionen.
        sys.modules["config_module_for_initialize_script"] = config_module
        # print(f"DEBUG [initialize.py]: Ejecutando módulo config...") # Log de depuración
        spec.loader.exec_module(
            config_module
        )  # Ejecutar el módulo para que se defina la clase Config
        # print(f"DEBUG [initialize.py]: Módulo config ejecutado.") # Log de depuración
        # print(f"DEBUG [initialize.py]: Contenido de config_module: {dir(config_module)}") # Log de depuración IMPORTANTE

        if hasattr(
            config_module, "Config"
        ):  # Verificar si el atributo 'Config' (la clase) existe en el módulo
            Config_class_from_root = (
                config_module.Config
            )  # Acceder a la clase Config desde el módulo cargado
            if (
                Config_class_from_root is None
            ):  # Esto no debería pasar si hasattr es True y Config es una clase
                raise ImportError(
                    "El atributo 'Config' en config_module es None, lo cual es inesperado para una clase."
                )
            # print(f"INFO [initialize.py]: Clase Config cargada exitosamente desde config.py.") # Log de éxito
            config_module_loaded_successfully = True
        else:
            # Si hasattr es False, la clase Config no se definió en config.py o tiene un nombre diferente
            raise ImportError(
                "El atributo 'Config' (la clase) no se encontró en el módulo config.py cargado. Verifica el nombre de la clase en config.py."
            )
    else:
        raise ImportError(
            f"No se pudo crear la especificación del módulo para config.py en {config_file_path}. Verifica la ruta y los permisos."
        )

except ImportError as e_config:
    print(
        f"ERROR CRÍTICO [initialize.py]: No se pudo importar/acceder a la clase 'Config' desde config.py: {e_config}"
    )
    # Si config_module se definió pero hasattr falló, su contenido podría dar pistas
    if "config_module" in locals() and config_module:
        print(f"  Contenido de config_module (en error): {dir(config_module)}")
    sys.exit(1)  # Salir si Config no se puede cargar, ya que es esencial
# --- Fin importación explícita de Config ---

# Verificar si la carga fue exitosa antes de continuar con otras importaciones
if not config_module_loaded_successfully or Config_class_from_root is None:
    print(
        "ERROR CRÍTICO [initialize.py]: La configuración (Config_class_from_root) no se cargó correctamente. Saliendo."
    )
    sys.exit(1)


# --- Importaciones de módulos de la aplicación (relativas al paquete 'app') ---
# Estas deberían funcionar si 'app' es un paquete y 'initialize.py' se ejecuta correctamente
# desde la raíz, ya que la raíz (que contiene 'app') está en sys.path.
try:
    from app.recommendation_engine import SoftwareTeamRecommender
    from app.services.data_processing import DataProcessor

    # Si necesitas FAISSEmbedding directamente aquí (aunque DataProcessor lo usa):
    # from app.services.embeddings import FAISSEmbedding
except ImportError as e_app:
    print(
        f"ERROR [initialize.py]: Failed to import app modules (Recommender, DataProcessor): {e_app}"
    )
    print(
        "  Verifica que estos módulos existan en las rutas app/ y app/services/ y no tengan errores de importación internos."
    )
    sys.exit(1)

# Configuración de Logging
# Usar Config_class_from_root para obtener el nivel de debug si está definido
log_level_init = "INFO"  # Default
# Acceder a DEBUG_MODE a través de la instancia de Config cargada
if hasattr(Config_class_from_root, "DEBUG_MODE") and Config_class_from_root.DEBUG_MODE:
    log_level_init = "DEBUG"

logging.basicConfig(
    level=log_level_init,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    logger.info(
        f"--- Starting Initialization Script (PROJECT_ROOT: {PROJECT_ROOT}) ---"
    )
    # Usar la clase Config importada explícitamente (Config_class_from_root)
    models_dir_path = os.path.join(PROJECT_ROOT, Config_class_from_root.MODELS_SUBDIR)
    faiss_index_full_path = os.path.join(
        models_dir_path, Config_class_from_root.EMBEDDINGS_FILE_NAME
    )

    os.makedirs(models_dir_path, exist_ok=True)  # Crear 'models/' si no existe

    mongo_client: Optional[MongoClient] = None
    df_collaborators_for_faiss: Optional[pd.DataFrame] = None

    # 1. Conectar a MongoDB y cargar datos de colaboradores
    if not Config_class_from_root.MONGO_DB_CONNECTION_STRING:
        logger.error(
            "CRITICAL: MONGO_DB_CONNECTION_STRING no definida en Config. Saliendo."
        )
        return
    try:
        logger.info("Connecting to MongoDB for data loading...")
        mongo_client = MongoClient(
            Config_class_from_root.MONGO_DB_CONNECTION_STRING,
            serverSelectionTimeoutMS=5000,
        )
        mongo_client.admin.command("ping")
        db = mongo_client[Config_class_from_root.MONGO_DB_NAME]
        collaborator_collection = db[
            Config_class_from_root.MONGO_EMPLOYEES_COLLECTION_NAME
        ]
        logger.info(
            f"Connected to MongoDB: DB '{Config_class_from_root.MONGO_DB_NAME}', Collection '{Config_class_from_root.MONGO_EMPLOYEES_COLLECTION_NAME}'."
        )
        collaborators_cursor = collaborator_collection.find({})
        collaborators_list = list(collaborators_cursor)
        if not collaborators_list:
            logger.error("No documents found in MongoDB. Cannot create FAISS index.")
            if mongo_client:
                mongo_client.close()  # Cerrar cliente
            return
        logger.info(f"Loaded {len(collaborators_list)} collaborators from MongoDB.")
        df_collaborators_for_faiss = pd.DataFrame(collaborators_list)
        if "_id" in df_collaborators_for_faiss.columns:
            df_collaborators_for_faiss["_id"] = df_collaborators_for_faiss[
                "_id"
            ].astype(str)
    except Exception as e:
        logger.exception(f"Error during MongoDB operations: {e}")
        if mongo_client:
            mongo_client.close()  # Cerrar en caso de error también
        return
    finally:
        # El cliente se cierra aquí solo si la carga fue parcial o falló antes del bloque principal de FAISS.
        # Si la carga es exitosa, se mantiene abierto para DataProcessor si fuera necesario (aunque no lo es actualmente).
        # Es mejor cerrar explícitamente cuando ya no se necesita.
        if mongo_client:
            logger.debug(
                "MongoDB client connection was established; will be closed if not used further or at script end."
            )
            # No lo cerramos aquí para que esté disponible si DataProcessor lo necesitara.
            # Se cerrará al final de main() o si hay un error en la siguiente sección.

    if df_collaborators_for_faiss is None or df_collaborators_for_faiss.empty:
        logger.error("No data loaded from MongoDB for FAISS. Saliendo.")
        if mongo_client and mongo_client.admin.command("ping"):
            mongo_client.close()  # Asegurar cierre si no se usó
        return

    # 2. Inicializar Recommender (para preprocesar datos para FAISS)
    logger.info(
        "Initializing SoftwareTeamRecommender to preprocess data for FAISS index..."
    )
    try:
        recommender_instance = SoftwareTeamRecommender(
            df_collaborators_for_faiss.copy()
        )
        if (
            recommender_instance.df_employees is None
            or recommender_instance.df_employees.empty
        ):
            logger.error(
                "DataFrame vacío post-preproc. No se pueden generar embeddings."
            )
            if mongo_client and mongo_client.admin.command("ping"):
                mongo_client.close()
            return
        logger.info("SoftwareTeamRecommender initialized, data preprocessed.")
    except Exception as e:
        logger.exception(f"Failed to init/preprocess with Recommender: {e}")
        if mongo_client and mongo_client.admin.command("ping"):
            mongo_client.close()
        return

    # 3. Crear y guardar embeddings FAISS
    logger.info("--- FAISS Embeddings Generation ---")
    try:
        logger.info("Initializing DataProcessor for FAISS embeddings...")
        data_processor_instance = DataProcessor(
            recommender_instance.df_employees.copy(),  # Pasar el DF PREPROCESADO
            recommender_instance=recommender_instance,  # Pasar la instancia del motor
        )
        logger.info("DataProcessor initialized.")
        text_descriptions = data_processor_instance.generate_text_descriptions()
        if not text_descriptions:
            logger.error("No text descriptions generated. Cannot create FAISS index.")
            if mongo_client and mongo_client.admin.command("ping"):
                mongo_client.close()
            return

        logger.info(f"Attempting to create FAISS index at: {faiss_index_full_path}")
        faiss_index = data_processor_instance.generate_faiss_index(
            descriptions=text_descriptions, save_path=faiss_index_full_path
        )
        if faiss_index and hasattr(faiss_index, "ntotal") and faiss_index.ntotal > 0:
            logger.info(
                f"FAISS index created/saved at {faiss_index_full_path} with {faiss_index.ntotal} vectors."
            )
        else:
            logger.error("Failed to create/save FAISS index, or index is empty.")
    except Exception as e:
        logger.exception(f"Error during DataProcessing/FAISS generation: {e}")
    finally:  # Asegurar que el cliente de Mongo se cierre después de todas las operaciones
        if mongo_client:  # Verificar si la variable existe y no es None
            try:
                if mongo_client.admin.command(
                    "ping"
                ):  # Verificar si la conexión sigue viva antes de cerrar
                    logger.info(
                        "Closing MongoDB client connection at the end of main function."
                    )
                    mongo_client.close()
            except Exception as e_close:
                logger.warning(
                    f"Could not definitively close MongoDB connection or ping failed: {e_close}"
                )

    logger.info("--- Initialization Script Completed ---")


if __name__ == "__main__":
    main()
