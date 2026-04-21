import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QStackedWidget)
from PySide6.QtCore import Qt
from telas.procedimentos import TelaProcedimentos
from telas.dashboard import TelaDashboard
from telas.historico import TelaHistorico
from telas.freebets import TelaFreebets
from telas.casas_apostas import TelaCasasApostas
from telas.calculadora import TelaCalculadora
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

        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setAlignment(Qt.AlignCenter)
        top_bar_layout.setContentsMargins(0, 15, 0, 15)
        top_bar_layout.setSpacing(10)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_procedimentos = QPushButton("Procedimentos")
        self.btn_freebets = QPushButton("Freebets")
        self.btn_casas = QPushButton("Bancas")
        self.btn_calculadora = QPushButton("Calculadora")
        self.btn_historico = QPushButton("Histórico")

        for btn in [self.btn_dashboard, self.btn_procedimentos, self.btn_freebets, self.btn_casas, self.btn_calculadora, self.btn_historico]:
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            top_bar_layout.addWidget(btn)

        self.telas = QStackedWidget()
        self.tela_dashboard = TelaDashboard()
        self.tela_procedimentos = TelaProcedimentos()
        self.tela_freebets = TelaFreebets()
        self.tela_casas = TelaCasasApostas()
        self.tela_calculadora = TelaCalculadora()
        self.tela_historico = TelaHistorico()

        self.telas.addWidget(self.tela_dashboard)
        self.telas.addWidget(self.tela_procedimentos)
        self.telas.addWidget(self.tela_freebets)
        self.telas.addWidget(self.tela_casas)
        self.telas.addWidget(self.tela_calculadora)
        self.telas.addWidget(self.tela_historico)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.telas)

        self.btn_dashboard.clicked.connect(lambda: self.mudar_tela(self.btn_dashboard, self.tela_dashboard))
        self.btn_procedimentos.clicked.connect(lambda: self.mudar_tela(self.btn_procedimentos, self.tela_procedimentos))
        self.btn_freebets.clicked.connect(lambda: self.mudar_tela(self.btn_freebets, self.tela_freebets))
        self.btn_casas.clicked.connect(lambda: self.mudar_tela(self.btn_casas, self.tela_casas))
        self.btn_calculadora.clicked.connect(lambda: self.mudar_tela(self.btn_calculadora, self.tela_calculadora))
        self.btn_historico.clicked.connect(lambda: self.mudar_tela(self.btn_historico, self.tela_historico))

        # Conecta o sinal da aba de freebets para enviar as informações para a calculadora
        self.tela_freebets.sinal_converter_calculadora.connect(self.ir_para_calculadora_com_freebet)

        self.aplicar_estilo()
        self.mudar_tela(self.btn_dashboard, self.tela_dashboard)

    def aplicar_estilo(self):
        estilo = """
        * {
            font-family: 'Inter', 'Segoe UI Variable', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        }
        QMainWindow { background-color: #09090b; }
        #topBar { background-color: #09090b; border-bottom: 1px solid rgba(255,255,255,0.03); }
        QPushButton {
            background-color: transparent;
            color: #a1a1aa;
            font-size: 14px;
            font-weight: 600;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
        }
        QPushButton:hover { background-color: rgba(255,255,255,0.05); color: #f4f4f5; }
        QPushButton:checked {
            background-color: rgba(255,255,255,0.03);
            color: #f4f4f5;
            border: 1px solid rgba(255,255,255,0.05);
        }
        """
        self.setStyleSheet(estilo)

    def ir_para_calculadora_com_freebet(self, casa, valor_total, ids):
        # Preenche as informações na calculadora
        self.tela_calculadora.preencher_dados_freebet(casa, valor_total, ids)
        # Muda para a tela da calculadora
        self.mudar_tela(self.btn_calculadora, self.tela_calculadora)
        
    def mudar_tela(self, botao_ativo, tela_alvo):
        for btn in [self.btn_dashboard, self.btn_procedimentos, self.btn_freebets, self.btn_casas, self.btn_calculadora, self.btn_historico]:
            btn.setChecked(False)
            
        botao_ativo.setChecked(True)
        self.telas.setCurrentWidget(tela_alvo)

        if tela_alvo == self.tela_dashboard: self.tela_dashboard.atualizar_dados()
        elif tela_alvo == self.tela_procedimentos: self.tela_procedimentos.carregar_tabela()
        elif tela_alvo == self.tela_freebets: self.tela_freebets.carregar_freebets_ativas()
        elif tela_alvo == self.tela_casas: self.tela_casas.atualizar_dados()
        elif tela_alvo == self.tela_historico: self.tela_historico.atualizar_lista_meses()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())