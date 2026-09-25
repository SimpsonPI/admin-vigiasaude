# notifications.py
import logging
from telegram.ext import ContextTypes
from config import supabase, ADMIN_ID
from helpers import fmt_data, fmt_moeda, emoji_status_plano
from state import carregar_state, salvar_state

logger = logging.getLogger(__name__)


async def verificar_novidades(context: ContextTypes.DEFAULT_TYPE):
    """Job que roda a cada 30s verificando novidades no banco."""
    state = carregar_state()
    alterou = False

    # ─── 1. Novos usuários ───
    try:
        res = (
            supabase.table("assinaturas")
            .select("id, chat_id, tipo_plano, status, created_at")
            .gt("id", state["ultimo_chat_id"])
            .order("id", desc=False)
            .execute()
        )
        for u in (res.data or []):
            uid = u.get("id", 0)
            if uid > state["ultimo_chat_id"]:
                state["ultimo_chat_id"] = uid
                alterou = True
                texto = (
                    "🆕 <b>NOVO USUÁRIO CADASTRADO</b>\n\n"
                    f"🆔 <b>ID:</b> <code>{u.get('chat_id')}</code>\n"
                    f"👑 <b>Plano inicial:</b> {u.get('tipo_plano') or '—'}\n"
                    f"📊 <b>Status:</b> {emoji_status_plano(u.get('status'))}\n"
                    f"📅 {fmt_data(u.get('created_at'))}\n\n"
                    f"👉 <code>/user {u.get('chat_id')}</code>"
                )
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=texto, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Erro ao notificar novo usuário: {e}")
    except Exception as e:
        logger.error(f"Erro ao checar novos usuários: {e}")

    # ─── 2. Novos pagamentos ───
    try:
        res = (
            supabase.table("pagamentos_pix")
            .select("id, chat_id, valor, tipo_plano, status, created_at")
            .gt("id", state["ultimo_pagamento_id"])
            .order("id", desc=False)
            .execute()
        )
        for p in (res.data or []):
            pid = p.get("id", 0)
            if pid > state["ultimo_pagamento_id"]:
                state["ultimo_pagamento_id"] = pid
                alterou = True
                status = str(p.get("status", "")).lower()
                emoji = "✅" if status in ("approved", "aprovado") else "⏳" if status in ("pending", "pendente") else "❌"
                texto = (
                    f"{emoji} <b>PAGAMENTO {'APROVADO' if status == 'approved' else 'RECEBIDO'}</b>\n\n"
                    f"💰 <b>Valor:</b> {fmt_moeda(p.get('valor'))}\n"
                    f"📦 <b>Plano:</b> {p.get('tipo_plano')}\n"
                    f"🆔 <b>Usuário:</b> <code>{p.get('chat_id')}</code>\n"
                    f"📅 {fmt_data(p.get('created_at'))}\n\n"
                    f"👉 <code>/user {p.get('chat_id')}</code>"
                )
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=texto, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Erro ao notificar pagamento: {e}")
    except Exception as e:
        logger.error(f"Erro ao checar novos pagamentos: {e}")

    # ─── 3. Novos chamados ───
    try:
        res = (
            supabase.table("chamados_suporte")
            .select("id, chat_id, nome_usuario, mensagem, status, created_at")
            .gt("id", state["ultimo_chamado_id"])
            .order("id", desc=False)
            .execute()
        )
        for c in (res.data or []):
            cid = c.get("id", 0)
            if cid > state["ultimo_chamado_id"]:
                state["ultimo_chamado_id"] = cid
                alterou = True
                texto = (
                    "📞 <b>NOVO CHAMADO DE SUPORTE</b>\n\n"
                    f"🔔 <b>#{c.get('id')}</b>\n"
                    f"👤 {c.get('nome_usuario', '—')}\n"
                    f"🆔 <code>{c.get('chat_id')}</code>\n"
                    f"📝 {str(c.get('mensagem', ''))[:100]}\n"
                    f"📅 {fmt_data(c.get('created_at'))}\n\n"
                    "👉 <i>Responda pelo bot Central</i>"
                )
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=texto, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Erro ao notificar chamado: {e}")
    except Exception as e:
        logger.error(f"Erro ao checar novos chamados: {e}")

    if alterou:
        salvar_state(state)


async def inicializar_state(context: ContextTypes.DEFAULT_TYPE):
    """Na primeira execução, salva o estado atual para não notificar o histórico."""
    state = carregar_state()

    if state["ultimo_chat_id"] > 0 or state["ultimo_pagamento_id"] > 0 or state["ultimo_chamado_id"] > 0:
        logger.info("State já inicializado. Pulando bootstrap.")
        return

    logger.info("Inicializando state pela primeira vez...")

    try:
        res = supabase.table("assinaturas").select("id").order("id", desc=True).limit(1).execute()
        if res.data:
            state["ultimo_chat_id"] = res.data[0].get("id", 0)
    except Exception:
        pass

    try:
        res = supabase.table("pagamentos_pix").select("id").order("id", desc=True).limit(1).execute()
        if res.data:
            state["ultimo_pagamento_id"] = res.data[0].get("id", 0)
    except Exception:
        pass

    try:
        res = supabase.table("chamados_suporte").select("id").order("id", desc=True).limit(1).execute()
        if res.data:
            state["ultimo_chamado_id"] = res.data[0].get("id", 0)
    except Exception:
        pass

    salvar_state(state)
    logger.info(f"State inicializado: {state}")