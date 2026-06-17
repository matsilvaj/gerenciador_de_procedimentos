from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QGridLayout, QFrame, QCompleter
)
from PySide6.QtCore import Qt, QSettings
from core import database

def carregar_casas_ativas():
    casas_db = database.listar_casas_ativas()
    if casas_db:
        return casas_db

    settings = QSettings("GerenciadorProcedimentos", "Bancas")
    casas_ativas = settings.value("casas_ativas", [])
    if casas_ativas is None:
        return []
    if isinstance(casas_ativas, str):
        casas_ativas = [casas_ativas] if casas_ativas.strip() else []

    casas_migradas = [str(casa).strip() for casa in casas_ativas if str(casa).strip()]
    for casa in casas_migradas:
        database.definir_casa_ativa(casa, True)
    return casas_migradas

def normalizar_casas(casas):
    if isinstance(casas, str):
        casas = casas.split(" | ")

    nomes = []
    vistos = set()
    for casa in casas or []:
        nome = str(casa).strip()
        if not nome or nome in ["None", "-", "Nenhuma selecionada"]:
            continue

        chave = nome.lower()
        if chave not in vistos:
            nomes.append(nome)
            vistos.add(chave)

    return nomes

def adicionar_casas_a_bancas(casas):
    nomes = normalizar_casas(casas)
    if not nomes:
        return []

    casas_ativas = carregar_casas_ativas()
    casas_ativas_normalizadas = {casa.lower() for casa in casas_ativas}
    casas_adicionadas = []

    for nome in nomes:
        if nome.lower() in casas_ativas_normalizadas:
            continue

        database.definir_casa_ativa(nome, True)
        casas_ativas.append(nome)
        casas_ativas_normalizadas.add(nome.lower())
        casas_adicionadas.append(nome)

    return casas_adicionadas

def montar_mensagem_casas_adicionadas(casas_adicionadas):
    nomes = ", ".join(casas_adicionadas)
    if len(casas_adicionadas) == 1:
        return f"Casa adicionada na aba Bancas: {nomes}"
    return f"Casas adicionadas na aba Bancas: {nomes}"

class TelaCasasApostas(QWidget):
    def __init__(self):
        super().__init__()
        
        self.casas_ativas = carregar_casas_ativas()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20) 
        layout.setSpacing(20)
        
        # --- CABEÇALHO ---
        header_lay = QVBoxLayout()
        titulo = QLabel("Minhas Casas de Apostas")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #f4f4f5;")
        header_lay.addWidget(titulo)
        
        self.input_add = QLineEdit()
        self.input_add.setPlaceholderText("Digite a casa e aperte Enter (adiciona nova ou fixa existente)...")
        self.input_add.setFixedHeight(45)
        self.input_add.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 0 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.input_add.returnPressed.connect(self.adicionar_casa_grade)
        
        header_lay.addWidget(self.input_add)
        layout.addLayout(header_lay)
        
        # --- ÁREA DE GRADE ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.container_grid = QWidget()
        self.container_grid.setStyleSheet("background-color: transparent;")
        self.container_grid.setSizePolicy(self.container_grid.sizePolicy().Policy.Expanding, self.container_grid.sizePolicy().Policy.Fixed)
        
        self.grid_lay = QGridLayout(self.container_grid)
        self.grid_lay.setSpacing(15)
        self.grid_lay.setAlignment(Qt.AlignTop) 
        
        self.scroll.setWidget(self.container_grid)
        layout.addWidget(self.scroll)
        
        # Auto-completar 
        self.lista_casas_db = database.listar_casas()
        self.completer = QCompleter(self.lista_casas_db)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.popup().setStyleSheet("""
            QListView { background-color: #18181b; color: #f4f4f5; border: 1px solid #3b82f6; border-radius: 5px; font-size: 14px; }
            QListView::item:selected { background-color: #27272a; }
        """)
        self.input_add.setCompleter(self.completer)
        
        self.renderizar_grid()

    def adicionar_casa_grade(self):
        texto = self.input_add.text().strip()
        if not texto: return
        
        nome_escolhido = None
        nova_casa = False
        
        # 1. Tenta correspondência exata primeiro no banco existente
        for casa in self.lista_casas_db:
            if casa.lower() == texto.lower():
                nome_escolhido = casa
                break
        
        # 2. Se não bateu exato, verifica se o autocompletar tem algo válido selecionado
        if not nome_escolhido:
            sugestao = self.completer.currentCompletion()
            if sugestao and sugestao.lower().startswith(texto.lower()):
                nome_escolhido = sugestao

        # 3. Se não achou na lista nem no autocompletar, então é uma casa nova de verdade
        if not nome_escolhido:
            nome_escolhido = texto
            nova_casa = True

        # Se for casa nova, salva no banco e atualiza o autocomplete
        if nova_casa:
            database.definir_casa_ativa(nome_escolhido, True)
            self.lista_casas_db = database.listar_casas()
            self.completer.model().setStringList(self.lista_casas_db)

        # Adiciona na grade se já não estiver ativada
        if nome_escolhido not in self.casas_ativas:
            database.definir_casa_ativa(nome_escolhido, True)
            self.casas_ativas.append(nome_escolhido)
            self.renderizar_grid()
                
        self.input_add.clear()

    def remover_casa(self, nome):
        if nome in self.casas_ativas:
            self.casas_ativas.remove(nome)
            database.definir_casa_ativa(nome, False)
            self.renderizar_grid()

    def renderizar_grid(self):
        for i in reversed(range(self.grid_lay.count())): 
            w = self.grid_lay.itemAt(i).widget()
            if w: w.deleteLater()
            
        for i, nome in enumerate(self.casas_ativas):
            card = QFrame()
            card.setFixedHeight(80) 
            card.setStyleSheet("""
                QFrame {
                    background-color: #18181b;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                }
                QFrame:hover { border: 1px solid #3b82f6; }
            """)
            
            card_grid = QGridLayout(card)
            card_grid.setContentsMargins(10, 5, 10, 5)
            
            lbl_nome = QLabel(nome)
            lbl_nome.setAlignment(Qt.AlignCenter)
            lbl_nome.setStyleSheet("font-size: 20px; font-weight: bold; color: #f4f4f5; border: none; background: transparent;")
            
            btn_remover = QPushButton("✕")
            btn_remover.setFixedSize(24, 24)
            btn_remover.setCursor(Qt.PointingHandCursor)
            btn_remover.setStyleSheet("""
                QPushButton { background-color: transparent; color: #52525b; border: none; }
                QPushButton:hover { color: #ef4444; background-color: rgba(239, 68, 68, 0.1); border-radius: 12px; }
            """)
            btn_remover.clicked.connect(lambda checked=False, n=nome: self.remover_casa(n))
            
            card_grid.addWidget(lbl_nome, 0, 0, 1, 1)
            card_grid.addWidget(btn_remover, 0, 0, Qt.AlignTop | Qt.AlignRight)

            self.grid_lay.addWidget(card, i // 4, i % 4)

    def atualizar_dados(self):
        self.casas_ativas = carregar_casas_ativas()
        self.lista_casas_db = database.listar_casas()
        self.completer.model().setStringList(self.lista_casas_db)
        self.renderizar_grid()
