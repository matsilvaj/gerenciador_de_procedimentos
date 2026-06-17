from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QGroupBox, QCheckBox,
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QToolTip)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QCursor
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from core import database
from telas.procedimentos import TabelaProcedimentos, DialogEscolherCasas, TIPOS_MOVIMENTACAO, COR_AZUL_DESTAQUE

COR_VERDE = "#34d399"
COR_VERMELHO = "#f87171"

class DialogFiltrosHistorico(QDialog):
    def __init__(self, parent=None, filtros_atuais=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.filtros_atuais = filtros_atuais if filtros_atuais else {"tipos": [], "casas": []}
        
        self.setStyleSheet("""
            QDialog { background-color: #09090b; }
            QGroupBox { border: none; margin-top: 15px; padding-top: 15px; color: #f4f4f5; font-weight: bold;}
            QLabel { color: #a1a1aa; font-weight: bold; }
            QCheckBox { color: #f4f4f5; font-size: 14px; padding: 5px; }
            QPushButton { background-color: #27272a; color: white; border-radius: 8px; padding: 10px; font-weight: bold; border: none; }
        """)

        layout = QVBoxLayout(self)

        grupo_tipos = QGroupBox("Tipo de Movimentação")
        lay_tipos = QVBoxLayout()
        self.checks_tipos = {}
        for t in TIPOS_MOVIMENTACAO:
            chk = QCheckBox(t)
            if t in self.filtros_atuais["tipos"]: chk.setChecked(True)
            lay_tipos.addWidget(chk)
            self.checks_tipos[t] = chk
        grupo_tipos.setLayout(lay_tipos)
        layout.addWidget(grupo_tipos)

        grupo_casas = QGroupBox("Casas Envolvidas")
        lay_casas = QVBoxLayout()
        self.lbl_casas = QLabel("Nenhuma selecionada")
        self.lbl_casas.setAlignment(Qt.AlignCenter) 
        if self.filtros_atuais["casas"]:
            self.lbl_casas.setText(" | ".join(self.filtros_atuais["casas"]))
            self.lbl_casas.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
            
        btn_casas = QPushButton("Escolher Casas")
        btn_casas.clicked.connect(self.abrir_seletor_casas)
        lay_casas.addWidget(self.lbl_casas); lay_casas.addWidget(btn_casas)
        grupo_casas.setLayout(lay_casas)
        layout.addWidget(grupo_casas)

        botoes = QHBoxLayout()
        btn_limpar = QPushButton("Limpar")
        btn_limpar.setStyleSheet("background-color: transparent; color: #71717a;")
        btn_limpar.clicked.connect(self.limpar)
        
        btn_aplicar = QPushButton("APLICAR")
        btn_aplicar.setStyleSheet(f"background-color: {COR_AZUL_DESTAQUE}; color: white;")
        btn_aplicar.clicked.connect(self.aplicar)
        
        botoes.addWidget(btn_limpar); botoes.addWidget(btn_aplicar)
        layout.addLayout(botoes)

    def abrir_seletor_casas(self):
        atuais = self.lbl_casas.text().split(" | ") if self.lbl_casas.text() != "Nenhuma selecionada" else []
        dialog = DialogEscolherCasas(self, atuais)
        if dialog.exec() == QDialog.Accepted:
            sel = dialog.get_selecionadas()
            if sel:
                self.lbl_casas.setText(" | ".join(sel)); self.lbl_casas.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
            else:
                self.lbl_casas.setText("Nenhuma selecionada"); self.lbl_casas.setStyleSheet("color: #a1a1aa;")

    def limpar(self):
        for chk in self.checks_tipos.values(): chk.setChecked(False)
        self.lbl_casas.setText("Nenhuma selecionada"); self.lbl_casas.setStyleSheet("color: #a1a1aa;")

    def aplicar(self):
        self.filtros_atuais["tipos"] = [t for t, chk in self.checks_tipos.items() if chk.isChecked()]
        self.filtros_atuais["casas"] = [] if self.lbl_casas.text() == "Nenhuma selecionada" else self.lbl_casas.text().split(" | ")
        self.accept()


class TelaHistorico(QWidget):
    def __init__(self):
        super().__init__()
        self.filtros_avancados = {"tipos": [], "casas": []}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(25)

        topo_layout = QHBoxLayout()
        lbl_titulo = QLabel("Arquivo Histórico")
        lbl_titulo.setStyleSheet("color: #f4f4f5; font-size: 22px; font-weight: bold;")
        
        self.combo_meses = QComboBox()
        self.combo_meses.setMinimumWidth(150)
        self.combo_meses.setStyleSheet("background-color: #18181b; color: #f4f4f5; padding: 10px; border: none; border-radius: 8px; outline: none;")
        self.combo_meses.currentTextChanged.connect(lambda: self.carregar_dados_historicos())

        self.btn_filtros = QPushButton("Filtros")
        self.btn_filtros.setStyleSheet("background-color: #27272a; color: white; font-weight: bold; padding: 10px 20px; border-radius: 8px; border: none;")
        self.btn_filtros.clicked.connect(self.abrir_filtros)

        topo_layout.addWidget(lbl_titulo)
        topo_layout.addStretch()
        topo_layout.addWidget(self.btn_filtros)
        topo_layout.addWidget(self.combo_meses)
        layout.addLayout(topo_layout)

        resumo_layout = QHBoxLayout()

        self.card_resumo = QFrame()
        self.card_resumo.setStyleSheet("background-color: #18181b; border-radius: 16px; border: none;")
        self.card_resumo.setFixedHeight(120)
        layout_card = QVBoxLayout(self.card_resumo)
        layout_card.setContentsMargins(20,20,20,20)
        
        lbl_desc = QLabel("RESULTADO NO PERÍODO")
        lbl_desc.setStyleSheet("color: #71717a; font-size: 13px; font-weight: bold;")
        lbl_desc.setAlignment(Qt.AlignCenter)
        
        self.lbl_lucro_total = QLabel("R$ 0.00")
        self.lbl_lucro_total.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_desc)
        layout_card.addWidget(self.lbl_lucro_total)

        self.card_pizza = QFrame()
        self.card_pizza.setStyleSheet("background-color: #18181b; border-radius: 16px; border: none;")
        self.card_pizza.setFixedHeight(150)
        lay_pizza = QVBoxLayout(self.card_pizza)
        lay_pizza.setContentsMargins(0,0,0,0)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setStyleSheet("background: transparent;")
        lay_pizza.addWidget(self.chart_view)

        resumo_layout.addWidget(self.card_resumo)
        resumo_layout.addWidget(self.card_pizza)
        layout.addLayout(resumo_layout)

        self.tabela = TabelaProcedimentos(0, 6)
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Evento/Cat.", "Casas", "Resultado Base", "Resultado Final"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.verticalHeader().setDefaultSectionSize(75)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.NoSelection)
        self.tabela.setFocusPolicy(Qt.NoFocus)
        self.tabela.setShowGrid(False)
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: transparent; color: #f4f4f5; border: none; gridline-color: transparent; font-size: 14px; outline: none; }
            QTableWidget::item { border: none; border-bottom: 1px solid rgba(255,255,255,0.03); padding: 5px; }
            QTableWidget::item:selected { background-color: transparent; color: #f4f4f5; }
            QHeaderView::section { background-color: transparent; color: #71717a; font-weight: bold; border: none; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 12px 8px; }
        """)
        layout.addWidget(self.tabela)

    def abrir_filtros(self):
        d = DialogFiltrosHistorico(self, self.filtros_avancados)
        if d.exec() == QDialog.Accepted:
            self.filtros_avancados = d.filtros_atuais
            self.carregar_dados_historicos()

    def atualizar_lista_meses(self):
        self.combo_meses.blockSignals(True)
        self.combo_meses.clear()
        meses = database.listar_meses_disponiveis()
        self.combo_meses.addItems(meses)
        self.combo_meses.blockSignals(False)
        if meses: self.carregar_dados_historicos(meses[0])

    def carregar_dados_historicos(self, mes_ref=None):
        if not mes_ref: 
            mes_ref = self.combo_meses.currentText()
        if not mes_ref: return

        self.tabela.setRowCount(0)
        registros = database.buscar_dados_mes(mes_ref)
        lucro_acumulado = 0.0

        v_ganhos = 0
        v_gastos = 0
        v_invest = 0
        self.ganhos_detalhes = {}
        self.gastos_detalhes = {}

        for reg in registros:
            data, tipo, jogo, casas, lucro_base, v_duplo, bateu, cat_gasto = reg

            if self.filtros_avancados["tipos"] and tipo not in self.filtros_avancados["tipos"]: continue
            if self.filtros_avancados["casas"] and not any(c in casas for c in self.filtros_avancados["casas"]): continue

            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            l_final = lucro_base + (v_duplo if bateu else 0)

            if tipo != "Investimento":
                lucro_acumulado += l_final

            tipo_normalizado = tipo.strip().title()

            if tipo == "Investimento":
                v_invest += abs(l_final)
            elif l_final < 0 or tipo == "Gasto":
                cat = cat_gasto.strip().title() if cat_gasto and cat_gasto.strip() else "Perdas Procedimentos"
                self.gastos_detalhes[cat] = self.gastos_detalhes.get(cat, 0) + abs(l_final)
                v_gastos += abs(l_final)
            elif l_final > 0:
                self.ganhos_detalhes[tipo_normalizado] = self.ganhos_detalhes.get(tipo_normalizado, 0) + l_final
                v_ganhos += l_final
            
            def item(t, cor=None):
                it = QTableWidgetItem(str(t) if t not in ["None", None, ""] else "-")
                it.setTextAlignment(Qt.AlignCenter)
                if cor: it.setForeground(QBrush(QColor(cor)))
                return it

            self.tabela.setItem(row, 0, item(data))
            self.tabela.setItem(row, 1, item(tipo))
            
            cat = cat_gasto.strip().title() if cat_gasto and cat_gasto.strip() else ""
            self.tabela.setItem(row, 2, item(cat if tipo in ["Gasto", "Investimento"] else jogo))
            
            item_casas = item(casas)
            item_casas.setToolTip(casas)
            self.tabela.setItem(row, 3, item_casas)
            
            moeda = "$" if tipo == "Investimento" else "R$"
            
            self.tabela.setItem(row, 4, item(f"{moeda} {lucro_base:.2f}"))

            c_valor = COR_VERDE if l_final >= 0 else COR_VERMELHO
            if tipo == "Investimento": c_valor = "#3b82f6" 
            self.tabela.setItem(row, 5, item(f"{moeda} {l_final:.2f}", c_valor))

        cor_total = COR_VERDE if lucro_acumulado >= 0 else COR_VERMELHO
        self.lbl_lucro_total.setText(f"R$ {lucro_acumulado:.2f}")
        self.lbl_lucro_total.setStyleSheet(f"color: {cor_total}; font-size: 32px; font-weight: bold;")

        chart = QChart()
        chart.setBackgroundBrush(QBrush(Qt.transparent))
        chart.legend().hide()
        series = QPieSeries()

        if v_ganhos > 0:
            s_ganhos = series.append("Ganhos", v_ganhos)
            s_ganhos.setColor(QColor("#34d399"))
            s_ganhos.setLabelBrush(QColor("#f4f4f5"))
        if v_gastos > 0:
            s_gastos = series.append("Gastos", v_gastos)
            s_gastos.setColor(QColor("#f87171"))
            s_gastos.setLabelBrush(QColor("#f4f4f5"))
        if v_invest > 0:
            s_invest = series.append("Investimento", v_invest)
            s_invest.setColor(QColor("#3b82f6"))
            s_invest.setLabelBrush(QColor("#f4f4f5"))
        
        series.setLabelsVisible(True)
        series.setLabelsPosition(QPieSlice.LabelOutside)
        
        series.hovered.connect(self.ao_passar_mouse_pizza)

        chart.addSeries(series)
        self.chart_view.setChart(chart)

    def ao_passar_mouse_pizza(self, slice, hovered):
        slice.setExploded(hovered)
        slice.setExplodeDistanceFactor(0.05)
        
        if hovered:
            texto = f"<b>{slice.label()}:</b> " + (f"$ {slice.value():.2f}<br>" if slice.label() == "Investimento" else f"R$ {slice.value():.2f}<br>")
            if slice.label() == "Ganhos":
                for k, v in self.ganhos_detalhes.items(): texto += f"<br>• {k}: R$ {v:.2f}"
            elif slice.label() == "Gastos":
                for k, v in self.gastos_detalhes.items(): texto += f"<br>• {k}: R$ {v:.2f}"

            self.chart_view.setStyleSheet("QToolTip { background-color: #18181b; color: #f4f4f5; border: 1px solid #3b82f6; border-radius: 8px; padding: 10px; font-size: 13px; }")
            QToolTip.showText(QCursor.pos(), texto, self.chart_view)
        else:
            QToolTip.hideText()