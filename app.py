from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Генерация случайного ключа для сессий

# Подключение к базе данных
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='db',  # Используем имя сервиса из docker-compose.yml
            database='airbnb',
            user='postgres',
            password='12345'
        )
        print("Подключение к базе данных успешно.")
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Перевод столбцов для отображения
column_translations = {
    'id': 'ID', 'name': 'Имя', 'email': 'Электронная почта', 'password': 'Пароль',
    'phone_number': 'Номер телефона', 'home_type': 'Тип жилья', 'address': 'Адрес',
    'has_tv': 'Наличие ТВ', 'has_internet': 'Наличие интернета', 'has_kitchen': 'Наличие кухни',
    'has_air_con': 'Наличие кондиционера', 'price': 'Цена', 'owner_id': 'ID владельца',
    'avg_rating': 'Средний рейтинг', 'user_id': 'ID пользователя', 'room_id': 'ID комнаты',
    'start_date': 'Дата начала', 'end_date': 'Дата окончания', 'total': 'Итоговая сумма',
    'reservation_id': 'ID бронирования', 'rating': 'Оценка'
}

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Защита маршрутов (проверка на авторизацию)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Главная страница
@app.route('/')
def home():
    return render_template('home.html')

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                       (name, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Пожалуйста, заполните все поля!', 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[3], password):  # Исправлено user[3]
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                flash('Вы успешно вошли!', 'success')
                return redirect(url_for('home'))  # Перенаправление на домашнюю страницу
            else:
                flash('Неверный email или пароль!', 'danger')
        except Exception as e:
            flash(f'Ошибка при входе: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
            admin = cursor.fetchone()
            if admin and admin[2] == password:
                session['user_id'] = admin[0]
                session['is_admin'] = True
                session['admin_username'] = username
                flash('Вы вошли как администратор!')
                return redirect(url_for('execute_query'))
            else:
                flash('Неверное имя пользователя или пароль.')
        
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
            
    return render_template('admin_login.html')


# Страница для выхода из системы
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('home'))

# Страница для отображения таблиц
@app.route('/table/<table_name>', methods=['GET', 'POST'])
@login_required
def show_table(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Обработка поиска по параметру
    search_query = request.form.get('search_query', '')
    where_clause = ''
    if search_query:
        where_clause = f"WHERE name ILIKE %s"  # Пример поиска по колонке 'name', используйте нужную колонку

    # Выполнение запроса с возможным поиском
    cursor.execute(f'SELECT * FROM {table_name} {where_clause}', ('%' + search_query + '%',))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # Добавление новой записи
    if request.method == 'POST' and 'add_record' in request.form:
        # Получаем данные из формы
        new_data = request.form.get('new_data').split(',')  # В примере данные разделены запятой
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(new_data))})"
        cursor.execute(insert_query, new_data)
        conn.commit()
        flash('Запись успешно добавлена!', 'success')

    # Удаление записи
    # Удаление записи
    if 'delete_record' in request.form:
        record_id = request.form.get('record_id')

        # Проверяем, пытается ли пользователь удалить свой собственный аккаунт
        if table_name == 'users' and int(record_id) == session.get('user_id'):
            flash('Вы не можете удалить свой собственный аккаунт, пока вы подключены.', 'danger')
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(f'DELETE FROM {table_name} WHERE id = %s', (record_id,))
                conn.commit()
                flash('Запись успешно удалена!', 'success')
            except Exception as e:
                flash(f'Ошибка удаления записи: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()


    # Переводим названия столбцов
    translated_columns = [column_translations.get(col, col) for col in columns]

    return render_template('show_table.html', rows=rows, columns=translated_columns, table_name=table_name, search_query=search_query)


# Страница для выполнения SQL-запросов
@app.route('/execute_query', methods=['GET', 'POST'])
@admin_required
def execute_query():
    result = None
    columns = []
    if request.method == 'POST':
        query = request.form['query']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()

            # Если это SELECT-запрос, получаем результаты
            if query.strip().lower().startswith('select'):
                result = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

            flash('Запрос выполнен успешно!', 'success')
        except Exception as e:
            flash(f'Ошибка выполнения запроса: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('execute_query.html', result=result, columns=columns)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
