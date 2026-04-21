from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QFrame, QTabWidget, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor
import pyqtgraph as pg
from datetime import datetime
import calendar
from core import database

class CardMetrica(QFrame):
    def __init__(self, titulo, valor, cor_valor="#f4f4f5"):
        super().__init__()
        self.setStyleSheet("""
            QFrame { 
                background-color: #18181b; 
                border-radius: 16px; 
                border: none; 
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            "color: #71717a; font-size: 13px; font-weight: bold; "
            "text-transform: uppercase; border: none;"
        )
        lbl_titulo.setAlignment(Qt.AlignCenter)

        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setStyleSheet(
            f"color: {cor_valor}; font-size: 28px; font-weight: bold; border: none;"
        )
        self.lbl_valor.setAlignment(Qt.AlignCenter)

        layout.addWidget(lbl_titulo)
        layout.addWidget(self.lbl_valor)

class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.mostrar_valor_freebet = False

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 40)
        layout_principal.setSpacing(25)

        # --- CABEÇALHO ---
        topo_layout = QHBoxLayout()
        mes_atual_nome = datetime.now().strftime("%m/%Y")

        lbl_titulo = QLabel(f"Visão Geral — {mes_atual_nome}")
        lbl_titulo.setStyleSheet("color: #f4f4f5; font-size: 26px; font-weight: bold;")

        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems([
            "Todos",
            "SureBet",
            "Tentativa de Duplo",
            "Coletar Freebet",
            "Converter Freebet"
        ])
        self.combo_filtro.setStyleSheet("""
            QComboBox {
                background-color: #18181b;
                color: #f4f4f5;
                padding: 10px 15px;
                border: none;
                border-radius: 8px;
                min-width: 150px;
                font-weight: bold;
                font-size: 14px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.combo_filtro.currentTextChanged.connect(self.atualizar_dados)

        topo_layout.addWidget(lbl_titulo)
        topo_layout.addStretch()
        topo_layout.addWidget(self.combo_filtro)
        layout_principal.addLayout(topo_layout)

        # --- GRADE DE CARDS ---
        grid_cards = QGridLayout()
        grid_cards.setSpacing(20)

        self.card_lucro_diario = CardMetrica("Lucro Hoje", "R$ 0.00")
        self.card_lucro_mensal = CardMetrica("Lucro Mensal", "R$ 0.00")
        self.card_media_diaria = CardMetrica("Média Diária", "R$ 0.00")
        self.card_media_proc = CardMetrica("Média / Proced", "R$ 0.00")
        self.card_proc_hoje = CardMetrica("Procedimentos Hoje", "0")
        # Freebet em aberto voltou a ser Quantidade
        self.card_freebets = CardMetrica("Freebets (Em Aberto)", "0", "#a855f7") 

        grid_cards.addWidget(self.card_lucro_diario, 0, 0)
        grid_cards.addWidget(self.card_lucro_mensal, 0, 1)
        grid_cards.addWidget(self.card_media_diaria, 0, 2)
        grid_cards.addWidget(self.card_media_proc, 1, 0)
        grid_cards.addWidget(self.card_proc_hoje, 1, 1)
        grid_cards.addWidget(self.card_freebets, 1, 2)

        layout_principal.addLayout(grid_cards)

        # --- ABAS DOS GRÁFICOS ---
        self.abas_graficos = QTabWidget()
        self.abas_graficos.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #18181b;
                border-radius: 16px;
            }
            QTabBar::tab {
                background: transparent;
                color: #71717a;
                padding: 10px 20px;
                border: none;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }
            QTabBar::tab:selected { 
                color: #3b82f6; 
                border-bottom: 2px solid #3b82f6; 
            }
        """)

        # Gráficos Adicionados Diretamente (Design Limpo)
        self.grafico_linha = self.criar_grafico()
        self.abas_graficos.addTab(self.criar_aba_padrao(self.grafico_linha), "Evolução Mensal")

        self.grafico_barra_lucro = self.criar_grafico()
        self.abas_graficos.addTab(self.criar_aba_padrao(self.grafico_barra_lucro), "Lucro Diário")

        self.grafico_barra_vol = self.criar_grafico()
        self.abas_graficos.addTab(self.criar_aba_padrao(self.grafico_barra_vol), "Volume Diário")

        # Aba Freebet
        aba_freebet = QWidget()
        aba_freebet.setStyleSheet("background: transparent;") 
        layout_freebet = QVBoxLayout(aba_freebet)
        layout_freebet.setContentsMargins(20, 20, 20, 20)
        layout_freebet.setSpacing(15)

        topo_freebet = QHBoxLayout()
        self.lbl_g3 = QLabel("")
        self.lbl_g3.setStyleSheet("color: #f4f4f5; font-size: 16px; font-weight: bold; border: none;")
        
        self.btn_toggle_freebet = QPushButton("Ver em Dinheiro (R$)")
        self.btn_toggle_freebet.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_freebet.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a1a1aa;
                font-weight: bold;
                font-size: 12px;
                padding: 4px 12px;
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QPushButton:hover { 
                background-color: rgba(255,255,255,0.05); 
                color: #f4f4f5;
            }
        """)
        self.btn_toggle_freebet.clicked.connect(self.alternar_modo_freebet)

        topo_freebet.addWidget(self.lbl_g3)
        topo_freebet.addStretch()
        topo_freebet.addWidget(self.btn_toggle_freebet)

        self.grafico_barra_freebet = self.criar_grafico()
        layout_freebet.addLayout(topo_freebet)
        layout_freebet.addWidget(self.grafico_barra_freebet)

        self.abas_graficos.addTab(aba_freebet, "Métricas Freebet")
        layout_principal.addWidget(self.abas_graficos)

        # --- TOOLTIPS ---
        estilo_tooltip = """
            QLabel {
                background-color: rgba(24, 24, 27, 240);
                color: #f4f4f5;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 13px;
            }
        """
        self.tt_linha = QLabel(self.grafico_linha); self.tt_linha.setStyleSheet(estilo_tooltip); self.tt_linha.hide()
        self.tt_lucro = QLabel(self.grafico_barra_lucro); self.tt_lucro.setStyleSheet(estilo_tooltip); self.tt_lucro.hide()
        self.tt_vol = QLabel(self.grafico_barra_vol); self.tt_vol.setStyleSheet(estilo_tooltip); self.tt_vol.hide()
        self.tt_freebet = QLabel(self.grafico_barra_freebet); self.tt_freebet.setStyleSheet(estilo_tooltip); self.tt_freebet.hide()

        self.hover_dot = pg.ScatterPlotItem(size=12, pen=pg.mkPen('#18181b', width=2), brush=pg.mkBrush('#3b82f6'))
        self.hover_dot.setZValue(12)
        self.grafico_linha.addItem(self.hover_dot)
        self.hover_dot.hide()

        self.grafico_linha.scene().sigMouseMoved.connect(self.hover_linha)
        self.grafico_barra_lucro.scene().sigMouseMoved.connect(self.hover_lucro)
        self.grafico_barra_vol.scene().sigMouseMoved.connect(self.hover_vol)
        self.grafico_barra_freebet.scene().sigMouseMoved.connect(self.hover_freebet)

        self.grafico_linha.viewport().installEventFilter(self)
        self.grafico_barra_lucro.viewport().installEventFilter(self)
        self.grafico_barra_vol.viewport().installEventFilter(self)
        self.grafico_barra_freebet.viewport().installEventFilter(self)

        self.atualizar_dados()

    def criar_aba_padrao(self, grafico):
        """Padroniza as abas para que tenham as mesmas margens e o mesmo fundo invisível"""
        aba = QWidget()
        aba.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(aba)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.addWidget(grafico)
        return aba

    def criar_grafico(self):
        g = pg.PlotWidget()
        g.setBackground('transparent') 
        g.showGrid(x=False, y=True, alpha=0.15) 

        linha_base = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(color=(255, 255, 255, 30), width=1))
        g.addItem(linha_base)

        g.getPlotItem().getViewBox().setBorder(None)
        g.getAxis('left').setPen(pg.mkPen(None))
        g.getAxis('left').setTextPen('#71717a')
        g.getAxis('bottom').setPen(pg.mkPen(None))
        g.getAxis('bottom').setTextPen('#71717a')
        g.setMouseEnabled(x=False, y=False)
        g.setMenuEnabled(False)
        g.hideButtons()
        return g

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Leave:
            self.esconder_todos_tooltips()
        return super().eventFilter(watched, event)

    def esconder_todos_tooltips(self):
        self.tt_linha.hide()
        self.tt_lucro.hide()
        self.tt_vol.hide()
        self.tt_freebet.hide()
        self.hover_dot.hide()

    def mostrar_hover(self, grafico, tooltip, x, y, texto, show_dot=False):
        tooltip.setText(texto)
        tooltip.adjustSize()

        vp = grafico.getPlotItem().getViewBox().mapViewToScene(pg.Point(x, y))
        pos_widget = grafico.mapFromScene(vp)

        w = tooltip.width()
        h = tooltip.height()

        px = int(pos_widget.x()) - (w // 2)
        if y >= 0: py = int(pos_widget.y()) - h - 15
        else: py = int(pos_widget.y()) + 15

        if px < 0: px = 5
        if py < 0: py = 5

        tooltip.move(px, py)
        tooltip.show()

        if show_dot:
            self.hover_dot.setData([x], [y])
            self.hover_dot.show()
        else:
            self.hover_dot.hide()

    def alternar_modo_freebet(self):
        self.mostrar_valor_freebet = not self.mostrar_valor_freebet
        if self.mostrar_valor_freebet:
            self.btn_toggle_freebet.setText("Ver em Quantidade")
        else:
            self.btn_toggle_freebet.setText("Ver em Dinheiro (R$)")
        
        self.atualizar_dados()

    def atualizar_dados(self):
        conexao = database.conectar()
        cursor = conexao.cursor()

        hoje_obj = datetime.now()
        hoje_str = hoje_obj.strftime("%d/%m/%Y")
        mes_atual = hoje_obj.strftime("%m/%Y")
        filtro = self.combo_filtro.currentText()

        # Dados Globais (Caixa Geral)
        if filtro == "Todos":
            cursor.execute("""
                SELECT data_operacao, lucro_final, tipo_procedimento,
                       valor_freebet_coletada, bateu_duplo
                FROM Procedimentos_Historico
                WHERE mes_referencia = ?
            """, (mes_atual,))
        elif filtro == "Converter Freebet":
            cursor.execute("""
                SELECT v.data_operacao, 
                       COALESCE(v.lucro_final, 0) + COALESCE(c.lucro_final, 0) + CASE WHEN c.bateu_duplo IN (1, 'true', 'True') THEN COALESCE(c.valor_freebet_coletada, 0) ELSE 0 END AS lucro_final, 
                       v.tipo_procedimento,
                       v.valor_freebet_coletada, 
                       v.bateu_duplo
                FROM Procedimentos_Historico v
                INNER JOIN Procedimentos_Historico c ON v.id_freebet_origem = c.id
                WHERE v.mes_referencia = ? AND v.tipo_procedimento = 'Converter Freebet'
            """, (mes_atual,))
        else:
            cursor.execute("""
                SELECT data_operacao, lucro_final, tipo_procedimento,
                       valor_freebet_coletada, bateu_duplo
                FROM Procedimentos_Historico
                WHERE mes_referencia = ? AND tipo_procedimento = ?
            """, (mes_atual, filtro))

        registros = cursor.fetchall()

        # CONSERTO CARD 1: Quantidade em Aberto
        cursor.execute("""
            SELECT COUNT(*)
            FROM Procedimentos_Historico
            WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'
        """)
        resultado_fb = cursor.fetchone()
        total_pendente = resultado_fb[0] if resultado_fb else 0

        # CONSERTO GRÁFICO: Lógica Separada para extrair o LUCRO LÍQUIDO da Freebet
        conversoes_liquidas = []
        if filtro in ["Todos", "Converter Freebet"]:
            cursor.execute("""
                SELECT v.data_operacao, 
                       COALESCE(v.lucro_final, 0) + COALESCE(c.lucro_final, 0) + CASE WHEN c.bateu_duplo IN (1, 'true', 'True') THEN COALESCE(c.valor_freebet_coletada, 0) ELSE 0 END
                FROM Procedimentos_Historico v
                INNER JOIN Procedimentos_Historico c ON v.id_freebet_origem = c.id
                WHERE v.mes_referencia = ? AND v.tipo_procedimento = 'Converter Freebet'
            """, (mes_atual,))
            conversoes_liquidas = cursor.fetchall()
        
        conexao.close()

        # Configuração do Eixo X (Dias)
        _, max_dias = calendar.monthrange(hoje_obj.year, hoje_obj.month)
        dia_atual = hoje_obj.day 

        self.dados_dias = list(range(1, max_dias + 1))
        self.dados_dias_linha = list(range(1, dia_atual + 1))

        lucro_por_dia = {d: 0.0 for d in self.dados_dias}
        volume_por_dia = {d: 0 for d in self.dados_dias}
        freebet_qtd_dia = {d: 0 for d in self.dados_dias}
        freebet_lucro_dia = {d: 0.0 for d in self.dados_dias}

        lucro_mensal = 0.0
        lucro_hoje = 0.0
        proc_hoje = 0

        # Preenche Métricas Globais e a Quantidade de Freebet Coletada
        for data_op, lucro_base, tipo, valor_freebet, bateu in registros:
            try: dia = int(data_op.split('/')[0])
            except: continue
            
            idx = dia - 1
            if 0 <= idx < max_dias:
                lucro_base = lucro_base or 0.0
                valor_freebet = valor_freebet or 0.0
                bateu_bool = str(bateu).lower() in ['1', 'true']
                
                lucro_real = lucro_base + (valor_freebet if bateu_bool else 0.0)

                lucro_mensal += lucro_real
                lucro_por_dia[dia] += lucro_real
                volume_por_dia[dia] += 1

                # O Gráfico de Qtd vai contar os recolhimentos
                if tipo == "Coletar Freebet":
                    freebet_qtd_dia[dia] += 1

                if data_op == hoje_str:
                    lucro_hoje += lucro_real
                    proc_hoje += 1

        # Preenche exclusivamente o Gráfico de Dinheiro das Freebets com a consulta Liquida Segura
        for data_op, lucro_liq in conversoes_liquidas:
            try:
                dia_c = int(data_op.split('/')[0])
                if 1 <= dia_c <= max_dias:
                    freebet_lucro_dia[dia_c] += float(lucro_liq or 0.0)
            except: pass

        cor_up = "#34d399"
        cor_down = "#f87171"

        self.card_lucro_diario.lbl_valor.setText(f"R$ {lucro_hoje:.2f}")
        self.card_lucro_diario.lbl_valor.setStyleSheet(f"color: {cor_up if lucro_hoje >= 0 else cor_down}; font-size: 28px; font-weight: bold; border: none;")

        self.card_lucro_mensal.lbl_valor.setText(f"R$ {lucro_mensal:.2f}")
        self.card_lucro_mensal.lbl_valor.setStyleSheet(f"color: {cor_up if lucro_mensal >= 0 else cor_down}; font-size: 28px; font-weight: bold; border: none;")

        self.card_media_diaria.lbl_valor.setText(f"R$ {(lucro_mensal / dia_atual):.2f}")
        self.card_media_proc.lbl_valor.setText(f"R$ {(lucro_mensal / len(registros)) if registros else 0:.2f}")
        self.card_proc_hoje.lbl_valor.setText(str(proc_hoje))
        
        # Freebets em aberto atualizado
        self.card_freebets.lbl_valor.setText(str(total_pendente))

        # Acumula para a linha
        acumulado = 0
        self.dados_linha_y = []
        for d in self.dados_dias_linha:
            acumulado += lucro_por_dia[d]
            self.dados_linha_y.append(acumulado)

        self.dados_lucro_y = [lucro_por_dia[d] for d in self.dados_dias]
        self.dados_vol_y = [volume_por_dia[d] for d in self.dados_dias]
        self.dados_freebet_qtd = [freebet_qtd_dia[d] for d in self.dados_dias]
        self.dados_freebet_lucro = [freebet_lucro_dia[d] for d in self.dados_dias]

        # Limpeza Visual
        for g in [self.grafico_linha, self.grafico_barra_lucro, self.grafico_barra_vol, self.grafico_barra_freebet]:
            g.clear()
            linha_base = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(color=(255, 255, 255, 30), width=1))
            g.addItem(linha_base)

        self.grafico_linha.addItem(self.hover_dot)

        # Plotar Área
        pen_linha = pg.mkPen(color='#3b82f6', width=3)
        brush = QColor(59, 130, 246, 50)
        self.grafico_linha.plot(
            self.dados_dias_linha, 
            self.dados_linha_y, 
            pen=pen_linha,
            fillLevel=0,
            fillBrush=brush,
            antialias=True
        )

        cores_lucro = [cor_up if l >= 0 else cor_down for l in self.dados_lucro_y]
        self.grafico_barra_lucro.addItem(pg.BarGraphItem(
            x=self.dados_dias, height=self.dados_lucro_y, width=0.35, brushes=cores_lucro
        ))

        self.grafico_barra_vol.addItem(pg.BarGraphItem(
            x=self.dados_dias, height=self.dados_vol_y, width=0.35, brush='#3b82f6'
        ))

        if self.mostrar_valor_freebet:
            cores_fb = [cor_up if l >= 0 else cor_down for l in self.dados_freebet_lucro]
            bg_freebet = pg.BarGraphItem(x=self.dados_dias, height=self.dados_freebet_lucro, width=0.35, brushes=cores_fb)
        else:
            bg_freebet = pg.BarGraphItem(x=self.dados_dias, height=self.dados_freebet_qtd, width=0.35, brush='#a855f7')
        
        self.grafico_barra_freebet.addItem(bg_freebet)

        for grafico in [self.grafico_linha, self.grafico_barra_lucro, self.grafico_barra_vol, self.grafico_barra_freebet]:
            grafico.setXRange(0.5, max_dias + 0.5, padding=0)
            grafico.getAxis('bottom').setTicks([[(d, str(d)) for d in self.dados_dias]])

        self.aplicar_margem_y_geral()
        self.esconder_todos_tooltips()

    def aplicar_margem_y_geral(self):
        def aplicar_margem_y(grafico, dados, aceita_negativo=True):
            if not dados: return
            v_min = min(dados); v_max = max(dados)
            margem = (v_max - v_min) * 0.15 if v_max != v_min else (abs(v_max) * 0.2 if v_max else 10)
            y_topo = v_max + margem
            y_base = (v_min - margem) if aceita_negativo and v_min < 0 else 0
            grafico.setYRange(y_base, y_topo)

        aplicar_margem_y(self.grafico_linha, self.dados_linha_y)
        aplicar_margem_y(self.grafico_barra_lucro, self.dados_lucro_y)
        aplicar_margem_y(self.grafico_barra_vol, self.dados_vol_y, aceita_negativo=False)

        dados_fb = self.dados_freebet_lucro if self.mostrar_valor_freebet else self.dados_freebet_qtd
        aplicar_margem_y(self.grafico_barra_freebet, dados_fb, aceita_negativo=self.mostrar_valor_freebet)

    def validar_hover(self, grafico, pos):
        if not hasattr(self, 'dados_dias'): return None
        if not grafico.sceneBoundingRect().contains(pos): return None
        return grafico.plotItem.vb.mapSceneToView(pos)

    def hover_linha(self, pos):
        mp = self.validar_hover(self.grafico_linha, pos)
        if not mp:
            self.hover_dot.hide(); self.tt_linha.hide()
            return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias_linha):
            y = self.dados_linha_y[x - 1]
            if abs(mp.y() - y) < max(max(self.dados_linha_y + [1])*0.2, 50):
                self.tt_lucro.hide(); self.tt_vol.hide(); self.tt_freebet.hide()
                self.mostrar_hover(self.grafico_linha, self.tt_linha, x, y, f"R$ {y:.2f}", show_dot=True)
            else:
                self.hover_dot.hide(); self.tt_linha.hide()
        else:
            self.hover_dot.hide(); self.tt_linha.hide()

    def hover_lucro(self, pos):
        mp = self.validar_hover(self.grafico_barra_lucro, pos)
        if not mp: return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_lucro_y[x - 1]
            dentro_barra = (abs(mp.x() - x) <= 0.22 and ((y >= 0 and 0 <= mp.y() <= y) or (y < 0 and y <= mp.y() <= 0)))

            if dentro_barra:
                self.tt_linha.hide(); self.tt_vol.hide(); self.tt_freebet.hide(); self.hover_dot.hide()
                self.mostrar_hover(self.grafico_barra_lucro, self.tt_lucro, x, y, f"R$ {y:.2f}")
            else:
                self.tt_lucro.hide()
        else:
            self.tt_lucro.hide()

    def hover_vol(self, pos):
        mp = self.validar_hover(self.grafico_barra_vol, pos)
        if not mp: return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_vol_y[x - 1]
            if abs(mp.x() - x) <= 0.22 and 0 <= mp.y() <= y:
                self.tt_linha.hide(); self.tt_lucro.hide(); self.tt_freebet.hide(); self.hover_dot.hide()
                self.mostrar_hover(self.grafico_barra_vol, self.tt_vol, x, y, f"{int(y)}")
            else:
                self.tt_vol.hide()
        else:
            self.tt_vol.hide()

    def hover_freebet(self, pos):
        mp = self.validar_hover(self.grafico_barra_freebet, pos)
        if not mp: return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_freebet_lucro[x - 1] if self.mostrar_valor_freebet else self.dados_freebet_qtd[x - 1]
            texto = f"R$ {y:.2f}" if self.mostrar_valor_freebet else f"{int(y)}"
            dentro_barra = (abs(mp.x() - x) <= 0.22 and ((y >= 0 and 0 <= mp.y() <= y) or (y < 0 and y <= mp.y() <= 0)))

            if dentro_barra:
                self.tt_linha.hide(); self.tt_lucro.hide(); self.tt_vol.hide(); self.hover_dot.hide()
                self.mostrar_hover(self.grafico_barra_freebet, self.tt_freebet, x, y, texto)
            else:
                self.tt_freebet.hide()
        else:
            self.tt_freebet.hide()