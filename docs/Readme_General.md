README General Conceptual del Sistema "Planilla Rubik"
Planilla Rubik - Sistema Integral de Gestión y Recomendación


Planilla Rubik** es un sistema diseñado para [**"optimizar la asignación de colaboradores a proyectos y tareas, facilitando la gestión de planillas y la toma de decisiones basada en datos y recomendaciones inteligentes."**].

El sistema se compone de tres módulos principales que trabajan en conjunto:

Frontend (Planilla Rubik UI):** Una interfaz web moderna y responsiva construida con Next.js para la interacción del usuario, visualización de datos y gestión de planillas.
Backend (Planilla Rubik API):** Un servicio API robusto desarrollado en Node.js con Express, encargado de la lógica de negocio principal, gestión de datos (MongoDB) y comunicación en tiempo real.
Motor de IA (Software Team Builder):** Un servicio especializado en Python (FastAPI) que provee funcionalidades avanzadas de recomendación de equipos y análisis de perfiles basado en IA.
🏗️ Arquitectura del Sistema

El sistema sigue una arquitectura de microservicios (o servicios distribuidos) donde el frontend interactúa principalmente con el Backend API, y este último puede, a su vez, consultar al Motor de IA para obtener recomendaciones especializadas.


┌──────────────────────┐      HTTP/API       ┌──────────────────────┐      HTTP/API       ┌────────────────────────┐
│                      │─────────────────────►│                      │─────────────────────►│                        │
│  Frontend (Next.js)  │                      │  Backend API (Node.js) │                      │  Motor de IA (Python)  │
│  (localhost:3000)    │◄─────────────────────┤  (localhost:3900)    │◄─────────────────────┤  (localhost:8000)      │
│                      │      Socket.IO       │                      │                      │                        │
└──────────────────────┘                      └──────────────────────┘                      └────────────────────────┘
         │                                              │                                       ▲
         │                                              ▼                                       │
         │                                    ┌────────────────┐                                │
         └────────────────────────────────────►│   MongoDB      │◄────────────────────────────────┘
                                              └────────────────┘
                                           (Base de Datos Principal)


                             "El frontend es una Single Page Application (SPA) construida con Next.js que consume los servicios del Backend API."
                             "El Backend API actúa como el orquestador principal, manejando la lógica de negocio, la autenticación y la persistencia en MongoDB."
                             "Para funcionalidades de recomendación o análisis avanzado, el Backend API puede delegar en el Motor de IA, que es un servicio especializado en Python."
                             "La comunicación en tiempo real para notificaciones o actualizaciones instantáneas se maneja vía Socket.IO directamente entre el Frontend y el Backend API."

Componentes Detallados:
1. Frontend (planilla-rubik)
tecnologia: Next.js (v15+), React, TypeScript, Tailwind CSS, Material-UI (MUI).

front/
└── planilla-rubik/
    ├── .env.local                  # Variables de entorno locales (ej. URL de la API)
    ├── .eslintignore               # (Inferido,  ESLint)
    ├── .eslintrc.json              # Configuración de ESLint
    ├── .gitignore                  # Archivos y carpetas a ignorar por Git
    ├── .gitlab-ci.yml              # Configuración de CI/CD para GitLab
    ├── .next/                      # Directorio de build y caché de Next.js (generado)
    │   ├── cache/
    │   ├── server/
    │   ├── static/
    │   ├── types/
    │   ├── app-build-manifest.json
    │   ├── build-manifest.json
    │   └── react-loadable-manifest.json
    ├── node_modules/               # Dependencias del proyecto (generado por npm/yarn)
    │   └── ...
    ├── package-lock.json           # Lockfile de NPM 
    ├── package.json                # Metadatos del proyecto, scripts y dependencias
    ├── postcss.config.mjs          # Configuración de PostCSS (usado por Tailwind CSS)
    ├── public/                     # Archivos estáticos públicos
    │   └── ... (contenido no visible en las capturas,  favicon, imágenes, etc.)
    ├── README.md                   # Documentación del proyecto frontend
    ├── src/                        # Directorio principal del código fuente
    │   ├── app/                    # Rutas y UI principal (Next.js App Router)
    │   │   ├── asyncMock.js        # Mock de datos asíncronos (para pruebas/desarrollo)
    │   │   ├── favicon.ico         # Ícono de la aplicación 
    │   │   ├── fonts/              # (Carpeta para fuentes personalizadas)
    │   │   │   └── ...
    │   │   ├── globals.css         # Estilos CSS globales
    │   │   ├── hooks/              # Custom React Hooks
    │   │   │   └── ...
    │   │   ├── layout.tsx          # Layout raíz de la aplicación
    │   │   ├── page.tsx            # Página principal o de inicio (ruta '/')
    │   │   ├── pages/              # Sub-rutas o páginas específicas de la aplicación
    │   │   │   └── ... (ej. dashboard/page.tsx, projects/page.tsx)
    │   │   └── ThemeProviderClient.tsx # Proveedor de tema para el lado del cliente (MUI, etc.)
    │   ├── components/             # Componentes UI reutilizables
    │   │   ├── add_cards/          # Componentes para "añadir tarjetas" (nombre ambiguo)
    │   │   │   └── ...
    │   │   ├── component-dashboard/  # Componentes específicos para el dashboard
    │   │   │   └── ...
    │   │   ├── component-projects/   # Componentes específicos para la sección de proyectos
    │   │   │   └── ...
    │   │   ├── component-tecnology/  # Componentes relacionados con tecnologias
    │   │   │   └── ...
    │   │   ├── component-vacancies/  # Componentes para la gestión de vacantes
    │   │   │   └── ...
    │   │   ├── components-collaborators/ # Componentes para colaboradores/usuarios
    │   │   │   └── ...
    │   │   ├── configuration/      # Componentes para la configuración
    │   │   │   └── ...
    │   │   ├── LoadingAnimation/   # Componente de animación de carga
    │   │   │   └── ...
    │   │   ├── login/              # Componentes para la página de login
    │   │   │   └── ...
    │   │   ├── navbar/             # Componente de la barra de navegación
    │   │   │   └── ...
    │   │   ├── notification/       # Componente para mostrar notificaciones
    │   │   │   └── ...
    │   │   ├── register/           # Componentes para la página de registro
    │   │   │   └── ...
    │   │   ├── resetPassword/      # Componentes para la funcionalidad de reseteo de contraseña
    │   │   │   └── ...
    │   │   ├── SearchCard/         # Componente de tarjeta de búsqueda o para mostrar resultados
    │   │   │   └── ...
    │   │   └── shearch/            #  Componentes relacionados con búsqueda
    │   │       └── ...
    │   ├── services/               # Lógica para interactuar con APIs externas (el backend)
    │   │   └── api.tsx             # Funciones o instancia configurada para llamadas a la API
    │   └── types/                  # Definiciones de tipos TypeScript
    │       └── interface.ts        # Interfaces y tipos personalizados
    ├── tailwind.config.ts          # Configuración de Tailwind CSS
    ├── trace                       # (Archivo 'trace',  log)
    ├── tsconfig.json               # Configuración del compilador TypeScript
    └── yarn.lock                   # Lockfile de Yarn (indica que podrían usar Yarn)

Propósito: Proporcionar la interfaz de usuario para todas las funcionalidades del sistema.

2. Backend API (planilla-rubik-back)

tecnologia: Node.js, Express, MongoDB (con Mongoose), JWT, Socket.IO.

Ubicación: back/planilla-rubik-back

back/
└── planilla-rubik-back/
    ├── .env                        # Variables de entorno (conexión a BD, puerto, secretos JWT, etc.)
    ├── .gitignore                  # Archivos y carpetas a ignorar por Git
    ├── .gitlab-ci.yml              # Configuración de CI/CD para GitLab
    ├── .trace                      # (Archivo 'trace')
    ├── .vscode/                    # Configuración específica del editor VS Code para este proyecto
    │   └── settings.json           # Ejemplo: formateo, linters específicos para el workspace
    ├── controllers/                # Lógica de manejo de las peticiones HTTP (la "C" de MVC)
    │   ├── collaborator.js         # Controlador para la entidad/recurso "colaborador"
    │   ├── configuration.js        # Controlador para configuraciones o entidades relacionadas
    │   ├── infocolaborator.js      # Controlador para información detallada de colaboradores
    │   ├── notification.js         # Controlador para notificaciones
    │   ├── projects.js             # Controlador para proyectos
    │   ├── tecnology.js            # Controlador para tecnologias
    │   ├── user.js                 # Controlador para usuarios (autenticación, perfiles)
    │   └── vacancie.js             # Controlador para vacantes
    ├── database/                   # Módulo para la conexión a la base de datos
    │   └── connection.js           # Lógica para establecer la conexión con MongoDB (usando Mongoose)
    ├── index.js                    # Punto de entrada principal de la aplicación Node.js/Express
    ├── models/                     # Definición de los esquemas de datos para Mongoose (la "M" de MVC)
    │   ├── collaborator.js         # Modelo Mongoose para "colaborador"
    │   ├── configuration.js        # Modelo Mongoose para "configuration"
    │   ├── infocolaborator.js      # Modelo Mongoose para "infocolaborator"
    │   ├── notification.js         # Modelo Mongoose para "notification"
    │   ├── projects.js             # Modelo Mongoose para "projects"
    │   ├── tecnology.js            # Modelo Mongoose para "tecnology"
    │   ├── user.js                 # Modelo Mongoose para "user"
    │   └── vacancie.js             # Modelo Mongoose para "vacancie"
    ├── node_modules/               # Dependencias del proyecto (generado por npm/yarn)
    │   └── ...
    ├── package-lock.json           # Lockfile de NPM (indica que se usa NPM)
    ├── package.json                # Metadatos del proyecto, scripts y dependencias
    ├── README.md                   # Documentación del proyecto backend
    ├── routes/                     # Definición de los endpoints de la API y su asociación con controladores
    │   ├── collaborator.js         # Rutas para el recurso "colaborador"
    │   ├── configuration.js        # Rutas para "configuration"
    │   ├── infocolaborator.js      # Rutas para "infocolaborator"
    │   ├── notification.js         # Rutas para "notification"
    │   ├── projects.js             # Rutas para "projects"
    │   ├── tecnology.js            # Rutas para "tecnology"
    │   ├── user.js                 # Rutas para "user" (ej. /api/user/register, /api/user/login)
    │   └── vacancie.js             # Rutas para "vacancie"
    └── services/                   # Lógica de negocio auxiliar o servicios específicos
        └── jwt.js                  # Funciones para generar y verificar JSON Web Tokens (JWT)
Propósito: Gestionar la lógica de negocio, persistencia de datos, autenticación, y comunicación en tiempo real con el frontend. Puede interactuar con el Motor de IA.

3. Motor de IA (SIMULADOR_1 / software-team-builder)

tecnologia: Python, FastAPI, spaCy (NLP), FAISS, Pandas.
Ubicación: SIMULADOR_1/software-team-builder (o su ruta correspondiente)
Estructura Clave:

Rubik_IA/
└── software-team-builder/
    ├── .env                        # Variables de entorno para configuración
    ├── .gitignore                  # Especifica archivos no rastreados intencionalmente por Git
    ├── app/                        # Código principal de la aplicación backend (FastAPI)
    │   ├── __init__.py             # Hace de 'app' un paquete Python
    │   ├── ai_assistants/          # Módulos relacionados con el asistente de IA
    │   │   ├── __init__.py         # Hace de 'ai_assistants' un subpaquete
    │   │   ├── chat_processor.py   # Lógica para procesar conversaciones/chat
    │   │   └── intent_detection.py # Lógica para detectar la intención del usuario
    │   ├── auth/                   # Módulos de autenticación y autorización
    │   │   ├── __init__.py         # Hace de 'auth' un subpaquete
    │   │   └── router.py           # Endpoints de API para autenticación
    │   ├── dependencies.py         # Funciones de dependencia para FastAPI (ej. obtener usuario actual)
    │   ├── initialize.py           # Scripts o lógica de inicialización de la aplicación
    │   ├── main.py                 # Punto de entrada principal de la aplicación FastAPI
    │   ├── routers/                # Definición de los endpoints/rutas de la API
    │   │   ├── __init__.py         # Hace de 'routers' un subpaquete
    │   │   ├── chat.py             # Endpoints de API para la funcionalidad de chat
    │   │   └── teams.py            # Endpoints de API para la gestión/recomendación de equipos
    │   └── services/               # Lógica de negocio y servicios principales
    │       ├── __init__.py         # Hace de 'services' un subpaquete
    │       ├── data_processing.py  # Funciones para procesar los datos de entrada
    │       ├── embeddings.py       # Lógica para generar o manejar embeddings vectoriales
    │       └── history_manager.py  # Gestión del historial de interacciones o datos
    ├── config.py                   # Archivo de configuración general de la aplicación
    ├── data/                       # Directorio para datasets y archivos de datos
    │   ├── empleados_software.csv
    │   ├── employees_for_mongo.json
    │   ├── history.json
    │   ├── script_csv_to_json.py   # Script para convertir CSV a JSON
    │   └── users_mindfactory.csv
    ├── index.html                  #  página de demo  (simulador input/output postman en html)
    ├── models/                     # Almacenamiento de modelos de IA precalculados o artefactos
    │   └── embeddings.faiss        # Ejemplo: índice FAISS para búsqueda de similitud
    ├── readme_1.txt                # Archivo README adicional o notas
    ├── Readme.md                   # Documentación principal del proyecto
    ├── recommendation_engine.py    # Módulo principal con el algoritmo de recomendación
    ├── requirements_render.txt     # (Asumiendo corrección de 'requeriments') Dependencias para un entorno específico (ej. Render)
    ├── requirements.txt            # Lista de dependencias Python del proyecto
    ├── script.js                   # script  para el index.html 
    ├── start.sh                    # Script para iniciar la aplicación (ej. con Uvicorn para FastAPI)
    ├── tests/                      # Directorio para pruebas (unitarias, de integración)
    │   └── ...                     # Contenido de las pruebas
    └── venv/                       # Entorno virtual de Python (no se versiona)
        └── ...
Propósito: Proporcionar capacidades de recomendación inteligente, procesamiento de lenguaje natural y análisis avanzado de datos para la formación de equipos o asignación de recursos.


## 🚀 tecnologias y Herramientas Clave

Lenguajes: JavaScript (Node.js), TypeScript, Python.

Frontend: Next.js, React, Tailwind CSS, Material-UI.

Backend API: Node.js, Express, Mongoose.

Motor de IA: Python, FastAPI, spaCy, FAISS, Pandas, Scikit-learn.

Base de Datos: MongoDB.

Comunicación en Tiempo Real: Socket.IO.

Autenticación: JWT (JSON Web Tokens).

Gestión de Paquetes: NPM (y/o Yarn en frontend - se recomienda estandarizar), Pip (Python).

Servidor de Desarrollo (Backend Node.js): Nodemon.

Servidor de Desarrollo (Motor IA Python): Uvicorn.

CI/CD: GitLab CI/CD (indicado por archivos .gitlab-ci.yml).

Contenedorización (sugerido por Motor IA): Docker.

🛠️ Instalación y Ejecución (General)
Para correr el sistema completo localmente, cada componente debe ser configurado y ejecutado en su propia terminal:

Base de Datos MongoDB: Asegurar que una instancia de MongoDB esté accesible (local o remota).

Motor de IA (software-team-builder):

Navegar a su directorio.
Configurar su entorno virtual y .env.
Instalar dependencias (pip install -r requirements.txt).
Ejecutar (uvicorn app.main:app --reload o según su README.md).
Puerto por defecto (ej. 8000).

Backend API (planilla-rubik-back):

Navegar a su directorio.
Configurar su archivo .env (con la URI de MongoDB, puerto, secreto JWT, y opcionalmente la URL del Motor de IA si lo consume).
Instalar dependencias (npm install).
Ejecutar (npm start).
Puerto por defecto (ej. 3900).

Frontend (planilla-rubik):

Navegar a su directorio.
Configurar su archivo .env.local (con NEXT_PUBLIC_API_URL apuntando al puerto del Backend API local).
Instalar dependencias (npm install o yarn install).
Ejecutar (npm run dev o yarn dev).
Puerto por defecto (ej. 3000).

(Consulte los README.md específicos de cada proyecto para instrucciones detalladas de instalación y configuración).

📋 Flujo de Trabajo Típico del Usuario

El usuario accede al Frontend (http://localhost:3000).
El Frontend realiza peticiones (HTTP y Socket.IO) al Backend API (http://localhost:3900) para:
Autenticación de usuarios.
Obtención y guardado de datos de planillas, proyectos, colaboradores.
Notificaciones en tiempo real.

Para funcionalidades de recomendación avanzada, el Backend API puede realizar peticiones al Motor de IA (http://localhost:8000).
El Motor de IA procesa la solicitud y devuelve las recomendaciones al Backend API.
El Backend API reenvía la información relevante al Frontend para su visualización.