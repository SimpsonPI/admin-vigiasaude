# handlers_planos.py
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import supabase
from helpers import eh_admin, responder

logger = logging.getLogger(__name__)


async def comando_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if len(context.args) < 3:
        await responder(
            update,
            "⚠️ <b>Uso:</b> <code>/plano &lt;ID&gt; &lt;tipo&gt; &lt;dias&gt;</code>\n\n"
            "<b>Tipos:</b> trimestral, semestral, pro, cortesia, degustacao\n\n"
            "<i>Exemplo:</i> <code>/plano 5444152614 semestral 180</code>",
        )
        return

    target_id = context.args[0].strip()
    tipo_plano = context.args[1].strip().lower()

    try:
        dias = int(context.args[2])
    except ValueError:
        await responder(update, "❌ O número de dias precisa ser inteiro.")
        return

    agora = datetime.now(timezone.utc)
    vencimento = agora + timedelta(days=dias)

    try:
        supabase.table("assinaturas").upsert({
            "chat_id": target_id,
            "tipo_plano": tipo_plano,
            "status": "ativo",
            "data_inicio": agora.isoformat(),
            "data_vencimento": vencimento.isoformat(),
        }, on_conflict="chat_id").execute()

        await responder(
            update,
            f"✅ <b>Plano concedido!</b>\n\n"
            f"• <b>ID:</b> <code>{target_id}</code>\n"
            f"• <b>Plano:</b> {tipo_plano}\n"
            f"• <b>Validade:</b> {dias} dias (até {vencimento.strftime('%d/%m/%Y')})",
        )
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"🎁 <b>Seu plano foi atualizado!</b>\n\n"
                    f"Plano: <b>{tipo_plano.upper()}</b>\n"
                    f"Válido até: <b>{vencimento.strftime('%d/%m/%Y')}</b>"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Erro em /plano: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_cortesia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/cortesia &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip().strip("<>").strip()  # ← limpa colchetes

    try:
        supabase.table("assinaturas").upsert({
            "chat_id": target_id,
            "tipo_plano": "cortesia",
            "status": "ativo",
            "data_inicio": datetime.now(timezone.utc).isoformat(),
            "data_vencimento": None,
            "limite_ids": 999,            # ← corrigido (era 99)
            "usou_degustacao": False,     # ← NOVO: reseta degustação
        }, on_conflict="chat_id").execute()

        await responder(
            update,
            f"✅ <b>Cortesia aplicada com sucesso!</b>\n\n"
            f"• <b>ID:</b> <code>{target_id}</code>\n"
            f"• <b>Plano:</b> Cortesia VIP 👑\n"
            f"• <b>Limite:</b> Ilimitado\n"
            f"• <b>Vencimento:</b> Sem vencimento"
        )
    except Exception as e:
        logger.error(f"Erro em /cortesia: {e}")
        await responder(update, f"❌ Erro: {e}")

        await responder(update, f"👑 Cortesia concedida para <code>{target_id}</code>.")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    "👑 <b>Você recebeu acesso Cortesia VIP!</b>\n\n"
                    "Sua conta agora tem acesso <b>ilimitado e gratuito</b> ao VigiaSaúde. Aproveite! 🎉"
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Erro em /cortesia: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_remover_cortesia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/remover_cortesia &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        supabase.table("assinaturas").update({
            "tipo_plano": None, "status": None, "data_inicio": None,
            "data_vencimento": None, "limite_ids": None, "usou_degustacao": True,
        }).eq("chat_id", target_id).execute()

        await responder(update, f"✅ Cortesia removida de <code>{target_id}</code>. Usuário agora está neutro.")
    except Exception as e:
        logger.error(f"Erro em /remover_cortesia: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_retirar_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/retirar_plano &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        supabase.table("assinaturas").update({
            "tipo_plano": None, "status": None, "data_inicio": None,
            "data_vencimento": None, "limite_ids": None, "usou_degustacao": True,
        }).eq("chat_id", target_id).execute()

        await responder(update, f"✅ Plano retirado de <code>{target_id}</code>. Usuário agora está neutro.")
    except Exception as e:
        logger.error(f"Erro em /retirar_plano: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_retirar_degustacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/retirar_degustacao &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        supabase.table("assinaturas").update({
            "usou_degustacao": True, "tipo_plano": None, "status": None,
            "data_inicio": None, "data_vencimento": None, "limite_ids": None,
        }).eq("chat_id", target_id).execute()

        await responder(update, f"✅ Degustação retirada de <code>{target_id}</code>. Usuário agora está neutro.")
    except Exception as e:
        logger.error(f"Erro em /retirar_degustacao: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_bloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/bloquear &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        supabase.table("assinaturas").update({"status": "bloqueado"}).eq("chat_id", target_id).execute()
        await responder(update, f"🔴 Usuário <code>{target_id}</code> bloqueado.")
    except Exception as e:
        logger.error(f"Erro em /bloquear: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_desbloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/desbloquear &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        supabase.table("assinaturas").update({"status": "ativo"}).eq("chat_id", target_id).execute()
        await responder(update, f"🟢 Usuário <code>{target_id}</code> desbloqueado.")
    except Exception as e:
        logger.error(f"Erro em /desbloquear: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_aviso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/aviso &lt;mensagem&gt;</code>")
        return

    mensagem = " ".join(context.args)

    try:
        res = supabase.table("assinaturas").select("chat_id").execute()
        chat_ids = list(set(str(r.get("chat_id")) for r in (res.data or []) if r.get("chat_id")))

        if not chat_ids:
            await responder(update, "ℹ️ Nenhum usuário encontrado.")
            return

        enviados, falhas = 0, 0
        detalhes_falha = []

        for cid in chat_ids:
            try:
                await context.bot.send_message(
                    chat_id=cid,
                    text=f"📢 <b>AVISO — VigiaSaúde</b>\n\n{mensagem}",
                    parse_mode="HTML",
                )
                enviados += 1
            except Exception as e:
                falhas += 1
                detalhes_falha.append(f"• <code>{cid}</code>: {type(e).__name__}: {str(e)[:80]}")

        relatorio = (
            f"✅ <b>Broadcast concluído</b>\n\n"
            f"• Enviados: <b>{enviados}</b>\n"
            f"• Falhas: <b>{falhas}</b>"
        )
        if detalhes_falha:
            relatorio += "\n\n<b>Detalhes das falhas:</b>\n" + "\n".join(detalhes_falha)

        await responder(update, relatorio)
    except Exception as e:
        logger.error(f"Erro em /aviso: {e}")
        await responder(update, f"❌ Erro: {e}")