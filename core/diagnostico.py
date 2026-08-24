"""Registro de erros do GerProce.

Grava em um arquivo de log tanto as excecoes do Python quanto os travamentos
de baixo nivel (segfault), que no executavel sem console sumiriam sem deixar
rastro. O objetivo e que um fechamento inesperado deixe evidencia do que houve.
"""

import faulthandler
import os
import sys
import traceback
from datetime import datetime

NOME_LOG = "gerproce_erros.log"
_arquivo_faulthandler = None


def pasta_do_app():
    """Pasta onde o app roda: ao lado do .exe ou da pasta do projeto."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def caminho_log():
    return os.path.join(pasta_do_app(), NOME_LOG)


def registrar(titulo, detalhe=""):
    """Escreve uma entrada no log, sem nunca derrubar o app por causa disso."""
    try:
        with open(caminho_log(), "a", encoding="utf-8") as log:
            log.write(f"\n{'=' * 70}\n")
            log.write(f"{datetime.now():%d/%m/%Y %H:%M:%S} | {titulo}\n")
            if detalhe:
                log.write(detalhe.rstrip() + "\n")
    except Exception:
        pass


def _tratar_excecao(tipo, valor, tb):
    registrar("Exceção não tratada", "".join(traceback.format_exception(tipo, valor, tb)))
    sys.__excepthook__(tipo, valor, tb)


def ativar():
    """Liga o registro de erros. Chamar uma vez, no inicio do app."""
    global _arquivo_faulthandler

    try:
        _arquivo_faulthandler = open(caminho_log(), "a", encoding="utf-8", buffering=1)
        # Mantido aberto durante toda a execucao: e para onde o faulthandler
        # despeja a pilha em C caso o processo morra de verdade.
        faulthandler.enable(file=_arquivo_faulthandler, all_threads=True)
    except Exception:
        pass

    sys.excepthook = _tratar_excecao
    registrar("Aplicação iniciada", f"pasta: {pasta_do_app()}")


def registrar_encerramento(codigo):
    registrar("Aplicação encerrada", f"codigo de saida: {codigo}")
