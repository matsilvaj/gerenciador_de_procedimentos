from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QGridLayout, QFrame, QCompleter
)
from PySide6.QtCore import Qt, QSettings, QStringListModel
from core import database

class TelaCasasApostas(QWidget):
    def __init__(self):
        super().__init__()
        
        # Persistência para salvar quais casas você adicionou na grade
        self.settings = QSettings("GerenciadorProcedimentos", "Bancas")
        self.casas_ativas = self.settings.value("casas_ativas", [])
        if self.casas_ativas is None: self.casas_ativas = []
        if isinstance(self.casas_ativas, str): self.casas_ativas = [self.casas_ativas]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(30)
        
        # --- CABEÇALHO ---
        header_lay = QVBoxLayout()
        titulo = QLabel("Minhas Casas de Apostas")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #f4f4f5;")
        header_lay.addWidget(titulo)
        
        # Input para digitar e adicionar
        self.input_add = QLineEdit()
        self.input_add.setPlaceholderText("Digite o nome da casa e aperte Enter para adicionar...")
        self.input_add.setFixedHeight(50)
        self.input_add.setStyleSheet("""
            QLineEdit {
                background-color: #18181b;
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 0 20px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.input_add.returnPressed.connect(self.adicionar_casa)
        header_lay.addWidget(self.input_add)
        
        # --- AUTO-COMPLETAR (Busca do Banco) ---
        self.lista_casas_db = [c[0] for c in database.listar_casas_com_saldo()]
        self.completer = QCompleter(self.lista_casas_db)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        
        # Estilo da caixinha de sugestões do auto-completar
        self.completer.popup().setStyleSheet("""
            QListView {
                background-color: #18181b;
                color: #f4f4f5;
                font-size: 14px;
                border: 1px solid #3b82f6;
                border-radius: 5px;
            }
            QListView::item:hover, QListView::item:selected {
                background-color: #27272a;
                color: white;
            }
        """)
        self.input_add.setCompleter(self.completer)
        
        layout.addLayout(header_lay)
        
        # --- ÁREA DE SCROLL COM A GRADE ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.container_grid = QWidget()
        self.container_grid.setStyleSheet("background-color: transparent;")
        
        self.grid_lay = QGridLayout(self.container_grid)
        self.grid_lay.setSpacing(20)
        self.grid_lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll.setWidget(self.container_grid)
        layout.addWidget(self.scroll)
        
        self.renderizar_grid()

    def adicionar_casa(self):
        nome = self.input_add.text().strip()
        if not nome: return
        
        # 1. Garante que a casa seja salva no banco de dados
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT nome FROM Casas_de_Apostas WHERE nome = ?", (nome,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Casas_de_Apostas (nome, saldo) VALUES (?, 0.0)", (nome,))
            conexao.commit()
        conexao.close()
        
        # 2. Atualiza a lista do Auto-completar para as próximas vezes
        if nome not in self.lista_casas_db:
            self.lista_casas_db.append(nome)
            # Atualiza o modelo do completer
            self.completer.model().setStringList(self.lista_casas_db)

        # 3. Adiciona na grade se não estiver lá
        if nome not in self.casas_ativas:
            self.casas_ativas.append(nome)
            self.settings.setValue("casas_ativas", self.casas_ativas)
            self.renderizar_grid()
        
        self.input_add.clear()

    def remover_casa(self, nome):
        if nome in self.casas_ativas:
            self.casas_ativas.remove(nome)
            self.settings.setValue("casas_ativas", self.casas_ativas)
            self.renderizar_grid()

    def renderizar_grid(self):
        # Limpa o layout atual
        for i in reversed(range(self.grid_lay.count())): 
            w = self.grid_lay.itemAt(i).widget()
            if w: w.deleteLater()
            
        # Cria os cards (3 colunas)
        for i, nome in enumerate(self.casas_ativas):
            card = QFrame()
            card.setFixedSize(300, 130)
            card.setStyleSheet("""
                QFrame {
                    background-color: #18181b;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                }
                QFrame:hover {
                    border: 1px solid #3b82f6;
                    background-color: #202023;
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 10, 15, 20)
            
            # --- LINHA DO BOTÃO X ---
            top_bar = QHBoxLayout()
            top_bar.setContentsMargins(0, 0, 0, 0)
            top_bar.addStretch()
            
            btn_remover = QPushButton("✕")
            btn_remover.setFixedSize(28, 28)
            btn_remover.setCursor(Qt.PointingHandCursor)
            btn_remover.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #71717a;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    color: #ef4444;
                    background-color: rgba(239, 68, 68, 0.1);
                    border-radius: 14px;
                }
            """)
            btn_remover.clicked.connect(lambda checked=False, n=nome: self.remover_casa(n))
            top_bar.addWidget(btn_remover)
            
            card_layout.addLayout(top_bar)
            
            # --- NOME DA CASA ---
            lbl_nome = QLabel(nome)
            lbl_nome.setAlignment(Qt.AlignCenter)
            lbl_nome.setStyleSheet("font-size: 22px; font-weight: bold; color: #f4f4f5; border: none; background: transparent;")
            card_layout.addWidget(lbl_nome)
            
            card_layout.addStretch()

            # Posicionamento na grade (3 colunas)
            self.grid_lay.addWidget(card, i // 3, i % 3)

    def atualizar_dados(self):
        # Quando entra na aba, atualiza a lista de auto-completar com casas novas
        self.lista_casas_db = [c[0] for c in database.listar_casas_com_saldo()]
        self.completer.model().setStringList(self.lista_casas_db)
        self.renderizar_grid()