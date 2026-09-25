# handlers_comunicacao.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import supabase
from helpers import eh_admin, responder

logger = logging.getLogger(__name__)


async def comando_enviar_midia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    await responder(
        update,
        "📤 <b>Envio de Mídia</b>\n\n"
        "1. Envie uma imagem/documento/vídeo no chat\n"
        "2. Responda essa mensagem com <code>/enviar_midia todos</code> ou <code>/enviar_midia &lt;ID&gt;</code>"
    )


async def processar_envio_midia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not update.message.reply_to_message:
        await responder(update, "⚠️ Responda a uma mensagem com imagem/documento/vídeo para enviar.")
        return

    original = update.message.reply_to_message
    file_id = None
    tipo = None
    caption = original.caption or ""

    if original.photo:
        file_id = original.photo[-1].file_id
        tipo = "photo"
    elif original.document:
        file_id = original.document.file_id
        tipo = "document"
    elif original.video:
        file_id = original.video.file_id
        tipo = "video"
    else:
        await responder(update, "❌ A mensagem original não contém imagem/documento/vídeo.")
        return

    if not context.args:
        await responder(update, "⚠️ Informe o destino: <code>/enviar_midia todos</code> ou <code>/enviar_midia &lt;ID&gt;</code>")
        return

    destino = context.args[0].strip().lower()

    if destino == "todos":
        try:
            res = supabase.table("assinaturas").select("chat_id").execute()
            chat_ids = list(set(str(r.get("chat_id")) for r in (res.data or []) if r.get("chat_id")))
        except Exception as e:
            await responder(update, f"❌ Erro ao buscar usuários: {e}")
            return
    else:
        chat_ids = [destino]

    await responder(update, f"📤 Enviando para <b>{len(chat_ids)}</b> usuário(s)...")

    enviados, falhas = 0, 0
    for cid in chat_ids:
        try:
            if tipo == "photo":
                await context.bot.send_photo(chat_id=cid, photo=file_id, caption=caption or None)
            elif tipo == "document":
                await context.bot.send_document(chat_id=cid, document=file_id, caption=caption or None)
            elif tipo == "video":
                await context.bot.send_video(chat_id=cid, video=file_id, caption=caption or None)
            enviados += 1
        except Exception:
            falhas += 1

    await responder(update, f"✅ <b>Envio concluído</b>\n\n• Enviados: <b>{enviados}</b>\n• Falhas: <b>{falhas}</b>")


async def comando_enviar_enquete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    await responder(
        update,
        "📊 <b>Envio de Enquete</b>\n\n"
        "<code>/enviar_enquete &lt;pergunta&gt; | &lt;opção1&gt; | &lt;opção2&gt; | ...</code>\n\n"
        "<i>Exemplo:</i> <code>/enviar_enquete Gostou do app? | Sim | Não | Talvez</code>"
    )


async def processar_envio_enquete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await comando_enviar_enquete(update, context)
        return

    texto = " ".join(context.args)
    partes = [p.strip() for p in texto.split("|")]

    if len(partes) < 3:
        await responder(update, "⚠️ Formato inválido. Use: <code>/enviar_enquete todos | Pergunta | Op1 | Op2</code>")
        return

    destino = partes[0].lower()
    pergunta = partes[1]
    opcoes = partes[2:]

    if len(opcoes) < 2:
        await responder(update, "❌ Precisa de pelo menos 2 opções.")
        return
    if len(opcoes) > 10:
        await responder(update, "❌ Máximo de 10 opções.")
        return

    if destino == "todos":
        try:
            res = supabase.table("assinaturas").select("chat_id").execute()
            chat_ids = list(set(str(r.get("chat_id")) for r in (res.data or []) if r.get("chat_id")))
        except Exception as e:
            await responder(update, f"❌ Erro: {e}")
            return
    else:
        chat_ids = [destino]

    await responder(update, f"📊 Enviando enquete para <b>{len(chat_ids)}</b> usuário(s)...")

    enviados, falhas = 0, 0
    for cid in chat_ids:
        try:
            await context.bot.send_poll(
                chat_id=cid, question=pergunta, options=opcoes,
                is_anonymous=True, allows_multiple_answers=False,
            )
            enviados += 1
        except Exception:
            falhas += 1

    await responder(update, f"✅ <b>Enquete enviada</b>\n\n• Enviadas: <b>{enviados}</b>\n• Falhas: <b>{falhas}</b>")