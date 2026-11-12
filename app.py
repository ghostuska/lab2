import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_lab'
DB_NAME = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            secret_note TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT INTO users (username, password, secret_note) VALUES ('admin', 'admin_pass_999', 'Флаг администратора: FLAG{SQLI_AND_IDOR_MASTER}')")
    cursor.execute("INSERT INTO users (username, password, secret_note) VALUES ('alice', 'alice123', 'Личная заметка Алисы: купить молоко')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('profile', user_id=session['user_id']))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Уязвимость 1: SQL Injection
        query = f"SELECT id, username FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('profile', user_id=user[0]))
        else:
            error = 'Неверный логин или пароль'
            
    return render_template_string('''
        <h2>Вход в систему</h2>
        <p style="color:red">{{ error }}</p>
        <form method="post">
            Логин: <input type="text" name="username"><br>
            Пароль: <input type="password" name="password"><br>
            <input type="submit" value="Войти">
        </form>
    ''', error=error)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Уязвимость 2: IDOR 
    cursor.execute("SELECT username, secret_note FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return render_template_string('''
            <h2>Профиль пользователя: {{ username }}</h2>
            <p><b>Секретная заметка:</b> {{ note }}</p>
            <a href="/logout">Выйти</a>
        ''', username=user[0], note=user[1])
    return "Пользователь не найден", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False)
