from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QLineEdit, QPushButton, QCheckBox, 
                               QFormLayout, QGroupBox, QDialog, QGridLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QMessageBox, QInputDialog, QMenu)
from PySide6.QtCore import Qt
from datetime import datetime
from core import database
import locale

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# ==========================================
# 1. COMPONENTE: ÁREA DE CLIQUE EXPANDIDA PARA CHECKBOX
# ==========================================
class CheckBoxContainer(QWidget):
    """Transforma a célula inteira da tabela em área clicável para o CheckBox."""
    def __init__(self, checkbox):
        super().__init__()
        self.cb = checkbox
        # Faz o checkbox ignorar os cliques diretos nele, passando a responsabilidade para o container
        self.cb.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.cb)
        self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.cb.toggle() # Clicou na célula? O checkbox muda de estado!
        super().mouseReleaseEvent(event)


# ==========================================
# 2. SUB-POPUP: SELETOR DE MÚLTIPLAS CASAS
# ==========================================
class DialogEscolherCasas(QDialog):
    def __init__(self, parent=None, casas_selecionadas=None):
        super().__init__(parent)
        self.setWindowTitle("Escolher Casas Envolvidas")
        self.setFixedSize(500, 400) 
        self.setModal(True)
        self.casas_selecionadas = casas_selecionadas if casas_selecionadas else []
        self.modo_exclusao = False 
        
        self.setStyleSheet("""
            QDialog { background-color: #1a1d2d; color: white; }
            QCheckBox { color: white; font-size: 14px; padding: 5px; }
            QPushButton { background-color: #282c38; color: white; border-radius: 4px; padding: 8px; font-weight: bold; }
            QLineEdit { background-color: #0f111a; color: white; padding: 8px; border: 1px solid #282c38; border-radius: 4px; }
        """)

        layout = QVBoxLayout(self)

        topo_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("Pesquisar casa ou adicionar...")
        self.input_busca.textChanged.connect(self.filtrar_casas)
        
        self.btn_modo_exclusao = QPushButton("Excluir")
        self.btn_modo_exclusao.setStyleSheet("background-color: #282c38; color: #ff5252; font-size: 14px; padding: 8px 15px;")
        self.btn_modo_exclusao.clicked.connect(self.alternar_modo_exclusao)
        
        topo_layout.addWidget(self.input_busca)
        topo_layout.addWidget(self.btn_modo_exclusao)
        layout.addLayout(topo_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: 1px solid #282c38; background-color: #161925;")
        
        self.scroll_content = QWidget()
        self.layout_checks = QGridLayout(self.scroll_content) 
        self.layout_checks.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch() 
        self.btn_ok = QPushButton("CONFIRMAR")
        self.btn_ok.setStyleSheet("background-color: #00e676; color: black; font-size: 14px; padding: 8px 25px;")
        self.btn_ok.clicked.connect(self.confirmar_e_fechar)
        botoes_layout.addWidget(self.btn_ok)
        layout.addLayout(botoes_layout)

        self.checkboxes = {}
        self.botoes_deletar = [] 
        self.carregar_lista_casas()

    def alternar_modo_exclusao(self):
        self.modo_exclusao = not self.modo_exclusao
        if self.modo_exclusao:
            self.btn_modo_exclusao.setText("Concluir Exclusão")
            self.btn_modo_exclusao.setStyleSheet("background-color: #ff5252; color: white; font-size: 14px; padding: 8px 15px;")
        else:
            self.btn_modo_exclusao.setText("Excluir")
            self.btn_modo_exclusao.setStyleSheet("background-color: #282c38; color: #ff5252; font-size: 14px; padding: 8px 15px;")
        for btn in self.botoes_deletar:
            btn.setVisible(self.modo_exclusao)

    def sync_selecionadas(self):
        for casa, chk in self.checkboxes.items():
            if chk.isChecked() and casa not in self.casas_selecionadas:
                self.casas_selecionadas.append(casa)
            elif not chk.isChecked() and casa in self.casas_selecionadas:
                self.casas_selecionadas.remove(casa)

    def filtrar_casas(self, texto):
        self.sync_selecionadas()
        self.carregar_lista_casas(texto)

    def carregar_lista_casas(self, filtro=""):
        for i in reversed(range(self.layout_checks.count())):
            widget = self.layout_checks.itemAt(i).widget()
            if widget: widget.deleteLater()
        
        self.checkboxes.clear()
        self.botoes_deletar.clear()

        casas = database.listar_casas()
        row, col = 0, 0
        for casa in casas:
            if filtro.lower() in casa.lower():
                container_casa = QWidget()
                lay_casa = QHBoxLayout(container_casa)
                lay_casa.setContentsMargins(0, 0, 0, 0)
                lay_casa.setSpacing(5)
                
                chk = QCheckBox(casa)
                if casa in self.casas_selecionadas:
                    chk.setChecked(True)
                
                btn_del = QPushButton("✖")
                btn_del.setFixedSize(20, 20)
                btn_del.setCursor(Qt.PointingHandCursor)
                btn_del.setStyleSheet("color: #ff5252; background: transparent; font-weight: bold; border: none;")
                btn_del.clicked.connect(lambda _, c=casa: self.deletar_casa(c))
                btn_del.setVisible(self.modo_exclusao) 
                self.botoes_deletar.append(btn_del)
                
                lay_casa.addWidget(chk)
                lay_casa.addWidget(btn_del)
                lay_casa.addStretch() 
                
                self.layout_checks.addWidget(container_casa, row, col)
                self.checkboxes[casa] = chk
                
                col += 1
                if col > 2:
                    col = 0
                    row += 1

    def deletar_casa(self, nome_casa):
        resposta = QMessageBox.question(self, "Excluir Casa", f"Deseja realmente excluir a casa '{nome_casa}'?", QMessageBox.Yes | QMessageBox.No)
        if resposta == QMessageBox.Yes:
            database.excluir_casa(nome_casa)
            if nome_casa in self.casas_selecionadas:
                self.casas_selecionadas.remove(nome_casa)
            self.carregar_lista_casas(self.input_busca.text()) 

    def processar_texto_busca(self):
        texto = self.input_busca.text().strip()
        if texto:
            casas_lower = [c.lower() for c in database.listar_casas()]
            if texto.lower() not in casas_lower:
                database.adicionar_casa(texto)
            self.sync_selecionadas()
            casa_exata = next((c for c in database.listar_casas() if c.lower() == texto.lower()), texto)
            if casa_exata not in self.casas_selecionadas:
                self.casas_selecionadas.append(casa_exata)
            self.input_busca.clear()
            self.carregar_lista_casas()

    def confirmar_e_fechar(self):
        self.processar_texto_busca()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.input_busca.hasFocus():
                self.processar_texto_busca()
            elif self.btn_ok.hasFocus():
                self.confirmar_e_fechar()
            else:
                self.focusNextChild()
        else:
            super().keyPressEvent(event)

    def get_selecionadas(self):
        self.sync_selecionadas()
        return self.casas_selecionadas


# ==========================================
# 3. POP-UP DE FILTROS AVANÇADOS
# ==========================================
class DialogFiltros(QDialog):
    def __init__(self, parent=None, filtros_atuais=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros de Tabela")
        self.setMinimumWidth(400)
        self.setModal(True)
        # O dicionário guarda listas vazias se não houver filtro
        self.filtros_atuais = filtros_atuais if filtros_atuais else {"tipos": [], "casas": []}
        
        self.setStyleSheet("""
            QDialog { background-color: #0f111a; color: white; }
            QGroupBox { font-weight: bold; border: 1px solid #282c38; border-radius: 5px; margin-top: 15px; padding-top: 15px; color: #ffffff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QCheckBox { color: white; font-size: 14px; padding: 5px; }
            QPushButton { background-color: #282c38; color: white; border-radius: 4px; padding: 8px; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)

        # Filtro de Procedimentos
        grupo_tipos = QGroupBox("Filtrar por Procedimento")
        lay_tipos = QVBoxLayout()
        self.checks_tipos = {}
        for t in ["SureBet", "Tentativa de Duplo", "Coletar Freebet", "Converter Freebet"]:
            chk = QCheckBox(t)
            if t in self.filtros_atuais["tipos"]:
                chk.setChecked(True)
            lay_tipos.addWidget(chk)
            self.checks_tipos[t] = chk
        grupo_tipos.setLayout(lay_tipos)
        layout.addWidget(grupo_tipos)

        # Filtro de Casas
        grupo_casas = QGroupBox("Filtrar por Casas Envolvidas")
        lay_casas = QVBoxLayout()
        
        self.lbl_casas = QLabel("Nenhuma selecionada")
        self.lbl_casas.setStyleSheet("color: #7b849b; font-style: italic;")
        self.lbl_casas.setAlignment(Qt.AlignCenter) 
        self.lbl_casas.setWordWrap(True)
        
        if self.filtros_atuais["casas"]:
            self.lbl_casas.setText(" | ".join(self.filtros_atuais["casas"]))
            self.lbl_casas.setStyleSheet("color: #00e676; font-weight: bold;")
            
        btn_casas = QPushButton("Escolher Casas")
        btn_casas.setCursor(Qt.PointingHandCursor)
        btn_casas.clicked.connect(self.abrir_seletor_casas)
        
        lay_casas.addWidget(self.lbl_casas)
        lay_casas.addWidget(btn_casas)
        grupo_casas.setLayout(lay_casas)
        layout.addWidget(grupo_casas)

        # Botões Base
        botoes = QHBoxLayout()
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setStyleSheet("background-color: transparent; border: 1px solid #ff5252; color: #ff5252;")
        btn_limpar.clicked.connect(self.limpar)
        
        btn_aplicar = QPushButton("APLICAR FILTROS")
        btn_aplicar.setStyleSheet("background-color: #00e676; color: black;")
        btn_aplicar.clicked.connect(self.aplicar)
        
        botoes.addWidget(btn_limpar)
        botoes.addWidget(btn_aplicar)
        layout.addLayout(botoes)

    def abrir_seletor_casas(self):
        atuais = []
        if self.lbl_casas.text() not in ["Nenhuma selecionada", ""]:
            atuais = self.lbl_casas.text().split(" | ")
            
        dialog = DialogEscolherCasas(self, atuais)
        if dialog.exec() == QDialog.Accepted:
            selecionadas = dialog.get_selecionadas()
            if selecionadas:
                self.lbl_casas.setText(" | ".join(selecionadas))
                self.lbl_casas.setStyleSheet("color: #00e676; font-weight: bold;")
            else:
                self.lbl_casas.setText("Nenhuma selecionada")
                self.lbl_casas.setStyleSheet("color: #7b849b; font-style: italic;")

    def limpar(self):
        for chk in self.checks_tipos.values():
            chk.setChecked(False)
        self.lbl_casas.setText("Nenhuma selecionada")
        self.lbl_casas.setStyleSheet("color: #7b849b; font-style: italic;")

    def aplicar(self):
        self.filtros_atuais["tipos"] = [t for t, chk in self.checks_tipos.items() if chk.isChecked()]
        if self.lbl_casas.text() == "Nenhuma selecionada":
            self.filtros_atuais["casas"] = []
        else:
            self.filtros_atuais["casas"] = self.lbl_casas.text().split(" | ")
        self.accept()


# ==========================================
# 4. POPUP PRINCIPAL: NOVO PROCEDIMENTO
# ==========================================
class DialogNovoProcedimento(QDialog):
    def __init__(self, parent=None, dados_edicao=None):
        super().__init__(parent)
        self.dados_edicao = dados_edicao
        self.setWindowTitle("Editar Procedimento" if dados_edicao else "Novo Procedimento")
        self.setMinimumWidth(600)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog { background-color: #0f111a; }
            QGroupBox { font-weight: bold; border: 1px solid #282c38; border-radius: 5px; margin-top: 15px; padding-top: 15px; color: #ffffff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLabel { color: #ffffff; }
            QLineEdit, QComboBox { background-color: #161925; color: white; border: 1px solid #282c38; padding: 6px; border-radius: 4px; }
        """)

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setSizeConstraint(QVBoxLayout.SetFixedSize) 

        layout_botoes = QHBoxLayout()
        self.botoes_tipo = []
        for tipo in ["SureBet", "Tentativa de Duplo", "Coletar Freebet", "Converter Freebet"]:
            btn = QPushButton(tipo)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tipo: self.selecionar_tipo(t))
            layout_botoes.addWidget(btn)
            self.botoes_tipo.append(btn)
        self.layout_principal.addLayout(layout_botoes)

        self.grupo_detalhes = QGroupBox("Detalhes da Partida")
        self.layout_detalhes = QFormLayout()
        
        self.input_jogo = QLineEdit()
        self.combo_condicao = QComboBox()
        self.combo_condicao.addItems(["Freebet Garantida", "Apenas se perder a aposta"])
        
        self.lbl_casa_freebet = QLabel("")
        self.lbl_casa_freebet.setStyleSheet("color: #7b849b; font-style: italic;")
        
        self.btn_escolher_casa_fb = QPushButton("Escolher Casa")
        self.btn_escolher_casa_fb.setCursor(Qt.PointingHandCursor)
        self.btn_escolher_casa_fb.setStyleSheet("background-color: #282c38; color: white; border-radius: 4px; padding: 6px 15px;")
        self.btn_escolher_casa_fb.clicked.connect(self.abrir_seletor_casa_freebet)
        
        self.container_casa_fb = QWidget()
        lay_cfb = QHBoxLayout(self.container_casa_fb)
        lay_cfb.setContentsMargins(0, 0, 0, 0)
        lay_cfb.addWidget(self.lbl_casa_freebet, stretch=1)
        lay_cfb.addWidget(self.btn_escolher_casa_fb)

        self.layout_detalhes.addRow("Jogo/Time:", self.input_jogo)
        self.layout_detalhes.addRow("Condição Freebet:", self.combo_condicao)
        self.layout_detalhes.addRow("Casa da Freebet:", self.container_casa_fb)
        self.grupo_detalhes.setLayout(self.layout_detalhes)
        self.layout_principal.addWidget(self.grupo_detalhes)

        grupo_casas = QGroupBox("Casas Envolvidas")
        layout_casas = QHBoxLayout()
        
        self.lbl_casas_selecionadas = QLabel("Nenhuma selecionada")
        self.lbl_casas_selecionadas.setStyleSheet("color: #7b849b; font-style: italic;")
        self.lbl_casas_selecionadas.setAlignment(Qt.AlignCenter) 
        self.lbl_casas_selecionadas.setWordWrap(True)
    
        self.btn_escolher_casas = QPushButton("Escolher Casas")
        self.btn_escolher_casas.setCursor(Qt.PointingHandCursor)
        self.btn_escolher_casas.setStyleSheet("background-color: #282c38; color: white; border-radius: 4px; padding: 6px 15px;")
        self.btn_escolher_casas.clicked.connect(self.abrir_seletor_casas)
        
        layout_casas.addWidget(self.lbl_casas_selecionadas, stretch=1)
        layout_casas.addWidget(self.btn_escolher_casas)
        grupo_casas.setLayout(layout_casas)
        self.layout_principal.addWidget(grupo_casas)

        grupo_valores = QGroupBox("Valores (Lucro/Perca)")
        self.layout_valores = QFormLayout()
        
        self.input_valor_duplo = QLineEdit()
        self.check_lucro_igual = QCheckBox("Lucro igual em todas as posições")
        self.check_lucro_igual.toggled.connect(self.alternar_lucro_igual)
        self.input_entrada = QLineEdit()
        
        self.lista_inputs_protecoes = []
        self.lista_containers_protecoes = []
        
        self.btn_add_protecao = QPushButton("+ Adicionar mais proteções")
        self.btn_add_protecao.setCursor(Qt.PointingHandCursor)
        self.btn_add_protecao.setStyleSheet("color: #00bcd4; background: transparent; border: none; text-align: left;")
        self.btn_add_protecao.clicked.connect(lambda: self.adicionar_campo_protecao())
        
        self.layout_valores.addRow("Valor do Duplo (R$):", self.input_valor_duplo)
        self.layout_valores.addRow("", self.check_lucro_igual)
        self.layout_valores.addRow("Lucro da Entrada (R$):", self.input_entrada)
        self.adicionar_campo_protecao(texto_padrao="Lucro da Proteção 1 (R$):", eh_padrao=True)
        self.layout_valores.addRow("", self.btn_add_protecao)
        
        grupo_valores.setLayout(self.layout_valores)
        self.layout_principal.addWidget(grupo_valores)

        self.btn_add_obs = QPushButton("+ Adicionar Observação")
        self.btn_add_obs.setCursor(Qt.PointingHandCursor)
        self.btn_add_obs.setStyleSheet("color: #ffb300; background: transparent; border: none; text-align: left; padding-top: 10px;")
        self.btn_add_obs.clicked.connect(self.mostrar_campo_obs)
        
        self.container_obs = QWidget()
        lay_obs = QHBoxLayout(self.container_obs)
        lay_obs.setContentsMargins(0, 10, 0, 0)
        self.input_obs = QLineEdit()
        self.input_obs.setPlaceholderText("Escreva sua observação aqui...")
        
        btn_remover_obs = QPushButton("✖")
        btn_remover_obs.setFixedWidth(24)
        btn_remover_obs.setStyleSheet("color: #ff5252; background: transparent; font-weight: bold; border: none;")
        btn_remover_obs.clicked.connect(self.esconder_campo_obs)
        
        lay_obs.addWidget(self.input_obs)
        lay_obs.addWidget(btn_remover_obs)
        self.container_obs.hide()
        
        self.layout_principal.addWidget(self.btn_add_obs)
        self.layout_principal.addWidget(self.container_obs)

        self.btn_salvar = QPushButton("SALVAR ALTERAÇÕES" if dados_edicao else "SALVAR PROCEDIMENTO")
        self.btn_salvar.setStyleSheet("background-color: #00e676; color: black; font-weight: bold; border-radius: 5px; height: 45px; margin-top: 15px;")
        self.btn_salvar.setCursor(Qt.PointingHandCursor)
        self.btn_salvar.clicked.connect(self.processar_e_salvar)
        self.layout_principal.addWidget(self.btn_salvar)

        if dados_edicao:
            self.preencher_dados_edicao()
        else:
            self.selecionar_tipo("SureBet")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.btn_salvar.hasFocus():
                self.processar_e_salvar()
            else:
                self.focusNextChild()
        else:
            super().keyPressEvent(event)

    def abrir_seletor_casa_freebet(self):
        atuais = []
        if self.lbl_casa_freebet.text() not in ["", "Nenhuma selecionada"]:
            atuais = [self.lbl_casa_freebet.text()]
            
        dialog = DialogEscolherCasas(self, atuais)
        if dialog.exec() == QDialog.Accepted:
            selecionadas = dialog.get_selecionadas()
            if selecionadas:
                nova_casa = selecionadas[0] 
                self.lbl_casa_freebet.setText(nova_casa)
                self.lbl_casa_freebet.setStyleSheet("color: #00e676; font-weight: bold;")
                
                atuais_env = []
                if self.lbl_casas_selecionadas.text() not in ["Nenhuma selecionada", ""]:
                    atuais_env = self.lbl_casas_selecionadas.text().split(" | ")
                
                if nova_casa not in atuais_env:
                    atuais_env.append(nova_casa)
                    self.lbl_casas_selecionadas.setText(" | ".join(atuais_env))
                    self.lbl_casas_selecionadas.setStyleSheet("color: #00e676; font-weight: bold;")
            else:
                self.lbl_casa_freebet.setText("")
                self.lbl_casa_freebet.setStyleSheet("color: #7b849b; font-style: italic;")

    def abrir_seletor_casas(self):
        atuais = []
        if self.lbl_casas_selecionadas.text() not in ["Nenhuma selecionada", ""]:
            atuais = self.lbl_casas_selecionadas.text().split(" | ")
            
        dialog = DialogEscolherCasas(self, atuais)
        if dialog.exec() == QDialog.Accepted:
            selecionadas = dialog.get_selecionadas()
            if selecionadas:
                self.lbl_casas_selecionadas.setText(" | ".join(selecionadas))
                self.lbl_casas_selecionadas.setStyleSheet("color: #00e676; font-weight: bold;")
            else:
                self.lbl_casas_selecionadas.setText("Nenhuma selecionada")
                self.lbl_casas_selecionadas.setStyleSheet("color: #7b849b; font-style: italic;")

    def adicionar_campo_protecao(self, texto_padrao="Proteção Extra (R$):", eh_padrao=False):
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        
        novo_inp = QLineEdit()
        self.lista_inputs_protecoes.append(novo_inp)
        self.lista_containers_protecoes.append(container)
        lay.addWidget(novo_inp)
        
        if eh_padrao:
            self.layout_valores.addRow(texto_padrao, container)
        else:
            btn_remover = QPushButton("✖")
            btn_remover.setFixedWidth(24)
            btn_remover.setCursor(Qt.PointingHandCursor)
            btn_remover.setStyleSheet("color: #ff5252; background: transparent; font-weight: bold; border: none;")
            btn_remover.clicked.connect(lambda: self.remover_protecao(container, novo_inp))
            lay.addWidget(btn_remover)
            pos = self.layout_valores.rowCount() - 1
            self.layout_valores.insertRow(pos, texto_padrao, container)
            novo_inp.setFocus()

    def remover_protecao(self, container, inp):
        if inp in self.lista_inputs_protecoes:
            self.lista_inputs_protecoes.remove(inp)
        if container in self.lista_containers_protecoes:
            self.lista_containers_protecoes.remove(container)
        self.layout_valores.removeRow(container)

    def mostrar_campo_obs(self):
        self.btn_add_obs.hide()
        self.container_obs.show()
        self.input_obs.setFocus()

    def esconder_campo_obs(self):
        self.input_obs.clear()
        self.container_obs.hide()
        self.btn_add_obs.show()

    def selecionar_tipo(self, tipo):
        self.tipo_selecionado = tipo
        for btn in self.botoes_tipo:
            btn.setStyleSheet(f"background-color: {'#00e676' if btn.text() == tipo else '#282c38'}; color: {'black' if btn.text() == tipo else 'white'}; padding: 8px; border-radius: 4px; font-weight: bold;")
        
        self.grupo_detalhes.setVisible(tipo != "SureBet")
        self.input_valor_duplo.setVisible(tipo != "SureBet")
        self.layout_valores.labelForField(self.input_valor_duplo).setVisible(tipo != "SureBet")

        is_coleta = (tipo == "Coletar Freebet")
        self.combo_condicao.setVisible(is_coleta)
        self.layout_detalhes.labelForField(self.combo_condicao).setVisible(is_coleta)
        self.container_casa_fb.setVisible(is_coleta) 
        self.layout_detalhes.labelForField(self.container_casa_fb).setVisible(is_coleta)

    def alternar_lucro_igual(self, marcado):
        for container in self.lista_containers_protecoes:
            lbl = self.layout_valores.labelForField(container)
            container.setVisible(not marcado)
            if lbl: lbl.setVisible(not marcado)
            
        self.btn_add_protecao.setVisible(not marcado)
        lbl_base = self.layout_valores.labelForField(self.input_entrada)
        if lbl_base:
            lbl_base.setText("Valor Único (R$):" if marcado else "Lucro da Entrada (R$):")

    def preencher_dados_edicao(self):
        d = self.dados_edicao
        self.selecionar_tipo(d['tipo'])
        self.input_jogo.setText(d['jogo'])
        if d['casas'] and d['casas'] != "None" and d['casas'] != "---":
            self.lbl_casas_selecionadas.setText(d['casas'])
            self.lbl_casas_selecionadas.setStyleSheet("color: #00e676; font-weight: bold;")
            
        if d.get('casa_fb') and d['casa_fb'] != "None" and d['casa_fb'] != "---":
            self.lbl_casa_freebet.setText(d['casa_fb'])
            self.lbl_casa_freebet.setStyleSheet("color: #00e676; font-weight: bold;")
            
        self.check_lucro_igual.setChecked(True)
        self.input_entrada.setText(str(d['lucro_base']))
        self.input_valor_duplo.setText(str(d['v_duplo']))
        
        if d['obs']:
            self.mostrar_campo_obs()
            self.input_obs.setText(d['obs'])
            
        self.combo_condicao.setCurrentText(d.get('condicao', ''))
        
    def processar_e_salvar(self):
        try:
            v_entrada_texto = self.input_entrada.text().replace(',', '.')
            if not v_entrada_texto: raise ValueError
            v_entrada = float(v_entrada_texto)
            
            if self.check_lucro_igual.isChecked():
                lucro_base = v_entrada
            else:
                soma = v_entrada
                contagem = 1
                for inp in self.lista_inputs_protecoes:
                    txt = inp.text().replace(',', '.')
                    if txt:
                        soma += float(txt)
                        contagem += 1
                lucro_base = soma / contagem
                
            casas_env = self.lbl_casas_selecionadas.text()
            if casas_env == "Nenhuma selecionada": casas_env = ""
            
            self.dados_finais = {
                'data_operacao': datetime.now().strftime("%d/%m/%Y"),
                'tipo_procedimento': self.tipo_selecionado,
                'casas_envolvidas': casas_env,
                'jogo_time_pa': self.input_jogo.text(),
                'lucro_final': lucro_base,
                'valor_freebet_coletada': float(self.input_valor_duplo.text().replace(',', '.')) if self.input_valor_duplo.text() else 0.0,
                'condicao_freebet': self.combo_condicao.currentText() if self.combo_condicao.isVisible() else '',
                'observacao': self.input_obs.text(),
                'mes_referencia': datetime.now().strftime("%m/%Y"),
                'casa_destino_freebet': self.lbl_casa_freebet.text() if self.tipo_selecionado == "Coletar Freebet" else "",
                'status_freebet': 'Pendente' if self.tipo_selecionado == "Coletar Freebet" else 'N/A'
            }
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preencha o Lucro da Entrada corretamente com números.")


# ==========================================
# 5. PAINEL PRINCIPAL (TABELA E FILTROS)
# ==========================================
class TelaProcedimentos(QWidget):
    def __init__(self):
        super().__init__()
        # Dicionário para guardar as seleções de filtro da sessão
        self.filtros_avancados = {"tipos": [], "casas": []}
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        mes_atual = datetime.now().strftime("%B").capitalize()
        ano_atual = datetime.now().strftime("%Y")
        titulo = QLabel(f"Meus Procedimentos - {mes_atual} - {ano_atual}")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(titulo)
        
        filtros_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("Buscar por jogo ou casa...")
        self.input_busca.setStyleSheet("background-color: #161925; color: white; padding: 10px; border: 1px solid #282c38; border-radius: 5px;")
        self.input_busca.textChanged.connect(self.carregar_tabela)
        
        # O Novo Botão de Filtros Avançados
        self.btn_filtros = QPushButton("Filtros")
        self.btn_filtros.setCursor(Qt.PointingHandCursor)
        self.btn_filtros.setStyleSheet("background-color: #282c38; color: white; font-weight: bold; padding: 10px 15px; border-radius: 5px;")
        self.btn_filtros.clicked.connect(self.abrir_filtros)
        
        self.btn_abrir_modal = QPushButton("+ Adicionar Procedimento")
        self.btn_abrir_modal.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_modal.setStyleSheet("background-color: #00e676; color: black; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        self.btn_abrir_modal.clicked.connect(lambda: self.abrir_pop_up())

        filtros_layout.addWidget(self.input_busca)
        filtros_layout.addWidget(self.btn_filtros) # Inserido do lado da barra
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.btn_abrir_modal)
        layout.addLayout(filtros_layout)

        self.tabela = QTableWidget(0, 8) 
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Jogo", "Casas", "Base", "Duplo?", "Final", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SingleSelection) 
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38; outline: none; }
            QTableWidget::item:selected { background-color: #282c38; }
        """)
        self.tabela.setMouseTracking(True)
        self.tabela.cellEntered.connect(lambda r, c: self.tabela.selectRow(r))
        
        layout.addWidget(self.tabela)
        
        self.carregar_tabela()

    def abrir_filtros(self):
        """Abre a janela de filtros avançados."""
        dialog = DialogFiltros(self, self.filtros_avancados)
        if dialog.exec() == QDialog.Accepted:
            self.filtros_avancados = dialog.filtros_atuais
            
            # Se houver filtro ativo, pinta o botão de verde para sinalizar
            if self.filtros_avancados["tipos"] or self.filtros_avancados["casas"]:
                self.btn_filtros.setStyleSheet("background-color: #00e676; color: black; font-weight: bold; padding: 10px 15px; border-radius: 5px;")
            else:
                self.btn_filtros.setStyleSheet("background-color: #282c38; color: white; font-weight: bold; padding: 10px 15px; border-radius: 5px;")
                
            self.carregar_tabela()

    def abrir_pop_up(self, dados_edicao=None, id_op=None):
        modal = DialogNovoProcedimento(self, dados_edicao)
        if modal.exec() == QDialog.Accepted:
            if id_op:
                database.atualizar_procedimento(id_op, modal.dados_finais)
            else:
                database.salvar_procedimento(modal.dados_finais)
            self.carregar_tabela()

    def mostrar_observacao(self, obs):
        QMessageBox.information(self, "Observação do Procedimento", obs)

    def excluir_procedimento(self, id_op):
        resposta = QMessageBox.question(self, "Excluir Procedimento", "Tem certeza que deseja excluir permanentemente este procedimento?", QMessageBox.Yes | QMessageBox.No)
        if resposta == QMessageBox.Yes:
            database.excluir_procedimento(id_op)
            self.carregar_tabela()

    def carregar_tabela(self):
        self.tabela.setRowCount(0)
        filtro_texto = self.input_busca.text().lower()
        
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, data_operacao, tipo_procedimento, jogo_time_pa, casas_envolvidas, lucro_final, valor_freebet_coletada, bateu_duplo, condicao_freebet, observacao, casa_destino_freebet FROM Procedimentos_Historico")
        
        for id_op, data, tipo, jogo, casas, lucro, v_duplo, bateu, cond, obs, casa_fb in cursor.fetchall():
            
            # 1. Filtro da Barra de Pesquisa
            if filtro_texto and filtro_texto not in jogo.lower() and filtro_texto not in casas.lower():
                continue
                
            # 2. Filtro Avançado: Tipo de Procedimento
            if self.filtros_avancados["tipos"]:
                if tipo not in self.filtros_avancados["tipos"]:
                    continue
                    
            # 3. Filtro Avançado: Casas de Aposta
            if self.filtros_avancados["casas"]:
                # Pelo menos uma das casas filtradas tem que estar na operação
                if not any(casa_filtrada in casas for casa_filtrada in self.filtros_avancados["casas"]):
                    continue

            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            
            def item(t, c=None):
                if t == "None" or t is None or t == "": t = "---"
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                it.setToolTip(str(t)) 
                if c: it.setForeground(c)
                return it

            self.tabela.setItem(row, 0, item(data.split('/')[0]))
            
            tipo_display = tipo
            if obs:
                tipo_display += " •"
            self.tabela.setItem(row, 1, item(tipo_display))
            
            self.tabela.setItem(row, 2, item(jogo))
            self.tabela.setItem(row, 3, item(casas))
            self.tabela.setItem(row, 4, item(f"R$ {lucro:.2f}", Qt.green if lucro >= 0 else Qt.red))

            if tipo == "SureBet":
                self.tabela.setItem(row, 5, item("-", Qt.darkGray))
                self.tabela.setItem(row, 6, item(f"R$ {lucro:.2f}", Qt.green if lucro >= 0 else Qt.red))
            else:
                cb = QCheckBox()
                cb.setChecked(bool(bateu))
                cb.stateChanged.connect(lambda s, i=id_op, lb=lucro, vd=v_duplo, r=row: self.atualizar_duplo_tela(s, i, lb, vd, r))
                
                # A MÁGICA: O Checkbox agora mora dentro do Container Expansível
                container = CheckBoxContainer(cb)
                
                self.tabela.setCellWidget(row, 5, container)
                self.atualizar_duplo_tela(cb.checkState(), id_op, lucro, v_duplo, row, False)

            btn_acoes = QPushButton("⋮")
            btn_acoes.setStyleSheet("QPushButton { color: white; font-size: 20px; font-weight: bold; border: none; background: transparent; padding-bottom: 5px; } QPushButton::menu-indicator { image: none; }")
            btn_acoes.setCursor(Qt.PointingHandCursor)
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu { background-color: #1a1d2d; color: white; border: 1px solid #282c38; }
                QMenu::item { padding: 8px 25px; font-size: 14px; }
                QMenu::item:selected { background-color: #00e676; color: black; font-weight: bold; }
            """)
            
            if obs:
                acao_obs = menu.addAction("Ver Observação")
                acao_obs.triggered.connect(lambda _, o=obs: self.mostrar_observacao(o))
            
            acao_editar = menu.addAction("Editar")
            dados_para_edicao = {'tipo': tipo, 'jogo': jogo, 'casas': casas, 'lucro_base': lucro, 'v_duplo': v_duplo, 'obs': obs, 'condicao': cond, 'casa_fb': casa_fb}
            acao_editar.triggered.connect(lambda _, d=dados_para_edicao, i=id_op: self.abrir_pop_up(d, i))
            
            acao_excluir = menu.addAction("Excluir")
            acao_excluir.triggered.connect(lambda _, i=id_op: self.excluir_procedimento(i))
            
            btn_acoes.setMenu(menu)
            self.tabela.setCellWidget(row, 7, btn_acoes)

    def atualizar_duplo_tela(self, state, id_op, base, duplo, row, save=True):
        final = base + (duplo if state == 2 or state == Qt.Checked else 0)
        it = QTableWidgetItem(f"R$ {final:.2f}")
        it.setTextAlignment(Qt.AlignCenter); it.setForeground(Qt.green if final >= 0 else Qt.red)
        self.tabela.setItem(row, 6, it)
        if save: database.atualizar_status_duplo(id_op, state == 2 or state == Qt.Checked)