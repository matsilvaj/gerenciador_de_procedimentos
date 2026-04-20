from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGridLayout, QFrame, QTabWidget, QComboBox, QPushButton)
from PySide6.QtCore import Qt, QEvent
import pyqtgraph as pg
from datetime import datetime
import calendar
from core import database

class CardMetrica(QFrame):
    def __init__(self, titulo, valor, cor_valor="#ffffff"):
        super().__init__()
        self.setStyleSheet("QFrame { background-color: #1a1d2d; border-radius: 8px; border: 1px solid #282c38; }")
        layout = QVBoxLayout(self)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #7b849b; font-size: 13px; font-weight: bold; text-transform: uppercase;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(f"color: {cor_valor}; font-size: 26px; font-weight: bold;")
        self.lbl_valor.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_titulo)
        layout.addWidget(self.lbl_valor)

class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.mostrar_valor_freebet = False 

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        # --- 1. Topo: Título e Filtro ---
        topo_layout = QHBoxLayout()
        mes_atual_nome = datetime.now().strftime("%m/%Y")
        lbl_titulo = QLabel(f"Visão Geral - {mes_atual_nome}")
        lbl_titulo.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todos", "SureBet", "Tentativa de Duplo", "Coletar Freebet", "Converter Freebet"])
        self.combo_filtro.setStyleSheet("background-color: #161925; color: white; padding: 5px; border: 1px solid #282c38; border-radius: 4px; min-width: 150px;")
        self.combo_filtro.currentTextChanged.connect(self.atualizar_dados)

        topo_layout.addWidget(lbl_titulo)
        topo_layout.addStretch()
        topo_layout.addWidget(QLabel("Filtrar por:"))
        topo_layout.addWidget(self.combo_filtro)
        layout_principal.addLayout(topo_layout)

        # --- 2. Cards Numéricos ---
        grid_cards = QGridLayout()
        grid_cards.setSpacing(15)
        self.card_lucro_diario = CardMetrica("Lucro Hoje", "R$ 0.00", "#00e676")
        self.card_lucro_mensal = CardMetrica("Lucro Mensal", "R$ 0.00", "#00e676")
        self.card_media_diaria = CardMetrica("Média Diária", "R$ 0.00")
        self.card_media_proc = CardMetrica("Média / Procedimento", "R$ 0.00")
        self.card_proc_hoje = CardMetrica("Procedimentos Hoje", "0", "#00bcd4")
        self.card_freebets = CardMetrica("Freebets (Em Aberto)", "0", "#ffb300")

        grid_cards.addWidget(self.card_lucro_diario, 0, 0)
        grid_cards.addWidget(self.card_lucro_mensal, 0, 1)
        grid_cards.addWidget(self.card_media_diaria, 0, 2)
        grid_cards.addWidget(self.card_media_proc, 1, 0)
        grid_cards.addWidget(self.card_proc_hoje, 1, 1)
        grid_cards.addWidget(self.card_freebets, 1, 2)
        layout_principal.addLayout(grid_cards)

        # --- 3. Área de Gráficos (Abas) ---
        self.abas_graficos = QTabWidget()
        self.abas_graficos.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #282c38; background-color: #1a1d2d; border-radius: 5px; }
            QTabBar::tab { background: #161925; color: #7b849b; padding: 10px 20px; border: 1px solid #282c38; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: bold;}
            QTabBar::tab:selected { background: #1a1d2d; color: #00e676; border-bottom: 2px solid #00e676; }
        """)

        def criar_grafico(titulo):
            g = pg.PlotWidget(title=titulo)
            g.setBackground('#1a1d2d')
            g.showGrid(x=False, y=True, alpha=0.2)
            g.getAxis('left').setPen('#7b849b')
            g.getAxis('bottom').setPen('#7b849b')
            return g

        self.grafico_linha = criar_grafico("Evolução do Lucro")
        self.abas_graficos.addTab(self.grafico_linha, "Evolução Mensal")

        self.grafico_barra_lucro = criar_grafico("Lucro por Dia")
        self.abas_graficos.addTab(self.grafico_barra_lucro, "Lucro Diário")

        self.grafico_barra_vol = criar_grafico("Quantidade de Procedimentos por Dia")
        self.abas_graficos.addTab(self.grafico_barra_vol, "Volume Diário")

        aba_freebet = QWidget()
        layout_freebet = QVBoxLayout(aba_freebet)
        layout_freebet.setContentsMargins(0,0,0,0)
        
        topo_freebet = QHBoxLayout()
        self.btn_toggle_freebet = QPushButton("Visualizando: Quantidade")
        self.btn_toggle_freebet.setStyleSheet("background-color: #ffb300; color: black; font-weight: bold; padding: 5px 15px; border-radius: 4px;")
        self.btn_toggle_freebet.clicked.connect(self.alternar_modo_freebet)
        topo_freebet.addStretch()
        topo_freebet.addWidget(self.btn_toggle_freebet)
        
        self.grafico_barra_freebet = criar_grafico("Freebets Coletadas por Dia")
        layout_freebet.addLayout(topo_freebet)
        layout_freebet.addWidget(self.grafico_barra_freebet)
        self.abas_graficos.addTab(aba_freebet, "Métricas Freebet")

        layout_principal.addWidget(self.abas_graficos)

        self.grafico_linha.installEventFilter(self)
        self.grafico_barra_lucro.installEventFilter(self)
        self.grafico_barra_vol.installEventFilter(self)
        self.grafico_barra_freebet.installEventFilter(self)

        # --- 4. Sistema de Tooltips Discretos ---
        def criar_tooltip():
            tt = pg.TextItem("", anchor=(0.5, 1.2), color="white", fill=pg.mkBrush(22, 25, 37, 240))
            tt.setZValue(10)
            tt.hide()
            return tt

        self.tt_linha = criar_tooltip()
        self.tt_lucro = criar_tooltip()
        self.tt_vol = criar_tooltip()
        self.tt_freebet = criar_tooltip()

        self.hover_dot = pg.ScatterPlotItem(size=8, pen=pg.mkPen('#00e676', width=2), brush=pg.mkBrush('#1a1d2d'))
        self.hover_dot.setZValue(9)
        self.hover_dot.hide()

        self.grafico_linha.scene().sigMouseMoved.connect(self.hover_linha)
        self.grafico_barra_lucro.scene().sigMouseMoved.connect(self.hover_lucro)
        self.grafico_barra_vol.scene().sigMouseMoved.connect(self.hover_vol)
        self.grafico_barra_freebet.scene().sigMouseMoved.connect(self.hover_freebet)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Leave:
            if watched == self.grafico_linha:
                self.tt_linha.hide()
                self.hover_dot.hide()
            elif watched == self.grafico_barra_lucro:
                self.tt_lucro.hide()
            elif watched == self.grafico_barra_vol:
                self.tt_vol.hide()
            elif watched == self.grafico_barra_freebet:
                self.tt_freebet.hide()
        return super().eventFilter(watched, event)

    def alternar_modo_freebet(self):
        self.mostrar_valor_freebet = not self.mostrar_valor_freebet
        if self.mostrar_valor_freebet:
            self.btn_toggle_freebet.setText("Visualizando: Lucro Final (R$)")
            self.grafico_barra_freebet.setTitle("Lucro de Freebets Convertidas por Dia")
        else:
            self.btn_toggle_freebet.setText("Visualizando: Quantidade")
            self.grafico_barra_freebet.setTitle("Freebets Coletadas por Dia")
        self.atualizar_dados()

    def atualizar_dados(self):
        conexao = database.conectar()
        cursor = conexao.cursor()
        
        hoje_obj = datetime.now()
        hoje_str = hoje_obj.strftime("%d/%m/%Y")
        mes_atual = hoje_obj.strftime("%m/%Y")
        filtro = self.combo_filtro.currentText()
        
        if filtro == "Todos":
            cursor.execute("SELECT data_operacao, lucro_final, tipo_procedimento, valor_freebet_coletada, bateu_duplo FROM Procedimentos_Historico WHERE mes_referencia = ?", (mes_atual,))
        else:
            cursor.execute("SELECT data_operacao, lucro_final, tipo_procedimento, valor_freebet_coletada, bateu_duplo FROM Procedimentos_Historico WHERE mes_referencia = ? AND tipo_procedimento = ?", (mes_atual, filtro))
            
        registros = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM Procedimentos_Historico WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'")
        total_pendente = cursor.fetchone()[0]
        conexao.close()

        _, max_dias = calendar.monthrange(hoje_obj.year, hoje_obj.month)
        
        self.dados_dias = list(range(1, max_dias + 1))
        lucro_por_dia = {d: 0.0 for d in self.dados_dias}
        volume_por_dia = {d: 0 for d in self.dados_dias}
        freebet_qtd_dia = {d: 0 for d in self.dados_dias}
        freebet_lucro_dia = {d: 0.0 for d in self.dados_dias}

        lucro_mensal = 0.0
        lucro_hoje = 0.0
        proc_hoje = 0

        for data_op, lucro_base, tipo, valor_freebet, bateu in registros:
            if lucro_base is None: lucro_base = 0.0
            if valor_freebet is None: valor_freebet = 0.0
            
            dia_inteiro = int(data_op.split('/')[0])
            
            lucro_real = lucro_base + (valor_freebet if bateu else 0.0)
            
            lucro_mensal += lucro_real
            lucro_por_dia[dia_inteiro] += lucro_real
            volume_por_dia[dia_inteiro] += 1
            
            if tipo == "Coletar Freebet":
                freebet_qtd_dia[dia_inteiro] += 1
            
            if tipo == "Converter Freebet":
                freebet_lucro_dia[dia_inteiro] += lucro_real 

            if data_op == hoje_str:
                lucro_hoje += lucro_real
                proc_hoje += 1

        self.card_lucro_diario.lbl_valor.setText(f"R$ {lucro_hoje:.2f}")
        self.card_lucro_diario.lbl_valor.setStyleSheet(f"color: {'#00e676' if lucro_hoje >= 0 else '#ff5252'}; font-size: 26px; font-weight: bold;")
        self.card_lucro_mensal.lbl_valor.setText(f"R$ {lucro_mensal:.2f}")
        self.card_lucro_mensal.lbl_valor.setStyleSheet(f"color: {'#00e676' if lucro_mensal >= 0 else '#ff5252'}; font-size: 26px; font-weight: bold;")
        self.card_media_diaria.lbl_valor.setText(f"R$ {(lucro_mensal / hoje_obj.day):.2f}")
        self.card_media_proc.lbl_valor.setText(f"R$ {(lucro_mensal / len(registros)) if registros else 0:.2f}")
        self.card_proc_hoje.lbl_valor.setText(str(proc_hoje))
        self.card_freebets.lbl_valor.setText(str(total_pendente))

        acumulado = 0
        self.dados_linha_y = []
        for d in self.dados_dias:
            acumulado += lucro_por_dia[d]
            self.dados_linha_y.append(acumulado)
            
        self.dados_lucro_y = [lucro_por_dia[d] for d in self.dados_dias]
        self.dados_vol_y = [volume_por_dia[d] for d in self.dados_dias]
        self.dados_freebet_qtd = [freebet_qtd_dia[d] for d in self.dados_dias]
        self.dados_freebet_lucro = [freebet_lucro_dia[d] for d in self.dados_dias]

        self.grafico_linha.clear()
        self.grafico_barra_lucro.clear()
        self.grafico_barra_vol.clear()
        self.grafico_barra_freebet.clear()

        pen_linha = pg.mkPen(color='#00e676', width=3)
        self.grafico_linha.plot(self.dados_dias, self.dados_linha_y, pen=pen_linha)

        cores_lucro = ['#00e676' if l >= 0 else '#ff5252' for l in self.dados_lucro_y]
        bg_lucro = pg.BarGraphItem(x=self.dados_dias, height=self.dados_lucro_y, width=0.6, brushes=cores_lucro)
        self.grafico_barra_lucro.addItem(bg_lucro)

        bg_vol = pg.BarGraphItem(x=self.dados_dias, height=self.dados_vol_y, width=0.6, brush='#00bcd4')
        self.grafico_barra_vol.addItem(bg_vol)

        if self.mostrar_valor_freebet:
            cores_fb = ['#00e676' if l >= 0 else '#ff5252' for l in self.dados_freebet_lucro]
            bg_freebet = pg.BarGraphItem(x=self.dados_dias, height=self.dados_freebet_lucro, width=0.6, brushes=cores_fb)
        else:
            bg_freebet = pg.BarGraphItem(x=self.dados_dias, height=self.dados_freebet_qtd, width=0.6, brush='#ffb300')
        self.grafico_barra_freebet.addItem(bg_freebet)

        for grafico, tt in [(self.grafico_linha, self.tt_linha), (self.grafico_barra_lucro, self.tt_lucro), 
                            (self.grafico_barra_vol, self.tt_vol), (self.grafico_barra_freebet, self.tt_freebet)]:
            grafico.setXRange(0.5, max_dias + 0.5, padding=0)
            grafico.getAxis('bottom').setTicks([[(d, str(d)) for d in self.dados_dias]])
            grafico.addItem(tt)

        self.grafico_linha.addItem(self.hover_dot)

        # --- A MÁGICA PARA NÃO CORTAR O TEXTO NO TOPO ---
        def aplicar_margem_y(grafico, dados, aceita_negativo=True):
            if not dados: return
            v_min, v_max = min(dados), max(dados)
            margem = (v_max - v_min) * 0.15 if v_max != v_min else (abs(v_max) * 0.2 if v_max else 10)
            y_topo = v_max + margem
            y_base = (v_min - margem) if aceita_negativo and v_min < 0 else 0
            grafico.setYRange(y_base, y_topo)

        aplicar_margem_y(self.grafico_linha, self.dados_linha_y)
        aplicar_margem_y(self.grafico_barra_lucro, self.dados_lucro_y)
        aplicar_margem_y(self.grafico_barra_vol, self.dados_vol_y, aceita_negativo=False)
        dados_fb = self.dados_freebet_lucro if self.mostrar_valor_freebet else self.dados_freebet_qtd
        aplicar_margem_y(self.grafico_barra_freebet, dados_fb, aceita_negativo=self.mostrar_valor_freebet)

    # --- LÓGICA DE HOVER INTELIGENTE ---
    def hover_linha(self, pos):
        if not hasattr(self, 'dados_dias') or not self.grafico_linha.sceneBoundingRect().contains(pos):
            self.hover_dot.hide()
            self.tt_linha.hide()
            return
            
        mousePoint = self.grafico_linha.plotItem.vb.mapSceneToView(pos)
        x = int(round(mousePoint.x()))
        
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_linha_y[x - 1]
            self.hover_dot.setData([x], [y])
            self.hover_dot.show()
            self.tt_linha.setText(f"R$ {y:.2f}")
            self.tt_linha.setAnchor((0.5, 1.2) if y >= 0 else (0.5, -0.2)) 
            self.tt_linha.setPos(x, y)
            self.tt_linha.show()
        else:
            self.hover_dot.hide()
            self.tt_linha.hide()

    def hover_lucro(self, pos):
        if not hasattr(self, 'dados_dias') or not self.grafico_barra_lucro.sceneBoundingRect().contains(pos):
            self.tt_lucro.hide()
            return
        mousePoint = self.grafico_barra_lucro.plotItem.vb.mapSceneToView(pos)
        x = int(round(mousePoint.x()))
        mouse_y = mousePoint.y()
        
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_lucro_y[x - 1]
            is_x_hover = abs(mousePoint.x() - x) <= 0.3 
            is_y_hover = (y >= 0 and 0 <= mouse_y <= y) or (y < 0 and y <= mouse_y <= 0)
            
            if is_x_hover and is_y_hover:
                self.tt_lucro.setText(f"R$ {y:.2f}")
                self.tt_lucro.setAnchor((0.5, 1.2) if y >= 0 else (0.5, -0.2))
                self.tt_lucro.setPos(x, y)
                self.tt_lucro.show()
            else:
                self.tt_lucro.hide()
        else:
            self.tt_lucro.hide()

    def hover_vol(self, pos):
        if not hasattr(self, 'dados_dias') or not self.grafico_barra_vol.sceneBoundingRect().contains(pos):
            self.tt_vol.hide()
            return
        mousePoint = self.grafico_barra_vol.plotItem.vb.mapSceneToView(pos)
        x = int(round(mousePoint.x()))
        mouse_y = mousePoint.y()
        
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_vol_y[x - 1]
            is_x_hover = abs(mousePoint.x() - x) <= 0.3
            is_y_hover = 0 <= mouse_y <= y
            
            if is_x_hover and is_y_hover:
                self.tt_vol.setText(f"{y}")
                self.tt_vol.setAnchor((0.5, 1.2))
                self.tt_vol.setPos(x, y)
                self.tt_vol.show()
            else:
                self.tt_vol.hide()
        else:
            self.tt_vol.hide()

    def hover_freebet(self, pos):
        if not hasattr(self, 'dados_dias') or not self.grafico_barra_freebet.sceneBoundingRect().contains(pos):
            self.tt_freebet.hide()
            return
        mousePoint = self.grafico_barra_freebet.plotItem.vb.mapSceneToView(pos)
        x = int(round(mousePoint.x()))
        mouse_y = mousePoint.y()
        
        if 1 <= x <= len(self.dados_dias):
            is_x_hover = abs(mousePoint.x() - x) <= 0.3
            
            if self.mostrar_valor_freebet:
                y = self.dados_freebet_lucro[x - 1]
                is_y_hover = (y >= 0 and 0 <= mouse_y <= y) or (y < 0 and y <= mouse_y <= 0)
                
                if is_x_hover and is_y_hover:
                    self.tt_freebet.setText(f"R$ {y:.2f}")
                    self.tt_freebet.setAnchor((0.5, 1.2) if y >= 0 else (0.5, -0.2))
                    self.tt_freebet.setPos(x, y)
                    self.tt_freebet.show()
                else:
                    self.tt_freebet.hide()
            else:
                y = self.dados_freebet_qtd[x - 1]
                is_y_hover = 0 <= mouse_y <= y
                
                if is_x_hover and is_y_hover:
                    self.tt_freebet.setText(f"{y}")
                    self.tt_freebet.setAnchor((0.5, 1.2))
                    self.tt_freebet.setPos(x, y)
                    self.tt_freebet.show()
                else:
                    self.tt_freebet.hide()
        else:
            self.tt_freebet.hide()