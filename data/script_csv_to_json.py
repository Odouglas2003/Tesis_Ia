# script_csv_to_json.py
import pandas as pd
import json

# Asegúrate de que el nombre del archivo CSV y las columnas coincidan EXACTAMENTE
csv_file_path = "users_mindfactory.csv"  # CAMBIA ESTO AL NOMBRE DE TU NUEVO CSV
json_file_path = "employees_for_mongo.json"

# Nombres de columna ESPERADOS en tu CSV (tal como están en el archivo)
# Ajusta estos nombres si son diferentes en tu CSV
expected_csv_columns = {
    "id": "employee_id_csv",  # El 'id' de tu CSV
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "Proyectos": "proyectos_raw",
    "Puesto de Tr.": "puesto_trabajo_raw",  # Ojo con el punto
    "rol": "rol_raw",
    "tecnologías": "tecnologias_raw",
    "seniority": "seniority_raw",
    "Fecha_de_salida": "Fecha_de_salida_raw",
    "Carga_Horaria": "Carga_horaria_raw",
}

try:
    df = pd.read_csv(csv_file_path, delimiter=";")  # o ',' si tu CSV usa comas
    print(f"CSV leído exitosamente. Columnas encontradas: {df.columns.tolist()}")

    # Renombrar columnas a los nombres de campo que quieres en MongoDB
    df_renamed = df.rename(columns=expected_csv_columns)

    # Verificar que todas las columnas esperadas (claves de expected_csv_columns) estén ahora en df_renamed
    # (las que no estaban en el CSV original no se habrán renombrado, pero las que sí, deben tener el nuevo nombre)
    missing_mongo_fields = []
    for original_csv_col, mongo_field_name in expected_csv_columns.items():
        if (
            mongo_field_name not in df_renamed.columns
            and original_csv_col in df.columns
        ):
            # Esto significa que el rename no ocurrió como se esperaba para esta columna
            # o que la columna original no estaba en el CSV
            print(
                f"Advertencia: La columna '{original_csv_col}' (esperada como '{mongo_field_name}') podría no estar procesándose correctamente."
            )
        if (
            mongo_field_name not in df_renamed.columns
            and original_csv_col not in df.columns
        ):
            print(
                f"Advertencia: La columna '{original_csv_col}' (esperada en CSV) no fue encontrada."
            )

    # Convertir 'Carga Horaria' a numérico, si no lo es ya. Coercionar errores a NaN.
    if "carga_horaria_raw" in df_renamed.columns:
        df_renamed["carga_horaria_raw"] = pd.to_numeric(
            df_renamed["carga_horaria_raw"], errors="coerce"
        )
    else:
        print("Advertencia: 'carga_horaria_raw' no encontrada después del renombrado.")

    # Convertir el DataFrame a una lista de diccionarios (JSON array format)
    # Pandas orient='records' es perfecto para esto.
    # Solo incluir las columnas que realmente quieres en MongoDB (las values de expected_csv_columns)
    mongo_field_names_to_include = [
        name for name in expected_csv_columns.values() if name in df_renamed.columns
    ]

    if not mongo_field_names_to_include:
        print(
            "Error: Ninguna columna para incluir en MongoDB. Verifica los nombres de columna y el mapeo."
        )
    else:
        records_list = df_renamed[mongo_field_names_to_include].to_dict(
            orient="records"
        )

        # Limpiar NaNs de los records (MongoDB no los quiere como float('nan'))
        # Los convierte a None (que se almacena como null o el campo se omite)
        cleaned_records_list = []
        for record in records_list:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):  # pd.isna() maneja None, np.nan, etc.
                    cleaned_record[key] = (
                        None  # O puedes decidir omitir la clave: if pd.notna(value): cleaned_record[key] = value
                    )
                else:
                    cleaned_record[key] = value
            cleaned_records_list.append(cleaned_record)

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_records_list, f, ensure_ascii=False, indent=2)

        print(
            f"Archivo JSON '{json_file_path}' creado exitosamente con {len(cleaned_records_list)} documentos."
        )
        print("Ejemplo del primer documento:")
        if cleaned_records_list:
            print(json.dumps(cleaned_records_list[0], indent=2, ensure_ascii=False))

except FileNotFoundError:
    print(f"Error: El archivo CSV '{csv_file_path}' no fue encontrado.")
except Exception as e:
    print(f"Ocurrió un error: {e}")
    import traceback

    traceback.print_exc()
