from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QTabWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from core import database
from telas.procedimentos import TabelaProcedimentos, DialogNovoProcedimento

COR_VERDE = "#34d399"
COR_VERMELHO = "#f87171"

class TelaFreebets(QWidget):
    
    sinal_converter_calculadora = Signal(str, float, list)
    
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

        # ABA 1: DISPONÍVEIS
        aba_disponiveis = QWidget()
        layout_disp = QVBoxLayout(aba_disponiveis)
        layout_disp.setContentsMargins(0,0,0,0)
        self.tab_ativas = TabelaProcedimentos(0, 5)
        self.tab_ativas.setHorizontalHeaderLabels(["Qtd", "Casa Agrupada", "Valor Total", "Lucro Base Total", ""]) 
        self.configurar_tabela(self.tab_ativas, tem_acao=True)
        layout_disp.addWidget(self.tab_ativas)
        self.abas.addTab(aba_disponiveis, "Disponíveis")

        # ABA 2: HISTÓRICO
        aba_convertidas = QWidget()
        layout_conv = QVBoxLayout(aba_convertidas)
        layout_conv.setContentsMargins(0,0,0,0)
        self.tab_convertidas = TabelaProcedimentos(0, 6)
        self.tab_convertidas.setHorizontalHeaderLabels(["Data (Col ➔ Conv)", "Casa", "Valor FB", "Lucro Base", "Lucro Final", "Total"])
        self.configurar_tabela(self.tab_convertidas) # Sem ação de botões extras
        layout_conv.addWidget(self.tab_convertidas)
        self.abas.addTab(aba_convertidas, "Histórico")

        layout.addWidget(self.abas)

    def configurar_tabela(self, tabela, tem_acao=False):
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if tem_acao:
            ultima_coluna = tabela.columnCount() - 1
            tabela.horizontalHeader().setSectionResizeMode(ultima_coluna, QHeaderView.Fixed)
            tabela.setColumnWidth(ultima_coluna, 90)

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
        cursor.execute("SELECT id, data_operacao, casa_destino_freebet, valor_da_freebet, lucro_final, bateu_duplo, valor_freebet_coletada FROM Procedimentos_Historico WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'")
        
        casas_agrupadas = {}
        for id_op, data, casa, valor_fb, lucro_base, bateu, v_duplo in cursor.fetchall():
            valor_fb = valor_fb or 0.0
            v_duplo = v_duplo or 0.0
            
            if not casa or casa == "None": 
                casa = "Desconhecida"
                
            if casa not in casas_agrupadas:
                casas_agrupadas[casa] = {'ids': [], 'valor_total': 0.0, 'lucro_total': 0.0}
            
            lucro_real = lucro_base + (v_duplo if bateu else 0)
            casas_agrupadas[casa]['ids'].append(id_op)
            casas_agrupadas[casa]['valor_total'] += valor_fb
            casas_agrupadas[casa]['lucro_total'] += lucro_real

        for row, (casa, dados) in enumerate(casas_agrupadas.items()):
            self.tab_ativas.insertRow(row)
            
            def item(t, cor=None):
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                if cor: it.setForeground(QBrush(QColor(cor)))
                return it

            self.tab_ativas.setItem(row, 0, item(f"{len(dados['ids'])}"))
            self.tab_ativas.setItem(row, 1, item(casa))
            self.tab_ativas.setItem(row, 2, item(f"R$ {dados['valor_total']:.2f}")) 
            self.tab_ativas.setItem(row, 3, item(f"R$ {dados['lucro_total']:.2f}", COR_VERDE if dados['lucro_total'] >= 0 else COR_VERMELHO))

            container_btn = QWidget()
            lay_btn = QHBoxLayout(container_btn)
            lay_btn.setContentsMargins(5, 2, 5, 2)
            btn_usar = QPushButton("Converter")
            btn_usar.setCursor(Qt.PointingHandCursor)
            btn_usar.setStyleSheet("""
                QPushButton { background-color: #f4f4f5; color: #09090b; font-weight: bold; border-radius: 6px; padding: 4px; font-size: 12px; }
                QPushButton:hover { background-color: #d4d4d8; }
            """)
            btn_usar.clicked.connect(lambda _, c=casa, v=dados['valor_total'], ids=dados['ids']: self.sinal_converter_calculadora.emit(c, v, ids))
            lay_btn.addWidget(btn_usar)
            self.tab_ativas.setCellWidget(row, 4, container_btn)
        
        conexao.close(); self.carregar_freebets_convertidas()

    def carregar_freebets_convertidas(self):
        self.tab_convertidas.setRowCount(0)
        conexao = database.conectar(); cursor = conexao.cursor()
        
        cursor.execute("""
            SELECT c.data_operacao, v.data_operacao, c.casa_destino_freebet, c.valor_da_freebet, c.lucro_final, c.bateu_duplo, c.valor_freebet_coletada, v.lucro_final, v.valor_da_freebet, v.bateu_duplo, v.valor_freebet_coletada
            FROM Procedimentos_Historico c INNER JOIN Procedimentos_Historico v ON v.id_freebet_origem = c.id
            WHERE c.tipo_procedimento = 'Coletar Freebet' AND c.status_freebet = 'Usada'
        """)

        for row, (data_col, data_conv, casa, v_fb_col, l_col_base, b_col, v_dup_col, l_conv_base, v_fb_conv, b_conv, v_dup_conv) in enumerate(cursor.fetchall()):
            v_fb_col = v_fb_col or 0.0
            v_dup_col = v_dup_col or 0.0
            v_dup_conv = v_dup_conv or 0.0
            
            self.tab_convertidas.insertRow(row)
            lucro_col_real = l_col_base + (v_dup_col if b_col else 0)
            lucro_conv_real = l_conv_base + (v_dup_conv if b_conv else 0)
            lucro_total = lucro_col_real + lucro_conv_real
            
            def item(t, cor=None, bold=False):
                it = QTableWidgetItem(str(t) if t not in ["None", None, ""] else "-")
                it.setTextAlignment(Qt.AlignCenter)
                if cor: it.setForeground(QBrush(QColor(cor)))
                if bold: f = it.font(); f.setBold(True); it.setFont(f)
                return it

            self.tab_convertidas.setItem(row, 0, item(f"{data_col} ➔ {data_conv}"))
            item_casa = item(casa)
            item_casa.setToolTip(casa)
            self.tab_convertidas.setItem(row, 1, item_casa)
            self.tab_convertidas.setItem(row, 2, item(f"R$ {v_fb_col:.2f}"))
            self.tab_convertidas.setItem(row, 3, item(f"R$ {lucro_col_real:.2f}", COR_VERDE if lucro_col_real >= 0 else COR_VERMELHO))
            self.tab_convertidas.setItem(row, 4, item(f"R$ {lucro_conv_real:.2f}", COR_VERDE if lucro_conv_real >= 0 else COR_VERMELHO))
            self.tab_convertidas.setItem(row, 5, item(f"R$ {lucro_total:.2f}", COR_VERDE if lucro_total >= 0 else COR_VERMELHO, bold=True))

        conexao.close()