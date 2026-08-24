from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout
from shiboken6 import isValid

from core import tema


def _vivo(widget):
    """True se o objeto C++ por tras do widget ainda existe.

    As notificacoes se autodestroem por tempo, entao a lista de ativas pode
    guardar itens ja destruidos. Mexer neles derruba o app.
    """
    return widget is not None and isValid(widget)


def _janela_alvo(parent):
    if parent is not None:
        return parent.window()
    return QApplication.activeWindow()


def _reposicionar_notificacoes(janela):
    if not _vivo(janela):
        return

    notificacoes = getattr(janela, "_notificacoes_ativas", [])
    # Descarta de uma vez as que ja foram destruidas.
    notificacoes[:] = [n for n in notificacoes if _vivo(n)]

    margem = 20
    espacamento = 10
    y = margem

    for notificacao in list(notificacoes):
        notificacao.adjustSize()
        x = max(margem, janela.width() - notificacao.width() - margem)
        notificacao.move(x, y)
        y += notificacao.height() + espacamento


class NotificacaoToast(QFrame):
    def __init__(self, parent, titulo, mensagem="", duracao=3500):
        super().__init__(parent)
        self.janela = parent
        self._fechando = False
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName("notificacaoToast")
        self.setFixedWidth(360)
        self.setStyleSheet(f"""
            QFrame#notificacaoToast {{
                background-color: {tema.SUPERFICIE};
                border: 1px solid {tema.BORDA_FORTE};
                border-radius: {tema.RAIO_G}px;
            }}
            QLabel#notificacaoTitulo {{
                color: {tema.TEXTO};
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#notificacaoMensagem {{
                color: {tema.TEXTO_SECUNDARIO};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("notificacaoTitulo")
        layout.addWidget(lbl_titulo)

        if mensagem:
            lbl_mensagem = QLabel(mensagem)
            lbl_mensagem.setObjectName("notificacaoMensagem")
            lbl_mensagem.setWordWrap(True)
            layout.addWidget(lbl_mensagem)

        self.adjustSize()
        # O 'self' no meio amarra o disparo ao tempo de vida da notificacao:
        # se ela for destruida antes da hora, o timer e descartado junto em vez
        # de chamar um metodo de um objeto que ja nao existe.
        QTimer.singleShot(duracao, self, self.fechar)

    def fechar(self):
        if self._fechando or not _vivo(self):
            return
        self._fechando = True

        janela = self.janela
        notificacoes = getattr(janela, "_notificacoes_ativas", []) if _vivo(janela) else []
        if self in notificacoes:
            notificacoes.remove(self)

        self.close()
        _reposicionar_notificacoes(janela)


def mostrar_notificacao(parent, titulo, mensagem="", duracao=3500):
    janela = _janela_alvo(parent)
    if not _vivo(janela):
        return

    if not hasattr(janela, "_notificacoes_ativas"):
        janela._notificacoes_ativas = []

    notificacao = NotificacaoToast(janela, titulo, mensagem, duracao)
    janela._notificacoes_ativas.append(notificacao)
    notificacao.show()
    notificacao.raise_()
    _reposicionar_notificacoes(janela)
