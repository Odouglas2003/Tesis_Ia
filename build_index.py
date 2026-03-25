# build_index.py

from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings  # Usamos OpenAI para los embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

# Cargar variables de entorno (especialmente OPENAI_API_KEY)
load_dotenv()

# --- CONFIGURACIÓN ---
DOCS_PATH = "docs"
MODELS_PATH = "models"
INDEX_NAME = "embeddings"


def build_index():
    """
    Lee todos los documentos de la carpeta /docs, los procesa y crea
    un índice vectorial FAISS para la búsqueda semántica.
    """
    print("Iniciando la construcción del índice vectorial...")

    if not os.path.exists(DOCS_PATH) or not os.listdir(DOCS_PATH):
        print(f"Error: La carpeta '{DOCS_PATH}' no existe o está vacía.")
        print(
            "Por favor, crea la carpeta 'docs' y añade tus archivos README.md antes de continuar."
        )
        return

    # 1. Cargar documentos desde la carpeta /docs
    loader = DirectoryLoader(
        DOCS_PATH, glob="**/*.md", show_progress=True, use_multithreading=True
    )
    documents = loader.load()
    if not documents:
        print(
            "No se encontraron documentos .md en la carpeta 'docs'. No se creará el índice."
        )
        return
    print(f"Cargados {len(documents)} documentos.")

    # 2. Dividir documentos en trozos más pequeños
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print(f"Documentos divididos en {len(texts)} trozos.")

    # 3. Crear el modelo de embeddings de OpenAI
    print("Creando embeddings con OpenAI (text-embedding-ada-002)...")
    try:
        embeddings = OpenAIEmbeddings()
    except Exception as e:
        print(f"Error al inicializar OpenAIEmbeddings: {e}")
        print(
            "Asegúrate de que tu variable de entorno OPENAI_API_KEY está configurada correctamente en tu archivo .env"
        )
        return

    # 4. Crear y guardar el índice FAISS en la carpeta /models
    print(f"Creando y guardando el índice FAISS en la carpeta '{MODELS_PATH}'...")
    if not os.path.exists(MODELS_PATH):
        os.makedirs(MODELS_PATH)

    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local(folder_path=MODELS_PATH, index_name=INDEX_NAME)

    print("---")
    print(
        f"¡Éxito! El índice ha sido construido y guardado en '{MODELS_PATH}/{INDEX_NAME}.faiss'"
    )
    print("---")


if __name__ == "__main__":
    build_index()
