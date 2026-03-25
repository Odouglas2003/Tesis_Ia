# Planilla Rubik - Backend API

Este proyecto es el componente backend de la aplicación Planilla Rubik, encargado de gestionar la lógica de negocio, la interacción con la base de datos (MongoDB), la autenticación de usuarios y la comunicación con otros servicios, como el Motor de IA.

## 🚀 tecnologias Utilizadas

*   **Node.js:** Entorno de ejecución para JavaScript del lado del servidor.
*   **Express.js:** Framework web para construir la API.
*   **MongoDB:** Base de datos NoSQL orientada a documentos.
*   **Mongoose:** ODM (Object Data Modeling) para interactuar con MongoDB.
*   **JWT (JSON Web Tokens):** Para la autenticación de usuarios.
    *   Implementado con `jwt-simple`.
*   **bcrypt:** Para el hashing de contraseñas.
*   **Nodemailer:** Para el envío de correos electrónicos (ej. autorización de registro, reseteo de contraseña).
*   **Winston:** Para un sistema de logging robusto y configurable.
*   **Socket.IO:**  Para comunicación en tiempo real.
*   **dotenv:** Para la gestión de variables de entorno.
*   **cors:** Para habilitar Cross-Origin Resource Sharing.
*   **express-async-errors:** Para un manejo de errores simplificado en rutas asíncronas.
*   **Nodemon:** Para el reinicio automático del servidor durante el desarrollo.

## 📋 Prerrequisitos

*   Node.js (se recomienda v18.x o superior, como se vio en logs v18.19.1)
*   npm (Node Package Manager, viene con Node.js)
*   Una instancia de MongoDB accesible (local o remota).
*   (Opcional) Git para el control de versiones.

## ⚙️ Configuración del Entorno

1.  **Clonar el Repositorio (si aún no lo has hecho):**
    ```bash
    git clone https://gitlab.mindfactory.ar/sol.checa/planilla-rubik-back.git
    cd planilla-rubik-back
    ```

2.  **Instalar Dependencias:**
    ```bash
    npm install
    ```

3.  **Crear el archivo `.env`:**
    En la raíz del proyecto, crea un archivo llamado `.env` y configura las siguientes variables según tu entorno. Adapta los valores de ejemplo:

    ```env
    # Configuración del Servidor
    PORT=3900

    # Configuración de MongoDB 
    MONGO_HOST=mongodb://user:rubik@tu_ip_o_host_mongodb:27017/Rubik # Reemplaza user:rubik y la IP/host
    # O si prefieres construirla con partes :
    # MONGO_USER=tu_usuario_mongo
    # MONGO_PASSWORD=tu_password_mongo
    # MONGO_DB=Rubik
    # MONGO_HOSTNAME=tu_ip_o_host_mongodb
    # MONGO_PORT=27017

    # Configuración de JWT
    JWT_SECRET=TU_SECRETO_JWT_SUPER_SEGURO_Y_LARGO # Cambia esto por una cadena aleatoria y segura

    # Configuración de Email (Nodemailer con Gmail)
    EMAIL_USER=tu_email_gmail_para_enviar@gmail.com
    EMAIL_PASSWORD=tu_contraseña_de_aplicacion_gmail # Si usas Gmail con 2FA, necesitas una contraseña de aplicación
    ADMIN_EMAIL=email_del_admin_para_recibir_solicitudes@example.com # Email para notificaciones de registro

    # URLs de Frontend y Backend (usadas en emails, etc.)
    FRONTEND_URL=http://localhost:3000 # URL de tu frontend en desarrollo
    BACKEND_URL=http://localhost:3900  # URL de este backend en desarrollo

    # Entorno de Node (development o production)
    NODE_ENV=development
    ```
    **Importante para `EMAIL_PASSWORD`:** Si usas Gmail y tienes la autenticación de dos factores (2FA) activada, necesitarás generar una "Contraseña de aplicación" específica para Nodemailer desde la configuración de seguridad de tu cuenta de Google.

4.  **Crear la carpeta de Logs:**
    En la raíz del proyecto, crea una carpeta llamada `logs`:
    ```bash
    mkdir logs
    ```
    Winston guardará aquí los archivos `combined.log`, `error.log`, y `http.log`.

## ▶️ Ejecutar la Aplicación

*   **Para Desarrollo (con Nodemon para recarga automática):**
    ```bash
    npm run dev
    ```
    El servidor debería iniciarse (por defecto en el puerto 3900) y conectarse a MongoDB. Verás logs en la consola y en la carpeta `logs/`.

*   **Para Producción:**
    ```bash
    npm start
    ```
    Este comando ejecutará `NODE_ENV=production node index.js`, optimizando la aplicación para producción y ajustando los niveles de logging. (Asegúrarse de que las variables de entorno en producción estén configuradas adecuadamente en el servidor).

## 📁 Estructura del Proyecto


planilla-rubik-back/
├── config/
│ └── logger.js # Configuración del logger Winston
├── controllers/ # Lógica para manejar requests y responses HTTP
│ ├── collaborator.js
│ ├── configuration.js
│ ├── extraFieldController.js
│ ├── infocolaborator.js
│ ├── notification.js
│ ├── personnelController.js
│ ├── projects.js
│ ├── tecnology.js
│ ├── user.js
│ └── vacancie.js
├── database/
│ └── connection.js # Lógica para la conexión a MongoDB
├── logs/ # Archivos de log generados por Winston (debe crearse)
├── middlewares/ # Middlewares personalizados (ej. auth, multerConfig)
│ └── multerConfig.js # (Si se usa para subida de archivos al backend)
├── models/ # Schemas y modelos de Mongoose
│ ├── BasicFieldDef.js
│ ├── collaborator.js
│ ├── configuration.js
│ ├── ExtraFieldDef.js
│ ├── infocolaborator.js
│ ├── notification.js
│ ├── Personnel.js
│ ├── projects.js
│ ├── tecnology.js
│ ├── user.js
│ └── vacancie.js
├── routes/ # Definición de los endpoints de la API
│ ├── basicFieldRoutes.js
│ ├── collaborator.js
│ ├── configuration.js
│ ├── extraFieldRoutes.js
│ ├── infocolaborator.js
│ ├── notification.js
│ ├── personnelRoutes.js
│ ├── projects.js
│ ├── tecnology.js
│ ├── user.js
│ └── vacancie.js
├── services/ # Lógica de negocio y interacción con la base de datos
│ ├── CollaboratorService.js
│ ├── ConfigurationService.js
│ ├── ExtraFieldService.js
│ ├── InfoCollaboratorService.js
│ ├── jwt.js # Servicio para JWT
│ ├── NotificationService.js
│ ├── PersonnelService.js
│ ├── ProjectService.js
│ ├── TecnologyService.js
│ ├── UserService.js
│ └── VacancieService.js
├── .env # Variables de entorno (NO comitear a Git)
├── .gitignore # Archivos ignorados por Git
├── .gitlab-ci.yml # Configuración de CI/CD para GitLab
├── index.js # Punto de entrada principal de la aplicación
├── package-lock.json
├── package.json
└── README.md # Este archivo




##  API Endpoints (Resumen para Frontend y Pruebas con Postman)

La URL base para todos los endpoints es `http://localhost:3900/api` 

---
### Módulo: User (`/api/user`)

*   **`GET /prueba`**: Para obtener una lista de todos los usuarios (uso de prueba/admin).
*   **`POST /register`**: Para registrar un nuevo usuario (enviar `name`, `email`, `password`, `rol` en el body).
*   **`POST /login`**: Para autenticar un usuario (enviar `email`, `password` en el body).
*   **`GET /authorize/:token/:action`**: Para procesar activación/rechazo de cuenta (usado por enlace de email).
*   **`PUT /update/:email`**: Para actualizar un usuario (reemplazar `:email`, enviar campos a modificar en body).
*   **`POST /delete/:email`**: Para marcar un usuario como eliminado (reemplazar `:email`). (Considerar cambiar a método `DELETE`).
*   **`POST /auth/editpws`**: Para solicitar reseteo de contraseña (enviar `email` en el body).
*   **`POST /auth/resetpassword`**: Para establecer nueva contraseña (enviar `email`, `newPassword`, `confirmPassword` en el body).
*   **`POST /profile/:userEmail/image`**: Para subir una imagen de perfil (reemplazar `:userEmail`, enviar imagen como form-data con campo `profileImageField`). *Nota: Actualmente, el backend guarda el archivo y devuelve la ruta. No lo asocia al UserSchema directamente.*

---
### Módulo: Collaborator (`/api/collaborator`)


*   **`GET /colaborador`**: Para obtener la lista de todos los colaboradores activos (opcional `?search=termino`).
*   **`POST /register`**: Para crear un nuevo colaborador (enviar datos del colaborador en el body).
*   **`GET /getone/:id`**: Para obtener los detalles de un colaborador específico (reemplazar `:id` con ID numérico).
*   **`PUT /editar/:id`**: Para actualizar un colaborador (reemplazar `:id`, enviar campos a modificar en body).
*   **`POST /eliminar/:id`**: Para marcar un colaborador como eliminado (reemplazar `:id`).
*   **`GET /check-contracts`**: Para obtener colaboradores con contratos por vencer/vencidos.

---
### Módulo: Projects (`/api/projects`)


*   **Si usas rutas originales:**
    *   **`GET /proyecto`**: Para obtener la lista de proyectos (con `?search=`).
    *   **`POST /register`**: Para crear un nuevo proyecto (enviar datos en el body).
    *   **`GET /buscar/:taxonId`**: Para obtener un proyecto por `taxonId`.
    *   **`PUT /editar/:taxonId`**: Para actualizar un proyecto (enviar datos a modificar en el body).
    *   **`POST /eliminar/:taxonId`**: Para marcar un proyecto como eliminado.
*   **Si usas rutas RESTful (ej. `GET /`, `POST /`, `GET /:taxonId`, etc.):** Adapta según corresponda.

---
### Módulo: Technology (`/api/technology`)


*   **`GET /tecnology`**: Para obtener la lista de todas las tecnologias.
*   **`POST /register`**: Para crear una nueva tecnologia (enviar `tecnologias` (nombre) en el body).
*   **`GET /tecnology/:id`**: Para obtener una tecnologia por su ID numérico (reemplazar `:id`).
*   **`PUT /tecnology/:id`**: Para actualizar una tecnologia (reemplazar `:id`, enviar `tecnologias` (nuevo nombre) en body).
*   **`DELETE /tecnology/:id`**: Para borrar una tecnologia (reemplazar `:id`).

---
### Módulo: Vacancie (`/api/vacancie`)

*   **`GET /`**: Para obtener la lista de todas las vacantes activas (opcional `?search=termino`).
*   **`POST /`**: Para crear una nueva vacante (enviar datos de la vacante en el body).
*   **`GET /:id`**: Para obtener una vacante por su `id` numérico (reemplazar `:id`).
*   **`PUT /:id`**: Para actualizar una vacante (reemplazar `:id`, enviar campos a modificar en body).
*   **`DELETE /:id`**: Para marcar una vacante como eliminada (reemplazar `:id`).

---
### Módulo: Configuration (`/api/configuration`)

*   **`GET /columns/:section`**: Para obtener la configuración de columnas para una `section` (ej. `/api/configuration/columns/projects`).
*   **`PUT /updateColumns`**: Para actualizar/crear la configuración de columnas (enviar `tableType` (sección) y `columns` (array de objetos) en el body).

---
### Módulo: Notification (`/api/notification`)

*   **`POST /checkContracts`**: Para activar la revisión de vencimientos de contratos de colaboradores.
*   **`POST /checkProjects`**: Para activar la revisión de vencimientos de proyectos.
*   **`GET /user/:email`**: Para obtener las notificaciones no leídas del usuario especificado por `:email`.
*   **`PUT /read/single`**: Para marcar una notificación específica como leída (enviar `email`, `notificationId` en el body).
*   **`PUT /read/all`**: Para marcar todas las notificaciones de un usuario como leídas (enviar `email` en el body).
*   **`GET /all`**: Para obtener todas las notificaciones (admin).
*   **`GET /manager`**: Para obtener notificaciones por email de manager (`?email=manager@example.com`).
*   **`GET /status`**: Para obtener por email y estado de lectura (`?email=user@example.com&read=true`).

---
### Módulo: InfoCollaborator (`/api/infocollaborator`)


*   **`GET /infocola`**: Para obtener la lista de toda la información de colaboradores activos.
*   **`POST /register`**: Para registrar nueva info de colaborador (enviar datos en el body).
*   **`GET /getone/:id`**: Para obtener info de un colaborador por su `id` numérico (reemplazar `:id`).
*   **`PUT /editar/:id`**: Para actualizar info de un colaborador (reemplazar `:id`, enviar datos a modificar en body).
*   **`POST /eliminar/:id`**: Para marcar info de un colaborador como eliminada (reemplazar `:id`).
*   **`GET /check-contracts`**: Para obtener info de colaboradores con contratos por vencer/vencidos.

---
### Módulo: Basic Fields (`/api/basic-fields`)

*   **`GET /`**: Para obtener la lista de todos los campos básicos.
*   **`POST /`**: Para crear un nuevo campo básico (enviar `key`, `label`, `type` en el body).
*   **`GET /:key`**: Para obtener detalles de un campo básico por su `key`.
*   **`PUT /:key`**: Para actualizar un campo básico por su `key` (enviar campos a modificar en el body).
*   **`DELETE /:key`**: Para borrar un campo básico por su `key`.

---
### Módulo: Extra Fields (`/api/extra-fields`)

*   **`GET /`**: Para obtener la lista de todas las definiciones de campos extras.
*   **`POST /`**: Para crear una nueva definición de campo extra (enviar `key`, `label`, `type`, `options` (si aplica) en el body).
*   **`GET /:id`**: Para obtener detalles de una definición de campo extra por su `_id` de MongoDB.
*   **`PUT /:id`**: Para actualizar una definición de campo extra por su `_id` (enviar campos a modificar en el body).
*   **`DELETE /:id`**: Para borrar una definición de campo extra por su `_id` (puede fallar si está en uso).

---
### Módulo: Personnel (`/api/personnel` o `/api/person`)

*   **`GET /`**: Para obtener la lista de todo el personal.
*   **`POST /`**: Para crear un nuevo registro de personal (enviar datos en el body).
*   **`GET /:id`**: Para obtener detalles de un registro de personal por su `_id` de MongoDB.
*   **`PUT /:id`**: Para actualizar un registro de personal por su `_id` (enviar campos a modificar en el body).
*   **`DELETE /:id`**: Para borrar un registro de personal por su `_id`.

---

## 📝 Logging

La aplicación utiliza **Winston** para el logging. Los logs se configuran para diferentes niveles y transportes:
*   **Consola:** Muestra logs en tiempo real (nivel `debug` en desarrollo, `warn` en producción).
*   **Archivos (en la carpeta `logs/`):**
    *   `http.log`: Registra todas las peticiones HTTP.
    *   `combined.log`: Registra todos los eventos de nivel `info` y superiores.
    *   `error.log`: Registra todos los eventos de nivel `error` y superiores (errores críticos del servidor).

##  errorHandler Middleware

Se utiliza `express-async-errors` para capturar errores en rutas asíncronas y un middleware de error global en `index.js` para:
1.  Loguear el error usando Winston.
2.  Enviar una respuesta JSON estandarizada al cliente.
    *   Errores 4xx (del cliente, operacionales) pueden mostrar el mensaje de error específico.
    *   Errores 5xx (del servidor, no operacionales) mostrarán un mensaje genérico en producción.

## 🧪 Pruebas con Postman

Para cada endpoint listado arriba, puedes usar Postman (o una herramienta similar) para enviar las peticiones.
*   **Método HTTP:** El indicado (GET, POST, PUT, DELETE).
*   **URL:** Construye la URL completa (ej. `http://localhost:3900/api/user/login`).
*   **Headers:** Para `POST` y `PUT` con body JSON, incluye `Content-Type: application/json`. Si tus rutas están protegidas, incluye `Authorization: Bearer TU_TOKEN_JWT`.
*   **Body:** Para `POST` y `PUT`, construye el JSON con los datos requeridos según la descripción del endpoint.

Revisar las respuestas HTTP (status code, body) y los logs del servidor para verificar el comportamiento.

## 💡 Próximos Pasos y Mejoras (Sugerencias)

*   **Autenticación y Autorización:** Implementar middlewares para proteger rutas que lo requieran.
*   **Validación de Entrada Avanzada:** Usar librerías como `express-validator` o `Joi` para validaciones más robustas en los controladores o a nivel de ruta.
*   **Documentación de API:** Generar documentación con Swagger/OpenAPI.
*   **Tests Automatizados:** Escribir tests unitarios para los servicios y tests de integración para los endpoints.
*   **Optimización de Base de Datos:** Revisar consultas y asegurar índices adecuados a medida que la aplicación crece.

## 🤝 Contribuciones

