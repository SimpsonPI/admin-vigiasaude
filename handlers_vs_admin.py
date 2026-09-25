# handlers_vs_admin.py
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from helpers import eh_admin, responder

logger = logging.getLogger(__name__)


def _limpar_html_ia(texto: str) -> str:
    """Remove tags HTML que o Telegram não aceita."""
    import re
    # Remove tags proibidas (preserva o conteúdo)
    texto = re.sub(r"</?(?:ul|ol|li|p|br|div|h[1-6]|table|tr|td|th|span|font|section|article)\b[^>]*>", "", texto, flags=re.IGNORECASE)
    # Converte <br> e <br/> em quebra de linha
    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    return texto

async def comando_vs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ativa o VS Admin e responde perguntas em linguagem natural."""
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if context.args:
        pergunta = " ".join(context.args)
        await responder(update, "🤖 Analisando...")

        from ia_admin import processar_consulta_admin
        resposta = await processar_consulta_admin(pergunta)

        context.user_data["vs_admin_ativo"] = True
        await responder(update, resposta + "\n\n<i>💬 Modo VS Admin ativo. Faça mais perguntas ou /vs_off para sair.</i>")
        return

    context.user_data["vs_admin_ativo"] = True
    texto = (
        "🤖 <b>VS Admin ativado!</b>\n\n"
        "Sou seu assistente executivo. Pergunte qualquer coisa sobre o sistema:\n\n"
        "• <i>Quantos usuários ativos temos?</i>\n"
        "• <i>Qual o faturamento deste mês?</i>\n"
        "• <i>Mostre os últimos pagamentos</i>\n"
        "• <i>Quem são os top 5 usuários?</i>\n"
        "• <i>Há chamados pendentes?</i>\n"
        "• <i>Como está o usuário 5444152614?</i>\n\n"
        "💬 Modo ativo. Envie /vs_off para desativar."
    )
    await responder(update, texto)


async def comando_vs_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    context.user_data.pop("vs_admin_ativo", None)
    await responder(update, "🔕 <b>VS Admin desativado.</b>\n\nUse /vs para reativar.")


async def mensagem_vs_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa qualquer mensagem do admin via VS Admin (sempre ativo)."""
    if not eh_admin(update.effective_user.id):
        return

    if not update.message or not update.message.text:
        return

    mensagem = update.message.text.strip()

    # Ignora comandos (já tratados em outros handlers)
    if mensagem.startswith("/"):
        return

    # Detecta se é pergunta sobre usuário específico
    match = re.search(r'\b(?:usu[aá]rio|user|id|cliente)\s+(\d{7,})', mensagem, re.IGNORECASE)

    try:
        if match:
            chat_id = match.group(1)
            from ia_admin import processar_consulta_usuario
            resposta = await processar_consulta_usuario(chat_id, mensagem)
        else:
            from ia_admin import processar_consulta_admin
            resposta = await processar_consulta_admin(mensagem)

            resposta_limpa = _limpar_html_ia(resposta)
        try:
            await update.message.reply_text(resposta_limpa, parse_mode="HTML")
        except Exception:
            # Fallback: envia sem parse_mode
            await update.message.reply_text(resposta_limpa)
            
    except Exception as e:
        logger.error(f"Erro no VS Admin: {e}")
        await update.message.reply_text(f"❌ Erro: {e}")