from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from config import Config
from db import get_db_connection

load_dotenv()

ALLOWED_ROLES = ["ADMIN", "AGENT", "USER"]
ALLOWED_STATUS = ["OPEN", "IN_PROGRESS", "RESOLVED"]
ALLOWED_PRIORITY = ["LOW", "MEDIUM", "HIGH"]

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first.", "warning")
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper

    def role_required(*roles):
        def deco(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                if "user_role" not in session:
                    flash("Please login first.", "warning")
                    return redirect(url_for("login"))
                if session["user_role"] not in roles:
                    flash("You do not have permission to access that page.", "danger")
                    return redirect(url_for("dashboard"))
                return fn(*args, **kwargs)
            return wrapper
        return deco

    @app.route("/", methods=["GET"])
    def home():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""

            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, name, email, password_hash, role FROM users WHERE email = %s",
                        (email,),
                    )
                    user = cursor.fetchone()
            finally:
                conn.close()

            if (not user) or (not check_password_hash(user["password_hash"], password)):
                flash("Invalid email or password.", "danger")
                return render_template("login.html")

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]
            flash("Welcome, {}!".format(user["name"]), "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard", methods=["GET"])
    @login_required
    def dashboard():
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT status, COUNT(*) AS total FROM tickets GROUP BY status")
                rows = cursor.fetchall()
            stats = {r["status"]: r["total"] for r in rows}
        finally:
            conn.close()

        for k in ALLOWED_STATUS:
            stats.setdefault(k, 0)

        return render_template("dashboard.html", stats=stats)

    @app.route("/tickets", methods=["GET"])
    @login_required
    def tickets_list():
        user_id = session["user_id"]
        role = session["user_role"]

        q = (request.args.get("q") or "").strip()
        status = (request.args.get("status") or "").strip()
        priority = (request.args.get("priority") or "").strip()

        where = []
        params = []

        if role == "USER":
            where.append("t.created_by = %s")
            params.append(user_id)
        elif role == "AGENT":
            where.append("(t.assigned_to = %s OR t.assigned_to IS NULL)")
            params.append(user_id)

        if q:
            where.append("t.title LIKE %s")
            params.append("%{}%".format(q))
        if status and status in ALLOWED_STATUS:
            where.append("t.status = %s")
            params.append(status)
        if priority and priority in ALLOWED_PRIORITY:
            where.append("t.priority = %s")
            params.append(priority)

        sql = """
            SELECT t.*,
                   u.name AS created_by_name,
                   a.name AS assigned_to_name
            FROM tickets t
            JOIN users u ON t.created_by = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY t.created_at DESC"

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                tickets = cursor.fetchall()
        finally:
            conn.close()

        return render_template(
            "tickets_list.html",
            tickets=tickets,
            allowed_status=ALLOWED_STATUS,
            allowed_priority=ALLOWED_PRIORITY,
        )

    @app.route("/tickets/create", methods=["GET", "POST"])
    @login_required
    def ticket_create():
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            description = (request.form.get("description") or "").strip()
            priority = (request.form.get("priority") or "MEDIUM").strip()

            if not title or not description:
                flash("Title and description are required.", "danger")
                return render_template("ticket_create.html", allowed_priority=ALLOWED_PRIORITY)

            if priority not in ALLOWED_PRIORITY:
                priority = "MEDIUM"

            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tickets (title, description, priority, status, created_by, assigned_to)
                        VALUES (%s, %s, %s, 'OPEN', %s, NULL)
                        """,
                        (title, description, priority, session["user_id"]),
                    )
                conn.commit()
            finally:
                conn.close()

            flash("Ticket created.", "success")
            return redirect(url_for("tickets_list"))

        return render_template("ticket_create.html", allowed_priority=ALLOWED_PRIORITY)

    def _load_ticket(cursor, ticket_id):
        cursor.execute(
            """
            SELECT t.*,
                   u.name AS created_by_name,
                   a.name AS assigned_to_name
            FROM tickets t
            JOIN users u ON t.created_by = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
            WHERE t.id = %s
            """,
            (ticket_id,),
        )
        return cursor.fetchone()

    @app.route("/tickets/<int:ticket_id>", methods=["GET"])
    @login_required
    def ticket_detail(ticket_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                ticket = _load_ticket(cursor, ticket_id)
                if not ticket:
                    flash("Ticket not found.", "danger")
                    return redirect(url_for("tickets_list"))

                role = session["user_role"]
                user_id = session["user_id"]
                if role == "USER" and ticket["created_by"] != user_id:
                    flash("No tienes permiso para ver ese ticket.", "danger")
                    return redirect(url_for("tickets_list"))
                if role == "AGENT" and ticket["assigned_to"] not in (None, user_id):
                    flash("No tienes permiso para ver ese ticket.", "danger")
                    return redirect(url_for("tickets_list"))

                cursor.execute(
                    """
                    SELECT c.*, u.name AS user_name
                    FROM ticket_comments c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.ticket_id = %s
                    ORDER BY c.created_at ASC
                    """,
                    (ticket_id,),
                )
                comments = cursor.fetchall()

                agents = []
                if role == "ADMIN":
                    cursor.execute("SELECT id, name, email FROM users WHERE role='AGENT' ORDER BY name")
                    agents = cursor.fetchall()
        finally:
            conn.close()

        return render_template(
            "ticket_detail.html",
            ticket=ticket,
            comments=comments,
            agents=agents,
            allowed_status=ALLOWED_STATUS,
            allowed_priority=ALLOWED_PRIORITY,
        )

    @app.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
    @login_required
    def ticket_add_comment(ticket_id):
        comment = (request.form.get("comment") or "").strip()
        if not comment:
            flash("Comment cannot be empty.", "danger")
            return redirect(url_for("ticket_detail", ticket_id=ticket_id))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                ticket = _load_ticket(cursor, ticket_id)
                if not ticket:
                    flash("Ticket not found.", "danger")
                    return redirect(url_for("tickets_list"))

                role = session["user_role"]
                user_id = session["user_id"]
                if role == "USER" and ticket["created_by"] != user_id:
                    flash("No tienes permiso para comentar aquí.", "danger")
                    return redirect(url_for("tickets_list"))
                if role == "AGENT" and ticket["assigned_to"] not in (None, user_id):
                    flash("No tienes permiso para comentar aquí.", "danger")
                    return redirect(url_for("tickets_list"))

                cursor.execute(
                    "INSERT INTO ticket_comments (ticket_id, user_id, comment) VALUES (%s, %s, %s)",
                    (ticket_id, user_id, comment),
                )
            conn.commit()
        finally:
            conn.close()

        flash("Comment added.", "success")
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    @app.route("/tickets/<int:ticket_id>/update", methods=["POST"])
    @login_required
    def ticket_update(ticket_id):
        role = session["user_role"]
        if role not in ["ADMIN", "AGENT"]:
            flash("You are not allowed to update tickets.", "danger")
            return redirect(url_for("ticket_detail", ticket_id=ticket_id))

        status = (request.form.get("status") or "").strip()
        priority = (request.form.get("priority") or "").strip()
        assigned_to = request.form.get("assigned_to") or None

        if status not in ALLOWED_STATUS:
            flash("Invalid status.", "danger")
            return redirect(url_for("ticket_detail", ticket_id=ticket_id))
        if priority not in ALLOWED_PRIORITY:
            flash("Invalid priority.", "danger")
            return redirect(url_for("ticket_detail", ticket_id=ticket_id))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                ticket = _load_ticket(cursor, ticket_id)
                if not ticket:
                    flash("Ticket not found.", "danger")
                    return redirect(url_for("tickets_list"))

                if role == "AGENT" and ticket["assigned_to"] not in (None, session["user_id"]):
                    flash("You are not allowed to update this ticket.", "danger")
                    return redirect(url_for("tickets_list"))

                if role != "ADMIN":
                    assigned_to = ticket["assigned_to"]

                cursor.execute(
                    "UPDATE tickets SET status=%s, priority=%s, assigned_to=%s WHERE id=%s",
                    (status, priority, assigned_to, ticket_id),
                )
            conn.commit()
        finally:
            conn.close()

        flash("Ticket updated.", "success")
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    @app.route("/tickets/<int:ticket_id>/ajax_update", methods=["POST"])
    @login_required
    def ticket_ajax_update(ticket_id):
        role = session["user_role"]
        if role not in ["ADMIN", "AGENT"]:
            return jsonify({"ok": False, "message": "Not allowed"}), 403

        data = request.get_json(silent=True) or {}
        status = (data.get("status") or "").strip()
        priority = (data.get("priority") or "").strip()

        if status not in ALLOWED_STATUS or priority not in ALLOWED_PRIORITY:
            return jsonify({"ok": False, "message": "Invalid values"}), 400

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                ticket = _load_ticket(cursor, ticket_id)
                if not ticket:
                    return jsonify({"ok": False, "message": "Ticket not found"}), 404

                if role == "AGENT" and ticket["assigned_to"] not in (None, session["user_id"]):
                    return jsonify({"ok": False, "message": "Not allowed"}), 403

                cursor.execute(
                    "UPDATE tickets SET status=%s, priority=%s WHERE id=%s",
                    (status, priority, ticket_id),
                )
            conn.commit()
        finally:
            conn.close()

        return jsonify({"ok": True, "message": "Updated"})

    @app.route("/users", methods=["GET"])
    @login_required
    @role_required("ADMIN")
    def users_list():
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC")
                users = cursor.fetchall()
        finally:
            conn.close()
        return render_template("users_list.html", users=users)

    @app.route("/users/create", methods=["GET", "POST"])
    @login_required
    @role_required("ADMIN")
    def user_create():
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            role = (request.form.get("role") or "USER").strip()

            if not name or not email or not password:
                flash("Name, email and password are required.", "danger")
                return render_template("user_create.html", allowed_roles=ALLOWED_ROLES)

            if role not in ALLOWED_ROLES:
                role = "USER"

            pw_hash = generate_password_hash(password)

            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                        (name, email, pw_hash, role),
                    )
                conn.commit()
                flash("User created.", "success")
            except Exception:
                flash("Could not create user. Email may already exist.", "danger")
            finally:
                conn.close()

            return redirect(url_for("users_list"))

        return render_template("user_create.html", allowed_roles=ALLOWED_ROLES)

    @app.route("/users/<int:user_id>/role", methods=["POST"])
    @login_required
    @role_required("ADMIN")
    def user_change_role(user_id):
        new_role = (request.form.get("role") or "").strip()
        if new_role not in ALLOWED_ROLES:
            flash("Invalid role.", "danger")
            return redirect(url_for("users_list"))

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET role=%s WHERE id=%s", (new_role, user_id))
            conn.commit()
        finally:
            conn.close()

        flash("Role updated.", "success")
        return redirect(url_for("users_list"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
