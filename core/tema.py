"""Tema central do GerProce.

Reúne em um único lugar a paleta, os espaçamentos e o stylesheet global do app.
As telas devem usar estas constantes e helpers em vez de repetir cores soltas,
para que toda a interface mude a partir daqui.
"""
import os
import sys

# ------------------------------------------------------------- recursos ----


def caminho_recurso(relativo):
    """Caminho de um arquivo da pasta do projeto, tambem dentro do PyInstaller."""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, relativo)


def _url_qss(relativo):
    """Caminho no formato aceito por url() dentro de um stylesheet."""
    return caminho_recurso(relativo).replace("\\", "/")


ICONE_SETA_BAIXO = _url_qss("icon/chevron_baixo.png")
ICONE_SETA_BAIXO_CLARO = _url_qss("icon/chevron_baixo_claro.png")
ICONE_CHECK = _url_qss("icon/check.png")

# ---------------------------------------------------------------- paleta ----
FUNDO = "#09090b"
SUPERFICIE = "#18181b"
SUPERFICIE_ALTA = "#27272a"
SUPERFICIE_HOVER = "#3f3f46"

TEXTO = "#f4f4f5"
TEXTO_SECUNDARIO = "#a1a1aa"
TEXTO_TERCIARIO = "#71717a"

BORDA = "rgba(255, 255, 255, 0.06)"
BORDA_SUTIL = "rgba(255, 255, 255, 0.03)"
BORDA_FORTE = "rgba(255, 255, 255, 0.12)"

AZUL = "#3b82f6"
AZUL_HOVER = "#2563eb"
VERDE = "#34d399"
VERMELHO = "#f87171"
VERMELHO_HOVER = "#ef4444"
ROXO = "#a855f7"
AMBAR = "#fbbf24"

# Aliases usados pelas telas para dar significado ao valor exibido.
COR_POSITIVO = VERDE
COR_NEGATIVO = VERMELHO
COR_DESTAQUE = AZUL
COR_FREEBET = ROXO

# ------------------------------------------------------------- métricas ----
RAIO_P = 6
RAIO_M = 8
RAIO_G = 12
RAIO_CARD = 16

ESPACO_P = 8
ESPACO_M = 16
ESPACO_G = 24
MARGEM_TELA = (40, 30, 40, 40)

FONTE = (
    "'Inter', 'Segoe UI Variable', 'Segoe UI', -apple-system, "
    "BlinkMacSystemFont, Roboto, sans-serif"
)


def cor_valor(valor):
    """Verde para resultado positivo ou neutro, vermelho para negativo."""
    return COR_POSITIVO if valor >= 0 else COR_NEGATIVO


def estilo_card(fundo=SUPERFICIE, raio=RAIO_CARD):
    return f"QFrame {{ background-color: {fundo}; border-radius: {raio}px; border: none; }}"


def estilo_titulo_tela():
    return f"color: {TEXTO}; font-size: 24px; font-weight: bold; background: transparent;"


def estilo_secao():
    return f"color: {TEXTO_SECUNDARIO}; font-size: 13px; font-weight: bold; background: transparent;"


def estilo_texto_secundario():
    return f"color: {TEXTO_SECUNDARIO}; font-size: 13px; background: transparent;"


def estilo_tabela_cartao():
    """Tabela dentro de um diálogo, desenhada como um bloco com borda."""
    return f"""
        QTableWidget {{
            background-color: #111113;
            color: {TEXTO};
            border: 1px solid {BORDA};
            border-radius: {RAIO_M}px;
            outline: none;
        }}
        QTableWidget::item {{ border: none; border-bottom: 1px solid {BORDA_SUTIL}; padding: 8px; }}
        QTableWidget::item:selected {{ background-color: {SUPERFICIE_ALTA}; color: {TEXTO}; }}
        QHeaderView::section {{
            background-color: {SUPERFICIE};
            color: {TEXTO_SECUNDARIO};
            border: none;
            padding: 10px 8px;
            font-weight: bold;
        }}
    """


def estilo_tooltip_flutuante():
    """Tooltip desenhado como QLabel sobre os gráficos (não expira sozinho)."""
    return (
        "QLabel {"
        f" background-color: rgba(24, 24, 27, 240); color: {TEXTO};"
        f" border: 1px solid {BORDA_FORTE}; border-radius: {RAIO_M}px;"
        " padding: 6px 12px; font-weight: bold; font-size: 13px; }"
    )


# ------------------------------------------------------ stylesheet global ---
# Variantes de botão são escolhidas pela propriedade dinâmica "variante".
# Ex.: botao.setProperty("variante", "primario")
ESTILO_GLOBAL = f"""
* {{
    font-family: {FONTE};
}}

QMainWindow, QDialog {{
    background-color: {FUNDO};
}}

QWidget {{
    color: {TEXTO};
}}

QLabel {{
    background: transparent;
    color: {TEXTO};
    font-size: 14px;
}}

/* ------------------------------------------------------------- botões --- */
QPushButton {{
    background-color: {SUPERFICIE_ALTA};
    color: {TEXTO};
    font-size: 14px;
    font-weight: 600;
    padding: 9px 16px;
    border: 1px solid {BORDA};
    border-radius: {RAIO_M}px;
}}
QPushButton:hover {{
    background-color: {SUPERFICIE_HOVER};
}}
QPushButton:pressed {{
    background-color: {SUPERFICIE_ALTA};
}}
QPushButton:disabled {{
    background-color: {SUPERFICIE};
    color: {TEXTO_TERCIARIO};
    border-color: {BORDA_SUTIL};
}}

QPushButton[variante="primario"] {{
    background-color: {TEXTO};
    color: {FUNDO};
    border: none;
}}
QPushButton[variante="primario"]:hover {{
    background-color: #d4d4d8;
}}
QPushButton[variante="primario"]:disabled {{
    background-color: {SUPERFICIE_ALTA};
    color: {TEXTO_TERCIARIO};
}}

QPushButton[variante="acento"] {{
    background-color: {AZUL};
    color: #ffffff;
    border: none;
}}
QPushButton[variante="acento"]:hover {{
    background-color: {AZUL_HOVER};
}}
QPushButton[variante="acento"]:disabled {{
    background-color: {SUPERFICIE_ALTA};
    color: {TEXTO_TERCIARIO};
}}

QPushButton[variante="fantasma"] {{
    background-color: transparent;
    color: {TEXTO_SECUNDARIO};
    border: none;
}}
QPushButton[variante="fantasma"]:hover {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {TEXTO};
}}

QPushButton[variante="perigo"] {{
    background-color: transparent;
    color: {VERMELHO};
    border: 1px solid {VERMELHO};
}}
QPushButton[variante="perigo"]:hover {{
    background-color: rgba(248, 113, 113, 0.12);
}}

QPushButton[variante="navegacao"] {{
    background-color: transparent;
    color: {TEXTO_SECUNDARIO};
    border: 1px solid transparent;
    padding: 8px 16px;
    border-radius: {RAIO_P}px;
}}
QPushButton[variante="navegacao"]:hover {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {TEXTO};
}}
QPushButton[variante="navegacao"]:checked {{
    background-color: {SUPERFICIE};
    color: {TEXTO};
    border: 1px solid {BORDA};
}}

/* ------------------------------------------------------------ entradas -- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit, QTextEdit {{
    background-color: {SUPERFICIE};
    color: {TEXTO};
    font-size: 14px;
    border: 1px solid {BORDA};
    border-radius: {RAIO_M}px;
    padding: 9px 12px;
    selection-background-color: {AZUL};
    selection-color: #ffffff;
}}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover {{
    border: 1px solid {BORDA_FORTE};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {AZUL};
}}
QLineEdit:disabled, QComboBox:disabled {{
    color: {TEXTO_TERCIARIO};
}}
QLineEdit[somenteLeitura="true"] {{
    background-color: {SUPERFICIE};
    color: {TEXTO_SECUNDARIO};
    border: 1px solid {BORDA_SUTIL};
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}}
QComboBox::down-arrow {{
    image: url({ICONE_SETA_BAIXO});
    width: 12px;
    height: 12px;
}}
QComboBox::down-arrow:hover, QComboBox::down-arrow:on {{
    image: url({ICONE_SETA_BAIXO_CLARO});
}}
QComboBox QAbstractItemView {{
    background-color: {SUPERFICIE};
    color: {TEXTO};
    border: 1px solid {BORDA};
    border-radius: {RAIO_M}px;
    padding: 4px;
    outline: none;
    selection-background-color: {SUPERFICIE_ALTA};
    selection-color: {TEXTO};
}}

QCheckBox {{
    color: {TEXTO};
    font-size: 14px;
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDA_FORTE};
    border-radius: {RAIO_P}px;
    background-color: {SUPERFICIE};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {AZUL};
}}
QCheckBox::indicator:checked {{
    background-color: {AZUL};
    border: 1px solid {AZUL};
    image: url({ICONE_CHECK});
}}

/* ------------------------------------------------------------ tabelas --- */
QTableWidget, QTableView {{
    background-color: transparent;
    alternate-background-color: transparent;
    color: {TEXTO};
    border: none;
    outline: none;
    font-size: 14px;
    gridline-color: transparent;
}}
QTableWidget::item, QTableView::item {{
    border: none;
    border-bottom: 1px solid {BORDA_SUTIL};
    padding: 6px;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {SUPERFICIE_ALTA};
    color: {TEXTO};
}}
QHeaderView::section {{
    background-color: transparent;
    color: {TEXTO_TERCIARIO};
    font-size: 12px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid {BORDA};
    padding: 12px 8px;
}}
QTableCornerButton::section {{
    background-color: transparent;
    border: none;
}}
QTableWidget::indicator, QTableView::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDA_FORTE};
    border-radius: 4px;
    background-color: {SUPERFICIE};
}}
QTableWidget::indicator:hover, QTableView::indicator:hover {{
    border: 1px solid {AZUL};
}}
QTableWidget::indicator:checked, QTableView::indicator:checked {{
    background-color: {AZUL};
    border: 1px solid {AZUL};
    image: url({ICONE_CHECK});
}}

/* --------------------------------------------------------------- abas --- */
QTabWidget::pane {{
    border: none;
    background-color: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXTO_TERCIARIO};
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: bold;
    font-size: 14px;
}}
QTabBar::tab:hover {{
    color: {TEXTO_SECUNDARIO};
}}
QTabBar::tab:selected {{
    color: {AZUL};
    border-bottom: 2px solid {AZUL};
}}
QTabBar::tab:focus {{
    outline: none;
}}

/* ------------------------------------------------------------- scroll --- */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {SUPERFICIE_ALTA};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SUPERFICIE_HOVER};
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {SUPERFICIE_ALTA};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {SUPERFICIE_HOVER};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
    width: 0;
    border: none;
    background: none;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}

/* -------------------------------------------------------- diversos ------ */
QGroupBox {{
    background-color: rgba(255, 255, 255, 0.02);
    border: 1px solid {BORDA};
    border-radius: {RAIO_G}px;
    margin-top: 14px;
    padding: 18px;
    font-size: 15px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 6px;
    color: {TEXTO};
}}

QToolTip {{
    background-color: {SUPERFICIE};
    color: {TEXTO};
    border: 1px solid {BORDA};
    border-radius: {RAIO_M}px;
    padding: 6px 10px;
    font-size: 13px;
}}

QMessageBox {{
    background-color: {FUNDO};
}}
QMessageBox QLabel {{
    color: {TEXTO};
    font-size: 14px;
}}

QDialogButtonBox QPushButton {{
    min-width: 96px;
}}
QDialogButtonBox QPushButton:default {{
    background-color: {TEXTO};
    color: {FUNDO};
    border: none;
}}
QDialogButtonBox QPushButton:default:hover {{
    background-color: #d4d4d8;
}}
QDialogButtonBox QPushButton:default:disabled {{
    background-color: {SUPERFICIE_ALTA};
    color: {TEXTO_TERCIARIO};
}}

#topBar {{
    background-color: {FUNDO};
    border-bottom: 1px solid {BORDA_SUTIL};
}}
"""


def aplicar_variante(widget, variante):
    """Define a variante visual de um botão e reaplica o estilo."""
    widget.setProperty("variante", variante)
    estilo = widget.style()
    estilo.unpolish(widget)
    estilo.polish(widget)
    return widget
