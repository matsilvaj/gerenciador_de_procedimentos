from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from core import database
from telas.procedimentos import TabelaProcedimentos

COR_VERDE = "#34d399"
COR_VERMELHO = "#f87171"
RESULTADO_SIM = "Sim"
RESULTADO_NAO = "N\u00e3o"


class ComboBoxContainer(QWidget):
    def __init__(self, combo):
        super().__init__()
        self.combo = combo
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.combo)


class TelaFreebets(QWidget):
    sinal_converter_calculadora = Signal(str, float, list)

    def __init__(self):
        super().__init__()
        self.historico_desfazer = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)

        topo = QHBoxLayout()
        titulo = QLabel("Gest\u00e3o de Freebets")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #f4f4f5;")
        topo.addWidget(titulo)
        layout.addLayout(topo)

        self.btn_desfazer = QPushButton("\u21b6 Desfazer mudan\u00e7a")
        self.btn_desfazer.setCursor(Qt.PointingHandCursor)
        self.btn_desfazer.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #71717a;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                color: #a1a1aa;
            }
        """)
        self.btn_desfazer.clicked.connect(self.desfazer_ultima_acao)
        self.btn_desfazer.hide()
        layout.addWidget(self.btn_desfazer, alignment=Qt.AlignRight)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: transparent; }
            QTabBar::tab { background: transparent; color: #71717a; padding: 10px 20px; border: none; font-weight: bold; font-size: 14px; margin-bottom: 20px; }
            QTabBar::tab:selected { color: #3b82f6; }
        """)

        aba_disponiveis = QWidget()
        layout_disp = QVBoxLayout(aba_disponiveis)
        layout_disp.setContentsMargins(0, 0, 0, 0)
        self.tab_ativas = TabelaProcedimentos(0, 6)
        self.tab_ativas.setHorizontalHeaderLabels(["Data / Qtd", "Casa", "Valor FB", "Lucro Base", "Ganhou?", ""])
        self.configurar_tabela(self.tab_ativas, tem_acao=True, tem_resultado=True)
        layout_disp.addWidget(self.tab_ativas)
        self.abas.addTab(aba_disponiveis, "Dispon\u00edveis")

        aba_convertidas = QWidget()
        layout_conv = QVBoxLayout(aba_convertidas)
        layout_conv.setContentsMargins(0, 0, 0, 0)
        self.tab_convertidas = TabelaProcedimentos(0, 6)
        self.tab_convertidas.setHorizontalHeaderLabels(["Data (Col \u2794 Conv)", "Casa", "Valor FB", "Lucro Base", "Lucro Final", "Total"])
        self.configurar_tabela(self.tab_convertidas)
        layout_conv.addWidget(self.tab_convertidas)
        self.abas.addTab(aba_convertidas, "Hist\u00f3rico")

        layout.addWidget(self.abas)

    def configurar_tabela(self, tabela, tem_acao=False, tem_resultado=False):
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if tem_acao:
            ultima_coluna = tabela.columnCount() - 1
            if tem_resultado:
                coluna_resultado = ultima_coluna - 1
                tabela.horizontalHeader().setSectionResizeMode(coluna_resultado, QHeaderView.Fixed)
                tabela.setColumnWidth(coluna_resultado, 130)
            tabela.horizontalHeader().setSectionResizeMode(ultima_coluna, QHeaderView.Fixed)
            tabela.setColumnWidth(ultima_coluna, 100)

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

    def criar_item(self, texto, cor=None, bold=False, mostrar_hifen=True):
        if texto in ["None", None, ""]:
            texto = "-" if mostrar_hifen else ""

        item = QTableWidgetItem(str(texto))
        item.setTextAlignment(Qt.AlignCenter)
        if cor:
            item.setForeground(QBrush(QColor(cor)))
        if bold:
            fonte = item.font()
            fonte.setBold(True)
            item.setFont(fonte)
        return item

    def texto_qtd_itens(self, quantidade):
        return f"{quantidade} item" if quantidade == 1 else f"{quantidade} itens"

    def criar_container_vazio(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        return container

    def criar_botao_converter(self, casa, valor, ids):
        container_btn = QWidget()
        lay_btn = QHBoxLayout(container_btn)
        lay_btn.setContentsMargins(5, 2, 5, 2)

        btn_usar = QPushButton("Converter")
        btn_usar.setCursor(Qt.PointingHandCursor)
        btn_usar.setStyleSheet("""
            QPushButton { background-color: #f4f4f5; color: #09090b; font-weight: bold; border-radius: 6px; padding: 4px; font-size: 12px; }
            QPushButton:hover { background-color: #d4d4d8; }
        """)
        btn_usar.clicked.connect(
            lambda _, c=casa, v=valor, ids_origem=ids: self.sinal_converter_calculadora.emit(c, v, ids_origem)
        )
        lay_btn.addWidget(btn_usar)
        return container_btn

    def criar_combo_resultado(self, id_op, valor_atual):
        combo = QComboBox()
        combo.addItems([RESULTADO_SIM, RESULTADO_NAO])
        combo.setCursor(Qt.PointingHandCursor)
        combo.setMinimumWidth(96)
        combo.setStyleSheet("""
            QComboBox { background-color: #18181b; color: #f4f4f5; border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 4px 10px; min-height: 28px; }
            QComboBox::drop-down { border: none; width: 22px; }
            QComboBox QAbstractItemView { background-color: #18181b; color: #f4f4f5; border: 1px solid rgba(255,255,255,0.06); selection-background-color: #27272a; }
        """)

        if valor_atual in [RESULTADO_SIM, RESULTADO_NAO]:
            combo.setCurrentText(valor_atual)
        else:
            combo.setCurrentIndex(-1)

        combo.currentTextChanged.connect(
            lambda texto, procedimento_id=id_op: self.atualizar_resultado_ganhou(procedimento_id, texto)
        )
        return ComboBoxContainer(combo)

    def atualizar_resultado_ganhou(self, id_op, resultado):
        if resultado not in [RESULTADO_SIM, RESULTADO_NAO]:
            return

        estado_anterior = database.buscar_estado_freebet(id_op)
        if not estado_anterior or estado_anterior.get('ganhou_freebet') == resultado:
            return

        self.registrar_acao_desfazer({
            'tipo': 'resultado',
            'estado_anterior': estado_anterior
        })
        database.atualizar_resultado_freebet(id_op, resultado)
        self.carregar_freebets_ativas()

    def registrar_acao_desfazer(self, acao):
        self.historico_desfazer.append(acao)
        self.atualizar_botao_desfazer()

    def atualizar_botao_desfazer(self):
        self.btn_desfazer.setVisible(bool(self.historico_desfazer))

    def registrar_conversao_salva(self, dados_conversao):
        if not dados_conversao:
            return

        self.registrar_acao_desfazer({
            'tipo': 'conversao',
            'id_conversao': dados_conversao.get('id_conversao'),
            'estados_origem': dados_conversao.get('estados_origem', [])
        })
        self.carregar_freebets_ativas()

    def desfazer_ultima_acao(self):
        if not self.historico_desfazer:
            return False

        acao = self.historico_desfazer.pop()
        if acao['tipo'] == 'resultado':
            estado = acao['estado_anterior']
            database.restaurar_estado_freebet(
                estado['id'],
                estado.get('ganhou_freebet', ''),
                estado.get('status_freebet', 'Pendente')
            )
        elif acao['tipo'] == 'conversao':
            if acao.get('id_conversao'):
                database.desfazer_conversao_freebet(
                    acao['id_conversao'],
                    acao.get('estados_origem', [])
                )

        self.atualizar_botao_desfazer()
        self.carregar_freebets_ativas()
        return True

    def carregar_freebets_ativas(self):
        self.tab_ativas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, data_operacao, casa_destino_freebet, valor_da_freebet, lucro_final,
                   bateu_duplo, valor_freebet_coletada, condicao_freebet, ganhou_freebet
            FROM Procedimentos_Historico
            WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'
            ORDER BY id DESC
        """)

        pendentes_confirmacao = []
        agrupadas_convertiveis = {}

        for id_op, data, casa, valor_fb, lucro_base, bateu, v_duplo, condicao, ganhou in cursor.fetchall():
            valor_fb = valor_fb or 0.0
            lucro_base = lucro_base or 0.0
            v_duplo = v_duplo or 0.0
            bateu_bool = str(bateu).lower() in ["1", "true"]
            lucro_real = lucro_base + (v_duplo if bateu_bool else 0.0)
            casa_exibicao = casa if casa not in ["", None, "None"] else "Desconhecida"
            condicao = condicao or ""
            ganhou = ganhou or ""

            if condicao == "Apenas se perder a aposta" and ganhou not in [RESULTADO_SIM, RESULTADO_NAO]:
                pendentes_confirmacao.append({
                    "id": id_op,
                    "data": data,
                    "casa": casa_exibicao,
                    "valor_fb": valor_fb,
                    "lucro_real": lucro_real,
                    "ganhou": ganhou,
                })
                continue

            grupo = agrupadas_convertiveis.setdefault(casa_exibicao, {
                "ids": [],
                "quantidade": 0,
                "valor_total": 0.0,
                "lucro_total": 0.0,
            })
            grupo["ids"].append(id_op)
            grupo["quantidade"] += 1
            grupo["valor_total"] += valor_fb
            grupo["lucro_total"] += lucro_real

        row = 0
        for pendente in pendentes_confirmacao:
            self.tab_ativas.insertRow(row)
            self.tab_ativas.setItem(row, 0, self.criar_item(pendente["data"]))
            self.tab_ativas.setItem(row, 1, self.criar_item(pendente["casa"]))
            self.tab_ativas.setItem(row, 2, self.criar_item(f"R$ {pendente['valor_fb']:.2f}"))
            self.tab_ativas.setItem(
                row, 3, self.criar_item(
                    f"R$ {pendente['lucro_real']:.2f}",
                    COR_VERDE if pendente["lucro_real"] >= 0 else COR_VERMELHO
                )
            )
            self.tab_ativas.setCellWidget(row, 4, self.criar_combo_resultado(pendente["id"], pendente["ganhou"]))
            self.tab_ativas.setCellWidget(row, 5, self.criar_container_vazio())
            row += 1

        for casa_exibicao, grupo in agrupadas_convertiveis.items():
            self.tab_ativas.insertRow(row)
            self.tab_ativas.setItem(row, 0, self.criar_item(self.texto_qtd_itens(grupo["quantidade"])))
            self.tab_ativas.setItem(row, 1, self.criar_item(casa_exibicao))
            self.tab_ativas.setItem(row, 2, self.criar_item(f"R$ {grupo['valor_total']:.2f}"))
            self.tab_ativas.setItem(
                row, 3, self.criar_item(
                    f"R$ {grupo['lucro_total']:.2f}",
                    COR_VERDE if grupo["lucro_total"] >= 0 else COR_VERMELHO
                )
            )
            self.tab_ativas.setItem(row, 4, self.criar_item("", mostrar_hifen=False))
            self.tab_ativas.setCellWidget(
                row, 5, self.criar_botao_converter(casa_exibicao, grupo["valor_total"], grupo["ids"])
            )
            row += 1

        conexao.close()
        self.carregar_freebets_convertidas()

    def carregar_freebets_convertidas(self):
        self.tab_convertidas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT c.data_operacao, v.data_operacao, c.casa_destino_freebet, c.valor_da_freebet,
                   c.lucro_final, c.bateu_duplo, c.valor_freebet_coletada, v.lucro_final,
                   v.valor_da_freebet, v.bateu_duplo, v.valor_freebet_coletada,
                   c.status_freebet, c.ganhou_freebet
            FROM Procedimentos_Historico c
            LEFT JOIN Procedimentos_Historico v
                ON v.id_freebet_origem = c.id AND v.tipo_procedimento = 'Converter Freebet'
            WHERE c.tipo_procedimento = 'Coletar Freebet' AND c.status_freebet IN ('Usada', 'Finalizada')
            ORDER BY c.id DESC
        """)

        for row, (data_col, data_conv, casa, v_fb_col, l_col_base, b_col, v_dup_col, l_conv_base, v_fb_conv, b_conv, v_dup_conv, status_fb, ganhou) in enumerate(cursor.fetchall()):
            self.tab_convertidas.insertRow(row)

            v_fb_col = v_fb_col or 0.0
            v_dup_col = v_dup_col or 0.0
            v_dup_conv = v_dup_conv or 0.0
            bateu_col = str(b_col).lower() in ["1", "true"]
            bateu_conv = str(b_conv).lower() in ["1", "true"]
            lucro_col_real = (l_col_base or 0.0) + (v_dup_col if bateu_col else 0.0)
            tem_conversao = data_conv not in [None, "", "None"]
            lucro_conv_real = (l_conv_base or 0.0) + (v_dup_conv if bateu_conv else 0.0) if tem_conversao else None
            lucro_total = lucro_col_real + (lucro_conv_real or 0.0)
            casa_exibicao = casa if casa not in ["", None, "None"] else "Desconhecida"

            if tem_conversao:
                texto_data = f"{data_col} -> {data_conv}"
            elif status_fb == "Finalizada" and ganhou == RESULTADO_NAO:
                texto_data = f"{data_col} -> {RESULTADO_NAO} ganhou"
            else:
                texto_data = f"{data_col} -> -"

            self.tab_convertidas.setItem(row, 0, self.criar_item(texto_data))
            item_casa = self.criar_item(casa_exibicao)
            item_casa.setToolTip(casa_exibicao)
            self.tab_convertidas.setItem(row, 1, item_casa)
            self.tab_convertidas.setItem(row, 2, self.criar_item(f"R$ {v_fb_col:.2f}"))
            self.tab_convertidas.setItem(
                row, 3, self.criar_item(
                    f"R$ {lucro_col_real:.2f}",
                    COR_VERDE if lucro_col_real >= 0 else COR_VERMELHO
                )
            )

            if tem_conversao:
                self.tab_convertidas.setItem(
                    row, 4, self.criar_item(
                        f"R$ {lucro_conv_real:.2f}",
                        COR_VERDE if lucro_conv_real >= 0 else COR_VERMELHO
                    )
                )
            else:
                self.tab_convertidas.setItem(row, 4, self.criar_item("-", "#71717a"))

            self.tab_convertidas.setItem(
                row, 5, self.criar_item(
                    f"R$ {lucro_total:.2f}",
                    COR_VERDE if lucro_total >= 0 else COR_VERMELHO,
                    bold=True
                )
            )

        conexao.close()
