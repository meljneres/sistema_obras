import sqlite3
import os


def get_db_connection():
    return sqlite3.connect('obras.db')


def create_tables():
    """Cria todas as tabelas necessárias no banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    # Tabela de obras
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        contrato TEXT,
        ordem_servico TEXT,
        contratante TEXT,
        contratada TEXT,
        valor_total REAL,
        data_inicio DATE,
        data_fim DATE,
        duracao_prevista INTEGER,
        num_medicoes INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Tabela de itens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS itens_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        descricao TEXT,
        valor_previsto REAL,
        FOREIGN KEY (obra_id) REFERENCES obras(id)
    )''')

    # Tabela de medições
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medicoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        numero_medicao INTEGER NOT NULL,
        valor_previsto REAL,
        valor_realizado REAL,
        percentual_previsto REAL,
        percentual_realizado REAL,
        data_medicao DATE,
        FOREIGN KEY (obra_id) REFERENCES obras(id),
        FOREIGN KEY (item_id) REFERENCES itens_obra(id)
    )''')

    # Tabela de fatores IMR
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imr_fatores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER NOT NULL,
        numero_medicao INTEGER NOT NULL,
        fator_ponderacao REAL NOT NULL,
        FOREIGN KEY (obra_id) REFERENCES obras(id),
        UNIQUE(obra_id, numero_medicao)
    )''')

    conn.commit()
    conn.close()


def add_user(username, password):
    """Adiciona um novo usuário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username, password):
    """Verifica credenciais do usuário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?',
                   (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None
