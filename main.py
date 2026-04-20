import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QStackedWidget, QLabel)
from PySide6.QtCore import Qt
from telas.procedimentos import TelaProcedimentos
from telas.dashboard import TelaDashboard
from telas.historico import TelaHistorico
from telas.freebets import TelaFreebets
from core import database

database.criar_tabelas()
database.atualizar_schema()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configurações básicas da janela
        self.setWindowTitle("Gerenciador de Procedimentos")
        self.resize(1200, 800) # Tamanho inicial excelente para dashboards
        
        # Central Widget e Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remove margens para colar no topo
        main_layout.setSpacing(0)

        # --- Top Bar (Menu Superior) ---
        top_bar = QWidget()
        top_bar.setObjectName("topBar") # Nomeado para aplicar o CSS depois
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_bar_layout.setAlignment(Qt.AlignCenter)
        top_bar_layout.setContentsMargins(30, 15, 30, 15)
        top_bar_layout.setSpacing(30)

        # Criando os Botões do Menu
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_procedimentos = QPushButton("Procedimentos")
        self.btn_historico = QPushButton("Histórico")
        self.btn_freebets = QPushButton("Freebets")

        # Configurando os botões para agirem como "abas" (ficam marcados quando clicados)
        self.btn_dashboard.setCheckable(True)
        self.btn_procedimentos.setCheckable(True)
        self.btn_historico.setCheckable(True)
        self.btn_freebets.setCheckable(True)

        # Adicionando os botões na barra superior
        top_bar_layout.addWidget(self.btn_dashboard)
        top_bar_layout.addWidget(self.btn_procedimentos)
        top_bar_layout.addWidget(self.btn_historico)
        top_bar_layout.addWidget(self.btn_freebets)

        # --- Gerenciador de Telas (Stacked Widget) ---
        # Isso permite trocar de tela sem abrir novas janelas
        self.telas = QStackedWidget()
        

        self.tela_dashboard = TelaDashboard()
        self.tela_procedimentos = TelaProcedimentos()
        self.tela_historico = TelaHistorico()
        self.tela_freebets = TelaFreebets()

        # Adicionando as telas ao gerenciador
        self.telas.addWidget(self.tela_dashboard)
        self.telas.addWidget(self.tela_procedimentos)
        self.telas.addWidget(self.tela_historico)
        self.telas.addWidget(self.tela_freebets)

        # Montando o Layout Final (Barra em cima, Telas em baixo)
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.telas)

        # --- Conectando os Botões e Lógica de Navegação ---
        self.btn_dashboard.clicked.connect(lambda: self.mudar_tela(self.btn_dashboard, self.tela_dashboard))
        self.btn_procedimentos.clicked.connect(lambda: self.mudar_tela(self.btn_procedimentos, self.tela_procedimentos))
        self.btn_historico.clicked.connect(lambda: self.mudar_tela(self.btn_historico, self.tela_historico))
        self.btn_freebets.clicked.connect(lambda: self.mudar_tela(self.btn_freebets, self.tela_freebets))

        # Aplica o Estilo Visual (Dark Mode)
        self.aplicar_estilo()
        
        # Inicia na aba Dashboard
        self.mudar_tela(self.btn_dashboard, self.tela_dashboard)

    def mudar_tela(self, botao_ativo, tela_alvo):
        """Muda a tela ativa e atualiza o visual dos botões."""
        # Desmarca todos
        self.btn_dashboard.setChecked(False)
        self.btn_procedimentos.setChecked(False)
        self.btn_historico.setChecked(False)
        
        
        # Marca o clicado e muda a tela
        botao_ativo.setChecked(True)
        self.telas.setCurrentWidget(tela_alvo)

    def aplicar_estilo(self):
        """Aqui fica o 'CSS' do nosso aplicativo Python."""
        estilo = """
        QMainWindow {
            background-color: #0f111a; /* Fundo principal super escuro e moderno */
        }
        #topBar {
            background-color: #161925; /* Fundo da barra superior */
            border-bottom: 1px solid #282c38;
        }
        QPushButton {
            background-color: transparent;
            color: #7b849b; /* Cor do texto inativo */
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            padding: 8px 10px;
            border: none;
            border-bottom: 3px solid transparent; /* Preparando para a linha verde */
        }
        QPushButton:hover {
            color: #ffffff; /* Fica branco ao passar o mouse */
        }
        QPushButton:checked {
            color: #00e676; /* Verde vibrante quando ativo */
            border-bottom: 3px solid #00e676; /* Linha verde embaixo */
        }
        #textoPlaceholder {
            color: #4a536b;
            font-size: 24px;
            font-weight: bold;
        }
        """
        self.setStyleSheet(estilo)
        
    def mudar_tela(self, botao_ativo, tela_alvo):
        """Muda a tela ativa e atualiza os dados se for o Dashboard."""
        self.btn_dashboard.setChecked(False)
        self.btn_procedimentos.setChecked(False)
        self.btn_historico.setChecked(False)
        self.btn_freebets.setChecked(False)
        
        botao_ativo.setChecked(True)
        self.telas.setCurrentWidget(tela_alvo)

        # Atualiza a tela de Dashboard toda vez que entrar nela
        if tela_alvo == self.tela_dashboard:
            self.tela_dashboard.atualizar_dados()
        # Atualiza a tabela de Procedimentos toda vez que entrar nela
        elif tela_alvo == self.tela_procedimentos:
            self.tela_procedimentos.carregar_tabela()
        elif tela_alvo == self.tela_historico:
            self.tela_historico.atualizar_lista_meses()
        elif tela_alvo == self.tela_freebets:
            self.tela_freebets.carregar_freebets_ativas()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())