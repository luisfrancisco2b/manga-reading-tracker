from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database import init_db

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Mude isso para uma chave segura

# Decorator para verificar se usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    conn = sqlite3.connect('manga_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM mangas WHERE user_id = ?', (session['user_id'],))
    mangas = c.fetchall()
    conn.close()
    return render_template('index.html', mangas=mangas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('manga_tracker.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos', 'error')
        conn.close()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        conn = sqlite3.connect('manga_tracker.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            conn.commit()
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email já cadastrado', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# Rotas CRUD para mangás
@app.route('/add_manga', methods=['POST'])
@login_required
def add_manga():
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        data_lancamento = request.form['data_lancamento']
        capitulo = request.form['capitulo']
        status = request.form['status']
        
        conn = sqlite3.connect('manga_tracker.db')
        c = conn.cursor()
        c.execute('''INSERT INTO mangas 
                    (user_id, titulo, autor, data_lancamento, capitulo, status) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], titulo, autor, data_lancamento, capitulo, status))
        conn.commit()
        conn.close()
        flash('Mangá adicionado com sucesso!', 'success')
        return redirect(url_for('index'))

@app.route('/edit_manga/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_manga(id):
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        data_lancamento = request.form['data_lancamento']
        capitulo = request.form['capitulo']
        status = request.form['status']
        
        conn = sqlite3.connect('manga_tracker.db')
        c = conn.cursor()
        c.execute('''UPDATE mangas 
                    SET titulo=?, autor=?, data_lancamento=?, capitulo=?, status=?
                    WHERE id=? AND user_id=?''',
                 (titulo, autor, data_lancamento, capitulo, status, id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Mangá atualizado com sucesso!', 'success')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('manga_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM mangas WHERE id=? AND user_id=?', (id, session['user_id']))
    manga = c.fetchone()
    conn.close()
    return render_template('edit_manga.html', manga=manga)

@app.route('/delete_manga/<int:id>')
@login_required
def delete_manga(id):
    conn = sqlite3.connect('manga_tracker.db')
    c = conn.cursor()
    c.execute('DELETE FROM mangas WHERE id=? AND user_id=?', (id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Mangá excluído com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 