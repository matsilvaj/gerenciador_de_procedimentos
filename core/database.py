import sqlite3
import os

DB_NAME = "dados_usuario.db"

def conectar():
    return sqlite3.connect(DB_NAME)

def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Casas_de_Apostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    """)

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

    conexao.commit()
    conexao.close()

def atualizar_schema():
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("PRAGMA table_info(Procedimentos_Historico)")
    colunas = [col[1] for col in cursor.fetchall()]
    if 'casa_destino_freebet' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN casa_destino_freebet TEXT")
    if 'status_freebet' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN status_freebet TEXT DEFAULT 'Pendente'")
    if 'id_freebet_origem' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN id_freebet_origem INTEGER")
    if 'valor_da_freebet' not in colunas:
        cursor.execute("ALTER TABLE Procedimentos_Historico ADD COLUMN valor_da_freebet REAL DEFAULT 0.0")
        
    cursor.execute("PRAGMA table_info(Casas_de_Apostas)")
    colunas_casas = [col[1] for col in cursor.fetchall()]
    if 'saldo' not in colunas_casas:
        cursor.execute("ALTER TABLE Casas_de_Apostas ADD COLUMN saldo REAL DEFAULT 0.0")
    
    conexao.commit()
    conexao.close()

def salvar_conversao_freebet(dados, ids_freebet_origem):
    conexao = conectar()
    cursor = conexao.cursor()
    
    id_referencia = ids_freebet_origem[0] if isinstance(ids_freebet_origem, list) else ids_freebet_origem
    
    query = """
    INSERT INTO Procedimentos_Historico 
    (data_operacao, tipo_procedimento, casas_envolvidas, jogo_time_pa, lucro_final, valor_freebet_coletada, condicao_freebet, observacao, mes_referencia, id_freebet_origem, casa_destino_freebet, valor_da_freebet)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    valores = (
        dados.get('data_operacao', ''), dados.get('tipo_procedimento', ''), dados.get('casas_envolvidas', ''),
        dados.get('jogo_time_pa', ''), dados.get('lucro_final', 0.0), dados.get('valor_freebet_coletada', 0.0),
        dados.get('condicao_freebet', ''), dados.get('observacao', ''), dados.get('mes_referencia', ''),
        id_referencia, dados.get('casa_destino_freebet', ''), dados.get('valor_da_freebet', 0.0)
    )
    cursor.execute(query, valores)
    
    if isinstance(ids_freebet_origem, list):
        for id_op in ids_freebet_origem:
            cursor.execute("UPDATE Procedimentos_Historico SET status_freebet = 'Usada' WHERE id = ?", (id_op,))
    else:
        cursor.execute("UPDATE Procedimentos_Historico SET status_freebet = 'Usada' WHERE id = ?", (ids_freebet_origem,))
    
    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    criar_tabelas()
    atualizar_schema()
    print(f"Banco de dados '{DB_NAME}' criado/verificado com sucesso!")
    
def adicionar_casa(nome_casa):
    conexao = conectar()
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO Casas_de_Apostas (nome) VALUES (?)", (nome_casa,))
        conexao.commit()
    except sqlite3.IntegrityError:
        pass 
    finally:
        conexao.close()

def listar_casas():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome FROM Casas_de_Apostas ORDER BY nome ASC")
    casas = [linha[0] for linha in cursor.fetchall()]
    conexao.close()
    return casas

def salvar_procedimento(dados):
    conexao = conectar()
    cursor = conexao.cursor()
    query = """
    INSERT INTO Procedimentos_Historico (
        data_operacao, tipo_procedimento, casas_envolvidas, jogo_time_pa,
        lucro_final, bateu_duplo, condicao_freebet, valor_freebet_coletada, 
        observacao, mes_referencia, casa_destino_freebet, status_freebet, valor_da_freebet
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    valores = (
        dados.get('data_operacao'), dados.get('tipo_procedimento'), dados.get('casas_envolvidas'),
        dados.get('jogo_time_pa'), dados.get('lucro_final'), dados.get('bateu_duplo'),
        dados.get('condicao_freebet'), dados.get('valor_freebet_coletada'), dados.get('observacao'),
        dados.get('mes_referencia'), dados.get('casa_destino_freebet', ''), dados.get('status_freebet', 'N/A'),
        dados.get('valor_da_freebet', 0.0)
    )
    cursor.execute(query, valores)
    conexao.commit()
    conexao.close()
    
def atualizar_status_duplo(id_procedimento, bateu):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("UPDATE Procedimentos_Historico SET bateu_duplo = ? WHERE id = ?", (bateu, id_procedimento))
    conexao.commit()
    conexao.close()
    
def atualizar_procedimento(id_op, dados):
    conexao = conectar()
    cursor = conexao.cursor()
    query = """
    UPDATE Procedimentos_Historico SET 
        tipo_procedimento = ?, jogo_time_pa = ?, casas_envolvidas = ?, 
        lucro_final = ?, valor_freebet_coletada = ?, condicao_freebet = ?, observacao = ?, casa_destino_freebet = ?, valor_da_freebet = ?
    WHERE id = ?
    """
    valores = (
        dados['tipo_procedimento'], dados['jogo_time_pa'], dados['casas_envolvidas'],
        dados['lucro_final'], dados['valor_freebet_coletada'], dados['condicao_freebet'],
        dados['observacao'], dados.get('casa_destino_freebet', ''), dados.get('valor_da_freebet', 0.0), id_op
    )
    cursor.execute(query, valores)
    conexao.commit()
    conexao.close()

def excluir_procedimento(id_op):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM Procedimentos_Historico WHERE id = ?", (id_op,))
    conexao.commit()
    conexao.close()
    
def listar_meses_disponiveis():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT DISTINCT mes_referencia FROM Procedimentos_Historico ORDER BY id DESC")
    meses = [linha[0] for linha in cursor.fetchall()]
    conexao.close()
    return meses

def buscar_dados_mes(mes_ref):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT data_operacao, tipo_procedimento, jogo_time_pa, casas_envolvidas, lucro_final, valor_freebet_coletada, bateu_duplo FROM Procedimentos_Historico WHERE mes_referencia = ?", (mes_ref,))
    dados = cursor.fetchall()
    conexao.close()
    return dados

def excluir_casa(nome_casa):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM Casas_de_Apostas WHERE nome = ?", (nome_casa,))
    conexao.commit()
    conexao.close()
    
def listar_casas_com_saldo():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome, saldo FROM Casas_de_Apostas ORDER BY nome ASC")
    dados = cursor.fetchall()
    conexao.close()
    return dados

def atualizar_saldo_casa(nome_casa, saldo):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("UPDATE Casas_de_Apostas SET saldo = ? WHERE nome = ?", (saldo, nome_casa))
    conexao.commit()
    conexao.close()