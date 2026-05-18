from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout


def _janela_alvo(parent):
    if parent is not None:
        return parent.window()
    return QApplication.activeWindow()


def _reposicionar_notificacoes(janela):
    notificacoes = getattr(janela, "_notificacoes_ativas", [])
    margem = 20
    espacamento = 10
    y = margem

    for notificacao in list(notificacoes):
        if notificacao is None:
            continue

        notificacao.adjustSize()
        x = max(margem, janela.width() - notificacao.width() - margem)
        notificacao.move(x, y)
        y += notificacao.height() + espacamento


class NotificacaoToast(QFrame):
    def __init__(self, parent, titulo, mensagem="", duracao=3500):
        super().__init__(parent)
        self.janela = parent
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName("notificacaoToast")
        self.setFixedWidth(360)
        self.setStyleSheet("""
            QFrame#notificacaoToast {
                background-color: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 10px;
            }
            QLabel#notificacaoTitulo {
                color: #f4f4f5;
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            QLabel#notificacaoMensagem {
                color: #a1a1aa;
                font-size: 13px;
                background: transparent;
                border: none;
            }
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
        QTimer.singleShot(duracao, self.fechar)

    def fechar(self):
        notificacoes = getattr(self.janela, "_notificacoes_ativas", [])
        if self in notificacoes:
            notificacoes.remove(self)
        self.close()
        _reposicionar_notificacoes(self.janela)


def mostrar_notificacao(parent, titulo, mensagem="", duracao=3500):
    janela = _janela_alvo(parent)
    if janela is None:
        return

    if not hasattr(janela, "_notificacoes_ativas"):
        janela._notificacoes_ativas = []

    notificacao = NotificacaoToast(janela, titulo, mensagem, duracao)
    janela._notificacoes_ativas.append(notificacao)
    notificacao.show()
    notificacao.raise_()
    _reposicionar_notificacoes(janela)
