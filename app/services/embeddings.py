import faiss
import pandas as pd
from typing import Tuple


def load_faiss_index_and_data(
    embeddings_path: str, df_employees: pd.DataFrame
) -> Tuple[faiss.Index, pd.DataFrame]:
    """
    Carga el índice FAISS desde la ruta proporcionada y simplemente devuelve el DataFrame
    que ya ha sido cargado.
    """
    try:
        print(f"Leyendo índice FAISS desde: {embeddings_path}")
        index = faiss.read_index(embeddings_path)

        # Ya no leemos el CSV/JSON aquí. Simplemente devolvemos el DataFrame que nos pasaron.
        print("DataFrame de empleados recibido, no se vuelve a cargar.")

        return index, df_employees
    except Exception as e:
        raise RuntimeError(f"Error cargando el índice FAISS: {str(e)}")
