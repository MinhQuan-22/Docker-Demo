import os
import time
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

def get_db_config():
    # Load config from env with defaults
    return {
        "host": os.getenv("DB_HOST", "db"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "fullstack_demo"),
        "user": os.getenv("DB_USER", "fullstack_user"),
        "password": os.getenv("DB_PASSWORD", "fullstack_pass"),
    }

def get_connection():
    return psycopg2.connect(**get_db_config())

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "service": "Docker Topic 5 API",
        "db_config": {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT")
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "up"})

@app.route("/db-check", methods=["GET"])
def db_check():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT current_database(), current_user;")
        db_info = cur.fetchone()
        cur.close()
        conn.close()

        return jsonify({
            "connection": "successful",
            "info": {
                "database": db_info[0],
                "user": db_info[1]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tasks", methods=["GET"])
def get_tasks():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, is_done, created_at FROM tasks ORDER BY id;")
        rows = cur.fetchall()
        
        tasks = [{
            "id": r[0],
            "title": r[1],
            "is_done": r[2],
            "created_at": r[3].isoformat()
        } for r in rows]

        cur.close()
        conn.close()
        return jsonify(tasks)
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return jsonify({"msg": "Failed to fetch tasks"}), 500

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json() or {}
    title = data.get("title")

    if not title:
        return jsonify({"error": "Title required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, is_done, created_at;",
            (title,)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": row[0],
            "title": row[1],
            "is_done": row[2],
            "created_at": row[3].isoformat()
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Wait for DB to be ready in dev
    time.sleep(1) 
    app.run(host="0.0.0.0", port=8080)
