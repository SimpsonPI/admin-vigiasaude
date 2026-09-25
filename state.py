# state.py
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).resolve().parent / "admin_state.json"


def carregar_state() -> dict:
    """Carrega o estado do arquivo JSON."""
    if not STATE_FILE.exists():
        return {"ultimo_chat_id": 0, "ultimo_pagamento_id": 0, "ultimo_chamado_id": 0}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ultimo_chat_id": 0, "ultimo_pagamento_id": 0, "ultimo_chamado_id": 0}


def salvar_state(state: dict):
    """Salva o estado no arquivo JSON."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar state: {e}")