import sqlite3
import os

# Define o nome do arquivo do banco de dados
DB_NAME = "dados_usuario.db"

def conectar():
    """Retorna uma conexão com o banco de dados SQLite."""
    return sqlite3.connect(DB_NAME)

def criar_tabelas():
    """Cria as tabelas no banco de dados se elas não existirem."""
    conexao = conectar()
    cursor = conexao.cursor()

    # Tabela 1: Casas de Apostas (Para salvar o menu dropdown)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Casas_de_Apostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    """)

    # Tabela 2: Histórico Geral de Procedimentos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Procedimentos_Historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_operacao DATE NOT NULL,
        tipo_procedimento TEXT NOT NULL,
        casas_envolvidas TEXT,
        jogo_time_pa TEXT,
        lucro_final REAL NOT NULL,
        bateu_duplo BOOLEAN,
        condicao_freebet TEXT,
        valor_freebet_coletada REAL,
        observacao TEXT,
        mes_referencia TEXT NOT NULL
    )
    """)

    # Salva as alterações e fecha a conexão
    conexao.commit()
    conexao.close()

def atualizar_schema():
    """Adiciona colunas novas em bancos já existentes sem apagar dados."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("PRAGMA table_info(Procedimentos_Historico)")
    colunas = [col[1] for col in cursor.fetchall()]
    
    if 'casa_destino_freebet' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN casa_destino_freebet TEXT")
    if 'status_freebet' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN status_freebet TEXT DEFAULT 'Pendente'")
    # --- NOVA COLUNA ADICIONADA ---
    if 'id_freebet_origem' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN id_freebet_origem INTEGER")
    
    conexao.commit()
    conexao.close()

def salvar_conversao_freebet(dados, id_freebet_origem):
    """Salva a conversão e muda o status da coleta original para 'Usada'."""
    conexao = conectar()
    cursor = conexao.cursor()
    
    # 1. Insere o NOVO procedimento (A Conversão) ligando ao ID original
    query = """
    INSERT INTO Procedimentos_Historico 
    (data_operacao, tipo_procedimento, casas_envolvidas, jogo_time_pa, lucro_final, valor_freebet_coletada, condicao_freebet, observacao, mes_referencia, id_freebet_origem)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    valores = (
        dados.get('data_operacao', ''), dados.get('tipo_procedimento', ''), dados.get('casas_envolvidas', ''),
        dados.get('jogo_time_pa', ''), dados.get('lucro_final', 0.0), dados.get('valor_freebet_coletada', 0.0),
        dados.get('condicao_freebet', ''), dados.get('observacao', ''), dados.get('mes_referencia', ''),
        id_freebet_origem
    )
    cursor.execute(query, valores)
    
    # 2. Atualiza a Coleta original para 'Usada'
    cursor.execute("UPDATE Procedimentos_Historico SET status_freebet = 'Usada' WHERE id = ?", (id_freebet_origem,))
    
    conexao.commit()
    conexao.close()

# Bloco de teste para rodar apenas este arquivo e gerar o banco
if __name__ == "__main__":
    criar_tabelas()
    atualizar_schema()
    print(f"Banco de dados '{DB_NAME}' criado/verificado com sucesso!")
    
def adicionar_casa(nome_casa):
    """Adiciona uma nova casa de aposta ao banco, se não existir."""
    conexao = conectar()
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO Casas_de_Apostas (nome) VALUES (?)", (nome_casa,))
        conexao.commit()
    except sqlite3.IntegrityError:
        pass # Ignora se a casa já estiver cadastrada (UNIQUE)
    finally:
        conexao.close()

def listar_casas():
    """Retorna uma lista com os nomes de todas as casas cadastradas."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome FROM Casas_de_Apostas ORDER BY nome ASC")
    casas = [linha[0] for linha in cursor.fetchall()]
    conexao.close()
    return casas

def salvar_procedimento(dados):
    """
    Recebe um dicionário com os dados da operação e salva no banco de dados.
    """
    conexao = conectar()
    cursor = conexao.cursor()
    
    query = """
    INSERT INTO Procedimentos_Historico (
        data_operacao, tipo_procedimento, casas_envolvidas, jogo_time_pa,
        lucro_final, bateu_duplo, condicao_freebet, valor_freebet_coletada, 
        observacao, mes_referencia
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    valores = (
        dados.get('data_operacao'),
        dados.get('tipo_procedimento'),
        dados.get('casas_envolvidas'),
        dados.get('jogo_time_pa'),
        dados.get('lucro_final'),
        dados.get('bateu_duplo'),
        dados.get('condicao_freebet'),
        dados.get('valor_freebet_coletada'),
        dados.get('observacao'),
        dados.get('mes_referencia')
    )
    
    cursor.execute(query, valores)
    conexao.commit()
    conexao.close()
    
def atualizar_status_duplo(id_procedimento, bateu):
    """Atualiza o status do duplo no banco de dados."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("UPDATE Procedimentos_Historico SET bateu_duplo = ? WHERE id = ?", (bateu, id_procedimento))
    conexao.commit()
    conexao.close()
    
def atualizar_procedimento(id_op, dados):
    """Atualiza um registro existente no banco."""
    conexao = conectar()
    cursor = conexao.cursor()
    query = """
    UPDATE Procedimentos_Historico SET 
        tipo_procedimento = ?, jogo_time_pa = ?, casas_envolvidas = ?, 
        lucro_final = ?, valor_freebet_coletada = ?, condicao_freebet = ?, observacao = ?
    WHERE id = ?
    """
    valores = (
        dados['tipo_procedimento'], dados['jogo_time_pa'], dados['casas_envolvidas'],
        dados['lucro_final'], dados['valor_freebet_coletada'], dados['condicao_freebet'],
        dados['observacao'], id_op
    )
    cursor.execute(query, valores)
    conexao.commit()
    conexao.close()

def excluir_procedimento(id_op):
    """Remove um procedimento do banco."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM Procedimentos_Historico WHERE id = ?", (id_op,))
    conexao.commit()
    conexao.close()
    
def listar_meses_disponiveis():
    """Retorna uma lista de todos os meses/anos que possuem registros (Ex: ['04/2026', '03/2026'])."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT mes_referencia FROM Procedimentos_Historico ORDER BY id DESC")
    meses = [linha[0] for linha in cursor.fetchall()]
    conexao.close()
    return meses

def buscar_dados_mes(mes_ref):
    """Retorna todos os registros de um mês específico."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT data_operacao, tipo_procedimento, jogo_time_pa, casas_envolvidas, lucro_final, valor_freebet_coletada, bateu_duplo FROM Procedimentos_Historico WHERE mes_referencia = ?", (mes_ref,))
    dados = cursor.fetchall()
    conexao.close()
    return dados

def excluir_casa(nome_casa):
    """Remove uma casa de aposta do banco de dados."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM Casas_de_Apostas WHERE nome = ?", (nome_casa,))
    conexao.commit()
    conexao.close()