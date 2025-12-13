import pymysql
from flask import current_app

def get_db_connection():
    return pymysql.connect(
        host=current_app.config["DB_HOST"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        port=current_app.config.get("DB_PORT", 3307),
        autocommit=False
    )
