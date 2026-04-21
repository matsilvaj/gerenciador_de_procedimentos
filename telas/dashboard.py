from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QFrame, QTabWidget, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, QEvent
import pyqtgraph as pg
from datetime import datetime
import calendar
from core import database


class CardMetrica(QFrame):
    def __init__(self, titulo, valor, cor_valor="#f4f4f5"):
        super().__init__()
        self.setStyleSheet("QFrame { background-color: #18181b; border-radius: 16px; border: none; }")

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

        topo_layout = QHBoxLayout()
        mes_atual_nome = datetime.now().strftime("%m/%Y")

        lbl_titulo = QLabel(f"Visão Geral — {mes_atual_nome}")
        lbl_titulo.setStyleSheet("color: #f4f4f5; font-size: 22px; font-weight: bold;")

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
            }
            QComboBox::drop-down { border: none; }
        """)
        self.combo_filtro.currentTextChanged.connect(self.atualizar_dados)

        topo_layout.addWidget(lbl_titulo)
        topo_layout.addStretch()
        topo_layout.addWidget(self.combo_filtro)
        layout_principal.addLayout(topo_layout)

        grid_cards = QGridLayout()
        grid_cards.setSpacing(20)

        self.card_lucro_diario = CardMetrica("Lucro Hoje", "R$ 0.00")
        self.card_lucro_mensal = CardMetrica("Lucro Mensal", "R$ 0.00")
        self.card_media_diaria = CardMetrica("Média Diária", "R$ 0.00")
        self.card_media_proc = CardMetrica("Média / Proced", "R$ 0.00")
        self.card_proc_hoje = CardMetrica("Procedimentos Hoje", "0")
        self.card_freebets = CardMetrica("Freebets (Em Aberto)", "0")

        grid_cards.addWidget(self.card_lucro_diario, 0, 0)
        grid_cards.addWidget(self.card_lucro_mensal, 0, 1)
        grid_cards.addWidget(self.card_media_diaria, 0, 2)
        grid_cards.addWidget(self.card_media_proc, 1, 0)
        grid_cards.addWidget(self.card_proc_hoje, 1, 1)
        grid_cards.addWidget(self.card_freebets, 1, 2)

        layout_principal.addLayout(grid_cards)

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
            QTabBar::tab:selected { color: #3b82f6; }
        """)

        self.grafico_linha = self.criar_grafico()
        self.abas_graficos.addTab(self.grafico_linha, "Evolução Mensal")

        self.grafico_barra_lucro = self.criar_grafico()
        self.abas_graficos.addTab(self.grafico_barra_lucro, "Lucro Diário")

        self.grafico_barra_vol = self.criar_grafico()
        self.abas_graficos.addTab(self.grafico_barra_vol, "Volume Diário")

        aba_freebet = QWidget()
        layout_freebet = QVBoxLayout(aba_freebet)
        layout_freebet.setContentsMargins(20, 20, 20, 0)

        topo_freebet = QHBoxLayout()
        self.btn_toggle_freebet = QPushButton("Visualizando: Quantidade")
        self.btn_toggle_freebet.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_freebet.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #f4f4f5;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #3f3f46; }
        """)
        self.btn_toggle_freebet.clicked.connect(self.alternar_modo_freebet)

        topo_freebet.addStretch()
        topo_freebet.addWidget(self.btn_toggle_freebet)

        self.grafico_barra_freebet = self.criar_grafico()
        layout_freebet.addLayout(topo_freebet)
        layout_freebet.addWidget(self.grafico_barra_freebet)

        self.abas_graficos.addTab(aba_freebet, "Métricas Freebet")
        layout_principal.addWidget(self.abas_graficos)

        self.tt_linha = self.criar_tooltip()
        self.tt_lucro = self.criar_tooltip()
        self.tt_vol = self.criar_tooltip()
        self.tt_freebet = self.criar_tooltip()

        self.hover_dot = pg.ScatterPlotItem(
            size=8,
            pen=pg.mkPen('#18181b', width=2),
            brush=pg.mkBrush('#3b82f6')
        )
        self.hover_dot.setZValue(12)
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

    def criar_grafico(self):
        g = pg.PlotWidget()
        g.setBackground('#18181b')
        g.showGrid(x=False, y=False)

        linha_base = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(color=(255, 255, 255, 22), width=1, style=Qt.SolidLine)
        )
        g.addItem(linha_base)

        g.getAxis('left').setPen(pg.mkPen(None))
        g.getAxis('left').setTextPen('#71717a')
        g.getAxis('bottom').setPen(pg.mkPen(None))
        g.getAxis('bottom').setTextPen('#71717a')
        g.setMouseEnabled(x=False, y=False)
        g.setMenuEnabled(False)
        g.hideButtons()
        return g

    def criar_tooltip(self):
        tt = pg.TextItem("", anchor=(0.5, 1.0))
        tt.setZValue(20)
        tt.hide()
        return tt

    def formatar_tooltip_html(self, texto):
        return f"""
        <div style="
            background-color: rgba(24,24,27,235);
            color: #f4f4f5;
            border: 1px solid rgba(255,255,255,20);
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 10pt;
            font-weight: 600;
        ">
            {texto}
        </div>
        """

    def configurar_grafico(self, grafico, tooltip, dot=None):
        grafico.clear()

        linha_base = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(color=(255, 255, 255, 22), width=1, style=Qt.SolidLine)
        )
        grafico.addItem(linha_base)
        grafico.addItem(tooltip)

        if dot is not None:
            grafico.addItem(dot)

        grafico.getAxis('left').setPen(pg.mkPen(None))
        grafico.getAxis('left').setTextPen('#71717a')
        grafico.getAxis('bottom').setPen(pg.mkPen(None))
        grafico.getAxis('bottom').setTextPen('#71717a')
        grafico.setMouseEnabled(x=False, y=False)
        grafico.setMenuEnabled(False)
        grafico.hideButtons()

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

    def mostrar_hover(self, grafico, tooltip, x, y, texto, dot=False):
        tooltip.setHtml(self.formatar_tooltip_html(texto))

        _, y_range = grafico.plotItem.vb.viewRange()
        y_min, y_max = y_range
        margem = (y_max - y_min) * 0.06

        if y >= 0:
            y_pos = min(y + margem, y_max - margem)
            tooltip.setAnchor((0.5, 1.0))
        else:
            y_pos = max(y - margem, y_min + margem)
            tooltip.setAnchor((0.5, 0.0))

        tooltip.setPos(x, y_pos)
        tooltip.show()

        if dot:
            self.hover_dot.setData([x], [y])
            self.hover_dot.show()
        else:
            self.hover_dot.hide()

    def alternar_modo_freebet(self):
        self.mostrar_valor_freebet = not self.mostrar_valor_freebet
        self.btn_toggle_freebet.setText(
            "Visualizando: Lucro Final (R$)"
            if self.mostrar_valor_freebet
            else "Visualizando: Quantidade"
        )
        self.atualizar_dados()

    def atualizar_dados(self):
        conexao = database.conectar()
        cursor = conexao.cursor()

        hoje_obj = datetime.now()
        hoje_str = hoje_obj.strftime("%d/%m/%Y")
        mes_atual = hoje_obj.strftime("%m/%Y")
        filtro = self.combo_filtro.currentText()

        if filtro == "Todos":
            cursor.execute("""
                SELECT data_operacao, lucro_final, tipo_procedimento,
                       valor_freebet_coletada, bateu_duplo
                FROM Procedimentos_Historico
                WHERE mes_referencia = ?
            """, (mes_atual,))
        elif filtro == "Converter Freebet":
            # Aqui unimos a Conversão (v) com sua Coleta de origem (c)
            # E somamos o lucro de ambas para obter o valor real (Total líquido)
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

        cursor.execute("""
            SELECT COUNT(*)
            FROM Procedimentos_Historico
            WHERE tipo_procedimento = 'Coletar Freebet'
              AND status_freebet = 'Pendente'
        """)
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
            lucro_base = lucro_base or 0.0
            valor_freebet = valor_freebet or 0.0
            dia_inteiro = int(data_op.split('/')[0])

            lucro_real = lucro_base + (valor_freebet if bateu else 0.0)

            lucro_mensal += lucro_real
            lucro_por_dia[dia_inteiro] += lucro_real
            volume_por_dia[dia_inteiro] += 1

            if tipo == "Coletar Freebet":
                freebet_qtd_dia[dia_inteiro] += 1
                freebet_lucro_dia[dia_inteiro] += lucro_real

            if tipo == "Converter Freebet":
                freebet_lucro_dia[dia_inteiro] += lucro_real

            if data_op == hoje_str:
                lucro_hoje += lucro_real
                proc_hoje += 1

        cor_up = "#34d399"
        cor_down = "#f87171"

        self.card_lucro_diario.lbl_valor.setText(f"R$ {lucro_hoje:.2f}")
        self.card_lucro_diario.lbl_valor.setStyleSheet(
            f"color: {cor_up if lucro_hoje >= 0 else cor_down}; font-size: 28px; font-weight: bold; border: none;"
        )

        self.card_lucro_mensal.lbl_valor.setText(f"R$ {lucro_mensal:.2f}")
        self.card_lucro_mensal.lbl_valor.setStyleSheet(
            f"color: {cor_up if lucro_mensal >= 0 else cor_down}; font-size: 28px; font-weight: bold; border: none;"
        )

        self.card_media_diaria.lbl_valor.setText(f"R$ {(lucro_mensal / hoje_obj.day):.2f}")
        self.card_media_proc.lbl_valor.setText(
            f"R$ {(lucro_mensal / len(registros)) if registros else 0:.2f}"
        )
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

        self.configurar_grafico(self.grafico_linha, self.tt_linha, self.hover_dot)
        self.configurar_grafico(self.grafico_barra_lucro, self.tt_lucro)
        self.configurar_grafico(self.grafico_barra_vol, self.tt_vol)
        self.configurar_grafico(self.grafico_barra_freebet, self.tt_freebet)

        pen_linha = pg.mkPen(color='#3b82f6', width=3)
        self.grafico_linha.plot(self.dados_dias, self.dados_linha_y, pen=pen_linha)

        cores_lucro = [cor_up if l >= 0 else cor_down for l in self.dados_lucro_y]
        self.grafico_barra_lucro.addItem(pg.BarGraphItem(
            x=self.dados_dias,
            height=self.dados_lucro_y,
            width=0.35,
            brushes=cores_lucro
        ))

        self.grafico_barra_vol.addItem(pg.BarGraphItem(
            x=self.dados_dias,
            height=self.dados_vol_y,
            width=0.35,
            brush='#3b82f6'
        ))

        if self.mostrar_valor_freebet:
            cores_fb = [cor_up if l >= 0 else cor_down for l in self.dados_freebet_lucro]
            bg_freebet = pg.BarGraphItem(
                x=self.dados_dias,
                height=self.dados_freebet_lucro,
                width=0.35,
                brushes=cores_fb
            )
        else:
            bg_freebet = pg.BarGraphItem(
                x=self.dados_dias,
                height=self.dados_freebet_qtd,
                width=0.35,
                brush='#3b82f6'
            )
        self.grafico_barra_freebet.addItem(bg_freebet)

        for grafico in [
            self.grafico_linha,
            self.grafico_barra_lucro,
            self.grafico_barra_vol,
            self.grafico_barra_freebet
        ]:
            grafico.setXRange(0.5, max_dias + 0.5, padding=0)
            grafico.getAxis('bottom').setTicks([[(d, str(d)) for d in self.dados_dias]])

        self.aplicar_margem_y_geral()
        self.esconder_todos_tooltips()

    def aplicar_margem_y_geral(self):
        def aplicar_margem_y(grafico, dados, aceita_negativo=True):
            if not dados:
                return

            v_min = min(dados)
            v_max = max(dados)
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
        if not hasattr(self, 'dados_dias'):
            self.esconder_todos_tooltips()
            return None

        if not grafico.sceneBoundingRect().contains(pos):
            self.esconder_todos_tooltips()
            return None

        return grafico.plotItem.vb.mapSceneToView(pos)

    def hover_linha(self, pos):
        mp = self.validar_hover(self.grafico_linha, pos)
        if not mp:
            return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_linha_y[x - 1]
            self.tt_lucro.hide()
            self.tt_vol.hide()
            self.tt_freebet.hide()

            self.mostrar_hover(
                self.grafico_linha,
                self.tt_linha,
                x,
                y,
                f"R$ {y:.2f}",
                dot=True
            )
        else:
            self.esconder_todos_tooltips()

    def hover_lucro(self, pos):
        mp = self.validar_hover(self.grafico_barra_lucro, pos)
        if not mp:
            return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_lucro_y[x - 1]
            dentro_barra = (
                abs(mp.x() - x) <= 0.22 and
                ((y >= 0 and 0 <= mp.y() <= y) or (y < 0 and y <= mp.y() <= 0))
            )

            if dentro_barra:
                self.tt_linha.hide()
                self.tt_vol.hide()
                self.tt_freebet.hide()
                self.hover_dot.hide()

                self.mostrar_hover(
                    self.grafico_barra_lucro,
                    self.tt_lucro,
                    x,
                    y,
                    f"R$ {y:.2f}"
                )
            else:
                self.tt_lucro.hide()
        else:
            self.tt_lucro.hide()

    def hover_vol(self, pos):
        mp = self.validar_hover(self.grafico_barra_vol, pos)
        if not mp:
            return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_vol_y[x - 1]

            if abs(mp.x() - x) <= 0.22 and 0 <= mp.y() <= y:
                self.tt_linha.hide()
                self.tt_lucro.hide()
                self.tt_freebet.hide()
                self.hover_dot.hide()

                self.mostrar_hover(
                    self.grafico_barra_vol,
                    self.tt_vol,
                    x,
                    y,
                    f"{y}"
                )
            else:
                self.tt_vol.hide()
        else:
            self.tt_vol.hide()

    def hover_freebet(self, pos):
        mp = self.validar_hover(self.grafico_barra_freebet, pos)
        if not mp:
            return

        x = int(round(mp.x()))
        if 1 <= x <= len(self.dados_dias):
            y = self.dados_freebet_lucro[x - 1] if self.mostrar_valor_freebet else self.dados_freebet_qtd[x - 1]
            texto = f"R$ {y:.2f}" if self.mostrar_valor_freebet else f"{y}"

            dentro_barra = (
                abs(mp.x() - x) <= 0.22 and
                ((y >= 0 and 0 <= mp.y() <= y) or (y < 0 and y <= mp.y() <= 0))
            )

            if dentro_barra:
                self.tt_linha.hide()
                self.tt_lucro.hide()
                self.tt_vol.hide()
                self.hover_dot.hide()

                self.mostrar_hover(
                    self.grafico_barra_freebet,
                    self.tt_freebet,
                    x,
                    y,
                    texto
                )
            else:
                self.tt_freebet.hide()
        else:
            self.tt_freebet.hide()