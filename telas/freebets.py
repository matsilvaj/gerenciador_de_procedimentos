from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QTabWidget, QComboBox,
    QDialog, QDialogButtonBox, QAbstractItemView, QLineEdit, QFormLayout,
    QCompleter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from datetime import datetime

from core import database
from core import tema
from telas.componentes import AvisoTabelaVazia
from telas.procedimentos import DialogNovoProcedimento, TabelaProcedimentos

COR_VERDE = tema.COR_POSITIVO
COR_VERMELHO = tema.COR_NEGATIVO
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


class DialogSelecionarFreebet(QDialog):
    def __init__(self, freebets, parent=None):
        super().__init__(parent)
        self.freebets = freebets
        self.id_selecionado = None
        self.setWindowTitle("Selecionar Freebet")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titulo = QLabel("Escolha qual freebet deseja editar")
        titulo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {tema.TEXTO};")
        layout.addWidget(titulo)

        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["Evento", "Valor FB", "Resultado Final"])
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.Stretch)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.setShowGrid(False)
        self.tabela.setStyleSheet(tema.estilo_tabela_cartao())
        self.tabela.cellDoubleClicked.connect(lambda row, _col: self.selecionar_linha(row))
        layout.addWidget(self.tabela)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.button(QDialogButtonBox.Ok).setText("Editar")
        botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.confirmar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        self.carregar()

    def criar_item(self, texto):
        item = QTableWidgetItem(str(texto))
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def carregar(self):
        for row, freebet in enumerate(self.freebets):
            self.tabela.insertRow(row)
            self.tabela.setItem(row, 0, self.criar_item(freebet.get("evento") or "Sem evento"))
            self.tabela.setItem(row, 1, self.criar_item(f"R$ {freebet.get('valor_fb', 0.0):.2f}"))
            self.tabela.setItem(row, 2, self.criar_item(f"R$ {freebet.get('resultado_final', 0.0):.2f}"))
            self.tabela.item(row, 0).setData(Qt.UserRole, freebet["id"])

        if self.freebets:
            self.tabela.selectRow(0)

    def selecionar_linha(self, row):
        item = self.tabela.item(row, 0)
        if item:
            self.id_selecionado = item.data(Qt.UserRole)
            self.accept()

    def confirmar(self):
        row = self.tabela.currentRow()
        if row >= 0:
            self.selecionar_linha(row)


class DialogSelecionarConversao(QDialog):
    """Permite escolher quais freebets do grupo serao convertidas."""

    def __init__(self, casa, freebets, parent=None):
        super().__init__(parent)
        self.freebets = freebets
        self.ids_selecionados = []
        self.valor_selecionado = 0.0
        self.setWindowTitle("Selecionar Freebets para Converter")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titulo = QLabel(f"Quais freebets de {casa} você quer converter?")
        titulo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {tema.TEXTO};")
        layout.addWidget(titulo)

        subtitulo = QLabel("Marque uma ou mais freebets. O valor total será enviado para a calculadora.")
        subtitulo.setStyleSheet(f"font-size: 12px; font-weight: normal; color: {tema.TEXTO_TERCIARIO};")
        layout.addWidget(subtitulo)

        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["Evento", "Valor FB", "Resultado Final"])
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.Stretch)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela.setShowGrid(False)
        self.tabela.setStyleSheet(tema.estilo_tabela_cartao())
        self.tabela.itemChanged.connect(self.atualizar_resumo)
        layout.addWidget(self.tabela)

        linha_acoes = QHBoxLayout()
        btn_todas = QPushButton("Selecionar todas")
        btn_nenhuma = QPushButton("Limpar seleção")
        for botao in (btn_todas, btn_nenhuma):
            botao.setCursor(Qt.PointingHandCursor)
            botao.setProperty("variante", "fantasma")
        btn_todas.clicked.connect(lambda: self.marcar_todas(True))
        btn_nenhuma.clicked.connect(lambda: self.marcar_todas(False))

        self.lbl_resumo = QLabel("")
        self.lbl_resumo.setStyleSheet(f"color: {tema.TEXTO_SECUNDARIO}; font-size: 13px; font-weight: bold;")

        linha_acoes.addWidget(btn_todas)
        linha_acoes.addWidget(btn_nenhuma)
        linha_acoes.addStretch()
        linha_acoes.addWidget(self.lbl_resumo)
        layout.addLayout(linha_acoes)

        self.botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botoes.button(QDialogButtonBox.Ok).setText("Converter")
        self.botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.botoes.accepted.connect(self.confirmar)
        self.botoes.rejected.connect(self.reject)
        layout.addWidget(self.botoes)

        self.carregar()

    def criar_item(self, texto):
        item = QTableWidgetItem(str(texto))
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def carregar(self):
        self.tabela.blockSignals(True)
        for row, freebet in enumerate(self.freebets):
            self.tabela.insertRow(row)
            item_evento = self.criar_item(freebet.get("evento") or "Sem evento")
            item_evento.setFlags(item_evento.flags() | Qt.ItemIsUserCheckable)
            item_evento.setCheckState(Qt.Unchecked)
            item_evento.setData(Qt.UserRole, freebet["id"])
            item_evento.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tabela.setItem(row, 0, item_evento)
            self.tabela.setItem(row, 1, self.criar_item(f"R$ {freebet.get('valor_fb', 0.0):.2f}"))
            self.tabela.setItem(row, 2, self.criar_item(f"R$ {freebet.get('resultado_final', 0.0):.2f}"))
        self.tabela.blockSignals(False)
        self.atualizar_resumo()

    def marcar_todas(self, marcar):
        self.tabela.blockSignals(True)
        for row in range(self.tabela.rowCount()):
            self.tabela.item(row, 0).setCheckState(Qt.Checked if marcar else Qt.Unchecked)
        self.tabela.blockSignals(False)
        self.atualizar_resumo()

    def coletar_selecao(self):
        ids = []
        valor = 0.0
        for row in range(self.tabela.rowCount()):
            item = self.tabela.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
                valor += self.freebets[row].get("valor_fb", 0.0)
        return ids, valor

    def atualizar_resumo(self, *_):
        ids, valor = self.coletar_selecao()
        self.lbl_resumo.setText(f"{len(ids)} selecionada(s) · R$ {valor:.2f}")
        self.botoes.button(QDialogButtonBox.Ok).setEnabled(bool(ids))

    def confirmar(self):
        ids, valor = self.coletar_selecao()
        if not ids:
            return
        self.ids_selecionados = ids
        self.valor_selecionado = valor
        self.accept()


class DialogNovaFreebet(QDialog):
    """Cadastro rapido de uma freebet: apenas casa e valor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dados_finais = None
        self.setWindowTitle("Adicionar Freebet")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Nova Freebet")
        titulo.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {tema.TEXTO};")
        layout.addWidget(titulo)

        subtitulo = QLabel("Informe a casa e o valor. A freebet entra como pendente e já fica disponível para conversão.")
        subtitulo.setStyleSheet(f"font-size: 12px; font-weight: normal; color: {tema.TEXTO_TERCIARIO};")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        formulario = QFormLayout()
        formulario.setSpacing(10)
        formulario.setLabelAlignment(Qt.AlignLeft)

        self.combo_casa = QComboBox()
        self.combo_casa.setEditable(True)
        self.combo_casa.addItems(database.listar_casas())
        self.combo_casa.setCurrentText("")
        self.combo_casa.lineEdit().setPlaceholderText("Selecione ou digite uma casa")
        self.combo_casa.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.combo_casa.completer().setCaseSensitivity(Qt.CaseInsensitive)

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText("0,00")
        self.input_valor.returnPressed.connect(self.confirmar)

        formulario.addRow("Casa", self.combo_casa)
        formulario.addRow("Valor da freebet (R$)", self.input_valor)
        layout.addLayout(formulario)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet(f"color: {COR_VERMELHO}; font-size: 12px; font-weight: bold;")
        self.lbl_erro.hide()
        layout.addWidget(self.lbl_erro)

        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.button(QDialogButtonBox.Ok).setText("Adicionar")
        botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.confirmar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        self.combo_casa.setFocus()

    def mostrar_erro(self, mensagem):
        self.lbl_erro.setText(mensagem)
        self.lbl_erro.show()

    def confirmar(self):
        casa = self.combo_casa.currentText().strip()
        if not casa:
            self.mostrar_erro("Escolha ou digite a casa da freebet.")
            self.combo_casa.setFocus()
            return

        texto_valor = self.input_valor.text().strip().replace("R$", "").strip()
        if "," in texto_valor:
            texto_valor = texto_valor.replace(".", "").replace(",", ".")
        try:
            valor = float(texto_valor)
        except ValueError:
            self.mostrar_erro("Valor inválido. Use apenas números, ex: 50,00.")
            self.input_valor.setFocus()
            return

        if valor <= 0:
            self.mostrar_erro("O valor da freebet precisa ser maior que zero.")
            self.input_valor.setFocus()
            return

        agora = datetime.now()
        self.dados_finais = {
            "data_operacao": agora.strftime("%d/%m/%Y"),
            "mes_referencia": agora.strftime("%m/%Y"),
            "tipo_procedimento": "Coletar Freebet",
            "casas_envolvidas": casa,
            "casa_destino_freebet": casa,
            "jogo_time_pa": "",
            "lucro_final": 0.0,
            "bateu_duplo": None,
            "condicao_freebet": "",
            "valor_freebet_coletada": 0.0,
            "valor_da_freebet": valor,
            "observacao": "",
            "status_freebet": "Pendente",
            "ganhou_freebet": "",
            "categoria_gasto": "",
        }
        self.accept()


class TelaFreebets(QWidget):
    sinal_converter_calculadora = Signal(str, float, list)

    def __init__(self):
        super().__init__()
        self.historico_desfazer = []
        self.freebets_por_linha = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)

        topo = QHBoxLayout()
        titulo = QLabel("Gest\u00e3o de Freebets")
        titulo.setStyleSheet(tema.estilo_titulo_tela())
        topo.addWidget(titulo)
        topo.addStretch()

        self.btn_adicionar = QPushButton("+ Adicionar Freebet")
        self.btn_adicionar.setCursor(Qt.PointingHandCursor)
        self.btn_adicionar.setProperty("variante", "primario")
        self.btn_adicionar.clicked.connect(self.adicionar_freebet)
        topo.addWidget(self.btn_adicionar)
        layout.addLayout(topo)

        self.btn_desfazer = QPushButton("\u21b6 Desfazer mudan\u00e7a")
        self.btn_desfazer.setCursor(Qt.PointingHandCursor)
        self.btn_desfazer.setProperty("variante", "fantasma")
        self.btn_desfazer.clicked.connect(self.desfazer_ultima_acao)
        self.btn_desfazer.hide()
        layout.addWidget(self.btn_desfazer, alignment=Qt.AlignRight)

        self.abas = QTabWidget()
        self.abas.setStyleSheet("QTabBar::tab { margin-bottom: 14px; }")

        aba_disponiveis = QWidget()
        layout_disp = QVBoxLayout(aba_disponiveis)
        layout_disp.setContentsMargins(0, 0, 0, 0)
        self.tab_ativas = TabelaProcedimentos(0, 6)
        self.tab_ativas.setHorizontalHeaderLabels(["Data / Qtd", "Casa", "Valor FB", "Lucro Base", "Ganhou?", ""])
        self.configurar_tabela(self.tab_ativas, tem_acao=True, tem_resultado=True)
        self.tab_ativas.cellClicked.connect(self.editar_freebet_da_linha)
        layout_disp.addWidget(self.tab_ativas)
        self.aviso_ativas = AvisoTabelaVazia(
            self.tab_ativas,
            "Nenhuma freebet dispon\u00edvel",
            "Use \u201c+ Adicionar Freebet\u201d para cadastrar uma e ela aparece aqui.",
        )
        self.abas.addTab(aba_disponiveis, "Dispon\u00edveis")

        aba_convertidas = QWidget()
        layout_conv = QVBoxLayout(aba_convertidas)
        layout_conv.setContentsMargins(0, 0, 0, 0)
        self.tab_convertidas = TabelaProcedimentos(0, 6)
        self.tab_convertidas.setHorizontalHeaderLabels(["Data (Col \u2794 Conv)", "Casa", "Valor FB", "Lucro Base", "Lucro Final", "Total"])
        self.configurar_tabela(self.tab_convertidas)
        self.tab_convertidas.cellClicked.connect(self.editar_freebet_da_linha)
        layout_conv.addWidget(self.tab_convertidas)
        self.aviso_convertidas = AvisoTabelaVazia(
            self.tab_convertidas,
            "Nenhuma freebet convertida ainda",
            "Depois de converter uma freebet, o hist\u00f3rico dela fica registrado aqui.",
        )
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

        tabela.setStyleSheet(
            "QTableWidget::item:selected { background-color: transparent; color: %s; }" % tema.TEXTO
        )

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

    def registrar_freebets_linha(self, tabela, row, freebets):
        self.freebets_por_linha[(id(tabela), row)] = freebets
        for col in range(tabela.columnCount()):
            item = tabela.item(row, col)
            if item:
                item.setToolTip("Clique para editar")

    def texto_qtd_itens(self, quantidade):
        return f"{quantidade} item" if quantidade == 1 else f"{quantidade} itens"

    def criar_container_vazio(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        return container

    def criar_botao_converter(self, casa, valor, freebets):
        container_btn = QWidget()
        lay_btn = QHBoxLayout(container_btn)
        lay_btn.setContentsMargins(5, 2, 5, 2)

        btn_usar = QPushButton("Converter")
        btn_usar.setCursor(Qt.PointingHandCursor)
        btn_usar.setProperty("variante", "primario")
        btn_usar.setStyleSheet("padding: 6px 10px; font-size: 12px;")
        btn_usar.clicked.connect(
            lambda _, c=casa, v=valor, fbs=list(freebets): self.iniciar_conversao(c, v, fbs)
        )
        lay_btn.addWidget(btn_usar)
        return container_btn

    def adicionar_freebet(self):
        dialog = DialogNovaFreebet(self)
        if not dialog.exec() or not dialog.dados_finais:
            return

        dados = dialog.dados_finais
        database.adicionar_casa(dados["casa_destino_freebet"])
        id_novo = database.salvar_procedimento(dados)
        if id_novo:
            self.registrar_acao_desfazer({"tipo": "nova_freebet", "id": id_novo})
        self.carregar_freebets_ativas()

    def iniciar_conversao(self, casa, valor_total, freebets):
        if len(freebets) <= 1:
            ids = [fb["id"] for fb in freebets]
            if not ids:
                return
            self.sinal_converter_calculadora.emit(casa, valor_total, ids)
            return

        dialog = DialogSelecionarConversao(casa, freebets, self)
        if dialog.exec() and dialog.ids_selecionados:
            self.sinal_converter_calculadora.emit(
                casa, dialog.valor_selecionado, dialog.ids_selecionados
            )

    def criar_combo_resultado(self, id_op, valor_atual):
        combo = QComboBox()
        combo.addItems([RESULTADO_SIM, RESULTADO_NAO])
        combo.setCursor(Qt.PointingHandCursor)
        combo.setMinimumWidth(96)
        combo.setStyleSheet("QComboBox { padding: 4px 10px; min-height: 26px; }")

        if valor_atual in [RESULTADO_SIM, RESULTADO_NAO]:
            combo.setCurrentText(valor_atual)
        else:
            combo.setCurrentIndex(-1)

        combo.currentTextChanged.connect(
            lambda texto, procedimento_id=id_op: self.atualizar_resultado_ganhou(procedimento_id, texto)
        )
        return ComboBoxContainer(combo)

    def editar_freebet_da_linha(self, row, _col):
        tabela = self.sender()
        freebets = self.freebets_por_linha.get((id(tabela), row), [])
        if not freebets:
            return

        if len(freebets) == 1:
            self.editar_procedimento(freebets[0]["id"])
            return

        dialog = DialogSelecionarFreebet(freebets, self)
        if dialog.exec() and dialog.id_selecionado:
            self.editar_procedimento(dialog.id_selecionado)

    def buscar_dados_edicao(self, id_op):
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT tipo_procedimento, jogo_time_pa, casas_envolvidas, lucro_final,
                   valor_freebet_coletada, observacao, condicao_freebet,
                   casa_destino_freebet, valor_da_freebet
            FROM Procedimentos_Historico
            WHERE id = ?
        """, (id_op,))
        linha = cursor.fetchone()
        conexao.close()

        if not linha:
            return None

        tipo, jogo, casas, lucro, v_duplo, obs, cond, casa_fb, v_fb = linha
        return {
            'tipo': tipo,
            'jogo': jogo,
            'casas': casas,
            'lucro_base': lucro,
            'v_duplo': v_duplo,
            'obs': obs,
            'condicao': cond,
            'casa_fb': casa_fb,
            'v_fb': v_fb,
        }

    def editar_procedimento(self, id_op):
        dados_edicao = self.buscar_dados_edicao(id_op)
        if not dados_edicao:
            return

        dialog = DialogNovoProcedimento(self, dados_edicao)
        if dialog.exec():
            database.atualizar_procedimento(id_op, dialog.dados_finais)
            self.carregar_freebets_ativas()

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
        elif acao['tipo'] == 'nova_freebet':
            database.excluir_procedimento(acao['id'])
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
        self.freebets_por_linha = {}
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id, data_operacao, jogo_time_pa, casa_destino_freebet, valor_da_freebet,
                   lucro_final, bateu_duplo, valor_freebet_coletada, condicao_freebet, ganhou_freebet
            FROM Procedimentos_Historico
            WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'
            ORDER BY id DESC
        """)

        pendentes_confirmacao = []
        agrupadas_convertiveis = {}

        for id_op, data, evento, casa, valor_fb, lucro_base, bateu, v_duplo, condicao, ganhou in cursor.fetchall():
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
                    "evento": evento,
                    "casa": casa_exibicao,
                    "valor_fb": valor_fb,
                    "lucro_real": lucro_real,
                    "ganhou": ganhou,
                    "resultado_final": lucro_real,
                })
                continue

            grupo = agrupadas_convertiveis.setdefault(casa_exibicao, {
                "ids": [],
                "quantidade": 0,
                "valor_total": 0.0,
                "lucro_total": 0.0,
                "eventos": [],
            })
            grupo["ids"].append(id_op)
            grupo["eventos"].append({
                "id": id_op,
                "evento": evento,
                "valor_fb": valor_fb,
                "resultado_final": lucro_real,
            })
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
            self.registrar_freebets_linha(
                self.tab_ativas,
                row,
                [{
                    "id": pendente["id"],
                    "evento": pendente["evento"],
                    "valor_fb": pendente["valor_fb"],
                    "resultado_final": pendente["resultado_final"],
                }]
            )
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
                row, 5, self.criar_botao_converter(casa_exibicao, grupo["valor_total"], grupo["eventos"])
            )
            self.registrar_freebets_linha(self.tab_ativas, row, grupo["eventos"])
            row += 1

        conexao.close()
        self.aviso_ativas.atualizar()
        self.carregar_freebets_convertidas()

    def carregar_freebets_convertidas(self):
        self.tab_convertidas.setRowCount(0)
        conexao = database.conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT c.id, c.data_operacao, v.data_operacao, c.jogo_time_pa,
                   c.casa_destino_freebet, c.valor_da_freebet,
                   c.lucro_final, c.bateu_duplo, c.valor_freebet_coletada, v.lucro_final,
                   v.valor_da_freebet, v.bateu_duplo, v.valor_freebet_coletada,
                   c.status_freebet, c.ganhou_freebet
            FROM Procedimentos_Historico c
            LEFT JOIN Procedimentos_Historico v
                ON v.id_freebet_origem = c.id AND v.tipo_procedimento = 'Converter Freebet'
            WHERE c.tipo_procedimento = 'Coletar Freebet' AND c.status_freebet IN ('Usada', 'Finalizada')
            ORDER BY c.id DESC
        """)

        for row, (id_col, data_col, data_conv, evento, casa, v_fb_col, l_col_base, b_col, v_dup_col, l_conv_base, v_fb_conv, b_conv, v_dup_conv, status_fb, ganhou) in enumerate(cursor.fetchall()):
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
            self.registrar_freebets_linha(
                self.tab_convertidas,
                row,
                [{
                    "id": id_col,
                    "evento": evento,
                    "valor_fb": v_fb_col,
                    "resultado_final": lucro_total,
                }]
            )

        conexao.close()
        self.aviso_convertidas.atualizar()
