from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QCheckBox,
    QFormLayout, QGroupBox, QDialog, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QMessageBox, QMenu, QAbstractItemView
)

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor, QBrush, QPainter
from datetime import datetime
from core import database
import locale


# Configuração de idioma para datas
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, '')

# Cores Suavizadas Globais (Paleta Modern Minimalist)
COR_VERDE = "#34d399"
COR_VERMELHO = "#f87171"
COR_AZUL_DESTAQUE = "#3b82f6"

class CheckBoxContainer(QWidget):
    """Container para o checkbox de duplo com área de clique expandida"""
    def __init__(self, checkbox):
        super().__init__()
        self.cb = checkbox
        self.cb.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.cb)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.cb.toggle()
        super().mousePressEvent(event)

class DialogEscolherCasas(QDialog):
    """Janela moderna para seleção e gestão de casas de apostas"""
    def __init__(self, parent=None, casas_selecionadas=None):
        super().__init__(parent)
        self.setWindowTitle("Escolher Casas")
        self.setFixedSize(500, 400) 
        self.setModal(True)
        self.casas_selecionadas = casas_selecionadas if casas_selecionadas else []
        self.modo_exclusao = False 
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #09090b; }}
            QCheckBox {{ color: #f4f4f5; font-size: 14px; padding: 5px; }}
            QPushButton {{ background-color: #27272a; color: white; border-radius: 8px; padding: 8px; font-weight: bold; border: none; }}
            QLineEdit {{ background-color: #18181b; color: white; padding: 10px; border: none; border-radius: 8px; outline: none; }}
        """)

        layout = QVBoxLayout(self)
        topo_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("Pesquisar ou adicionar nova casa...")
        self.input_busca.textChanged.connect(self.filtrar_casas)
        self.input_busca.returnPressed.connect(self.adicionar_nova_casa)
        
        self.btn_modo_exclusao = QPushButton("Excluir")
        self.btn_modo_exclusao.setStyleSheet("background-color: transparent; color: #71717a;")
        self.btn_modo_exclusao.setAutoDefault(False)
        self.btn_modo_exclusao.clicked.connect(self.alternar_modo_exclusao)
        
        topo_layout.addWidget(self.input_busca)
        topo_layout.addWidget(self.btn_modo_exclusao)
        layout.addLayout(topo_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: #18181b; border-radius: 12px;")
        
        self.scroll_content = QWidget()
        self.layout_checks = QGridLayout(self.scroll_content) 
        self.layout_checks.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch() 
        self.btn_ok = QPushButton("CONFIRMAR")
        self.btn_ok.setStyleSheet(f"background-color: {COR_AZUL_DESTAQUE}; color: white; padding: 10px 20px; border-radius: 8px;")
        self.btn_ok.setAutoDefault(False)
        self.btn_ok.setDefault(False)
        self.btn_ok.clicked.connect(self.confirmar_e_fechar)
        botoes_layout.addWidget(self.btn_ok)
        layout.addLayout(botoes_layout)

        self.checkboxes = {}
        self.botoes_deletar = [] 
        self.carregar_lista_casas()

    def alternar_modo_exclusao(self):
        self.modo_exclusao = not self.modo_exclusao
        self.btn_modo_exclusao.setText("Concluir" if self.modo_exclusao else "Excluir")
        self.btn_modo_exclusao.setStyleSheet(f"background-color: transparent; color: {COR_VERMELHO};" if self.modo_exclusao else "background-color: transparent; color: #71717a;")
        for btn in self.botoes_deletar: btn.setVisible(self.modo_exclusao)

    def carregar_lista_casas(self, filtro=""):
        for i in reversed(range(self.layout_checks.count())):
            widget = self.layout_checks.itemAt(i).widget()
            if widget: widget.deleteLater()
        self.checkboxes.clear(); self.botoes_deletar.clear()

        casas = database.listar_casas()
        row, col = 0, 0
        for casa in casas:
            if filtro.lower() in casa.lower():
                container_casa = QWidget()
                lay_casa = QHBoxLayout(container_casa)
                lay_casa.setContentsMargins(0, 0, 0, 0)
                
                chk = QCheckBox(casa)
                if casa in self.casas_selecionadas: chk.setChecked(True)
                
                btn_del = QPushButton("-")
                btn_del.setFixedSize(24, 24)
                btn_del.setStyleSheet(f"color: {COR_VERMELHO}; background: #27272a; border-radius: 6px;")
                btn_del.clicked.connect(lambda _, c=casa: self.deletar_casa(c))
                btn_del.setVisible(self.modo_exclusao) 
                self.botoes_deletar.append(btn_del)
                
                lay_casa.addWidget(chk); lay_casa.addWidget(btn_del); lay_casa.addStretch() 
                self.layout_checks.addWidget(container_casa, row, col)
                self.checkboxes[casa] = chk
                col += 1
                if col > 2: col = 0; row += 1

    def sync_selecionadas(self):
        for casa, chk in self.checkboxes.items():
            if chk.isChecked() and casa not in self.casas_selecionadas: self.casas_selecionadas.append(casa)
            elif not chk.isChecked() and casa in self.casas_selecionadas: self.casas_selecionadas.remove(casa)

    def filtrar_casas(self, texto):
        self.sync_selecionadas(); self.carregar_lista_casas(texto)
        
    def adicionar_nova_casa(self):
        nova_casa = self.input_busca.text().strip()
        if nova_casa:
            database.adicionar_casa(nova_casa)
            if nova_casa not in self.casas_selecionadas:
                self.casas_selecionadas.append(nova_casa)
            self.input_busca.clear()
            self.carregar_lista_casas()

    def deletar_casa(self, nome_casa):
        if QMessageBox.question(self, "Excluir", f"Deseja excluir '{nome_casa}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            database.excluir_casa(nome_casa)
            if nome_casa in self.casas_selecionadas: self.casas_selecionadas.remove(nome_casa)
            self.carregar_lista_casas(self.input_busca.text()) 

    def confirmar_e_fechar(self):
        self.sync_selecionadas(); self.accept()

    def get_selecionadas(self):
        return self.casas_selecionadas
    
class DialogFiltros(QDialog):
    """Popup para filtrar os procedimentos na tabela principal"""
    def __init__(self, parent=None, filtros_atuais=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.filtros_atuais = filtros_atuais if filtros_atuais else {"tipos": [], "casas": []}
        
        self.setStyleSheet("""
            QDialog { background-color: #09090b; }
            QGroupBox { border: none; margin-top: 15px; padding-top: 15px; color: #f4f4f5; }
            QLabel { color: #a1a1aa; font-weight: bold; }
            QCheckBox { color: #f4f4f5; font-size: 14px; padding: 5px; }
            QPushButton { background-color: #27272a; color: white; border-radius: 8px; padding: 10px; font-weight: bold; border: none; }
        """)

        layout = QVBoxLayout(self)

        grupo_tipos = QGroupBox("Tipo de Procedimento")
        lay_tipos = QVBoxLayout()
        self.checks_tipos = {}
        for t in ["SureBet", "Tentativa de Duplo", "Coletar Freebet", "Converter Freebet", "Cassino"]:
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

class DialogNovoProcedimento(QDialog):
    """Janela ultra moderna para criação ou edição de procedimentos"""
    def __init__(self, parent=None, dados_edicao=None):
        super().__init__(parent)
        self.dados_edicao = dados_edicao
        self.setWindowTitle("Editar" if dados_edicao else "Novo")
        self.setMinimumWidth(600)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog { background-color: #09090b; }
            QGroupBox { border: none; margin-top: 10px; padding-top: 20px; color: #a1a1aa; font-weight: normal; font-size: 13px; }
            QLabel { color: #f4f4f5; }
            QLineEdit, QComboBox { background-color: #18181b; color: white; border: none; padding: 12px; border-radius: 8px; outline: none; }
            QPushButton { background-color: #27272a; color: white; border-radius: 8px; padding: 10px; border: none;}
        """)

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setSizeConstraint(QVBoxLayout.SetFixedSize) 

        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(10)
        self.botoes_tipo = []
        for tipo in ["SureBet", "Tentativa de Duplo", "Coletar Freebet", "Converter Freebet", "Cassino"]:
            btn = QPushButton(tipo)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tipo: self.selecionar_tipo(t))
            layout_botoes.addWidget(btn)
            self.botoes_tipo.append(btn)
        self.layout_principal.addLayout(layout_botoes)

        self.grupo_detalhes = QGroupBox("Detalhes")
        self.layout_detalhes = QFormLayout()
        self.layout_detalhes.setVerticalSpacing(15)
        
        self.input_jogo = QLineEdit()
        self.combo_condicao = QComboBox()
        self.combo_condicao.addItems(["Freebet Garantida", "Apenas se perder a aposta"])
        
        self.lbl_casa_freebet = QLabel("")
        self.btn_escolher_casa_fb = QPushButton("Escolher")
        self.btn_escolher_casa_fb.clicked.connect(self.abrir_seletor_casa_freebet)
        
        self.container_casa_fb = QWidget()
        lay_cfb = QHBoxLayout(self.container_casa_fb)
        lay_cfb.setContentsMargins(0, 0, 0, 0)
        lay_cfb.addWidget(self.lbl_casa_freebet, stretch=1); lay_cfb.addWidget(self.btn_escolher_casa_fb)

        self.layout_detalhes.addRow("Jogo/Time:", self.input_jogo)
        self.layout_detalhes.addRow("Condição FB:", self.combo_condicao)
        self.layout_detalhes.addRow("Casa da FB:", self.container_casa_fb)
        self.grupo_detalhes.setLayout(self.layout_detalhes)
        self.layout_principal.addWidget(self.grupo_detalhes)

        grupo_casas = QGroupBox("Casas Envolvidas")
        layout_casas = QHBoxLayout()
        self.lbl_casas_selecionadas = QLabel("Nenhuma selecionada")
        self.btn_escolher_casas = QPushButton("Escolher")
        self.btn_escolher_casas.clicked.connect(self.abrir_seletor_casas)
        layout_casas.addWidget(self.lbl_casas_selecionadas, stretch=1); layout_casas.addWidget(self.btn_escolher_casas)
        grupo_casas.setLayout(layout_casas)
        self.layout_principal.addWidget(grupo_casas)

        grupo_valores = QGroupBox("Valores (R$)")
        self.layout_valores = QFormLayout()
        self.layout_valores.setVerticalSpacing(15)
        
        self.input_valor_duplo = QLineEdit() 
        self.input_valor_freebet = QLineEdit()
        
        self.check_lucro_igual = QCheckBox("Lucro igual nas posições")
        self.check_lucro_igual.toggled.connect(self.alternar_lucro_igual)
        self.input_entrada = QLineEdit()
        self.lista_inputs_protecoes = []; self.lista_containers_protecoes = []
        
        self.btn_add_protecao = QPushButton("+ add proteção")
        self.btn_add_protecao.setCursor(Qt.PointingHandCursor)
        self.btn_add_protecao.setStyleSheet("color: #71717a; background: transparent; text-align: left; font-size: 12px; padding: 0;")
        self.btn_add_protecao.clicked.connect(lambda: self.adicionar_campo_protecao())
        
        self.layout_valores.addRow("Valor Duplo (R$):", self.input_valor_duplo)
        self.layout_valores.addRow("Valor da Freebet (R$):", self.input_valor_freebet)
        self.layout_valores.addRow("", self.check_lucro_igual)
        self.layout_valores.addRow("Entrada principal:", self.input_entrada)
        self.adicionar_campo_protecao(texto_padrao="Proteção 1:", eh_padrao=True)
        self.layout_valores.addRow("", self.btn_add_protecao)
        grupo_valores.setLayout(self.layout_valores)
        self.layout_principal.addWidget(grupo_valores)

        self.btn_add_obs = QPushButton("+ add observação")
        self.btn_add_obs.setCursor(Qt.PointingHandCursor)
        self.btn_add_obs.setStyleSheet("color: #71717a; background: transparent; text-align: left; font-size: 12px; padding: 0;")
        self.btn_add_obs.clicked.connect(self.mostrar_campo_obs)
        
        self.container_obs = QWidget()
        lay_obs = QHBoxLayout(self.container_obs)
        lay_obs.setContentsMargins(0, 10, 0, 0)
        self.input_obs = QLineEdit()
        self.input_obs.setPlaceholderText("Obs...")
        btn_remover_obs = QPushButton("-")
        btn_remover_obs.setFixedSize(38, 38)
        btn_remover_obs.setStyleSheet("color: #71717a; background: #27272a; border-radius: 8px; font-weight: bold; font-size: 16px;")
        btn_remover_obs.clicked.connect(self.esconder_campo_obs)
        lay_obs.addWidget(self.input_obs); lay_obs.addWidget(btn_remover_obs)
        self.container_obs.hide()
        
        self.layout_principal.addWidget(self.btn_add_obs)
        self.layout_principal.addWidget(self.container_obs)

        self.btn_salvar = QPushButton("SALVAR" if dados_edicao else "CRIAR PROCEDIMENTO")
        self.btn_salvar.setStyleSheet(f"background-color: {COR_AZUL_DESTAQUE}; color: white; font-weight: bold; border-radius: 8px; height: 45px; margin-top: 20px;")
        self.btn_salvar.clicked.connect(self.processar_e_salvar)
        self.layout_principal.addWidget(self.btn_salvar)

        if dados_edicao: self.preencher_dados_edicao()
        else: self.selecionar_tipo("SureBet")

    def adicionar_campo_protecao(self, texto_padrao="Proteção:", eh_padrao=False):
        container = QWidget()
        lay = QHBoxLayout(container); lay.setContentsMargins(0, 0, 0, 0)
        novo_inp = QLineEdit()
        self.lista_inputs_protecoes.append(novo_inp); self.lista_containers_protecoes.append(container)
        lay.addWidget(novo_inp)
        if eh_padrao: self.layout_valores.addRow(texto_padrao, container)
        else:
            btn_remover = QPushButton("-")
            btn_remover.setFixedSize(38, 38) 
            btn_remover.setStyleSheet("color: #71717a; background: #27272a; border-radius: 8px; font-weight: bold; font-size: 16px;")
            btn_remover.clicked.connect(lambda: self.remover_protecao(container, novo_inp))
            lay.addWidget(btn_remover)
            self.layout_valores.insertRow(self.layout_valores.rowCount() - 1, texto_padrao, container)
            novo_inp.setFocus()

    def remover_protecao(self, container, inp):
        if inp in self.lista_inputs_protecoes: self.lista_inputs_protecoes.remove(inp)
        if container in self.lista_containers_protecoes: self.lista_containers_protecoes.remove(container)
        self.layout_valores.removeRow(container)

    def abrir_seletor_casa_freebet(self):
        atuais = [self.lbl_casa_freebet.text()] if self.lbl_casa_freebet.text() != "" else []
        dialog = DialogEscolherCasas(self, atuais)
        if dialog.exec() == QDialog.Accepted:
            sel = dialog.get_selecionadas()
            if sel:
                casa_escolhida = sel[0]
                self.lbl_casa_freebet.setText(casa_escolhida)
                self.lbl_casa_freebet.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
                if self.tipo_selecionado in ["Coletar Freebet", "Converter Freebet"]:
                    self.lbl_casas_selecionadas.setText(casa_escolhida)
                    self.lbl_casas_selecionadas.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
            else: 
                self.lbl_casa_freebet.setText("")
                self.lbl_casa_freebet.setStyleSheet("color: #a1a1aa;")

    def abrir_seletor_casas(self):
        atuais = self.lbl_casas_selecionadas.text().split(" | ") if self.lbl_casas_selecionadas.text() != "Nenhuma selecionada" else []
        dialog = DialogEscolherCasas(self, atuais)
        if dialog.exec() == QDialog.Accepted:
            sel = dialog.get_selecionadas()
            if sel: 
                self.lbl_casas_selecionadas.setText(" | ".join(sel))
                self.lbl_casas_selecionadas.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
                if self.tipo_selecionado in ["Coletar Freebet", "Converter Freebet"]:
                    self.lbl_casa_freebet.setText(sel[0])
                    self.lbl_casa_freebet.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
            else: 
                self.lbl_casas_selecionadas.setText("Nenhuma selecionada")
                self.lbl_casas_selecionadas.setStyleSheet("color: #a1a1aa;")

    def selecionar_tipo(self, tipo):
        self.tipo_selecionado = tipo
        for btn in self.botoes_tipo:
            if btn.text() == tipo: btn.setStyleSheet("background-color: #f4f4f5; color: #09090b; font-weight: bold;")
            else: btn.setStyleSheet("background-color: #27272a; color: #a1a1aa;")
            
        is_cassino = (tipo == "Cassino")
        is_coleta = (tipo == "Coletar Freebet")
        is_conversao = (tipo == "Converter Freebet")
        
        self.grupo_detalhes.setVisible(not is_cassino and tipo != "SureBet")
        
        # Valor Freebet APENAS para Coletar Freebet
        self.input_valor_freebet.setVisible(is_coleta)
        lbl_vfb = self.layout_valores.labelForField(self.input_valor_freebet)
        if lbl_vfb: lbl_vfb.setVisible(is_coleta)
        
        # Valor Duplo aparece sempre que não for Cassino ou Surebet
        self.input_valor_duplo.setVisible(not is_cassino and tipo != "SureBet")
        lbl_vd = self.layout_valores.labelForField(self.input_valor_duplo)
        if lbl_vd: lbl_vd.setVisible(not is_cassino and tipo != "SureBet")
        
        self.combo_condicao.setVisible(is_coleta)
        self.container_casa_fb.setVisible(is_coleta or is_conversao)
        
        lbl_cond = self.layout_detalhes.labelForField(self.combo_condicao)
        if lbl_cond: lbl_cond.setVisible(is_coleta)
        lbl_cfb = self.layout_detalhes.labelForField(self.container_casa_fb)
        if lbl_cfb: lbl_cfb.setVisible(is_coleta or is_conversao)

        self.check_lucro_igual.setVisible(not is_cassino)
        if is_cassino:
            self.btn_add_protecao.setVisible(False)
            for c in self.lista_containers_protecoes:
                c.setVisible(False)
                lbl = self.layout_valores.labelForField(c)
                if lbl: lbl.setVisible(False)
        else:
            self.alternar_lucro_igual(self.check_lucro_igual.isChecked())

        lbl_base = self.layout_valores.labelForField(self.input_entrada)
        if lbl_base:
            if is_cassino: lbl_base.setText("Lucro / Perda (R$):")
            else: lbl_base.setText("Valor Único:" if self.check_lucro_igual.isChecked() else "Entrada principal:")

    def alternar_lucro_igual(self, marcado):
        for container in self.lista_containers_protecoes:
            lbl = self.layout_valores.labelForField(container)
            container.setVisible(not marcado); (lbl.setVisible(not marcado) if lbl else None)
        self.btn_add_protecao.setVisible(not marcado)
        lbl_base = self.layout_valores.labelForField(self.input_entrada)
        if lbl_base: lbl_base.setText("Valor Único:" if marcado else "Entrada principal:")

    def mostrar_campo_obs(self): self.btn_add_obs.hide(); self.container_obs.show(); self.input_obs.setFocus()
    def esconder_campo_obs(self): self.input_obs.clear(); self.container_obs.hide(); self.btn_add_obs.show()

    def preencher_dados_edicao(self):
        d = self.dados_edicao; self.selecionar_tipo(d['tipo']); self.input_jogo.setText(d['jogo'])
        if d['casas'] not in ["None", "-", ""]: self.lbl_casas_selecionadas.setText(d['casas']); self.lbl_casas_selecionadas.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
        if d.get('casa_fb') not in ["None", "-", ""]: self.lbl_casa_freebet.setText(d['casa_fb']); self.lbl_casa_freebet.setStyleSheet(f"color: {COR_AZUL_DESTAQUE};")
        self.check_lucro_igual.setChecked(True); self.input_entrada.setText(str(d['lucro_base']))
        self.input_valor_duplo.setText(str(d['v_duplo']))
        self.input_valor_freebet.setText(str(d.get('v_fb', 0.0)))
        if d['obs']: self.mostrar_campo_obs(); self.input_obs.setText(d['obs'])
        self.combo_condicao.setCurrentText(d.get('condicao', ''))

    def processar_e_salvar(self):
        try:
            v_ent = float(self.input_entrada.text().replace(',', '.'))
            
            if self.tipo_selecionado == "Cassino":
                l_base = v_ent
                jogo_nome = "-"
            else:
                jogo_nome = self.input_jogo.text()
                if self.check_lucro_igual.isChecked(): l_base = v_ent
                else:
                    soma = v_ent; cont = 1
                    for inp in self.lista_inputs_protecoes:
                        txt = inp.text().replace(',', '.')
                        if txt: soma += float(txt); cont += 1
                    l_base = soma / cont
                    
            c_env = self.lbl_casas_selecionadas.text() if self.lbl_casas_selecionadas.text() != "Nenhuma selecionada" else ""
            self.dados_finais = {
                'data_operacao': datetime.now().strftime("%d/%m/%Y"), 'tipo_procedimento': self.tipo_selecionado,
                'casas_envolvidas': c_env, 'jogo_time_pa': jogo_nome, 'lucro_final': l_base,
                'valor_freebet_coletada': float(self.input_valor_duplo.text().replace(',', '.')) if self.input_valor_duplo.isVisible() and self.input_valor_duplo.text() else 0.0,
                'valor_da_freebet': float(self.input_valor_freebet.text().replace(',', '.')) if self.input_valor_freebet.isVisible() and self.input_valor_freebet.text() else 0.0,
                'condicao_freebet': self.combo_condicao.currentText() if self.combo_condicao.isVisible() else '',
                'observacao': self.input_obs.text(), 'mes_referencia': datetime.now().strftime("%m/%Y"),
                'casa_destino_freebet': self.lbl_casa_freebet.text() if self.tipo_selecionado in ["Coletar Freebet", "Converter Freebet"] else "",
                'status_freebet': 'Pendente' if self.tipo_selecionado == "Coletar Freebet" else 'N/A'
            }
            self.accept()
        except: QMessageBox.warning(self, "Erro", "Verifique os números.")

class TabelaProcedimentos(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_row = -1
        
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.cellEntered.connect(self._ao_fazer_hover)
        self.viewport().installEventFilter(self)

    def _ao_fazer_hover(self, row, column):
        if self.hover_row == row:
            return
        self.hover_row = row
        self.viewport().update()

    def eventFilter(self, watched, event):
        if watched == self.viewport() and event.type() == QEvent.Leave:
            self.hover_row = -1
            self.viewport().update()
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        if self.hover_row >= 0:
            rect = self.visualRect(self.model().index(self.hover_row, 0))
            if rect.isValid():
                painter.fillRect(0, rect.top(), self.viewport().width(), rect.height(), QColor(255, 255, 255, 10))
        super().paintEvent(event)

class TelaProcedimentos(QWidget):
    """Painel principal que lista todos os procedimentos"""
    def __init__(self):
        super().__init__()
        self.filtros_avancados = {"tipos": [], "casas": []}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)
        
        titulo = QLabel(f"Procedimentos — {datetime.now().strftime('%B %Y').capitalize()}")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #f4f4f5;")
        layout.addWidget(titulo)
        
        filtros_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("Buscar jogo ou casa...")
        self.input_busca.setStyleSheet("background-color: #18181b; color: white; padding: 12px; border: none; border-radius: 8px; outline: none;")
        self.input_busca.textChanged.connect(self.carregar_tabela)
        
        self.btn_filtros = QPushButton("Filtros")
        self.btn_filtros.setStyleSheet("background-color: #27272a; color: white; font-weight: bold; padding: 12px 20px; border-radius: 8px; border: none;")
        self.btn_filtros.clicked.connect(self.abrir_filtros)
        
        self.btn_abrir_modal = QPushButton("Novo Procedimento")
        self.btn_abrir_modal.setStyleSheet("background-color: #f4f4f5; color: #09090b; border: none; font-weight: bold; padding: 12px 24px; border-radius: 8px;")
        self.btn_abrir_modal.clicked.connect(lambda: self.abrir_pop_up())

        filtros_layout.addWidget(self.input_busca); filtros_layout.addWidget(self.btn_filtros)
        filtros_layout.addStretch(); filtros_layout.addWidget(self.btn_abrir_modal)
        layout.addLayout(filtros_layout)

        self.tabela = TabelaProcedimentos(0, 8)
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Jogo", "Casas", "Lucro Base", "Duplo?", "Lucro Final", ""])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.tabela.setColumnWidth(7, 50)
        
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabela.setColumnWidth(0, 60)
        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tabela.setColumnWidth(5, 75)

        self.tabela.verticalHeader().setVisible(False)
        self.tabela.verticalHeader().setDefaultSectionSize(75)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        
        self.tabela.setShowGrid(False)
        self.tabela.setFocusPolicy(Qt.NoFocus)

        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                color: #f4f4f5;
                border: none;
                outline: none;
                font-size: 14px;
                gridline-color: transparent;
            }
            QTableWidget::item {
                border: none;
                border-bottom: 1px solid rgba(255,255,255,0.03);
                padding: 5px;
                background: transparent;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: #f4f4f5;
                border: none;
                outline: none;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #71717a;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid rgba(255,255,255,0.05);
                padding: 12px 8px;
            }
        """)
                
        layout.addWidget(self.tabela)
        self.carregar_tabela()

    def carregar_tabela(self):
        self.tabela.setRowCount(0)
        f_t = self.input_busca.text().lower()
        conexao = database.conectar(); cursor = conexao.cursor()
        cursor.execute("SELECT id, data_operacao, tipo_procedimento, jogo_time_pa, casas_envolvidas, lucro_final, valor_freebet_coletada, bateu_duplo, condicao_freebet, observacao, casa_destino_freebet, valor_da_freebet FROM Procedimentos_Historico ORDER BY id DESC")
        
        for id_op, data, tipo, jogo, casas, lucro, v_duplo, bateu, cond, obs, casa_fb, v_fb in cursor.fetchall():
            if f_t and f_t not in jogo.lower() and f_t not in casas.lower(): continue
            if self.filtros_avancados["tipos"] and tipo not in self.filtros_avancados["tipos"]: continue
            if self.filtros_avancados["casas"] and not any(c in casas for c in self.filtros_avancados["casas"]): continue

            v_fb = v_fb or 0.0
            row = self.tabela.rowCount(); self.tabela.insertRow(row)
            def item(t, cor=None):
                it = QTableWidgetItem(str(t) if t not in ["None", None, ""] else "-")
                it.setTextAlignment(Qt.AlignCenter); (it.setForeground(QBrush(QColor(cor))) if cor else None); return it

            self.tabela.setItem(row, 0, item(data.split('/')[0]))
            self.tabela.setItem(row, 1, item(tipo + (" •" if obs else "")))
            self.tabela.setItem(row, 2, item(jogo))
            it_c = item(casas); it_c.setToolTip(casas); self.tabela.setItem(row, 3, it_c)
            self.tabela.setItem(row, 4, item(f"R$ {lucro:.2f}", COR_VERDE if lucro >= 0 else COR_VERMELHO))

            if tipo == "SureBet":
                self.tabela.setItem(row, 5, item("-", "#71717a"))
                self.tabela.setItem(row, 6, item(f"R$ {lucro:.2f}", COR_VERDE if lucro >= 0 else COR_VERMELHO))
            else:
                cb = QCheckBox(); cb.setChecked(bool(bateu))
                cb.stateChanged.connect(lambda s, i=id_op, lb=lucro, vd=v_duplo, r=row: self.atualizar_duplo_tela(s, i, lb, vd, r))
                self.tabela.setCellWidget(row, 5, CheckBoxContainer(cb))
                self.atualizar_duplo_tela(cb.checkState(), id_op, lucro, v_duplo, row, False)

            btn_acoes = QPushButton("▼")
            btn_acoes.setCursor(Qt.PointingHandCursor)
            btn_acoes.setStyleSheet("""
                QPushButton { color: #71717a; font-size: 10px; border: none; background: transparent; padding: 5px; }
                QPushButton:hover { color: #f4f4f5; }
                QPushButton::menu-indicator { image: none; }
            """)
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { background-color: #18181b; color: #f4f4f5; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); outline: none; } QMenu::item { padding: 10px 25px; } QMenu::item:selected { background-color: #27272a; }")
            if obs: 
                menu.addAction("Ver Obs").triggered.connect(lambda checked=False, o=obs: self.mostrar_observacao(o))
            
            dados_edicao = {'tipo':tipo, 'jogo':jogo, 'casas':casas, 'lucro_base':lucro, 'v_duplo':v_duplo, 'obs':obs, 'condicao':cond, 'casa_fb':casa_fb, 'v_fb':v_fb}
            menu.addAction("Editar").triggered.connect(lambda checked=False, d=dados_edicao, i=id_op: self.abrir_pop_up(d, i))
            
            menu.addAction("Excluir").triggered.connect(lambda checked=False, i=id_op: self.excluir_procedimento(i))
            btn_acoes.setMenu(menu); self.tabela.setCellWidget(row, 7, btn_acoes)

    def atualizar_duplo_tela(self, state, id_op, base, duplo, row, save=True):
        final = base + (duplo if state == 2 or state == Qt.Checked else 0)
        it = QTableWidgetItem(f"R$ {final:.2f}"); it.setTextAlignment(Qt.AlignCenter)
        it.setForeground(QBrush(QColor(COR_VERDE if final >= 0 else COR_VERMELHO)))
        self.tabela.setItem(row, 6, it)
        if save: database.atualizar_status_duplo(id_op, state == 2 or state == Qt.Checked)

    def abrir_filtros(self):
        d = DialogFiltros(self, self.filtros_avancados)
        if d.exec() == QDialog.Accepted:
            self.filtros_avancados = d.filtros_atuais; self.carregar_tabela()

    def abrir_pop_up(self, d_e=None, id_op=None):
        m = DialogNovoProcedimento(self, d_e)
        if m.exec() == QDialog.Accepted:
            (database.atualizar_procedimento(id_op, m.dados_finais) if id_op else database.salvar_procedimento(m.dados_finais))
            self.carregar_tabela()

    def mostrar_observacao(self, obs): QMessageBox.information(self, "Observação", obs)

    def excluir_procedimento(self, id_op):
        if QMessageBox.question(self, "Excluir", "Deseja excluir permanentemente?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            database.excluir_procedimento(id_op); self.carregar_tabela()