# helpers.py
from datetime import datetime
from telegram import Update
from config import ADMIN_ID


def eh_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def responder(update: Update, texto: str, parse_mode: str = "HTML", reply_markup=None):
    """Envia resposta independente de vir de comando ou callback."""
    if update.callback_query:
        await update.callback_query.message.reply_text(
            texto, parse_mode=parse_mode, reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            texto, parse_mode=parse_mode, reply_markup=reply_markup
        )


def fmt_data(iso_str):
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return str(iso_str)


def fmt_moeda(valor):
    try:
        return f"R$ {float(valor):.2f}".replace(".", ",")
    except Exception:
        return str(valor)


def emoji_status_plano(status: str) -> str:
    s = str(status or "").strip().lower()
    return {
        "ativo": "🟢 Ativo",
        "active": "🟢 Ativo",
        "ativa": "🟢 Ativo",
        "bloqueado": "🔴 Bloqueado",
        "expirado": "🟡 Expirado",
    }.get(s, f"⚪ {s.capitalize() or '—'}")