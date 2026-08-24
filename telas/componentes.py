"""Componentes de interface reutilizados pelas telas."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QEvent

from core import tema


class AvisoTabelaVazia(QWidget):
    """Mensagem centralizada exibida sobre uma tabela quando ela nao tem linhas.

    Fica sobreposta ao viewport da tabela, entao nao interfere no layout da tela.
    Chame `atualizar()` depois de recarregar os dados.
    """

    def __init__(self, tabela, titulo, descricao=""):
        super().__init__(tabela.viewport())
        self.tabela = tabela
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setStyleSheet(
            f"color: {tema.TEXTO_SECUNDARIO}; font-size: 15px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(self.lbl_titulo)

        self.lbl_descricao = QLabel(descricao)
        self.lbl_descricao.setAlignment(Qt.AlignCenter)
        self.lbl_descricao.setWordWrap(True)
        self.lbl_descricao.setStyleSheet(
            f"color: {tema.TEXTO_TERCIARIO}; font-size: 13px; background: transparent;"
        )
        self.lbl_descricao.setVisible(bool(descricao))
        layout.addWidget(self.lbl_descricao)

        tabela.viewport().installEventFilter(self)
        self.atualizar()

    def definir_texto(self, titulo, descricao=""):
        self.lbl_titulo.setText(titulo)
        self.lbl_descricao.setText(descricao)
        self.lbl_descricao.setVisible(bool(descricao))

    def eventFilter(self, observado, evento):
        if evento.type() == QEvent.Resize:
            self.reposicionar()
        return super().eventFilter(observado, evento)

    def reposicionar(self):
        self.setGeometry(self.tabela.viewport().rect())

    def atualizar(self):
        self.reposicionar()
        self.setVisible(self.tabela.rowCount() == 0)
        if self.isVisible():
            self.raise_()


class Cartao(QFrame):
    """Bloco de conteudo com fundo e cantos arredondados."""

    def __init__(self, parent=None, fundo=tema.SUPERFICIE, raio=tema.RAIO_CARD):
        super().__init__(parent)
        self.setStyleSheet(tema.estilo_card(fundo, raio))


class CabecalhoTela(QWidget):
    """Titulo (e subtitulo opcional) padrao no topo de cada tela."""

    def __init__(self, titulo, subtitulo="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet(tema.estilo_titulo_tela())
        layout.addWidget(self.lbl_titulo)

        self.lbl_subtitulo = QLabel(subtitulo)
        self.lbl_subtitulo.setStyleSheet(
            f"color: {tema.TEXTO_TERCIARIO}; font-size: 13px; background: transparent;"
        )
        self.lbl_subtitulo.setVisible(bool(subtitulo))
        layout.addWidget(self.lbl_subtitulo)

    def definir_subtitulo(self, texto):
        self.lbl_subtitulo.setText(texto)
        self.lbl_subtitulo.setVisible(bool(texto))
