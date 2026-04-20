from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGridLayout, QFrame, QTabWidget, QComboBox, QPushButton)
from PySide6.QtCore import Qt
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
        self.mostrar_valor_freebet = False # Controle do Toggle de Freebet

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

        # Configuração padrão para todos os gráficos
        def criar_grafico(titulo):
            g = pg.PlotWidget(title=titulo)
            g.setBackground('#1a1d2d')
            g.showGrid(x=False, y=True, alpha=0.2)
            g.getAxis('left').setPen('#7b849b')
            g.getAxis('bottom').setPen('#7b849b')
            return g

        # Aba 1: Evolução (Linha)
        self.grafico_linha = criar_grafico("Evolução do Lucro")
        self.abas_graficos.addTab(self.grafico_linha, "Evolução Mensal")

        # Aba 2: Lucro Diário (Barra)
        self.grafico_barra_lucro = criar_grafico("Lucro por Dia")
        self.abas_graficos.addTab(self.grafico_barra_lucro, "Lucro Diário")

        # Aba 3: Volume de Procedimentos (Barra)
        self.grafico_barra_vol = criar_grafico("Quantidade de Procedimentos por Dia")
        self.abas_graficos.addTab(self.grafico_barra_vol, "Volume Diário")

        # Aba 4: Freebets com Toggle
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

    def alternar_modo_freebet(self):
        self.mostrar_valor_freebet = not self.mostrar_valor_freebet
        texto = "Visualizando: Valor (R$)" if self.mostrar_valor_freebet else "Visualizando: Quantidade"
        self.btn_toggle_freebet.setText(texto)
        self.atualizar_dados()

    def atualizar_dados(self):
        conexao = database.conectar()
        cursor = conexao.cursor()
        
        hoje_obj = datetime.now()
        hoje_str = hoje_obj.strftime("%d/%m/%Y")
        mes_atual = hoje_obj.strftime("%m/%Y")
        filtro = self.combo_filtro.currentText()
        
        # Lógica de Filtro
        if filtro == "Todos":
            cursor.execute("SELECT data_operacao, lucro_final, tipo_procedimento, valor_freebet_coletada FROM Procedimentos_Historico WHERE mes_referencia = ?", (mes_atual,))
        else:
            cursor.execute("SELECT data_operacao, lucro_final, tipo_procedimento, valor_freebet_coletada FROM Procedimentos_Historico WHERE mes_referencia = ? AND tipo_procedimento = ?", (mes_atual, filtro))
            
        registros = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM Procedimentos_Historico WHERE tipo_procedimento = 'Coletar Freebet' AND status_freebet = 'Pendente'")
        total_pendente = cursor.fetchone()[0]

        conexao.close()

        # Descobre quantos dias tem o mês atual (Ex: 30 ou 31)
        _, max_dias = calendar.monthrange(hoje_obj.year, hoje_obj.month)
        
        # Cria listas zeradas do dia 1 até o último dia do mês
        dias_x = list(range(1, max_dias + 1))
        lucro_por_dia = {d: 0.0 for d in dias_x}
        volume_por_dia = {d: 0 for d in dias_x}
        freebet_qtd_dia = {d: 0 for d in dias_x}
        freebet_valor_dia = {d: 0.0 for d in dias_x}

        lucro_mensal = 0.0
        lucro_hoje = 0.0
        proc_hoje = 0
        freebets_abertas = 0 # Placeholder até termos status de uso

        # Processa os dados do banco
        for data_op, lucro, tipo, valor_freebet in registros:
            if lucro is None: lucro = 0.0
            if valor_freebet is None: valor_freebet = 0.0
            
            dia_inteiro = int(data_op.split('/')[0]) # Pega o "19" de "19/04/2026"
            
            lucro_mensal += lucro
            lucro_por_dia[dia_inteiro] += lucro
            volume_por_dia[dia_inteiro] += 1
            
            if tipo == "Coletar Freebet":
                freebet_qtd_dia[dia_inteiro] += 1
                freebet_valor_dia[dia_inteiro] += valor_freebet

            if data_op == hoje_str:
                lucro_hoje += lucro
                proc_hoje += 1

        # Atualiza Cards
        self.card_lucro_diario.lbl_valor.setText(f"R$ {lucro_hoje:.2f}")
        self.card_lucro_diario.lbl_valor.setStyleSheet(f"color: {'#00e676' if lucro_hoje >= 0 else '#ff5252'}; font-size: 26px; font-weight: bold;")
        self.card_lucro_mensal.lbl_valor.setText(f"R$ {lucro_mensal:.2f}")
        self.card_lucro_mensal.lbl_valor.setStyleSheet(f"color: {'#00e676' if lucro_mensal >= 0 else '#ff5252'}; font-size: 26px; font-weight: bold;")
        self.card_media_diaria.lbl_valor.setText(f"R$ {(lucro_mensal / hoje_obj.day):.2f}")
        self.card_media_proc.lbl_valor.setText(f"R$ {(lucro_mensal / len(registros)) if registros else 0:.2f}")
        self.card_proc_hoje.lbl_valor.setText(str(proc_hoje))
        self.card_freebets.lbl_valor.setText(str(total_pendente))

        # --- Limpa e Desenha os Gráficos ---
        self.grafico_linha.clear()
        self.grafico_barra_lucro.clear()
        self.grafico_barra_vol.clear()
        self.grafico_barra_freebet.clear()

        # Acumulado Mensal (Linha)
        acumulado = 0
        lucro_acumulado_y = []
        for d in dias_x:
            acumulado += lucro_por_dia[d]
            lucro_acumulado_y.append(acumulado)
            
        pen_linha = pg.mkPen(color='#00e676', width=3)
        self.grafico_linha.plot(dias_x, lucro_acumulado_y, pen=pen_linha, symbol='o', symbolBrush='#1a1d2d', symbolPen='#00e676')

        # Lucro Diário (Barra)
        cores_lucro = ['#00e676' if lucro_por_dia[d] >= 0 else '#ff5252' for d in dias_x]
        bg_lucro = pg.BarGraphItem(x=dias_x, height=[lucro_por_dia[d] for d in dias_x], width=0.6, brushes=cores_lucro)
        self.grafico_barra_lucro.addItem(bg_lucro)

        # Volume (Barra)
        bg_vol = pg.BarGraphItem(x=dias_x, height=[volume_por_dia[d] for d in dias_x], width=0.6, brush='#00bcd4')
        self.grafico_barra_vol.addItem(bg_vol)

        # Freebet Toggle (Barra)
        if self.mostrar_valor_freebet:
            dados_freebet = [freebet_valor_dia[d] for d in dias_x]
            cor_fb = '#ffb300'
        else:
            dados_freebet = [freebet_qtd_dia[d] for d in dias_x]
            cor_fb = '#ffb300'
            
        bg_freebet = pg.BarGraphItem(x=dias_x, height=dados_freebet, width=0.6, brush=cor_fb)
        self.grafico_barra_freebet.addItem(bg_freebet)

        # Fixa o Eixo X para mostrar os dias certinhos (1, 2, 3...)
        for grafico in [self.grafico_linha, self.grafico_barra_lucro, self.grafico_barra_vol, self.grafico_barra_freebet]:
            grafico.setXRange(0.5, max_dias + 0.5, padding=0)
            grafico.getAxis('bottom').setTicks([[(d, str(d)) for d in dias_x]])
            