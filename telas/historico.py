from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt
from core import database

class TelaHistorico(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- 1. Topo: Seleção de Período ---
        topo_layout = QHBoxLayout()
        lbl_titulo = QLabel("Arquivo Histórico")
        lbl_titulo.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        
        self.combo_meses = QComboBox()
        self.combo_meses.setMinimumWidth(150)
        self.combo_meses.setStyleSheet("background-color: #161925; color: white; padding: 5px; border: 1px solid #282c38;")
        self.combo_meses.currentTextChanged.connect(self.carregar_dados_historicos)

        topo_layout.addWidget(lbl_titulo)
        topo_layout.addStretch()
        topo_layout.addWidget(QLabel("Selecionar Período:"))
        topo_layout.addWidget(self.combo_meses)
        layout.addLayout(topo_layout)

        # --- 2. Card de Resumo do Mês Selecionado ---
        self.card_resumo = QFrame()
        self.card_resumo.setStyleSheet("background-color: #1a1d2d; border-radius: 8px; border: 1px solid #282c38;")
        self.card_resumo.setFixedHeight(100)
        layout_resumo = QVBoxLayout(self.card_resumo)
        
        self.lbl_lucro_total = QLabel("R$ 0.00")
        self.lbl_lucro_total.setStyleSheet("color: #00e676; font-size: 32px; font-weight: bold;")
        self.lbl_lucro_total.setAlignment(Qt.AlignCenter)
        
        lbl_desc = QLabel("LUCRO LÍQUIDO NO PERÍODO")
        lbl_desc.setStyleSheet("color: #7b849b; font-size: 12px; font-weight: bold;")
        lbl_desc.setAlignment(Qt.AlignCenter)
        
        layout_resumo.addWidget(self.lbl_lucro_total)
        layout_resumo.addWidget(lbl_desc)
        layout.addWidget(self.card_resumo)

        # --- 3. Tabela de Registros ---
        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Jogo / Casas", "Lucro Base", "Lucro Final"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setStyleSheet("background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38;")
        layout.addWidget(self.tabela)

    def atualizar_lista_meses(self):
        """Atualiza o dropdown com os meses que existem no banco."""
        self.combo_meses.blockSignals(True)
        self.combo_meses.clear()
        meses = database.listar_meses_disponiveis()
        self.combo_meses.addItems(meses)
        self.combo_meses.blockSignals(False)
        
        if meses:
            self.carregar_dados_historicos(meses[0])

    def carregar_dados_historicos(self, mes_ref):
        if not mes_ref: return
        
        self.tabela.setRowCount(0)
        registros = database.buscar_dados_mes(mes_ref)
        
        lucro_acumulado = 0.0

        for row, reg in enumerate(registros):
            data, tipo, jogo, casas, lucro_base, v_duplo, bateu = reg
            self.tabela.insertRow(row)
            
            # Cálculo do Lucro Final do registro
            l_final = lucro_base + (v_duplo if bateu else 0)
            lucro_acumulado += l_final
            
            def item(t, c=None):
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                if c: it.setForeground(c)
                return it

            self.tabela.setItem(row, 0, item(data))
            self.tabela.setItem(row, 1, item(tipo))
            self.tabela.setItem(row, 2, item(f"{jogo} | {casas}" if jogo else casas))
            self.tabela.setItem(row, 3, item(f"R$ {lucro_base:.2f}"))
            self.tabela.setItem(row, 4, item(f"R$ {l_final:.2f}", Qt.green if l_final >= 0 else Qt.red))

        # Atualiza o Card de Resumo
        self.lbl_lucro_total.setText(f"R$ {lucro_acumulado:.2f}")
        self.lbl_lucro_total.setStyleSheet(f"color: {'#00e676' if lucro_acumulado >= 0 else '#ff5252'}; font-size: 32px; font-weight: bold;")