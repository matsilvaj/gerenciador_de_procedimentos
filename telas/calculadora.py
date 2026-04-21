from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QGroupBox, QGridLayout, QPushButton, QComboBox, 
    QScrollArea, QFrame, QCheckBox, QDialog, QMessageBox
)
from PySide6.QtCore import Qt
from telas.procedimentos import DialogNovoProcedimento
from core import database

class TelaCalculadora(QWidget):
    def __init__(self):
        super().__init__()
        self.lucro_global_atual = 0.0
        self.media_retornos_atual = 0.0
        self.last_edited_index = 0
        
        self.casa_fb_pendente = None
        self.ids_fb_pendente = None
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: #09090b;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #09090b;")
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(40, 30, 40, 40)
        self.layout_container.setSpacing(30)
        
        titulo = QLabel("Calculadoras")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #f4f4f5;")
        self.layout_container.addWidget(titulo)

        self.estilo_geral = """
            QGroupBox { 
                border: 1px solid rgba(255,255,255,0.05); 
                border-radius: 12px; 
                margin-top: 20px; 
                padding-top: 30px; 
                color: #f4f4f5; 
                font-weight: bold; 
                font-size: 16px;
            }
            QLabel { color: #a1a1aa; font-weight: normal; font-size: 13px; }
            QLineEdit, QComboBox { 
                background-color: #18181b; 
                color: white; 
                border: 1px solid rgba(255,255,255,0.1); 
                padding: 10px; 
                border-radius: 6px; 
                outline: none; 
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; }
            QPushButton { 
                background-color: #27272a; 
                color: white; 
                border-radius: 6px; 
                padding: 8px; 
                font-weight: bold; 
                border: none; 
            }
            QPushButton:hover { background-color: #3f3f46; }
        """

        self.linhas_sure = []
        
        self.setup_secao_surebet()
        self.setup_secao_media()

        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

    def preencher_dados_freebet(self, casa, valor, ids_origem):
        self.casa_fb_pendente = casa
        self.ids_fb_pendente = ids_origem
        
        if self.linhas_sure:
            self.linhas_sure[0]["stake"].setText(f"{valor:.2f}")
            self.linhas_sure[0]["chk_fb"].setChecked(True)
            self.calcular_surebet()

    def setup_secao_surebet(self):
        grupo_sure = QGroupBox("Calculadora de Arbitragem Avançada")
        grupo_sure.setStyleSheet(self.estilo_geral)
        lay_sure = QVBoxLayout(grupo_sure)
        lay_sure.setSpacing(15)

        lay_seletores = QHBoxLayout()
        vbox_tipo = QVBoxLayout()
        vbox_tipo.addWidget(QLabel("Modelo de Cálculo:"))
        self.combo_modelo = QComboBox()
        self.combo_modelo.setFixedWidth(200)
        self.combo_modelo.addItems(["Surebet Padrão", "Surebet 0x0 (Empate Lado 1)"])
        self.combo_modelo.currentIndexChanged.connect(self.calcular_surebet)
        vbox_tipo.addWidget(self.combo_modelo)
        
        vbox_qtd = QVBoxLayout()
        vbox_qtd.addWidget(QLabel("Qtd. de Apostas:"))
        self.combo_qtd = QComboBox()
        self.combo_qtd.setFixedWidth(100)
        self.combo_qtd.addItems(["2", "3", "4", "5", "6"])
        self.combo_qtd.currentIndexChanged.connect(self.atualizar_linhas_surebet)
        vbox_qtd.addWidget(self.combo_qtd)

        lay_seletores.addLayout(vbox_tipo)
        lay_seletores.addLayout(vbox_qtd)
        lay_seletores.addStretch()
        lay_sure.addLayout(lay_seletores)

        self.container_linhas_sure = QWidget()
        self.layout_linhas = QVBoxLayout(self.container_linhas_sure)
        self.layout_linhas.setContentsMargins(0, 10, 0, 10)
        self.layout_linhas.setSpacing(10)
        lay_sure.addWidget(self.container_linhas_sure)

        self.frame_res = QFrame()
        self.frame_res.setStyleSheet("background-color: #18181b; border-radius: 8px; padding: 15px;")
        lay_res = QHBoxLayout(self.frame_res)
        
        self.lbl_investimento = QLabel("Custo Efetivo: R$ 0.00")
        self.lbl_retorno = QLabel("Retorno: R$ 0.00")
        self.lbl_lucro_sure = QLabel("Lucro: R$ 0.00 (0%)")
        self.lbl_lucro_sure.setStyleSheet("color: #34d399; font-weight: bold; font-size: 15px;")
        
        lay_res.addWidget(self.lbl_investimento)
        lay_res.addWidget(self.lbl_retorno)
        lay_res.addWidget(self.lbl_lucro_sure)
        lay_sure.addWidget(self.frame_res)

        lay_acoes = QHBoxLayout()
        self.check_duplo = QCheckBox("Possibilidade de Duplo Green (Média dos Retornos)")
        self.check_duplo.setStyleSheet("color: #a1a1aa; font-weight: bold; font-size: 13px;")
        
        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.setStyleSheet("background-color: transparent; color: #f87171; font-weight: bold; padding: 10px 20px; border: 1px solid #f87171; border-radius: 8px;")
        self.btn_limpar.clicked.connect(self.limpar_calculadora)
        
        self.btn_criar_proc = QPushButton("Criar Procedimento")
        self.btn_criar_proc.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 10px 20px; border-radius: 8px;")
        self.btn_criar_proc.clicked.connect(self.abrir_modal_procedimento)
        
        lay_acoes.addWidget(self.check_duplo)
        lay_acoes.addStretch()
        lay_acoes.addWidget(self.btn_limpar)
        lay_acoes.addWidget(self.btn_criar_proc)
        
        lay_sure.addLayout(lay_acoes)

        self.atualizar_linhas_surebet()
        self.layout_container.addWidget(grupo_sure)

    def atualizar_indicador_adv(self, idx):
        """Muda o estilo do botão ▼ se houver opções avançadas ativas na linha"""
        l = self.linhas_sure[idx]
        tem_algo = bool(l["inp_aum"].text().strip() or l["inp_com"].text().strip() or l["inp_cash"].text().strip() or l["chk_fb"].isChecked())
        sinal = "▲" if l["container_adv"].isVisible() else "▼"
        
        l["btn_adv"].setText(f"{sinal} *" if tem_algo else sinal)
        if tem_algo:
            l["btn_adv"].setStyleSheet("background-color: rgba(59, 130, 246, 0.1); color: #3b82f6; font-size: 12px; border: 1px solid #3b82f6; border-radius: 6px; font-weight: bold;")
        else:
            l["btn_adv"].setStyleSheet("background-color: transparent; color: #a1a1aa; font-size: 12px; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;")

    def atualizar_linhas_surebet(self):
        estados = []
        for l in self.linhas_sure:
            estados.append({
                "odd": l["odd"].text(), "stake": l["stake"].text(), "resp": l["inp_resp"].text(),
                "tipo": l["btn_tipo"].text(), "aum": l["inp_aum"].text(), "com": l["inp_com"].text(),
                "cash": l["inp_cash"].text(), "freebet": l["chk_fb"].isChecked(), "adv_vis": l["container_adv"].isVisible()
            })

        for i in reversed(range(self.layout_linhas.count())): 
            w = self.layout_linhas.itemAt(i).widget()
            if w: w.deleteLater()
        self.linhas_sure.clear()

        qtd = int(self.combo_qtd.currentText())
        
        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)
        
        lbl_h1 = QLabel("Odd")
        lbl_h2 = QLabel("Stake / Risco (Lay)")
        lbl_h4 = QLabel("B/L")
        lbl_h4.setFixedWidth(40)
        lbl_h4.setAlignment(Qt.AlignCenter)
        lbl_h5 = QLabel("")
        lbl_h5.setFixedWidth(35)
        lbl_h6 = QLabel("Lucro Líquido")
        lbl_h6.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        h_lay.addWidget(lbl_h1, 2)
        h_lay.addWidget(lbl_h2, 4)
        h_lay.addWidget(lbl_h4, 0)
        h_lay.addWidget(lbl_h5, 0)
        h_lay.addWidget(lbl_h6, 3)
        self.layout_linhas.addWidget(header)

        for i in range(qtd):
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 5)
            row_layout.setSpacing(5)

            main_row = QWidget()
            m_lay = QHBoxLayout(main_row)
            m_lay.setContentsMargins(0, 0, 0, 0)
            m_lay.setSpacing(10)
            
            inp_odd = QLineEdit(); inp_odd.setPlaceholderText("Odd")
            
            container_stake = QWidget()
            lay_stake = QHBoxLayout(container_stake)
            lay_stake.setContentsMargins(0, 0, 0, 0)
            lay_stake.setSpacing(10)
            
            inp_stake = QLineEdit()
            inp_resp = QLineEdit(); inp_resp.setPlaceholderText("Risco (Lay)")
            inp_resp.setStyleSheet("color: #ec4899; font-weight: bold; background-color: rgba(236, 72, 153, 0.05); border: 1px solid rgba(236, 72, 153, 0.2);")
            inp_resp.hide()
            
            lay_stake.addWidget(inp_stake, 1)
            lay_stake.addWidget(inp_resp, 1)
            
            inp_odd.returnPressed.connect(inp_odd.focusNextChild)
            inp_stake.returnPressed.connect(inp_stake.focusNextChild)
            inp_resp.returnPressed.connect(inp_resp.focusNextChild)

            if i == 0:
                inp_stake.setPlaceholderText("Sua Stake")
            else:
                inp_stake.setPlaceholderText("Stake Auto")

            btn_tipo = QPushButton("B")
            btn_tipo.setFixedSize(40, 40)
            btn_tipo.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
            btn_tipo.setCursor(Qt.PointingHandCursor)
            
            btn_adv = QPushButton("▼")
            btn_adv.setFixedSize(35, 40)
            btn_adv.setStyleSheet("background-color: transparent; color: #a1a1aa; font-size: 12px; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;")
            btn_adv.setCursor(Qt.PointingHandCursor)

            lbl_lucro = QLabel("R$ 0.00")
            lbl_lucro.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_lucro.setStyleSheet("color: #a1a1aa; font-weight: bold; background-color: #18181b; border-radius: 6px; padding: 8px 15px; font-size: 15px;")
            
            m_lay.addWidget(inp_odd, 2)
            m_lay.addWidget(container_stake, 4)
            m_lay.addWidget(btn_tipo, 0)
            m_lay.addWidget(btn_adv, 0)
            m_lay.addWidget(lbl_lucro, 3)

            adv_row = QWidget()
            a_lay = QHBoxLayout(adv_row)
            a_lay.setContentsMargins(10, 10, 10, 10)
            adv_row.setStyleSheet("background-color: #18181b; border-radius: 6px;")
            
            lbl_aum = QLabel("Aumento %:"); inp_aum = QLineEdit(); inp_aum.setFixedWidth(60)
            lbl_com = QLabel("Comissão %:"); inp_com = QLineEdit(); inp_com.setFixedWidth(60)
            lbl_cash = QLabel("Cashback %:"); inp_cash = QLineEdit(); inp_cash.setFixedWidth(60)
            chk_fb = QCheckBox("Freebet (Só Lucro)")
            chk_fb.setStyleSheet("color: #f4f4f5; font-weight: bold; margin-left: 10px;")

            a_lay.addStretch()
            a_lay.addWidget(lbl_aum); a_lay.addWidget(inp_aum); a_lay.addSpacing(15)
            a_lay.addWidget(lbl_com); a_lay.addWidget(inp_com); a_lay.addSpacing(15)
            a_lay.addWidget(lbl_cash); a_lay.addWidget(inp_cash); a_lay.addSpacing(15)
            a_lay.addWidget(chk_fb)
            a_lay.addStretch()
            
            adv_row.hide()

            row_layout.addWidget(main_row)
            row_layout.addWidget(adv_row)
            self.layout_linhas.addWidget(row_widget)

            self.linhas_sure.append({
                "odd": inp_odd, "stake": inp_stake, "inp_resp": inp_resp, "btn_tipo": btn_tipo, 
                "lucro_lbl": lbl_lucro, "btn_adv": btn_adv, "container_adv": adv_row,
                "inp_aum": inp_aum, "inp_com": inp_com, "inp_cash": inp_cash, "chk_fb": chk_fb
            })
            
            def toggle_tipo(checked=False, idx=i):
                b = self.linhas_sure[idx]["btn_tipo"]
                resp = self.linhas_sure[idx]["inp_resp"]
                if b.text() == "B":
                    b.setText("L")
                    b.setStyleSheet("background-color: #ec4899; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
                    resp.show()
                else:
                    b.setText("B")
                    b.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
                    resp.hide()
                self.sincronizar_campos(idx, "odd")
                self.calcular_surebet()

            def toggle_adv(checked=False, idx=i):
                c = self.linhas_sure[idx]["container_adv"]
                if c.isVisible(): c.hide()
                else: c.show()
                self.atualizar_indicador_adv(idx)

            btn_tipo.clicked.connect(lambda chk=False, idx=i: toggle_tipo(chk, idx))
            btn_adv.clicked.connect(lambda chk=False, idx=i: toggle_adv(chk, idx))
            
            if i < len(estados):
                e = estados[i]
                inp_odd.setText(e["odd"]); inp_stake.setText(e["stake"]); inp_resp.setText(e["resp"])
                inp_aum.setText(e["aum"]); inp_com.setText(e["com"]); inp_cash.setText(e["cash"])
                chk_fb.setChecked(e["freebet"])
                if e["tipo"] == "L":
                    btn_tipo.setText("L"); btn_tipo.setStyleSheet("background-color: #ec4899; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
                    inp_resp.show()
                if e["adv_vis"]: adv_row.show()

            inp_odd.textEdited.connect(lambda txt, idx=i: self.on_text_edited(idx, "odd"))
            inp_stake.textEdited.connect(lambda txt, idx=i: self.on_text_edited(idx, "stake"))
            inp_resp.textEdited.connect(lambda txt, idx=i: self.on_text_edited(idx, "resp"))
            
            for inp in [inp_aum, inp_com, inp_cash]: 
                inp.textChanged.connect(self.calcular_surebet)
                inp.textChanged.connect(lambda txt, idx=i: self.atualizar_indicador_adv(idx))
            
            chk_fb.stateChanged.connect(self.calcular_surebet)
            chk_fb.stateChanged.connect(lambda state, idx=i: self.atualizar_indicador_adv(idx))
            
            self.atualizar_indicador_adv(i)

        self.calcular_surebet()

    def limpar_calculadora(self):
        self.combo_modelo.setCurrentIndex(0)
        self.check_duplo.setChecked(False)
        self.casa_fb_pendente = None
        self.ids_fb_pendente = None
        
        for idx, l in enumerate(self.linhas_sure):
            l["odd"].setText("")
            l["stake"].setText("")
            l["inp_resp"].setText("")
            l["inp_aum"].setText("")
            l["inp_com"].setText("")
            l["inp_cash"].setText("")
            l["chk_fb"].setChecked(False)
            if l["btn_tipo"].text() == "L":
                l["btn_tipo"].setText("B")
                l["btn_tipo"].setStyleSheet("background-color: #3b82f6; color: white; border-radius: 6px; font-weight: bold; font-size: 16px;")
                l["inp_resp"].hide()
            self.atualizar_indicador_adv(idx)
                
        self.combo_qtd.blockSignals(True)
        self.combo_qtd.setCurrentIndex(0)
        self.combo_qtd.blockSignals(False)
        
        self.atualizar_linhas_surebet()
        
        for v_inp, o_inp in self.linhas_media:
            v_inp.setText("")
            o_inp.setText("")
        self.calcular_media()

    def on_text_edited(self, idx, source):
        if source in ["stake", "resp"]: self.last_edited_index = idx
        self.sincronizar_campos(idx, source)
        self.calcular_surebet()

    def sincronizar_campos(self, idx, source):
        l = self.linhas_sure[idx]
        if l["btn_tipo"].text() == "B":
            l["inp_resp"].blockSignals(True); l["inp_resp"].setText(""); l["inp_resp"].blockSignals(False)
            return 

        try:
            o = float(l["odd"].text().replace(',', '.'))
            if o <= 1: return
            
            if source in ["stake", "odd"]:
                s_str = l["stake"].text().replace(',', '.')
                if s_str:
                    s = float(s_str)
                    l["inp_resp"].blockSignals(True)
                    l["inp_resp"].setText(f"{s * (o - 1):.2f}")
                    l["inp_resp"].blockSignals(False)
            elif source == "resp":
                r_str = l["inp_resp"].text().replace(',', '.')
                if r_str:
                    r = float(r_str)
                    l["stake"].blockSignals(True)
                    l["stake"].setText(f"{r / (o - 1):.2f}")
                    l["stake"].blockSignals(False)
        except ValueError: pass

    def calcular_surebet(self):
        for l in self.linhas_sure:
            l["stake"].blockSignals(True)
            l["inp_resp"].blockSignals(True)
            
        try:
            for l in self.linhas_sure:
                o_str = l["odd"].text().replace(',', '.')
                o_raw = float(o_str) if o_str else 0.0
                aum = float(l["inp_aum"].text().replace(',', '.')) if l["inp_aum"].text() else 0.0
                com = float(l["inp_com"].text().replace(',', '.')) if l["inp_com"].text() else 0.0
                cash = float(l["inp_cash"].text().replace(',', '.')) if l["inp_cash"].text() else 0.0
                is_fb = l["chk_fb"].isChecked()
                is_lay = l["btn_tipo"].text() == "L"
                
                o_eff = 1 + (o_raw - 1) * (1 + aum/100)
                
                if is_lay:
                    M = (o_eff - 1) + (1 - com/100) - (o_eff - 1) * (cash/100)
                    k = (o_eff - 1)
                    b = (o_eff - 1) * (cash/100)
                else:
                    if is_fb:
                        M = (o_eff - 1) * (1 - com/100)
                        k = 0 
                        b = 0 
                    else:
                        M = 1 + (o_eff - 1) * (1 - com/100) - (cash/100)
                        k = 1
                        b = cash/100
                        
                l["math"] = {"M": M, "k": k, "b": b, "o_eff": o_eff, "is_lay": is_lay}

            b_idx = self.last_edited_index
            if b_idx >= len(self.linhas_sure): b_idx = 0
            base_str = self.linhas_sure[b_idx]["stake"].text().replace(',', '.')
            if not base_str: raise Exception("Vazio")
            s_base = float(base_str)
            
            modelo = self.combo_modelo.currentText()
            stakes = [0.0] * len(self.linhas_sure)
            stakes[b_idx] = s_base

            if "0x0" in modelo:
                soma_W = 0
                for j in range(1, len(self.linhas_sure)):
                    calc = self.linhas_sure[j]["math"]
                    if calc["M"] > 0: soma_W += (calc["k"] - calc["b"]) / calc["M"]
                
                if b_idx == 0:
                    c1 = self.linhas_sure[0]["math"]
                    nr_outros = (s_base * (c1["M"] - (c1["k"] - c1["b"]))) / soma_W if soma_W > 0 else 0
                    for j in range(1, len(self.linhas_sure)):
                        if self.linhas_sure[j]["math"]["M"] > 0: stakes[j] = nr_outros / self.linhas_sure[j]["math"]["M"]
                else:
                    nr_outros = s_base * self.linhas_sure[b_idx]["math"]["M"]
                    for j in range(1, len(self.linhas_sure)):
                        if j != b_idx and self.linhas_sure[j]["math"]["M"] > 0: stakes[j] = nr_outros / self.linhas_sure[j]["math"]["M"]
                    c1 = self.linhas_sure[0]["math"]
                    num = nr_outros * soma_W
                    den = c1["M"] - (c1["k"] - c1["b"])
                    stakes[0] = num / den if den != 0 else 0
            else:
                nr_alvo = s_base * self.linhas_sure[b_idx]["math"]["M"]
                for j in range(len(self.linhas_sure)):
                    if j != b_idx and self.linhas_sure[j]["math"]["M"] > 0:
                        stakes[j] = nr_alvo / self.linhas_sure[j]["math"]["M"]

            custo_total = 0.0
            cashback_total = 0.0
            lucros_brutos = []
            retornos_monetarios = []
            
            for i, l in enumerate(self.linhas_sure):
                c = l["math"]
                
                if i == b_idx:
                    s_final = s_base
                else:
                    if c["is_lay"]: s_final = round(stakes[i], 2)
                    else: s_final = float(int(round(stakes[i])))
                
                if i != b_idx: 
                    if c["is_lay"]: l["stake"].setText(f"{s_final:.2f}")
                    else: l["stake"].setText(f"{int(s_final)}")
                    
                if c["is_lay"]: 
                    l["inp_resp"].setText(f"{s_final * c['o_eff'] - s_final:.2f}")
                
                custo = s_final * c["k"]
                cb = s_final * c["b"]
                nr = s_final * c["M"]
                
                custo_total += custo
                cashback_total += cb
                lucros_brutos.append(nr)
                retornos_monetarios.append(nr + (custo - cb))

            investimento_liquido = custo_total - cashback_total
            lucros_finais = [lb - investimento_liquido for lb in lucros_brutos]

            for i, l in enumerate(self.linhas_sure):
                lf = lucros_finais[i]
                l["lucro_lbl"].setText(f"R$ {lf:.2f}")
                cor = "#34d399" if lf > 0 else ("#f87171" if lf < 0 else "#a1a1aa")
                l["lucro_lbl"].setStyleSheet(f"color: {cor}; font-weight: bold; background-color: #18181b; border-radius: 6px; padding: 8px 15px; font-size: 15px;")
                
            self.media_retornos_atual = sum(retornos_monetarios) / len(retornos_monetarios) if retornos_monetarios else 0.0
            
            if "0x0" in modelo:
                lg = lucros_finais[1] if len(lucros_finais) > 1 else 0
                ret_padrao = retornos_monetarios[1] if len(retornos_monetarios) > 1 else 0
            else:
                lg = min(lucros_finais) if lucros_finais else 0
                ret_padrao = min(retornos_monetarios) if retornos_monetarios else 0

            self.lbl_investimento.setText(f"Investimento Efetivo: R$ {investimento_liquido:.2f}")
            self.lbl_retorno.setText(f"Retorno Ref: R$ {ret_padrao:.2f}")
            porc = (lg / investimento_liquido * 100) if investimento_liquido > 0 else 0
            self.lbl_lucro_sure.setText(f"Lucro Líquido: R$ {lg:.2f} ({porc:.1f}%)")
            self.lbl_lucro_sure.setStyleSheet(f"color: {'#34d399' if lg >= 0 else '#f87171'}; font-weight: bold; font-size: 15px;")
            
            self.lucro_global_atual = lg

        except Exception as e:
            pass
        finally:
            for l in self.linhas_sure:
                l["stake"].blockSignals(False)
                l["inp_resp"].blockSignals(False)

    def abrir_modal_procedimento(self):
        try:
            if not self.linhas_sure[0]["stake"].text():
                QMessageBox.warning(self, "Aviso", "Preencha primeiro a sua Entrada Base e as Odds.")
                return
                
            lucro_base = getattr(self, 'lucro_global_atual', 0.0)
            media_retornos = getattr(self, 'media_retornos_atual', 0.0)
            is_duplo = self.check_duplo.isChecked()
            
            tipo = "Converter Freebet" if self.casa_fb_pendente else ('Tentativa de Duplo' if is_duplo else 'SureBet')
            casa_sugerida = self.casa_fb_pendente if self.casa_fb_pendente else 'Nenhuma selecionada'
            
            d = {
                'tipo': tipo,
                'jogo': '', 'casas': casa_sugerida,
                'lucro_base': round(lucro_base, 2),
                'v_duplo': round(media_retornos, 2) if is_duplo else 0.0,
                'obs': '', 'condicao': '', 'casa_fb': self.casa_fb_pendente if self.casa_fb_pendente else ''
            }
            
            dialog = DialogNovoProcedimento(self, dados_edicao=d)
            if dialog.exec() == QDialog.Accepted:
                if self.ids_fb_pendente:
                    database.salvar_conversao_freebet(dialog.dados_finais, self.ids_fb_pendente)
                    self.casa_fb_pendente = None
                    self.ids_fb_pendente = None
                else:
                    database.salvar_procedimento(dialog.dados_finais)
                    
                QMessageBox.information(self, "Sucesso", "Procedimento salvo com sucesso!\nEle já aparecerá na aba de Procedimentos.")
        except Exception:
            QMessageBox.warning(self, "Erro", "Houve um problema ao criar o procedimento. Verifique os valores.")

    def setup_secao_media(self):
        grupo_media = QGroupBox("Média Ponderada de Odds")
        grupo_media.setStyleSheet(self.estilo_geral)
        lay_media = QVBoxLayout(grupo_media)
        self.container_media = QWidget()
        self.grid_media = QGridLayout(self.container_media)
        lay_media.addWidget(self.container_media)
        btn_add = QPushButton("+ Adicionar Aposta")
        btn_add.setFixedWidth(200)
        btn_add.clicked.connect(self.add_linha_media)
        lay_media.addWidget(btn_add)
        self.lbl_res_media = QLabel("Odd Média: 0.00")
        self.lbl_res_media.setStyleSheet("color: #3b82f6; font-size: 18px; font-weight: bold; margin-top: 15px;")
        lay_media.addWidget(self.lbl_res_media)
        self.linhas_media = []
        self.add_linha_media(); self.add_linha_media()
        self.layout_container.addWidget(grupo_media)

    def add_linha_media(self):
        row = len(self.linhas_media) + 1
        if row == 1:
            self.grid_media.addWidget(QLabel("Valor (R$)"), 0, 0)
            self.grid_media.addWidget(QLabel("Odd"), 0, 1)
        inp_val = QLineEdit(); inp_val.setPlaceholderText("Valor"); inp_val.returnPressed.connect(inp_val.focusNextChild)
        inp_odd = QLineEdit(); inp_odd.setPlaceholderText("Odd"); inp_odd.returnPressed.connect(inp_odd.focusNextChild)
        inp_val.textChanged.connect(self.calcular_media); inp_odd.textChanged.connect(self.calcular_media)
        self.grid_media.addWidget(inp_val, row, 0); self.grid_media.addWidget(inp_odd, row, 1)
        self.linhas_media.append((inp_val, inp_odd))

    def calcular_media(self):
        soma_prod = 0; soma_val = 0
        try:
            for v_inp, o_inp in self.linhas_media:
                v = float(v_inp.text().replace(',', '.')) if v_inp.text() else 0
                o = float(o_inp.text().replace(',', '.')) if o_inp.text() else 0
                soma_prod += (v * o); soma_val += v
            self.lbl_res_media.setText(f"Odd Média: {soma_prod / soma_val:.2f}" if soma_val > 0 else "Odd Média: 0.00")
        except: pass