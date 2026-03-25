# Software Team Builder - Documentación

![Software Team Builder](https://i.imgur.com/JKvQ8aE.png)

## 📌 Descripción

**Software Team Builder** es una aplicación inteligente para construir equipos técnicos óptimos basados en habilidades, experiencia y compatibilidad con los requerimientos del proyecto. Utiliza técnicas de IA y recomendación personalizada según criterios técnicos y presupuesto.

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes

```plaintext

┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│   FastAPI App   │ ◄── │  Team Recommender   │ ◄── │  SentenceBERT    │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
        ▲                       ▲                         ▲
        │                       │                         │
        ▼                       ▼                         ▼
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  REST Endpoints  │     │  Recommendation     │     │   FAISS Index    │
│                 │     │  Engine             │     │                  │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
```json

### Decisiones Técnicas

- **FastAPI**: Elegido por su rendimiento, soporte nativo para async/await y generación automática de docs OpenAPI.
- **Sentence-BERT**: Para embeddings semánticos que permiten entender descripciones textuales de proyectos y perfiles.
- **FAISS**: Optimizado para búsqueda de similitud en espacios vectoriales de alta dimensión.
- **Pandas**: Manipulación eficiente de los datos de empleados.
- **React + Vite**: Frontend moderno con buen rendimiento y experiencia de desarrollo.

## 🚀 Instalación

### Requisitos Previos

- Python 3.9+
- Node.js 16+
- pip 20+
- Git

### Backend

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/software-team-builder.git
cd software-team-builder

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Descargar/colocar los datos
cp empleados_software.csv data/empleados_software.csv

# Crear embeddings
python app/initialize.py

# Ejecutar el servidor
uvicorn app.main:app --reload
```plaintext

### Frontend

```bash
cd frontend
npm install
npm run dev
```plaintext

## 📊 Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/teams/generate` | POST | Genera un nuevo equipo técnico |
| `/api/teams/history` | GET | Obtiene historial de equipos generados |
| `/api/teams/last-team` | GET | Obtiene el último equipo generado |
| `/api/chat` | POST | Endpoint para el chatbot de recomendaciones |

### Ejemplo de Request

```json
POST /api/teams/generate
Headers: {"Content-Type": "application/json"}
Body:
{
    "project_description": "Desarrollo de aplicación web con React y Node.js",
    "team_structure": {
        "backend": 2,
        "frontend": 2,
        "devops": 1
    },
    "budget": 50000,
    "criteria": {
        "backend": {
            "Node.js_exp": 0.7,
            "ingles_avanzado": 1
        },
        "frontend": {
            "React_exp": 0.8
        }
    }
}
```bash

## 🧪 Pruebas

Ejecutar todas las pruebas:

```bash
pytest --cov=app tests/
```bash

Cobertura actual:

- Recommendation Engine: 95%
- API Endpoints: 90%

## 🧩 Estructura del Proyecto


software-team-builder/
├── app/                  # Código backend
│   ├── ai_assistant/
                    |__ __init__.py
                    |__ chat_processor.py
                    |__ intent_detection.py     
    |__ auth/
            |__ init__.py
            |__ router.py
│   ├── routers/          # Endpoints de la API
             |__init__.py
             |__ chat.py
             |__ teams.py
│   ├── services/        # Servicios principales
             |__init__.py
             |__ data_processing.py
             |__ embeddings.py
             |__ history_manager.py
    |__ init__.py
│   ├── main.py           # Punto de entrada
│   └── initialize.py
    |__ Dockerfile    
    |__ recomendation_engine.py           # Otros módulos
├── data/                 # Datos de empleados
     |__empleados_software.csv
├── frontend/             # Aplicación React
│   ├── public/           # Assets públicos
│   └── src/              # Código fuente
      |__App.css
      |__App.jsx
      |__Dockerfile
      |__ Index.css
      |__ index.html
      |__ main.jsx
      |__ nginx.config
      |__ package-lock.json
      |__ package.json
      |__vite.config
├── models/               # Modelos de IA
    |__embeddings.faiss
    |__employess.faiss
├── tests/                # Pruebas unitarias
|__ venv
|__ .env
|__ .gitignore
|__ config.py
|__ docker-compose.yml
|__ dockerignore
|__ Readme.md
|__ requirements.txt                  # Archivos de configuración
```

## 🛠️ Extensibilidad

El sistema está diseñado para:

- Añadir nuevos roles técnicos: Modificar `_calculate_role_score()` en `recommendation_engine.py`
- Integrar nueva lógica de selección: Añadir métodos personalizados
- Cambiar almacenamiento de historial: Implementar nueva clase que herede de `HistoryManager`
- Escalar horizontalmente: Diseño stateless permite múltiples instancias

## 💡 Ejemplo de Uso

1. **Generar equipo**:
   - Describe tu proyecto ("app móvil con backend en Python")
   - Especifica estructura del equipo (2 backend, 1 frontend)
   - Define presupuesto y criterios adicionales

2. **Chatbot**:
   - Haz preguntas sobre tecnologías recomendadas
   - Consulta sobre combinaciones de habilidades
   - Pide análisis de equipos anteriores

## 🌐 Despliegue

### Opción 1: Docker

```bash
docker-compose up --build
```

### Opción 2: AWS EC2

1. Crear instancia EC2 (t3.medium recomendado)
2. Instalar dependencias
3. Configurar Nginx como reverse proxy
4. Ejecutar con Gunicorn:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## 📄 Licencia

MIT License

## 🤝 Contribución

1. Haz fork del proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Haz push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## ✉️ Contacto

Para preguntas o soporte, contacta al mantenedor del proyecto.

---

Api_swagger  

http://localhost:8000/docs   ##  prueba de endpoints 

## Autenticazion 

Claro, aquí tienes un resumen de los pasos y componentes involucrados en la implementación de esta etapa de autenticación básica:

Objetivo: Añadir una pantalla de inicio de sesión (login) para que solo usuarios registrados puedan acceder a la interfaz principal de la aplicación "Software Team Builder".

Base de Datos (MySQL):

Se creó una nueva base de datos (team_builder_auth) y una tabla users.

Esta tabla almacena username y password (actualmente en texto plano, ¡lo cual NO es seguro para producción!).

Se insertó un usuario de ejemplo (admin/password123).

Backend (FastAPI):

Nuevo Endpoint: Se creó un endpoint específico para el login: POST /api/auth/login.

Lógica de Verificación: Este endpoint recibe username y password, se conecta a la base de datos MySQL y compara las credenciales recibidas con las almacenadas.

Nuevo Router: La lógica y el endpoint se encapsularon en un nuevo archivo app/auth/router.py.

Conexión Segura a BD: Se configuró la conexión usando mysql-connector-python y se cargaron las credenciales de forma segura desde un archivo .env.

Integración: Se actualizó app/main.py para incluir el nuevo auth_router y asegurarse de que las peticiones CORS desde el frontend estén permitidas.

Frontend (React):

Nuevo Componente: Se creó un componente reutilizable LoginPage.jsx (con su archivo CSS LoginPage.css) que contiene el formulario de usuario y contraseña.

Estado de Autenticación: El componente principal App.jsx ahora maneja un estado (isAuthenticated, username) para saber si el usuario ha iniciado sesión.

Renderizado Condicional: App.jsx ahora decide qué mostrar:

Si isAuthenticated es false, renderiza el componente LoginPage.

Si isAuthenticated es true, renderiza la interfaz principal del constructor de equipos (el formulario y los resultados que ya tenías).

Llamada a la API: El componente LoginPage realiza la llamada fetch al endpoint /api/auth/login del backend al enviar el formulario.

Manejo de Respuesta: Si el login es exitoso (respuesta 200 OK del backend), se llama a una función (handleLoginSuccess) en App.jsx para actualizar el estado isAuthenticated a true. Si falla, se muestra un mensaje de error.

Logout: Se añadió un botón y una función (handleLogout) en App.jsx para volver a poner isAuthenticated en false y mostrar de nuevo la pantalla de login.

Flujo General:

El usuario accede a la aplicación y ve LoginPage.

Ingresa credenciales y hace clic en "Ingresar".

LoginPage envía los datos a /api/auth/login.

El backend verifica en la BD MySQL.

El backend responde éxito o error.

App.jsx actualiza su estado basado en la respuesta y muestra la interfaz principal o un error en LoginPage.

En esencia, se ha añadido una "barrera" de autenticación simple al inicio de la aplicación, separando la lógica de login en componentes y endpoints dedicados, y utilizando el estado en React para controlar qué interfaz ve el usuario.


*********************************************************************************************************
Logica del proyecto 
******************************************************

Flujo General de Funcionamiento
El sistema funciona en dos fases principales:
Inicialización (__init__): Cuando crea una instancia deRecomendador de SoftwareTeam, se prepara todo lo necesario:
Se cargan y preprocesan los datos de los empleados (limpieza, normalización de roles, etc.).
Se definen las tecnologías conocidas y cómo mapearlas (mapeo tecnológico).
Se normalizan los valores numéricos (experiencia, salario, etc.) para que se puedan comparar de forma justa en el puntaje.
Se guarde una copia de los valores originales (antes de normalizar) para usarlos en la salida (ej. salario real).
Recomendación (equipo recomendado): Cuando llamas a esta función con los requisitos del proyecto:
Itera por cada rol solicitado (backend, frontend, etc.).
Filtra a los candidatos que pertenecen a ese rol.
Aplica un Filtro Estricto (¡Clave!): Si se piden tecnologías específicas para ese rol y el modo de filtro estricto está activado (principaloexp), eliminar a los candidatos que NO cumplan este requisito mínimo (tener la tecnología como principal O tener una experiencia mínima).
Calcular unpuntajepara CADA candidato restante, basado en varios factores (tecnología requerida, experiencia general, capacitación, etc.).
Ordena a los candidatos (ya filtrados) por puntuación (mejor primero) y luego por salario (más bajo primero, como desempate).
Reúna a todos los candidatos preseleccionados de todos los roles en una lista global.
RealízaloSelección Final: Ordena la lista global por puntaje/salario y va eligiendo a los mejores candidatos para cada rol hasta llenar las vacantes solicitadas,siempre y cuando no se exceda el presupuesto total.
Devuelve el equipo final, el presupuesto utilizado y restante.
Componentes Clave y Puntos de Modificación
Aquí te explico cada parte importante y dónde modificarla:
__init__(self, df)(Inicialización)
Propósito:Prepare el objeto recomendador.
Modificaciones típicas:Poco probable que necesites cambiar esto, a menos que la estructura fundamental de tus datos cambie restrictivamente.
_preprocess_data(propio, df)(Preprocesamiento)
Propósito:Limpiar y estandarizar los datos del CSV.
Dónde modificar:
asignación de roles: Si quieres cambiar cómo se agrupan los roles (ej., si 'Arquitecto' debe ser 'backend' en lugar de 'devops'), modifica este diccionario.
Extracción detecnologías_principales: Si tus columnas booleanas de tecnología principal tienen otro formato (no terminan en_principal), ajusta la lógica que buscacolumnas booleanas tecnológicas.
Manejo de Booleanos (columnas booleanas para comprobar): Si tienes otras columnas sí/no relevantes (ej., 'dispuesto_a_viajar'), añádelas aquí para asegurar que se traten como booleanos.
Conversión a numérico: Si tienes otras columnas que deben ser números pero no terminan en_expo_proyectos, añádelas atodas las columnas numéricas.
_inicializar_mapping_tecnológico(self)(Mapeo de Tecnologías)
Propósito:Definir qué nombres de tecnología reconoce el sistema y cómo los estandariza internamente.
Dónde modificar:
Añadir Tecnologías:Si tu CSV tiene columnas_expy_principalpara tecnologías no listadas (ej.,Swift_exp,Swift_principal), añade una entrada como'rápido': ['rápido']. Laclave('rápido') es importante porque se usará para buscarswift_exp.
Añadir variantes:Si una tecnología se escribe de varias formas (ej., 'postgres', 'postgresql', 'pgsql'), añádelas a la lista de variantes:'postgresql': ['postgresql', 'postgres', 'pgsql'].
¡Crucial! Coincidencia Clave <-> Columna_exp: Asegúrate de que laclavedel mapeo (ej.,'nodo') coincide con el prefijo de tu columna de experiencia (el código buscará'exp_nodo') Si tu columna se llamaExp. node.js, la clavedebeser'node.js'(o debes renombrar la columna en el CSV).
_normalize_tech_name(self, tecnología)(Normalización de Nombres Tech)
Propósito:Convierta un nombre de tecnología de la entrada del usuario (o del CSV) a su clave estándar definida en el mapeo.
Modificaciones típicas:Generalmente no se modifica, depende del_inicializar_mapeo_tecnológico.
_get_csv_col_name(self, nombre_de_estándar_tecnológico, sufijo)(Obtener nombre de columna CSV)
Propósito:Dada una clave de tecnología normalizada (ej., 'python') y un sufijo ('_exp' o '_principal'), intenta encontrar el nombre exacto de la columna correspondiente en tu CSV original (ej.,Python_exp,Node.js_principal). Esto es vital para los filtros estrictos y el puntaje.
Dónde modificar:Si la lógica actual para adivinar el nombre original (mayúscula, casos especiales como 'Node.js') no funciona para tus nombres de columna, necesitarás ajustar la lógica aquí o (más fácil) estandarizar tus nombres de columna en el CSV.
_normalizar_valores_numéricos(self)(Normalización Numérica)
Propósito:Escalar valores numéricos (0-1) para que elpuntajemar justo
Dónde modificar:
Columnas a Normalizar:Si desea normalizar columnas numéricas adicionales, asegúrese de que se incluyan encolumnas_a_normalizar.
Manejo deYaya: Actualmente rellena los valores faltantes con 0 (fillna(0)) antes de escalar. Podrías cambiarlo para usar la media (.fillna(df_para_normalizar[col].mean())) o mediana si tiene más sentido para alguna columna.
calcular_puntuación(self, fila, técnicas_requeridas)(Cálculo de puntuación)
Propósito:Asignar una puntuación a cada candidato basada en múltiples factores. ¡Aquí define qué es "mejor"!
Dónde modificar:
Peso de Tecnología Requerida (puntuación técnica): Cambia el multiplicador (* 20.0). Un número más alto hace que la tecnología específica sea mucho más importante.
Peso de Experiencia General (puntuación de exp): Cambia los multiplicadores paraaños_experiencia(* 3.0) yproyectos_completados(* 1.5).
Peso de Capacitación (puntuación de entrenamiento): Cambia los multiplicadores paracertificaciones(* 1.0) yhoras_capacitacion(* 0.5).
Bono (puntuación de bonificación): Cambia los puntos fijos poringlés avanzado(+ 1.5) olíder_equipo(+ 2.5). Puedes añadir bonus por otros factores booleanos.
Ponderación final: Modifica los porcentajes en la combinación final (ej.,puntuación técnica * 0,60,puntuación de exp * 0.25, etc.) para cambiar la importancia relativa global de cada componente. ¡Asegúrate de que sumen aproximadamente 1.0 (o ajusta todos proporcionalmente)!
Añadir nuevos factores: Puedes leer otras columnas defila(ej.,fila.get('ubicacion')) y añadir lógica para incorporarlas al score. Recuerda normalizarlas si son numéricas.
recomendar_equipo(yo mismo, ...)(Lógica Principal de Recomendación)
Propósito:Orquestar todo el proceso de selección.
Dónde modificar:
MODO DE FILTRO ESTRICTO(al inicio del archivo):Cambia entre'principal','exp', o'ninguno'para controlar cuán estricto es el filtro inicial de tecnología. Es la forma más fácil de exigir tecnologías.
UMBRAL DE EXP MÍNIMO(al inicio del archivo):Ajusta el umbral si lo usasMODO DE FILTRO ESTRICTO = 'exp'.
Lógica del Filtro Estricto (dentro deequipo recomendado): Si necesitas una lógica de filtrado más compleja (ej., requerir experiencia entodaslas tecnologías pedidas en lugar deal menos una), modifica la sección delconsulta_str = " o ".join(...)Podrías cambiar' o 'por' y '.
Lógica de Selección Final: La parte final que itera sobrecandidatos_del_equipo_recomendadosy aplica el presupuesto es bastante estándar, pero podrías ajustarla si tienes reglas de negocio complejas (ej., no permitir más de X personas de nivel 'JR').
En resumen:
Para exigir tecnologías:EE.UUMODO_FILTRO_ESTRICTO = 'principal'(y asegúrese de que los nombres entecnologías explícitascoinciden con tus columnas_principal) oMODO DE FILTRO ESTRICTO = 'exp'.
Para cambiar la importancia de factores (tech vs exp general):Ajusta los pesos y multiplicadores encalcular_puntuación.
Para reconocer nuevas tecnologías:Actualiza_inicializar_mapeo_tecnológicoy verifica que las columnas_expy_principalexistan y se nombren correctamente.
Para cambiar cómo se definen los roles:Modificaasignación de rolesen_preprocesar_datos.


No es "IA" en el sentido moderno de Machine Learning (Aprendizaje Automático), pero es una herramientainteligenteBasado en algoritmos y reglas.
Aq
¿Qué hace?
Toma **datosdatos estructurados(tu CSV de
Aplicareglas predefinidas(mapa
Utilizar unalgoritmo de puntuaciónestafapesos definidos manualmente(tú decides cuánto vale la
Realizar **optimoptimización restringida(encuentro
Utiliza técnicas deprocesamiento de datos(comoEscalador mínimo-máximode scikit-learn)aprenderpatrones compl
¿QuéNO¿Hace (que haría una IA basada en Machine Learning)?
Aprender de la experiencia:No mejora sus
Descubrir patrones ocultos:No analiza la dedescripción del proyecto) usaninferirqué habili
Adaptarse dinámicamente:No se ajusta a su estrado
Hacer predicciones complejas:No
Conclusión y cómo describirla:
Puedes describirlo
Una herramienta avanzada de recomendación de equipos.
Un sistema de soporte a la decisión.
Un motor de reglas y optimización para la formación de equipos.
Una aplicación basada en algoritmos que automatiza la selección de personal.
Si quiutiliza técnicas inspiradas en la IAo **elementos deelementos de sistemas expertos, como:
Base de conocimiento:Tu CSV actúa como una base
Motor de inferencia:Yocalcular_puntuaciónactúan
En resumen:Es unasistema experto algorítmicoque una IA de aprendiz


*******************************
empezando como IA 
*****************************
 (PNL Simple para Techs):Es probablemente la más directa y con mayor impacto inicial para hacer la herramienta más "conversacional" o inteligente desde la perspectiva del usuario.

 InstalarspaCyy descargar un modelo de lenguaje:Si no lo has hecho, abre tu terminalen el entorno donde ejecutas tu backend de Pythony corre:
pip install spacy
python -m spacy download es_core_news_sm
Utilice el código con precaución .
Intento
(EE.UUen_core_web_smsi tus descripciones de proyecto estarán en inglés).
Modificarmotor_de_recomendación.py:
ImportarspaCy.
Cargar el modelo de lenguaje en el__init__.
Modificarequipo recomendadopara procesardescripción del proyecto, extraer tecnologías inferidas y combinarlas con lastecnologías explícitas.
ModificarAplicación.jsx(Opcional pero recomendado):Agregue una forma visual para indicar al usuario qué tecnologías se infirieron de la descripción.

tipos de pruebas : 

Escenario 1: Prueba Básica (Sin Foco en PNL)
Objetivo:Verificar
Descripción del proyecto:`Aplicación simpleAplicación sencilla de gestión de tareas.(Algodón co
Estructura del equipo:
Backend:1
Interfaz:1
DevOps0
Control de calidad:0
Presupuesto Máximo: 150000(Un presupuesto razonable).
Tecnologías Clave:
Backend: Marca la casilla `PythoPitón.
Frontend: Marca la casilla `RReaccionar.
DevOps: (No se aplica porque
Qué esperar:
mi
La lista de "Tecnologías Inferidas"
El equipo recomendado
Escenario 2: Prueba de PNL (Descripción Rica)
Objetivo:Verifica que el PNL extrae tecnologías de la descripción y que e
Descripción del proyecto:(Usa el ejemplo detallado o uno similar adaptado a tus da
Necesitamos desarrollar una API RESTful segura usando Python y el framework Flask para gestionar usuarios y productos. Además, requerimos una interfaz de frontend moderna construida con React y TypeScript. El despliegue se realizará en AWS usando contenedores Docker y Kubernetes para la orquestación. Se usará PostgreSQL como base de datos.
Utilice el código con precaución .
Estructura del equipo:
Backend:1
Interfaz:1
Operaciones de desarrollo:1
Control de calidad:0
Presupuesto Máximo: 300000(Más generoso para dar opciones)
Tecnologías Clave:
Deja la mayoría sin marcar, la marca solo unaAWSen DevOps.
Qué esperar:
Interfaz:La secciónpitón,matraz,reaccionar,mecanografiado,aws,estibador,Kubernetes, `publicarPostgreSQL(o los nombres normalizados corresponden
Backend/Resultado:El equipo seleccionado debería reflejar est
Escenario 3: Prueba de Filtro Estricto (MODO_FILTRO_ESTRICTO = 'principal')
Objetivo:Asegurarse de que solo se seleccionan candidatos que te_principal = Verdadero.
Backend:Asegúrate de queMODO DE FILTRO ESTRICTOesté configurado en `'principal'enmotor_de_recomendación.pyy reinicie el servidor backend.
Descripción del proyecto:`Sistema backend conSistema backend con Java.(Simple).
Estructura del equipo:
Backend:2
Interfaz0
Operaciones de desarrollo:0
Control de calidad:0
Presupuesto Máximo: 250000.
Tecnologías Clave:
Backend: Marcaexactamenteel nombre que aparece en tu columna_principal, por ejemplo,Java.Nomarcas otras.
Qué esperar:
Registros de backend:Deberías ver `yoINFORMACIÓN: Aplicando filtro estricto por Tecnología Principal...y una consulta como\Java_pr
Resultado:Solo deberían aparecer candidatos backend pJava_principalen tu CSV seaVerdaderoSi nadie cumple, él
Escenario 4: Prueba de Presupuesto Ajustado
Objetivo:Ver cómo se comporta el
Descripción del proyecto: Prototipo rápido con Node y React.
Estructura del equipo:
Backend:1
Es1
Operaciones de desarrollo:1
Control de calidad:0
Presupuesto Máximo: 90000(U
Tecnologías Clave:
Backend: MarcaNode.js.
FrontenReaccionar.
DevOps: Marca `DoEstibador.
Qué esperar:
Es positivo
Puede que se seleccionepuntuación menor(pero
Elpresupuesto_restanteDebería ser muy bajo o cero. Verificarpresupuesto_utilizadono exceder el
Escenario 5: Conflicto/Combinación (PNL + Explícitas)
Objetivo:Ver cómo se manejan tecnologías inferidas y explícitas juntas.
Descripción del proyecto:`Plataforma de análisis de datosPlataforma de análisis de datos con Python y visualizaciones en Javascript.
Estructura del equipo:
Backend:1
Interfaz:1
Operaciones de desarrollo:0
Control de calidad:0
Presupuesto Máximo: 200000.
Tecnologías Clave:
Backend: MarcaJava(explícitamente diferente a la descripción).
Frontend: MarcaReaccionar(explícitamente
Qué esperar:
La PNL te dirá: pitón,Javascript.
Tecnologías Finales Consideradas:Para el backend:Java(exppitón(inferida). Para Frontendreaccionar(explícita),Javascript(inferior
Resultado:El sistema buscará candidatos que idealmente cumplanembajadores(explícita e inferida) o al menos una de ellas, dependiendo del filtro y la puntuació

*************  logica de IA *************

¡Excelente! Es fundamental entender cómo funciona "debajo del capó" para poder ajustarla a tus necesidades futuras. Aquí tienes una guía explicativa de `recommendation_engine.py`, enfocada en dónde modificar cada aspecto clave:

**1. Flujo General (Recordatorio Rápido)**

*   **`__init__`**: Carga datos, preprocesa, define mapeos, normaliza números, carga modelo NLP.
*   **`recommend_team`**:
    *   Infiere tecnologías de la descripción (NLP).
    *   Combina techs inferidas y explícitas.
    *   **Por cada rol:**
        *   Filtra candidatos por rol.
        *   **Aplica Filtro Estricto (si está activo):** Elimina candidatos que no cumplen requisito mínimo de tecnología (`_principal` o `_exp`).
        *   **Calcula Score:** Puntúa a los candidatos restantes según múltiples factores.
        *   Ordena por score y salario.
        *   Añade a lista global.
    *   **Selección Final:** Elige de la lista global según presupuesto y estructura.
    *   Devuelve resultado.

**2. Guía de Modificaciones: ¿Qué Quieres Cambiar y Dónde?**

---

**A. Si Quieres... Añadir/Modificar TECNOLOGÍAS Reconocidas:**

*   **Objetivo:** Hacer que el sistema reconozca una nueva tecnología (ej. "Swift") o diferentes formas de escribir una existente (ej. "NodeJS").
*   **Dónde Modificar:**
    1.  **`_initialize_tech_mapping(self)`:**
        *   **Añadir Nueva:** Agrega una nueva entrada clave-valor. La *clave* debe ser el nombre estándar que usarás internamente y que (idealmente) coincide con el prefijo de tus columnas `_exp` (ej. `swift_exp`). El valor es una lista de cómo podría escribirse.
            ```python
            'swift': ['swift', 'swiftlang'], # Nueva tecnología
            'node': ['node.js', 'node', 'nodejs', 'NodeJS'], # Añadir variante NodeJS
            ```
        *   **¡Importante!** Después de añadirla, asegúrate de que:
            *   Tu archivo CSV tenga las columnas correspondientes (ej. `swift_exp`, `swift_principal`). Los nombres deben ser consistentes.
            *   Actualices el `_create_reverse_tech_mapping` o la lógica en `_get_csv_col_name` si el nombre de la columna en el CSV no sigue un patrón simple (como `Node.js_principal`).
    2.  **`_create_reverse_tech_mapping(self)` / `_get_csv_col_name(...)` (Posiblemente):** Si el nombre de la columna `_principal` o `_exp` en tu CSV es muy diferente del nombre estándar (ej. no es solo capitalizar), puede que necesites ajustar la lógica que busca el nombre de columna original para que lo encuentre correctamente, especialmente para el filtro por `_principal`.
    3.  **`App.jsx` (Frontend):** Añade la nueva tecnología a la lista `availableTechs` para que aparezca como checkbox seleccionable por el usuario.

---

**B. Si Quieres... Cambiar Cómo se Definen los ROLES:**

*   **Objetivo:** Agrupar perfiles del CSV de manera diferente (ej. 'Arquitecto' ahora es 'Backend').
*   **Dónde Modificar:**
    *   **`_preprocess_data(self)` -> `role_mapping`**: Modifica el diccionario. Cambia a qué lista pertenece un perfil o añade nuevos roles estándar si es necesario.
        ```python
        role_mapping = {
            'backend': ['backend', 'arquitecto'], # Arquitecto ahora es Backend
            'frontend': ['frontend'],
            # ... resto ...
        }
        ```
*   **Consideraciones:** Asegúrate de que los nombres de rol que usas en el frontend (en `App.jsx` para la estructura y las tecnologías) coincidan con las *claves* de `role_mapping` (`backend`, `frontend`, etc.).

---

**C. Si Quieres... Ajustar la IMPORTANCIA de los Factores de Selección (El "Corazón" del Score):**

*   **Objetivo:** Cambiar qué es más importante al elegir un candidato (ej. priorizar más la experiencia general sobre la tecnología específica, o viceversa).
*   **Dónde Modificar:**
    *   **`calculate_score(self, row, required_techs)`:** Aquí es donde se define "qué es bueno".
        *   **Peso Tecnología Específica (`tech_score`)**: Cambia el `* 20.0`. Un valor más alto = la tecnología requerida domina el score. Más bajo = influye menos.
        *   **Peso Experiencia General (`exp_score`)**: Ajusta los `* 3.0` (años) y `* 1.5` (proyectos).
        *   **Peso Capacitación/Certificaciones (`training_score`)**: Ajusta los `* 1.0` (certs) y `* 0.5` (horas).
        *   **Bonus Fijos (`bonus_score`)**: Cambia los `+ 1.5` (inglés) y `+ 2.5` (liderazgo). Puedes añadir más bonus basados en otras columnas booleanas.
        *   **Ponderación Final (Porcentajes)**: Modifica los `* 0.60` (tech), `* 0.25` (exp), `* 0.15` (training) en la línea `total_score = (...)`. Estos controlan la importancia *relativa* de cada bloque. Si cambias uno, considera ajustar los otros para que sigan sumando aproximadamente 1.0 (o para reflejar la nueva importancia relativa).
            *   *Ejemplo:* Para dar MÁS peso a la experiencia general: `total_score = (tech_score * 0.40) + (exp_score * 0.45) + (training_score * 0.15) + bonus_score` (Ahora la experiencia es 45% y la tecnología 40%).

---

**D. Si Quieres... Cambiar la ESTRICTEZ del Requisito de Tecnología:**

*   **Objetivo:** Decidir si un candidato DEBE tener la tecnología pedida (y cómo) o si solo es un "plus".
*   **Dónde Modificar:**
    1.  **(Principal) Variables Globales al inicio del archivo:**
        *   **`STRICT_FILTER_MODE`**: Cámbiala a:
            *   `'principal'`: Exige `Tecnologia_principal == True`. Requiere que uses los nombres exactos de las columnas principales en la petición del frontend.
            *   `'exp'`: Exige `Tecnologia_exp >= MIN_EXP_THRESHOLD`.
            *   `'none'`: Sin filtro estricto, solo usa el bonus del score (comportamiento más flexible).
        *   **`MIN_EXP_THRESHOLD`**: Ajusta el umbral (0 a 1) si usas `STRICT_FILTER_MODE = 'exp'`.
    2.  **(Avanzado) Lógica del Filtro en `recommend_team`**: Si quieres una lógica más compleja (ej. requerir *todas* las tecnologías en lugar de *al menos una*), modifica la línea `query_str = " or ".join(query_conditions)`. Cambiar `" or "` por `" and "` requeriría que se cumplan *todas* las condiciones del filtro.

---

**E. Si Quieres... Modificar Cómo Funciona el NLP (Inferencia de Descripción):**

*   **Objetivo:** Cambiar qué palabras clave se extraen o cómo se usan.
*   **Dónde Modificar:**
    1.  **`_infer_techs_from_description(self, description)`:**
        *   **Extracción:** Cambia los `token.pos_ in ["NOUN", "PROPN"]` para incluir/excluir tipos de palabras (ej., añadir 'ADJ' para adjetivos técnicos). Ajusta el filtrado de `stop words` (`token.is_stop == False`).
        *   **Modelo NLP:** Cambia `NLP_MODEL_NAME` al inicio del archivo si quieres usar otro modelo de spaCy (ej., uno más grande o para otro idioma). Recuerda descargarlo.
    2.  **`recommend_team(...)` (Combinación de Techs):** Modifica la lógica donde se combinan `explicit_techs_normalized` e `inferred_standard_techs` si quieres una estrategia diferente (ej., que las inferidas solo se usen si no hay explícitas, o darles menos prioridad en el filtro/score).

---

**F. Si Quieres... Añadir Nuevos Datos/Factores al Score o Filtro:**

*   **Objetivo:** Considerar una nueva columna del CSV (ej. "ubicacion", "certificacion_especifica").
*   **Dónde Modificar (Requiere cambios en varios lugares):**
    1.  **`_preprocess_data(self)`:** Asegúrate de que la columna se carga y se limpia (ej. convertir a tipo correcto, manejar nulos).
    2.  **`_normalize_numeric_values(self)`:** Si el nuevo factor es numérico y quieres usarlo en el score de forma comparativa, añádelo a la lista de columnas a normalizar.
    3.  **`calculate_score(self, ...)`:** Lee el valor de la nueva columna desde `row.get('nombre_nueva_columna')` y añádelo a la lógica del score (con su propio peso/multiplicador si es numérico, o como un bonus si es booleano).
    4.  **`recommend_team(self, ...)` (Filtro):** Si quieres filtrar por este nuevo factor (ej. `ubicacion == 'Madrid'`), añade la condición al DataFrame `candidates` después de filtrar por rol (antes o después del filtro de tecnología).
    5.  **`recommend_team(self, ...)` (Salida):** Añade el valor de la nueva columna al diccionario que se crea para cada miembro en `recommended_team_candidates` para que se incluya en la respuesta JSON.
    6.  **`App.jsx` (Frontend):** Muestra el nuevo dato en la `member-card`.

---

**G. Si Quieres... Ajustar el Manejo del Presupuesto:**

*   **Objetivo:** Cambiar cómo se selecciona el equipo final respecto al presupuesto.
*   **Dónde Modificar:**
    *   **`recommend_team(self, ...)` (Selección Final):** La lógica actual ordena a *todos* los candidatos preseleccionados por score/salario y luego itera eligiendo a los mejores que quepan hasta llenar roles/presupuesto.
        *   Podrías cambiar el ordenamiento secundario (ej. priorizar más experiencia sobre salario bajo si hay presupuesto de sobra).
        *   Podrías implementar una lógica más compleja si tienes reglas como "no gastar más del X% del presupuesto restante en una sola persona".

---

**H. Variables de Configuración (Fácil Acceso):**

*   **Al inicio del archivo `recommendation_engine.py`:**
    *   `DEBUG_MODE = False / True`: Activa/desactiva logs detallados. ¡Muy útil!
    *   `STRICT_FILTER_MODE = 'principal' / 'exp' / 'none'`: Controla el filtro estricto.
    *   `MIN_EXP_THRESHOLD = 0.1`: Umbral para el modo `'exp'`.
    *   `NLP_MODEL_NAME = "es_core_news_sm"`: Modelo de lenguaje spaCy a usar.

---

# software-team-builder
