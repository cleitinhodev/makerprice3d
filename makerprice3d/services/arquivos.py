# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Abrir e salvar projetos com segurança.

* Formato ``.mp3d`` (JSON com ``schema_version``).
* Abre ``.json`` da v1.x e migra automaticamente.
* Salvamento atômico (arquivo temporário + ``os.replace``) com backup ``.bak``
  da versão anterior.
* Autosave/recuperação em caso de fechamento inesperado.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from makerprice3d.core.projeto import Projeto, ProjetoInvalidoError, migrar, preparar_para_salvar

EXTENSAO = ".mp3d"
EXTENSAO_LEGADA = ".json"
EXTENSAO_BACKUP = ".bak"
EXTENSAO_AUTOSAVE = ".autosave"


@dataclass
class ProjetoCarregado:
    """Projeto aberto do disco."""

    projeto: Projeto
    caminho: Path
    migrado: bool

    @property
    def sugerir_salvar_como(self) -> bool:
        """Arquivos antigos (``.json``) devem ser salvos como ``.mp3d``."""
        return self.migrado or self.caminho.suffix.lower() != EXTENSAO


def abrir_projeto(caminho: str | os.PathLike[str]) -> ProjetoCarregado:
    """Lê um ``.mp3d`` ou ``.json`` (v1.x) e devolve o projeto já migrado.

    :raises ProjetoInvalidoError: arquivo corrompido ou que não é um projeto.
    :raises OSError: problema de leitura.
    """
    caminho = Path(caminho)
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ProjetoInvalidoError(f"O arquivo não é um JSON válido: {erro.msg} (linha {erro.lineno}).") from erro
    projeto, migrado = migrar(dados)
    return ProjetoCarregado(projeto=projeto, caminho=caminho, migrado=migrado)


def escrever_json_atomico(caminho: str | os.PathLike[str], dados: Any, fazer_backup: bool = True) -> Path:
    """Escreve JSON de forma atômica.

    Grava em um temporário na mesma pasta, faz ``fsync`` e troca com ``os.replace``.
    Se o arquivo já existia e ``fazer_backup`` for verdadeiro, a versão anterior é
    copiada para ``<arquivo>.bak`` antes da troca.
    """
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    descritor, temporario = tempfile.mkstemp(prefix=f".{destino.name}.", suffix=".tmp", dir=destino.parent)
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=4, ensure_ascii=False)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        if fazer_backup and destino.exists():
            shutil.copy2(destino, destino.with_name(destino.name + EXTENSAO_BACKUP))
        os.replace(temporario, destino)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporario)
        raise
    return destino


def salvar_projeto(projeto: Projeto, caminho: str | os.PathLike[str]) -> Path:
    """Salva o projeto no formato atual (atômico + backup)."""
    destino = Path(caminho)
    if destino.suffix.lower() != EXTENSAO:
        destino = destino.with_suffix(EXTENSAO)
    return escrever_json_atomico(destino, preparar_para_salvar(projeto))


class Autosave:
    """Salvamento automático para recuperar trabalho após um fechamento inesperado.

    Cada sessão grava em ``<pasta>/<id>.mp3d.autosave`` um envelope com o projeto e o
    caminho original. Ao fechar normalmente (ou salvar), o arquivo é apagado.
    """

    def __init__(self, pasta: str | os.PathLike[str]) -> None:
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.id_sessao = uuid.uuid4().hex
        self.caminho = self.pasta / f"{self.id_sessao}{EXTENSAO}{EXTENSAO_AUTOSAVE}"

    def gravar(self, projeto: Projeto, caminho_original: str | os.PathLike[str] | None) -> Path:
        """Grava o estado atual (sem backup)."""
        envelope = {
            "caminho_original": str(caminho_original) if caminho_original else None,
            "projeto": preparar_para_salvar(projeto),
        }
        return escrever_json_atomico(self.caminho, envelope, fazer_backup=False)

    def limpar(self) -> None:
        """Remove o autosave desta sessão."""
        with contextlib.suppress(FileNotFoundError):
            self.caminho.unlink()

    def pendentes(self) -> list[Path]:
        """Autosaves de sessões anteriores que não foram encerradas corretamente."""
        return sorted(
            (p for p in self.pasta.glob(f"*{EXTENSAO_AUTOSAVE}") if p != self.caminho),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    @staticmethod
    def ler(caminho: str | os.PathLike[str]) -> tuple[Projeto, str | None]:
        """Lê um autosave: ``(projeto, caminho_original)``."""
        with Path(caminho).open("r", encoding="utf-8") as arquivo:
            envelope = json.load(arquivo)
        if not isinstance(envelope, dict) or "projeto" not in envelope:
            raise ProjetoInvalidoError("Autosave inválido.")
        projeto, _ = migrar(envelope["projeto"])
        return projeto, envelope.get("caminho_original")

    @staticmethod
    def descartar(caminho: str | os.PathLike[str]) -> None:
        """Apaga um autosave antigo."""
        with contextlib.suppress(FileNotFoundError):
            Path(caminho).unlink()
