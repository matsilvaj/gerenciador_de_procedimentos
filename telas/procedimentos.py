from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QLineEdit, QPushButton, QCheckBox, 
                               QFormLayout, QGroupBox, QScrollArea, QDialog, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem, QSizePolicy, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt
from datetime import datetime
from core import database
import locale

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class DialogNovoProcedimento(QDialog):
    def __init__(self, parent=None, dados_edicao=None):
        super().__init__(parent)
        self.dados_edicao = dados_edicao
        self.setWindowTitle("Editar Procedimento" if dados_edicao else "Novo Procedimento")
        self.setMinimumWidth(600)
        self.setModal(True)
        
        # Estilo CSS para corrigir sobreposição
        self.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #282c38; border-radius: 5px; margin-top: 15px; padding-top: 15px; color: #ffffff; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLabel { color: #ffffff; }
            QLineEdit, QComboBox { background-color: #161925; color: white; border: 1px solid #282c38; padding: 5px; border-radius: 3px; }
        """)

        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;") 
        
        container = QWidget()
        self.layout_form = QVBoxLayout(container)
        
        # --- Seleção do Procedimento ---
        layout_botoes = QHBoxLayout()
        self.botoes_tipo = []
        for tipo in ["SureBet", "Tentativa de Duplo", "Coletar Freebet", "Converter Freebet"]:
            btn = QPushButton(tipo)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tipo: self.selecionar_tipo(t))
            layout_botoes.addWidget(btn)
            self.botoes_tipo.append(btn)
        self.layout_form.addLayout(layout_botoes)

        # --- Detalhes ---
        self.grupo_detalhes = QGroupBox("Detalhes da Partida")
        self.layout_detalhes = QFormLayout()
        self.input_jogo = QLineEdit()
        self.combo_condicao = QComboBox()
        self.combo_condicao.addItems(["Freebet Garantida", "Apenas se perder a aposta"])
        self.layout_detalhes.addRow("Jogo/Time:", self.input_jogo)
        self.layout_detalhes.addRow("Condição Freebet:", self.combo_condicao)
        self.grupo_detalhes.setLayout(self.layout_detalhes)
        self.layout_form.addWidget(self.grupo_detalhes)
        self.combo_casa_freebet = QComboBox()
        self.layout_detalhes.addRow("Casa da Freebet:", self.combo_casa_freebet)

        # --- Casas ---
        grupo_casas = QGroupBox("Casas Envolvidas")
        layout_casas = QHBoxLayout()
        self.combo_casas = QComboBox()
        self.atualizar_dropdown_casas()
        self.btn_nova_casa = QPushButton("+")
        self.btn_nova_casa.clicked.connect(self.adicionar_nova_casa_db)
        layout_casas.addWidget(self.combo_casas)
        layout_casas.addWidget(self.btn_nova_casa)
        grupo_casas.setLayout(layout_casas)
        self.layout_form.addWidget(grupo_casas)

        # --- Valores ---
        grupo_valores = QGroupBox("Valores (Lucro/Perca)")
        self.layout_valores = QFormLayout()
        self.input_valor_duplo = QLineEdit()
        self.check_lucro_igual = QCheckBox("Lucro igual em todas as posições")
        self.check_lucro_igual.toggled.connect(self.alternar_lucro_igual)
        self.input_entrada = QLineEdit()
        self.input_protecao1 = QLineEdit()
        
        self.layout_valores.addRow("Valor do Duplo (R$):", self.input_valor_duplo)
        self.layout_valores.addRow("", self.check_lucro_igual)
        self.layout_valores.addRow("Lucro da Entrada (R$):", self.input_entrada)
        self.layout_valores.addRow("Lucro da Proteção 1 (R$):", self.input_protecao1)
        grupo_valores.setLayout(self.layout_valores)
        self.layout_form.addWidget(grupo_valores)

        # --- Observações ---
        self.input_obs = QLineEdit()
        self.layout_form.addWidget(QLabel("Observações:"))
        self.layout_form.addWidget(self.input_obs)

        # --- Botão Final ---
        self.btn_salvar = QPushButton("SALVAR ALTERAÇÕES" if dados_edicao else "SALVAR PROCEDIMENTO")
        self.btn_salvar.setStyleSheet("background-color: #00e676; color: black; font-weight: bold; border-radius: 5px; height: 40px;")
        self.btn_salvar.clicked.connect(self.processar_e_salvar)
        self.layout_form.addWidget(self.btn_salvar)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

        # Se for edição, preenche os campos
        if dados_edicao:
            self.preencher_dados_edicao()
        else:
            self.selecionar_tipo("SureBet")

    def adicionar_nova_casa_db(self):
        nome, ok = QInputDialog.getText(self, "Nova Casa", "Nome da Casa de Aposta:")
        if ok and nome:
            database.adicionar_casa(nome)
            self.atualizar_dropdown_casas()
            self.combo_casas.setCurrentText(nome)

    def atualizar_dropdown_casas(self):
        self.combo_casas.clear()
        self.combo_casas.addItems(database.listar_casas())

    def selecionar_tipo(self, tipo):
        self.tipo_selecionado = tipo
        for btn in self.botoes_tipo:
            btn.setStyleSheet(f"background-color: {'#00e676' if btn.text() == tipo else '#282c38'}; color: {'black' if btn.text() == tipo else 'white'}; padding: 8px; border-radius: 4px;")
        self.grupo_detalhes.setVisible(tipo != "SureBet")
        self.input_valor_duplo.setVisible(tipo != "SureBet")
        self.layout_valores.labelForField(self.input_valor_duplo).setVisible(tipo != "SureBet")

    def alternar_lucro_igual(self, marcado):
        self.input_protecao1.setVisible(not marcado)
        self.layout_valores.labelForField(self.input_protecao1).setVisible(not marcado)

    def preencher_dados_edicao(self):
        d = self.dados_edicao
        self.selecionar_tipo(d['tipo'])
        self.input_jogo.setText(d['jogo'])
        self.combo_casas.setCurrentText(d['casas'])
        self.input_entrada.setText(str(d['lucro_base']))
        self.input_valor_duplo.setText(str(d['v_duplo']))
        self.input_obs.setText(d['obs'])
        self.combo_condicao.setCurrentText(d['condicao'])

    def processar_e_salvar(self):
        try:
            v_entrada = float(self.input_entrada.text().replace(',', '.'))
            v_prot = float(self.input_protecao1.text().replace(',', '.')) if self.input_protecao1.isVisible() and self.input_protecao1.text() else 0.0
            
            lucro_base = v_entrada if self.check_lucro_igual.isChecked() else (v_entrada + v_prot) / 2
            
            self.dados_finais = {
                'data_operacao': datetime.now().strftime("%d/%m/%Y"),
                'tipo_procedimento': self.tipo_selecionado,
                'casas_envolvidas': self.combo_casas.currentText(),
                'jogo_time_pa': self.input_jogo.text(),
                'lucro_final': lucro_base,
                'valor_freebet_coletada': float(self.input_valor_duplo.text().replace(',', '.')) if self.input_valor_duplo.text() else 0.0,
                'condicao_freebet': self.combo_condicao.currentText(),
                'observacao': self.input_obs.text(),
                'mes_referencia': datetime.now().strftime("%m/%Y"),
                'casa_destino_freebet': self.combo_casa_freebet.currentText() if self.tipo_selecionado == "Coletar Freebet" else "",
                'status_freebet': 'Pendente' if self.tipo_selecionado == "Coletar Freebet" else 'N/A'
            }
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Verifique os valores numéricos.")

class TelaProcedimentos(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        mes_atual = datetime.now().strftime("%B").capitalize()
        ano_atual = datetime.now().strftime("%Y")
        titulo = QLabel(f"Meus Procedimentos - {mes_atual} - {ano_atual}")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(titulo)
        
        # --- Filtros e Busca ---
        filtros_layout = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar por jogo ou casa...")
        self.input_busca.textChanged.connect(self.carregar_tabela)
        
        self.btn_abrir_modal = QPushButton("+ Adicionar Procedimento")
        self.btn_abrir_modal.setStyleSheet("background-color: #00e676; color: black; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        self.btn_abrir_modal.clicked.connect(lambda: self.abrir_pop_up())

        filtros_layout.addWidget(self.input_busca)
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.btn_abrir_modal)
        layout.addLayout(filtros_layout)

        # --- Tabela ---
        self.tabela = QTableWidget(0, 8) 
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Jogo", "Casas", "Base", "Duplo?", "Final", "Ações"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionMode(QTableWidget.NoSelection) # Remove a seleção de células
        self.tabela.setStyleSheet("background-color: #1a1d2d; color: white; border: none; gridline-color: #282c38;")
        layout.addWidget(self.tabela)
        
        self.carregar_tabela()

    def abrir_pop_up(self, dados_edicao=None, id_op=None):
        modal = DialogNovoProcedimento(self, dados_edicao)
        if modal.exec() == QDialog.Accepted:
            if id_op:
                database.atualizar_procedimento(id_op, modal.dados_finais)
            else:
                database.salvar_procedimento(modal.dados_finais)
            self.carregar_tabela()

    def carregar_tabela(self):
        self.tabela.setRowCount(0)
        filtro = self.input_busca.text().lower()
        
        conexao = database.conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, data_operacao, tipo_procedimento, jogo_time_pa, casas_envolvidas, lucro_final, valor_freebet_coletada, bateu_duplo, condicao_freebet, observacao FROM Procedimentos_Historico")
        
        for id_op, data, tipo, jogo, casas, lucro, v_duplo, bateu, cond, obs in cursor.fetchall():
            if filtro and filtro not in jogo.lower() and filtro not in casas.lower():
                continue

            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            
            def item(t, c=None):
                it = QTableWidgetItem(str(t))
                it.setTextAlignment(Qt.AlignCenter)
                if c: it.setForeground(c)
                return it

            self.tabela.setItem(row, 0, item(data.split('/')[0]))
            self.tabela.setItem(row, 1, item(tipo))
            self.tabela.setItem(row, 2, item(jogo if jogo else "---"))
            self.tabela.setItem(row, 3, item(casas))
            self.tabela.setItem(row, 4, item(f"R$ {lucro:.2f}", Qt.green if lucro >= 0 else Qt.red))

            # Checkbox Duplo
            if tipo == "SureBet":
                # Na Surebet, o duplo é "-" e o Lucro Final já é o Base
                self.tabela.setItem(row, 5, item("-", Qt.darkGray))
                self.tabela.setItem(row, 6, item(f"R$ {lucro:.2f}", Qt.green if lucro >= 0 else Qt.red))
            else:
                # Nos outros, cria o Checkbox e atualiza o Lucro Final baseado nele
                container = QWidget()
                l = QHBoxLayout(container)
                l.setContentsMargins(0,0,0,0)
                l.setAlignment(Qt.AlignCenter)
                cb = QCheckBox()
                cb.setChecked(bool(bateu))
                cb.stateChanged.connect(lambda s, i=id_op, lb=lucro, vd=v_duplo, r=row: self.atualizar_duplo_tela(s, i, lb, vd, r))
                l.addWidget(cb)
                self.tabela.setCellWidget(row, 5, container)
                
                # Executa a atualização inicial APENAS se o cb existir
                self.atualizar_duplo_tela(cb.checkState(), id_op, lucro, v_duplo, row, False)

            # Botão Editar
            btn_edit = QPushButton("✎")
            btn_edit.setStyleSheet("color: #00e676; font-size: 16px; border: none;")
            btn_edit.setCursor(Qt.PointingHandCursor)
            dados_para_edicao = {'tipo': tipo, 'jogo': jogo, 'casas': casas, 'lucro_base': lucro, 'v_duplo': v_duplo, 'obs': obs, 'condicao': cond}
            btn_edit.clicked.connect(lambda _, d=dados_para_edicao, i=id_op: self.abrir_pop_up(d, i))
            self.tabela.setCellWidget(row, 7, btn_edit)

    def atualizar_duplo_tela(self, state, id_op, base, duplo, row, save=True):
        final = base + (duplo if state == 2 or state == Qt.Checked else 0)
        it = QTableWidgetItem(f"R$ {final:.2f}")
        it.setTextAlignment(Qt.AlignCenter); it.setForeground(Qt.green if final >= 0 else Qt.red)
        self.tabela.setItem(row, 6, it)
        if save: database.atualizar_status_duplo(id_op, state == 2 or state == Qt.Checked)