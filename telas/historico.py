from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor, QBrush
from core import database
from telas.procedimentos import TabelaProcedimentos

COR_VERDE = "#34d399"
COR_VERMELHO = "#f87171"

class TelaHistorico(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(25)

        topo_layout = QHBoxLayout()
        lbl_titulo = QLabel("Arquivo Histórico")
        lbl_titulo.setStyleSheet("color: #f4f4f5; font-size: 22px; font-weight: bold;")
        
        self.combo_meses = QComboBox()
        self.combo_meses.setMinimumWidth(150)
        self.combo_meses.setStyleSheet("background-color: #18181b; color: #f4f4f5; padding: 10px; border: none; border-radius: 8px; outline: none;")
        self.combo_meses.currentTextChanged.connect(self.carregar_dados_historicos)

        topo_layout.addWidget(lbl_titulo)
        topo_layout.addStretch()
        topo_layout.addWidget(self.combo_meses)
        layout.addLayout(topo_layout)

        self.card_resumo = QFrame()
        self.card_resumo.setStyleSheet("background-color: #18181b; border-radius: 16px; border: none;")
        self.card_resumo.setFixedHeight(120)
        layout_resumo = QVBoxLayout(self.card_resumo)
        layout_resumo.setContentsMargins(20,20,20,20)
        
        lbl_desc = QLabel("LUCRO NO PERÍODO")
        lbl_desc.setStyleSheet("color: #71717a; font-size: 13px; font-weight: bold;")
        lbl_desc.setAlignment(Qt.AlignCenter)
        
        self.lbl_lucro_total = QLabel("R$ 0.00")
        self.lbl_lucro_total.setAlignment(Qt.AlignCenter)
        
        layout_resumo.addWidget(lbl_desc)
        layout_resumo.addWidget(self.lbl_lucro_total)
        layout.addWidget(self.card_resumo)

        self.tabela = TabelaProcedimentos(0, 6)
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Jogo", "Casas", "Lucro Base", "Lucro Final"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SingleSelection) 
        
        self.tabela.setFocusPolicy(Qt.NoFocus)
        self.tabela.setShowGrid(False)
        self.tabela.setMouseTracking(True)
        
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: transparent; color: #f4f4f5; border: none; gridline-color: transparent; font-size: 14px; outline: none; }
            QTableWidget::item { border: none; border-bottom: 1px solid rgba(255,255,255,0.03); padding: 5px; }
            QTableWidget::item:selected { background-color: rgba(255,255,255,0.04); color: #f4f4f5; }
            QHeaderView::section { background-color: transparent; color: #71717a; font-weight: bold; border: none; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 12px 8px; }
            QHeaderView::section:hover { background-color: transparent; }
        """)
        layout.addWidget(self.tabela)

    def atualizar_lista_meses(self):
        self.combo_meses.blockSignals(True)
        self.combo_meses.clear()
        meses = database.listar_meses_disponiveis()
        self.combo_meses.addItems(meses)
        self.combo_meses.blockSignals(False)
        if meses: self.carregar_dados_historicos(meses[0])

    def carregar_dados_historicos(self, mes_ref):
        if not mes_ref: return
        self.tabela.setRowCount(0)
        registros = database.buscar_dados_mes(mes_ref)
        lucro_acumulado = 0.0

        for row, reg in enumerate(registros):
            data, tipo, jogo, casas, lucro_base, v_duplo, bateu = reg
            self.tabela.insertRow(row)
            l_final = lucro_base + (v_duplo if bateu else 0)
            lucro_acumulado += l_final
            
            def item(t, cor=None):
                it = QTableWidgetItem(str(t) if t not in ["None", None, ""] else "---")
                it.setTextAlignment(Qt.AlignCenter)
                if cor: it.setForeground(QBrush(QColor(cor)))
                return it

            self.tabela.setItem(row, 0, item(data))
            self.tabela.setItem(row, 1, item(tipo))
            self.tabela.setItem(row, 2, item(jogo))
            
            item_casas = item(casas)
            item_casas.setToolTip(casas)
            self.tabela.setItem(row, 3, item_casas)
            
            self.tabela.setItem(row, 4, item(f"R$ {lucro_base:.2f}"))
            self.tabela.setItem(row, 5, item(f"R$ {l_final:.2f}", COR_VERDE if l_final >= 0 else COR_VERMELHO))

        cor_total = COR_VERDE if lucro_acumulado >= 0 else COR_VERMELHO
        self.lbl_lucro_total.setText(f"R$ {lucro_acumulado:.2f}")
        self.lbl_lucro_total.setStyleSheet(f"color: {cor_total}; font-size: 32px; font-weight: bold;")