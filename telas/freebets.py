from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QDialog)
from PySide6.QtCore import Qt
from core import database
from telas.procedimentos import DialogNovoProcedimento

class TelaFreebets(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        topo = QHBoxLayout()
        titulo = QLabel("Gestão de Freebets")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;") 
        topo.addWidget(titulo)
        layout.addLayout(topo)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #282c38; background-color: #1a1d2d; border-radius: 5px; }
            QTabBar::tab { background: #161925; color: #7b849b; padding: 10px 20px; border: 1px solid #282c38; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: bold;}
            QTabBar::tab:selected { background: #1a1d2d; color: #00e676; border-bottom: 2px solid #00e676; }
        """)

        # -- ABA 1: DISPONÍVEIS --
        aba_disponiveis = QWidget()
        layout_disp = QVBoxLayout(aba_disponiveis)
        self.tab_ativas = QTableWidget(0, 5)
        self.tab_ativas.setHorizontalHeaderLabels(["Data Coleta", "Casa", "Valor Freebet", "Lucro | Perda", "Ação"])
        self.tab_ativas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab_ativas.verticalHeader().setVisible(False)
        self.tab_ativas.setEditTriggers(QTableWidget.NoEditTriggers) 
        
        # Hover Linha
        self.tab_ativas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab_ativas.setSelectionMode(QTableWidget.SingleSelection) 
        self.tab_ativas.setStyleSheet("""
            QTableWidget { background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38; outline: none; }
            QTableWidget::item:selected { background-color: #282c38; }
        """)
        self.tab_ativas.setMouseTracking(True)
        self.tab_ativas.cellEntered.connect(lambda r, c: self.tab_ativas.selectRow(r))
        layout_disp.addWidget(self.tab_ativas)
        self.abas.addTab(aba_disponiveis, "Freebets Disponíveis")

        # -- ABA 2: CONVERTIDAS --
        aba_convertidas = QWidget()
        layout_conv = QVBoxLayout(aba_convertidas)
        self.tab_convertidas = QTableWidget(0, 6)
        self.tab_convertidas.setHorizontalHeaderLabels(["Datas (Col / Conv)", "Casa", "Valor Freebet", "Lucro Coleta", "Lucro Conversão", "Lucro Total"])
        self.tab_convertidas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab_convertidas.verticalHeader().setVisible(False)
        self.tab_convertidas.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Hover Linha
        self.tab_convertidas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tab_convertidas.setSelectionMode(QTableWidget.SingleSelection)
        self.tab_convertidas.setStyleSheet("""
            QTableWidget { background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38; outline: none; }
            QTableWidget::item:selected { background-color: #282c38; }
        """)
        self.tab_convertidas.setMouseTracking(True)
        self.tab_convertidas.cellEntered.connect(lambda r, c: self.tab_convertidas.selectRow(r))
        layout_conv.addWidget(self.tab_convertidas)
        self.abas.addTab(aba_convertidas, "Histórico de Conversões")

        layout.addWidget(self.abas)

    def carregar_freebets_ativas(self):
        self.tab_ativas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, data_operacao, casa_destino_freebet, valor_freebet_coletada, lucro_final, bateu_duplo
            FROM Procedimentos_Historico 
            WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'
        """)
        
        for row, (id_op, data, casa, valor, lucro_base, bateu) in enumerate(cursor.fetchall()):
            self.tab_ativas.insertRow(row)
            lucro_real = lucro_base + (valor if bateu else 0)
            
            def item(t, c=None):
                if t == "None" or t is None or t == "": t = "---"
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                it.setToolTip(str(t)) # Tooltip de Expansão
                if c: it.setForeground(c)
                return it

            self.tab_ativas.setItem(row, 0, item(data))
            self.tab_ativas.setItem(row, 1, item(casa))
            self.tab_ativas.setItem(row, 2, item(f"R$ {valor:.2f}", Qt.yellow))
            self.tab_ativas.setItem(row, 3, item(f"R$ {lucro_real:.2f}", Qt.red if lucro_real < 0 else Qt.green))

            container_btn = QWidget()
            lay_btn = QHBoxLayout(container_btn)
            lay_btn.setContentsMargins(20, 2, 20, 2)
            btn_usar = QPushButton("Converter")
            btn_usar.setCursor(Qt.PointingHandCursor)
            btn_usar.setStyleSheet("background-color: #282c38; color: #ffb300; font-weight: bold; border: 1px solid #ffb300; border-radius: 4px; padding: 5px;")
            btn_usar.clicked.connect(lambda _, i=id_op, c=casa: self.abrir_popup_conversao(i, c))
            lay_btn.addWidget(btn_usar)
            self.tab_ativas.setCellWidget(row, 4, container_btn)
        
        conexao.close()
        self.carregar_freebets_convertidas()

    def abrir_popup_conversao(self, id_origem, casa_origem):
        modal = DialogNovoProcedimento(self)
        modal.selecionar_tipo("Converter Freebet")
        
        if casa_origem and casa_origem != "None" and casa_origem != "---":
            modal.lbl_casas_selecionadas.setText(casa_origem)
            modal.lbl_casas_selecionadas.setStyleSheet("color: #00e676; font-weight: bold;")

        if modal.exec() == QDialog.Accepted:
            dados_novos = modal.dados_finais
            database.salvar_conversao_freebet(dados_novos, id_origem)
            self.carregar_freebets_ativas()

    def carregar_freebets_convertidas(self):
        self.tab_convertidas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT 
                c.data_operacao, v.data_operacao, c.casa_destino_freebet, 
                c.valor_freebet_coletada, c.lucro_final, c.bateu_duplo,
                v.lucro_final, v.valor_freebet_coletada, v.bateu_duplo
            FROM Procedimentos_Historico c
            INNER JOIN Procedimentos_Historico v ON v.id_freebet_origem = c.id
            WHERE c.tipo_procedimento = 'Coletar Freebet' AND c.status_freebet = 'Usada'
        """)

        for row, (data_col, data_conv, casa, valor_fb, l_col_base, b_col, l_conv_base, val_conv, b_conv) in enumerate(cursor.fetchall()):
            self.tab_convertidas.insertRow(row)
            
            lucro_col_real = l_col_base + (valor_fb if b_col else 0)
            lucro_conv_real = l_conv_base + (val_conv if b_conv else 0)
            lucro_total = lucro_col_real + lucro_conv_real
            
            def item(t, c=None, bold=False):
                if t == "None" or t is None or t == "": t = "---"
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                it.setToolTip(str(t)) # Tooltip de Expansão
                if c: it.setForeground(c)
                if bold:
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
                return it

            datas = f"{data_col} ➔ {data_conv}"
            self.tab_convertidas.setItem(row, 0, item(datas))
            self.tab_convertidas.setItem(row, 1, item(casa))
            self.tab_convertidas.setItem(row, 2, item(f"R$ {valor_fb:.2f}", Qt.yellow))
            self.tab_convertidas.setItem(row, 3, item(f"R$ {lucro_col_real:.2f}", Qt.red if lucro_col_real < 0 else Qt.green))
            self.tab_convertidas.setItem(row, 4, item(f"R$ {lucro_conv_real:.2f}", Qt.red if lucro_conv_real < 0 else Qt.green))
            self.tab_convertidas.setItem(row, 5, item(f"R$ {lucro_total:.2f}", Qt.green if lucro_total >= 0 else Qt.red, bold=True))

        conexao.close()