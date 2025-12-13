# Manual Técnico – Sistema Help Desk


## 1. Descripción General
Este documento describe la arquitectura, configuración, tecnologías y funcionamiento técnico del sistema Help Desk desarrollado para el curso.
El sistema permite la gestión de tickets de soporte con control de usuarios y roles.

## 2. Tecnologías Utilizadas
- Lenguaje: Python
- Framework Backend: Flask
- Base de Datos: MariaDB
- Frontend: HTML, Bootstrap 5
- Interactividad: jQuery y AJAX
- Editor: Visual Studio Code
- Sistema Operativo: Windows

## 3. Arquitectura del Sistema
El sistema sigue una arquitectura cliente-servidor:
- El cliente accede mediante un navegador web.
- Flask actúa como servidor web y lógica de negocio.
- MariaDB almacena usuarios, tickets y comentarios.
- Flask se conecta a MariaDB usando PyMySQL.

## 4. Estructura del Proyecto
helpdesk_full_project/
- app.py
- config.py
- db.py
- generate_password_hash.py
- requirements.txt
- .env
- templates/
- static/
- docs/
  - sql/
  - screenshots/
  - manual_tecnico.md

## 5. Entorno Virtual
Se utiliza un entorno virtual para aislar dependencias.

Comandos:
- python -m venv venv
- venv\Scripts\activate
- pip install -r requirements.txt

## 6. Base de Datos
- Motor: MariaDB
- Puerto: 3307
- Base de datos: helpdesk_db

El archivo schema.sql crea:
- users
- tickets
- ticket_comments

## 7. Conexión a la Base de Datos
La conexión se gestiona desde db.py utilizando PyMySQL.
Los datos de conexión se obtienen desde variables de entorno.

## 8. Usuarios y Roles
Roles implementados:
- ADMIN
- AGENT
- USER

Las contraseñas se almacenan cifradas usando hashes.

## 9. Seguridad
- Hash de contraseñas
- Manejo de sesiones
- Control de acceso por rol
- Entorno virtual aislado

## 10. Funcionalidades
- Inicio de sesión
- Creación de tickets
- Comentarios
- Cambio de estado y prioridad
- Gestión de usuarios
- Actualización AJAX

## 11. AJAX
Se utiliza jQuery para realizar actualizaciones sin recargar la página.

## 12. Evidencia de Funcionamiento
Se valida MariaDB usando:
- USE helpdesk_db;
- SHOW TABLES;

Las capturas se almacenan en docs/screenshots/.

## 13. Ejecución
- Activar entorno virtual
- Ejecutar python app.py
- Acceder desde navegador

## 14. Conclusión
El sistema cumple con los requisitos técnicos del curso y demuestra integración completa de backend y base de datos.