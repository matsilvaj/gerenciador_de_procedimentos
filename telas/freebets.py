from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QDialog)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor, QBrush
from core import database
from telas.procedimentos import TabelaProcedimentos, DialogNovoProcedimento

COR_VERDE = "#34d399"
COR_VERMELHO = "#f87171"

class TelaFreebets(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)

        topo = QHBoxLayout()
        titulo = QLabel("Gestão de Freebets")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #f4f4f5;") 
        topo.addWidget(titulo)
        layout.addLayout(topo)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: transparent; }
            QTabBar::tab { background: transparent; color: #71717a; padding: 10px 20px; border: none; font-weight: bold; font-size: 14px; margin-bottom: 20px;}
            QTabBar::tab:selected { color: #3b82f6; }
        """)

        aba_disponiveis = QWidget()
        layout_disp = QVBoxLayout(aba_disponiveis)
        layout_disp.setContentsMargins(0,0,0,0)
        self.tab_ativas = TabelaProcedimentos(0, 5)
        self.tab_ativas.setHorizontalHeaderLabels(["Coleta", "Casa", "Valor", "Lucro Base", ""]) 
        self.configurar_tabela(self.tab_ativas, tem_acao=True)
        layout_disp.addWidget(self.tab_ativas)
        self.abas.addTab(aba_disponiveis, "Disponíveis")

        aba_convertidas = QWidget()
        layout_conv = QVBoxLayout(aba_convertidas)
        layout_conv.setContentsMargins(0,0,0,0)
        self.tab_convertidas = TabelaProcedimentos(0, 6)
        self.tab_convertidas.setHorizontalHeaderLabels(["Data (Col ➔ Conv)", "Casa", "Valor FB", "Lucro Base", "Lucro Final", "Total"])
        self.configurar_tabela(self.tab_convertidas)
        layout_conv.addWidget(self.tab_convertidas)
        self.abas.addTab(aba_convertidas, "Histórico")

        layout.addWidget(self.abas)

    def configurar_tabela(self, tabela, tem_acao=False):
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if tem_acao:
            tabela.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
            tabela.setColumnWidth(4, 90)

        tabela.verticalHeader().setVisible(False)
        tabela.verticalHeader().setDefaultSectionSize(75)
        tabela.setEditTriggers(QTableWidget.NoEditTriggers) 
        tabela.setSelectionBehavior(QTableWidget.SelectRows)
        tabela.setSelectionMode(QTableWidget.NoSelection)
        
        tabela.setFocusPolicy(Qt.NoFocus)
        tabela.setShowGrid(False)
        tabela.setMouseTracking(True)
        
        tabela.setStyleSheet("""
            QTableWidget { background-color: transparent; color: #f4f4f5; border: none; outline: none; font-size: 14px; }
            QTableWidget::item { border: none; border-bottom: 1px solid rgba(255,255,255,0.03); padding: 5px; }
            QTableWidget::item:selected { background-color: transparent; color: #f4f4f5; border: none; }
            QHeaderView::section { background-color: transparent; color: #71717a; font-weight: bold; border: none; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 12px 8px; }
        """)

    def carregar_freebets_ativas(self):
        self.tab_ativas.setRowCount(0)
        conexao = database.conectar(); cursor = conexao.cursor()
        cursor.execute("SELECT id, data_operacao, casa_destino_freebet, valor_freebet_coletada, lucro_final, bateu_duplo FROM Procedimentos_Historico WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'")
        
        for row, (id_op, data, casa, valor, lucro_base, bateu) in enumerate(cursor.fetchall()):
            self.tab_ativas.insertRow(row)
            lucro_real = lucro_base + (valor if bateu else 0)
            
            def item(t, cor=None):
                it = QTableWidgetItem(str(t) if t not in ["None", None, ""] else "---")
                it.setTextAlignment(Qt.AlignCenter)
                if cor: it.setForeground(QBrush(QColor(cor)))
                return it

            self.tab_ativas.setItem(row, 0, item(data))
            item_casa = item(casa)
            item_casa.setToolTip(casa)
            self.tab_ativas.setItem(row, 1, item_casa)
            self.tab_ativas.setItem(row, 2, item(f"R$ {valor:.2f}")) 
            self.tab_ativas.setItem(row, 3, item(f"R$ {lucro_real:.2f}", COR_VERDE if lucro_real >= 0 else COR_VERMELHO))

            container_btn = QWidget()
            lay_btn = QHBoxLayout(container_btn)
            lay_btn.setContentsMargins(5, 2, 5, 2)
            btn_usar = QPushButton("Converter")
            btn_usar.setCursor(Qt.PointingHandCursor)
            btn_usar.setStyleSheet("""
                QPushButton { background-color: #f4f4f5; color: #09090b; font-weight: bold; border-radius: 6px; padding: 4px; font-size: 12px; }
                QPushButton:hover { background-color: #d4d4d8; }
            """)
            btn_usar.clicked.connect(lambda _, i=id_op, c=casa: self.abrir_popup_conversao(i, c))
            lay_btn.addWidget(btn_usar)
            self.tab_ativas.setCellWidget(row, 4, container_btn)
        
        conexao.close(); self.carregar_freebets_convertidas()

    def abrir_popup_conversao(self, id_origem, casa_origem):
        modal = DialogNovoProcedimento(self)
        modal.selecionar_tipo("Converter Freebet")
        if casa_origem and casa_origem not in ["None", "---"]:
            modal.lbl_casas_selecionadas.setText(casa_origem)
            modal.lbl_casas_selecionadas.setStyleSheet("color: #3b82f6;")
        if modal.exec() == QDialog.Accepted:
            database.salvar_conversao_freebet(modal.dados_finais, id_origem)
            self.carregar_freebets_ativas()

    def carregar_freebets_convertidas(self):
        self.tab_convertidas.setRowCount(0)
        conexao = database.conectar(); cursor = conexao.cursor()
        cursor.execute("""
            SELECT c.data_operacao, v.data_operacao, c.casa_destino_freebet, c.valor_freebet_coletada, c.lucro_final, c.bateu_duplo, v.lucro_final, v.valor_freebet_coletada, v.bateu_duplo
            FROM Procedimentos_Historico c INNER JOIN Procedimentos_Historico v ON v.id_freebet_origem = c.id
            WHERE c.tipo_procedimento = 'Coletar Freebet' AND c.status_freebet = 'Usada'
        """)

        for row, (data_col, data_conv, casa, valor_fb, l_col_base, b_col, l_conv_base, val_conv, b_conv) in enumerate(cursor.fetchall()):
            self.tab_convertidas.insertRow(row)
            lucro_col_real = l_col_base + (valor_fb if b_col else 0)
            lucro_conv_real = l_conv_base + (val_conv if b_conv else 0)
            lucro_total = lucro_col_real + lucro_conv_real
            
            def item(t, cor=None, bold=False):
                it = QTableWidgetItem(str(t) if t not in ["None", None, ""] else "---")
                it.setTextAlignment(Qt.AlignCenter)
                if cor: it.setForeground(QBrush(QColor(cor)))
                if bold: f = it.font(); f.setBold(True); it.setFont(f)
                return it

            self.tab_convertidas.setItem(row, 0, item(f"{data_col} ➔ {data_conv}"))
            item_casa = item(casa)
            item_casa.setToolTip(casa)
            self.tab_convertidas.setItem(row, 1, item_casa)
            self.tab_convertidas.setItem(row, 2, item(f"R$ {valor_fb:.2f}"))
            self.tab_convertidas.setItem(row, 3, item(f"R$ {lucro_col_real:.2f}", COR_VERDE if lucro_col_real >= 0 else COR_VERMELHO))
            self.tab_convertidas.setItem(row, 4, item(f"R$ {lucro_conv_real:.2f}", COR_VERDE if lucro_conv_real >= 0 else COR_VERMELHO))
            self.tab_convertidas.setItem(row, 5, item(f"R$ {lucro_total:.2f}", COR_VERDE if lucro_total >= 0 else COR_VERMELHO, bold=True))
        conexao.close()