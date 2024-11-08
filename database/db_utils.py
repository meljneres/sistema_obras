import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('obras.db')
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Recria as tabelas
    cursor.execute('DROP TABLE IF EXISTS medicoes')
    cursor.execute('DROP TABLE IF EXISTS medicoes_previstas')
    cursor.execute('DROP TABLE IF EXISTS itens_obra')
    cursor.execute('DROP TABLE IF EXISTS obras')

    # Tabela de Obras
    cursor.execute('''
    CREATE TABLE obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        contrato TEXT,
        ordem_servico TEXT,
        contratante TEXT,
        contratada TEXT,
        valor_total REAL,
        data_inicio DATE,
        data_fim DATE,
        duracao_prevista INTEGER,
        duracao_realizada INTEGER,
        num_medicoes INTEGER
    )''')

    # Tabela de Itens/Descrições
    cursor.execute('''
    CREATE TABLE itens_obra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER,
        descricao TEXT,
        valor_previsto REAL,
        FOREIGN KEY (obra_id) REFERENCES obras(id)
    )''')

    # Tabela de Medições
    cursor.execute('''
    CREATE TABLE medicoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER,
        item_id INTEGER,
        numero_medicao INTEGER,
        valor_previsto REAL,
        valor_realizado REAL,
        percentual_previsto REAL,
        percentual_realizado REAL,
        data_medicao DATE,
        FOREIGN KEY (obra_id) REFERENCES obras(id),
        FOREIGN KEY (item_id) REFERENCES itens_obra(id)
    )''')

    conn.commit()
    conn.close()