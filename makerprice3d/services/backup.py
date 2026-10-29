# Maker Price 3D
# Copyright (C) 2026 CleitinhoDEV
# Licensed under the GNU GPL v3 or later
# Site Oficial: https://www.bugzinho.com/
# GitHub: https://github.com/cleitinhodev
"""Backup automático do banco e exportação completa dos dados."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

from makerprice3d.services.banco import Banco


def fazer_backup(banco: Banco, pasta: Path, manter: int = 10) -> Path:
    """Copia o banco para ``pasta`` e mantém só os ``manter`` backups mais novos."""
    pasta.mkdir(parents=True, exist_ok=True)
    destino = banco.backup_para(pasta / f"makerprice3d-{datetime.now():%Y%m%d-%H%M%S}.db")
    antigos = sorted(pasta.glob("makerprice3d-*.db"), reverse=True)[max(1, manter) :]
    for arquivo in antigos:
        arquivo.unlink(missing_ok=True)
    return destino


def backup_automatico(banco: Banco, pasta: Path) -> Path | None:
    """Faz no máximo um backup por dia (chamado ao abrir o programa)."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    if banco.config("ultimo_backup") == hoje:
        return None
    try:
        manter = int(banco.config("backups_manter") or 10)
    except ValueError:
        manter = 10
    destino = fazer_backup(banco, pasta, manter)
    banco.definir_config("ultimo_backup", hoje)
    return destino


def exportar_tudo(banco: Banco, destino_zip: Path, pasta_fotos: Path | None = None) -> Path:
    """Gera um ``.zip`` com o banco, um JSON legível de todos os dados e as fotos."""
    destino_zip = Path(destino_zip)
    temporario = destino_zip.with_suffix(".tmp.db")
    banco.backup_para(temporario)
    try:
        with zipfile.ZipFile(destino_zip, "w", compression=zipfile.ZIP_DEFLATED) as zip_:
            zip_.write(temporario, "makerprice3d.db")
            zip_.writestr("dados.json", json.dumps(banco.exportar_tudo(), indent=2, ensure_ascii=False))
            if pasta_fotos and pasta_fotos.exists():
                for foto in pasta_fotos.iterdir():
                    if foto.is_file():
                        zip_.write(foto, f"fotos/{foto.name}")
    finally:
        temporario.unlink(missing_ok=True)
    return destino_zip
