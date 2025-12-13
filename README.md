# HelpDesk (Flask + MariaDB + Bootstrap + jQuery)

Proyecto de Help Desk con roles (ADMIN/AGENT/USER), tickets y comentarios.

## Requisitos
- Python (recomendado 3.8+)
- MariaDB (en tu caso puerto 3307)

## Setup rápido
1) Crea DB y tablas:
- Dentro de MariaDB: `SOURCE docs/sql/schema.sql;`

2) Crea `.env` basado en `.env.example`

3) Instala dependencias:
- `pip install -r requirements.txt`

4) Crea un ADMIN:
- `python generate_password_hash.py`
- Inserta el admin en MariaDB (ver comentario al final de `docs/sql/schema.sql`)

5) Ejecuta:
- `python app.py`
