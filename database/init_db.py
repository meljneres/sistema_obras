import sqlite3
from datetime import datetime, timedelta


def init_database():
    """Inicializa o banco de dados com dados de exemplo"""
    conn = sqlite3.connect('obras.db')
    cursor = conn.cursor()

    # Inserir usuário de exemplo
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password) 
    VALUES (?, ?)
    ''', ('engenheiro1', 'senha123'))

    # Pegar ID do usuário
    cursor.execute('SELECT id FROM users WHERE username = ?', ('engenheiro1',))
    user_id = cursor.fetchone()[0]

    # Inserir obra de exemplo
    data_inicio = datetime.now()
    data_fim = data_inicio + timedelta(days=365)

    cursor.execute('''
    INSERT OR IGNORE INTO obras (
        user_id, nome, contrato, ordem_servico, contratante, contratada,
        valor_total, data_inicio, data_fim, duracao_prevista, num_medicoes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        'Construção Edifício Sede',
        '2023/0001',
        'OS-001/2023',
        'Empresa Contratante LTDA',
        'Construtora XYZ LTDA',
        5000000.00,
        data_inicio,
        data_fim,
        12,
        12
    ))

    # Pegar ID da obra
    cursor.execute('SELECT id FROM obras WHERE contrato = ?', ('2023/0001',))
    obra_id = cursor.fetchone()[0]

    # Inserir itens de exemplo
    itens = [
        ('Fundação', 1000000.00),
        ('Estrutura', 2000000.00),
        ('Acabamento', 1500000.00),
        ('Instalações', 500000.00)
    ]

    for desc, valor in itens:
        cursor.execute('''
        INSERT OR IGNORE INTO itens_obra (obra_id, descricao, valor_previsto)
        VALUES (?, ?, ?)
        ''', (obra_id, desc, valor))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
