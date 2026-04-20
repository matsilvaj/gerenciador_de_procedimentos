from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QDialog)
from PySide6.QtCore import Qt
from core import database
from telas.procedimentos import DialogNovoProcedimento # Importamos o seu Pop-up!

class TelaFreebets(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        topo = QHBoxLayout()
        titulo = QLabel("Gestão de Freebets")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffb300;") 
        topo.addWidget(titulo)
        layout.addLayout(topo)

        # --- Sistema de Abas ---
        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #282c38; background-color: #1a1d2d; border-radius: 5px; }
            QTabBar::tab { background: #161925; color: #7b849b; padding: 10px 20px; border: 1px solid #282c38; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: bold;}
            QTabBar::tab:selected { background: #1a1d2d; color: #ffb300; border-bottom: 2px solid #ffb300; }
        """)

        # -- ABA 1: DISPONÍVEIS --
        aba_disponiveis = QWidget()
        layout_disp = QVBoxLayout(aba_disponiveis)
        self.tab_ativas = QTableWidget(0, 5)
        self.tab_ativas.setHorizontalHeaderLabels(["Data Coleta", "Casa", "Valor Freebet", "Lucro | Perda", "Ação"])
        self.tab_ativas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab_ativas.verticalHeader().setVisible(False)
        self.tab_ativas.setStyleSheet("background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38;")
        layout_disp.addWidget(self.tab_ativas)
        self.abas.addTab(aba_disponiveis, "Freebets Disponíveis")

        # -- ABA 2: CONVERTIDAS --
        aba_convertidas = QWidget()
        layout_conv = QVBoxLayout(aba_convertidas)
        self.tab_convertidas = QTableWidget(0, 6)
        self.tab_convertidas.setHorizontalHeaderLabels(["Datas (Col / Conv)", "Casa", "Valor Freebet", "Lucro | Perda", "Lucro Conversão", "Lucro Total"])
        self.tab_convertidas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab_convertidas.verticalHeader().setVisible(False)
        self.tab_convertidas.setStyleSheet("background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38;")
        layout_conv.addWidget(self.tab_convertidas)
        self.abas.addTab(aba_convertidas, "Histórico de Conversões")

        layout.addWidget(self.abas)

    def carregar_freebets_ativas(self):
        """Busca as freebets pendentes e atualiza também a aba de convertidas."""
        self.tab_ativas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, data_operacao, casa_destino_freebet, valor_freebet_coletada, lucro_final
            FROM Procedimentos_Historico 
            WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'
        """)
        
        for row, (id_op, data, casa, valor, lucro_coleta) in enumerate(cursor.fetchall()):
            self.tab_ativas.insertRow(row)
            
            def item(t, c=None):
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                if c: it.setForeground(c)
                return it

            self.tab_ativas.setItem(row, 0, item(data))
            self.tab_ativas.setItem(row, 1, item(casa))
            self.tab_ativas.setItem(row, 2, item(f"R$ {valor:.2f}", Qt.yellow))
            self.tab_ativas.setItem(row, 3, item(f"R$ {lucro_coleta:.2f}", Qt.red if lucro_coleta < 0 else Qt.green))

            # O Botão que abre o Pop-up inteligente
            btn_usar = QPushButton("Converter")
            btn_usar.setCursor(Qt.PointingHandCursor)
            btn_usar.setStyleSheet("background-color: #282c38; color: #ffb300; font-weight: bold; border: 1px solid #ffb300; border-radius: 4px;")
            btn_usar.clicked.connect(lambda _, i=id_op, c=casa: self.abrir_popup_conversao(i, c))
            self.tab_ativas.setCellWidget(row, 4, btn_usar)
        
        conexao.close()
        self.carregar_freebets_convertidas()

    def abrir_popup_conversao(self, id_origem, casa_origem):
        """Abre o Pop-up de Procedimentos já preenchido."""
        modal = DialogNovoProcedimento(self)
        
        # Preenche os campos automaticamente
        modal.selecionar_tipo("Converter Freebet")
        
        # Tenta selecionar a casa na caixinha, se não existir, ele escreve
        if modal.combo_casas.findText(casa_origem) >= 0:
            modal.combo_casas.setCurrentText(casa_origem)
        else:
            modal.combo_casas.addItem(casa_origem)
            modal.combo_casas.setCurrentText(casa_origem)

        if modal.exec() == QDialog.Accepted:
            dados_novos = modal.dados_finais
            database.salvar_conversao_freebet(dados_novos, id_origem)
            self.carregar_freebets_ativas() # Recarrega as duas tabelas

    def carregar_freebets_convertidas(self):
        """Cruza os dados da Coleta com a Conversão e calcula o Lucro Total."""
        self.tab_convertidas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()
        
        # O SQL faz um JOIN entre a Coleta Original (c) e a Conversão Nova (v)
        cursor.execute("""
            SELECT 
                c.data_operacao, v.data_operacao, c.casa_destino_freebet, 
                c.valor_freebet_coletada, c.lucro_final, v.lucro_final
            FROM Procedimentos_Historico c
            INNER JOIN Procedimentos_Historico v ON v.id_freebet_origem = c.id
            WHERE c.tipo_procedimento = 'Coletar Freebet' AND c.status_freebet = 'Usada'
        """)

        for row, (data_col, data_conv, casa, valor_fb, lucro_col, lucro_conv) in enumerate(cursor.fetchall()):
            self.tab_convertidas.insertRow(row)
            
            def item(t, c=None, bold=False):
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                if c: it.setForeground(c)
                if bold:
                    f = it.font()
                    f.setBold(True)
                    it.setFont(f)
                return it

            lucro_total = lucro_col + lucro_conv

            datas = f"{data_col} ➔ {data_conv}"
            self.tab_convertidas.setItem(row, 0, item(datas))
            self.tab_convertidas.setItem(row, 1, item(casa))
            self.tab_convertidas.setItem(row, 2, item(f"R$ {valor_fb:.2f}", Qt.yellow))
            self.tab_convertidas.setItem(row, 3, item(f"R$ {lucro_col:.2f}", Qt.red if lucro_col < 0 else Qt.green))
            self.tab_convertidas.setItem(row, 4, item(f"R$ {lucro_conv:.2f}", Qt.red if lucro_conv < 0 else Qt.green))
            self.tab_convertidas.setItem(row, 5, item(f"R$ {lucro_total:.2f}", Qt.green if lucro_total >= 0 else Qt.red, bold=True))

        conexao.close()