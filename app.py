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
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM mangas WHERE user_id = ?', (session['user_id'],))
    mangas = c.fetchall()
    
    # Obter nome do usuário
    c.execute('SELECT nome FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    user_name = user['nome'] if user else 'Usuário'
    
    conn.close()
    return render_template('index.html', mangas=mangas, user_name=user_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('manga_tracker.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['nome']
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos', 'error')
        conn.close()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        conn = sqlite3.connect('manga_tracker.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (nome, email, password) VALUES (?, ?, ?)', (nome, email, password))
            conn.commit()
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email já cadastrado', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = sqlite3.connect('manga_tracker.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user:
            # Em um projeto real, enviaríamos um email com link.
            # Aqui vamos renderizar um template para redefinir a senha
            conn.close()
            return render_template('reset_password.html', email=email)
        else:
            flash('Email não encontrado em nossa base de dados.', 'error')
            conn.close()
            
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form['email']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('As senhas não coincidem.', 'error')
        return render_template('reset_password.html', email=email)
        
    hashed_password = generate_password_hash(new_password)
    
    conn = sqlite3.connect('manga_tracker.db')
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
    conn.commit()
    conn.close()
    
    flash('Senha alterada com sucesso! Faça login com sua nova senha.', 'success')
    return redirect(url_for('login'))

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