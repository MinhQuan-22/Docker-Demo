import os
import time
import json
from datetime import datetime
from collections import deque
from threading import Lock

import psycopg2
from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

# TODO: move this to redis or something more persistent
# keeping activity log in memory for now - good enough for demo
activity_log = deque(maxlen=100)
log_lock = Lock()


def get_db_config():
    """grab database config from env vars"""
    return {
        'host': os.getenv('DB_HOST', 'db'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'dbname': os.getenv('DB_NAME', 'fullstack_demo'),
        'user': os.getenv('DB_USER', 'fullstack_user'),
        'password': os.getenv('DB_PASSWORD', 'fullstack_pass'),
    }


def get_connection():
    return psycopg2.connect(**get_db_config())


def init_db():
    # FIXME: this retry logic is kinda hacky, should use proper connection pooling
    max_retries = 10
    for attempt in range(max_retries):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    is_done BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)


def log_activity(method, path, status_code, request_body=None, response_body=None):
    """Log API activity for monitoring"""
    with log_lock:
        activity = {
            'timestamp': datetime.now().isoformat() + 'Z',
            'method': method,
            'path': path,
            'status': status_code,
            'request': request_body,
            'response': response_body,
        }
        activity_log.append(activity)


@app.after_request
def after_request(response):
    # only log task endpoints to avoid cluttering the monitor
    if request.path.startswith('/tasks'):
        req_body = None
        if request.is_json and request.method in ['POST', 'PATCH', 'PUT']:
            try:
                req_body = request.get_json()
            except:
                pass
        
        resp_body = None
        if response.is_json:
            try:
                resp_body = response.get_json()
            except:
                pass
        
        log_activity(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            request_body=req_body,
            response_body=resp_body
        )
    
    return response


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/api', methods=['GET'])
def api_docs():
    return render_template('api.html')


@app.route("/api/monitor", methods=["GET"])
def api_monitor():
    """API Activity Monitor page"""
    return render_template("monitor.html")


@app.route("/api/monitor/stream", methods=["GET"])
def stream_activity():
    """SSE stream for real-time activity updates"""
    def generate():
        # send what we have so far
        with log_lock:
            for activity in list(activity_log):
                yield f"data: {json.dumps(activity)}\n\n"
        
        # keep alive and push new stuff
        last_count = len(activity_log)
        while True:
            time.sleep(0.5)
            with log_lock:
                current = len(activity_log)
                if current > last_count:
                    new_items = list(activity_log)[-(current - last_count):]
                    for activity in new_items:
                        yield f"data: {json.dumps(activity)}\n\n"
                    last_count = current
    
    return Response(generate(), mimetype='text/event-stream')


@app.route("/api/json", methods=["GET"])
def api_info():
    return jsonify(
        {
            "status": "online",
            "service": "Docker Topic 5 API",
            "ui": "available at /",
            "api_docs": "available at /api",
            "endpoints": {
                "health": "/health",
                "database_check": "/db-check",
                "get_tasks": "GET /tasks",
                "create_task": "POST /tasks",
                "toggle_task": "PATCH /tasks/<id>/toggle",
                "delete_task": "DELETE /tasks/<id>",
            },
            'db_config': {
                'host': os.getenv('DB_HOST'),
                'port': os.getenv('DB_PORT'),
                'database': os.getenv('DB_NAME'),
            },
        }
    )


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'up', 'service': 'api'})


@app.route("/db-check", methods=["GET"])
def check_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT current_database(), current_user;")
        db_info = cur.fetchone()
        cur.close()
        conn.close()

        return jsonify(
            {
                'connection': 'successful',
                'info': {
                    'database': db_info[0],
                    'user': db_info[1],
                },
            }
        )
    except Exception as e:
        return jsonify({'connection': 'failed', 'error': str(e)}), 500


@app.route("/tasks", methods=["GET"])
def get_tasks():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, is_done, created_at FROM tasks ORDER BY id DESC;")
        rows = cur.fetchall()

        tasks = []
        for r in rows:
            tasks.append({
                'id': r[0],
                'title': r[1],
                'is_done': r[2],
                'created_at': r[3].isoformat(),
            })

        cur.close()
        conn.close()
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Task title is required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, is_done, created_at;",
            (title,),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify(
            {
                'id': row[0],
                'title': row[1],
                'is_done': row[2],
                'created_at': row[3].isoformat(),
            }
        ), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<int:task_id>/toggle", methods=["PATCH"])
def toggle_task(task_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE tasks
            SET is_done = NOT is_done
            WHERE id = %s
            RETURNING id, title, is_done, created_at;
            """,
            (task_id,),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if not row:
            return jsonify({"error": "Task not found"}), 404

        return jsonify(
            {
                'id': row[0],
                'title': row[1],
                'is_done': row[2],
                'created_at': row[3].isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if not row:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({'deleted': True, 'id': row[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    # print("Starting Flask app on port 8080...")  # debug line, keeping for now
    app.run(host="0.0.0.0", port=8080)
