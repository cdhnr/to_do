from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key ="segredo_super_secreto"

def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("todo"))
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Usuário já existe"
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            return "Usuário ou senha inválidos"
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/todo", methods=["GET", "POST"])
def todo():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        title = request.form["title"]
        conn.execute("INSERT INTO tasks (user_id, title) VALUES (?, ?)", (session["user_id"], title))
        conn.commit()
    
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (session["user_id"],)).fetchall()
    conn.close()

    return render_template("todo.html", tasks=tasks, username=session["username"])

@app.route("/done/<int:task_id>")
def mark_done(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.execute("UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?", (task_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect(url_for("todo"))

@app.route("/delete/<int:task_id>")
def delete(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("todo"))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":
        new_title = request.form["title"]
        cursor.execute("UPDATE tasks SET title = ? WHERE ID = ? and USER_ID = ?", (new_title, task_id, session["user_id"]))
        conn.commit()
        conn.close()
        return redirect(url_for("todo"))

    # GET method: pegar tarefa e mostrar formulário

    cursor.execute("SELECT title FROM tasks WHERE id = ? AND user_id = ?", (task_id, session["user_id"]))
    task = cursor.fetchone()
    conn.close()

    if task:
        return render_template("edit.html", task_id=task_id, title=task[0])
    else:
        return redirect(url_for("todo"))

if __name__ == "__main__":
    app.run(debug=True)