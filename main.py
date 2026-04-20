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
        self.setWindowTitle("Gerenciador de Procedimentos")
        self.resize(1200, 800) 
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top Bar ---
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_bar_layout.setAlignment(Qt.AlignCenter)
        top_bar_layout.setContentsMargins(30, 15, 30, 15)
        top_bar_layout.setSpacing(30)

        # Criando os Botões na Nova Ordem
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_procedimentos = QPushButton("Procedimentos")
        self.btn_freebets = QPushButton("Freebets") # Invertido
        self.btn_historico = QPushButton("Histórico") # Invertido

        self.btn_dashboard.setCheckable(True)
        self.btn_procedimentos.setCheckable(True)
        self.btn_freebets.setCheckable(True)
        self.btn_historico.setCheckable(True)

        top_bar_layout.addWidget(self.btn_dashboard)
        top_bar_layout.addWidget(self.btn_procedimentos)
        top_bar_layout.addWidget(self.btn_freebets)
        top_bar_layout.addWidget(self.btn_historico)

        # --- Gerenciador de Telas ---
        self.telas = QStackedWidget()

        self.tela_dashboard = TelaDashboard()
        self.tela_procedimentos = TelaProcedimentos()
        self.tela_freebets = TelaFreebets() # Invertido
        self.tela_historico = TelaHistorico() # Invertido

        self.telas.addWidget(self.tela_dashboard)
        self.telas.addWidget(self.tela_procedimentos)
        self.telas.addWidget(self.tela_freebets)
        self.telas.addWidget(self.tela_historico)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.telas)

        # --- Conectando os Cliques ---
        self.btn_dashboard.clicked.connect(lambda: self.mudar_tela(self.btn_dashboard, self.tela_dashboard))
        self.btn_procedimentos.clicked.connect(lambda: self.mudar_tela(self.btn_procedimentos, self.tela_procedimentos))
        self.btn_freebets.clicked.connect(lambda: self.mudar_tela(self.btn_freebets, self.tela_freebets))
        self.btn_historico.clicked.connect(lambda: self.mudar_tela(self.btn_historico, self.tela_historico))

        self.aplicar_estilo()
        self.mudar_tela(self.btn_dashboard, self.tela_dashboard)

    def aplicar_estilo(self):
        estilo = """
        QMainWindow {
            background-color: #0f111a;
        }
        #topBar {
            background-color: #161925;
            border-bottom: 1px solid #282c38;
        }
        QPushButton {
            background-color: transparent;
            color: #7b849b;
            font-size: 16px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
            padding: 8px 10px;
            border: none;
            border-bottom: 3px solid transparent;
        }
        QPushButton:hover {
            color: #ffffff;
        }
        QPushButton:checked {
            color: #00e676;
            border-bottom: 3px solid #00e676;
        }
        """
        self.setStyleSheet(estilo)
        
    def mudar_tela(self, botao_ativo, tela_alvo):
        """Muda a tela ativa e atualiza os dados automaticamente."""
        self.btn_dashboard.setChecked(False)
        self.btn_procedimentos.setChecked(False)
        self.btn_freebets.setChecked(False)
        self.btn_historico.setChecked(False)
        
        botao_ativo.setChecked(True)
        self.telas.setCurrentWidget(tela_alvo)

        # Atualiza a aba que está sendo aberta no momento
        if tela_alvo == self.tela_dashboard:
            self.tela_dashboard.atualizar_dados()
        elif tela_alvo == self.tela_procedimentos:
            self.tela_procedimentos.carregar_tabela()
        elif tela_alvo == self.tela_freebets:
            self.tela_freebets.carregar_freebets_ativas()
        elif tela_alvo == self.tela_historico:
            self.tela_historico.atualizar_lista_meses()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())