# Sistema de Gestão de Obras

Sistema para gerenciamento de obras e geração de relatórios de medições.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
git clone https://github.com/seu-usuario/sistema-obras.git
cd sistema-obras

2. Crie um ambiente virtual:
python -m venv .venv

3. Ative o ambiente virtual:
- Windows:
.venv\Scripts\activate

- Linux/Mac:
source .venv/bin/activate

4. Instale as dependências:
pip install -r requirements.txt

## Uso

1. Inicie o sistema:
streamlit run main.py


2. Acesse no navegador:
- O sistema abrirá automaticamente em http://localhost:8501

## Funcionalidades

1. Cadastro de Obras
- Dados básicos da obra
- Itens e descrições
- Valores previstos por medição
- Configuração de fatores IMR

2. Registro de Medições
- Seleção da obra
- Registro de valores realizados
- Cálculo automático de indicadores
- Análise de desempenho

3. Relatórios
- Gráficos de desempenho
- Análise de IDP
- Geração de PDF
- Exportação de dados

## Estrutura do Projeto

sistema_obras/
├── main.py # Arquivo principal
├── requirements.txt # Dependências
├── database/ # Módulos do banco de dados
│ ├── init.py
│ └── db_utils.py
├── utils/ # Utilitários
│ ├── init.py
│ ├── formatters.py
│ ├── calculadora.py
│ └── validators.py
└── modules/ # Módulos principais
├── init.py
├── auth.py
├── cadastro.py
├── medicoes.py
├── relatorios.py
└── pdf_generator.py

