-- Таблица users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    phone_number VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

INSERT INTO admins (username, password) VALUES ('admin', 'password');


-- Таблица rooms
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    home_type VARCHAR(255),
    address VARCHAR(255),
    has_tv BOOLEAN,
    has_internet BOOLEAN,
    has_kitchen BOOLEAN,
    has_air_con BOOLEAN,
    price INTEGER,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    avg_rating INTEGER
);

-- Таблица reservations
CREATE TABLE IF NOT EXISTS reservations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    start_date TIMESTAMP WITHOUT TIME ZONE,
    end_date TIMESTAMP WITHOUT TIME ZONE,
    price INTEGER,
    total INTEGER
);

-- Таблица reviews
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    reservation_id INTEGER REFERENCES reservations(id) ON DELETE CASCADE,
    rating INTEGER
);

-- Шаг 3: Заполнение таблиц данными

-- Заполнение таблицы users
INSERT INTO users (name, email, password, phone_number)
VALUES 
    ('John Smith', 'john@gmail.com', '12345', '+74372847328'),
    ('Maxim Bolotov', 'bolotov@mirea.ru', 'password123', '+71234567890'),
    ('Donald Trump', 'trump@mirea.ru', 'BidenIsGay', '+3124567878'),
    ('Joe Biden', 'biden@mirea.ru', 'IamGay', '+4478239472'),
    ('Alex Bebra', 'fgndji@yandex.ru', 'psswrd', '+7463278231');

-- Заполнение таблицы rooms
INSERT INTO rooms (home_type, address, has_tv, has_internet, has_kitchen, has_air_con, price, owner_id, avg_rating)
VALUES
    ('Apartment', '32 dssfs st', TRUE, TRUE, TRUE, FALSE, 100, 1, NULL),
    ('Studio', '32 vfnuvir st', TRUE, TRUE, FALSE, FALSE, 100500, 3, NULL),
    ('Cottage', '52 grenuvne st', FALSE, TRUE, TRUE, TRUE, 200, 4, NULL),
    ('House', '21 bgneirg st', TRUE, TRUE, TRUE, TRUE, 150, 2, NULL);

-- Заполнение таблицы reservations
INSERT INTO reservations (user_id, room_id, start_date, end_date, price, total)
VALUES
    (1, 1, '2024-09-11 14:00:00', '2024-09-18 12:00:00', 100, 500),
    (2, 2, '2024-08-15 14:00:00', '2024-08-20 12:00:00', 150, 250),
    (3, 3, '2024-09-01 14:00:00', '2024-09-10 12:00:00', 100500, 100501),
    (4, 4, '2024-09-05 14:00:00', '2024-09-12 12:00:00', 200, 630),
    (5, 4, '2024-10-11 14:00:00', '2024-10-18 12:00:00', 200, 1000);

-- Заполнение таблицы reviews
INSERT INTO reviews (reservation_id, rating)
VALUES
    (1, 5),
    (2, 4),
    (3, 5),
    (4, 4),
    (5, 4);
