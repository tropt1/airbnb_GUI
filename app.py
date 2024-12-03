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


# Страница для выхода из системы
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('home'))

# Страница для отображения таблиц
@app.route('/table/<table_name>')
@login_required
def show_table(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()

    # Переводим названия столбцов
    translated_columns = [column_translations.get(col, col) for col in columns]

    return render_template('show_table.html', rows=rows, columns=translated_columns, table_name=table_name)

# Страница для выполнения SQL-запросов
@app.route('/execute_query', methods=['GET', 'POST'])
@login_required
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
