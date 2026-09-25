# admin_bot.py
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import TELEGRAM_ADMIN_TOKEN
from helpers import eh_admin
from notifications import verificar_novidades, inicializar_state

# Handlers
from handlers_menu import comando_start, callback_menu
from handlers_relatorios import (
    comando_stats, comando_assinaturas, comando_ativos,
    comando_pagamentos, comando_chamados, comando_regulacao,
)
from handlers_usuarios import (
    comando_user, comando_buscar, comando_historico, comando_top10,
)
from handlers_planos import (
    comando_plano, comando_cortesia, comando_remover_cortesia,
    comando_retirar_plano, comando_retirar_degustacao,
    comando_bloquear, comando_desbloquear, comando_aviso,
)
from handlers_comunicacao import (
    comando_enviar_midia, processar_envio_midia,
    comando_enviar_enquete, processar_envio_enquete,
)
from handlers_vs_admin import comando_vs, comando_vs_off, mensagem_vs_admin

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def erro_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exceção capturada:", exc_info=context.error)


def main():
    app = ApplicationBuilder().token(TELEGRAM_ADMIN_TOKEN).build()
    app.add_error_handler(erro_handler)

    # ─── Comandos principais ───
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("menu", comando_start))
    app.add_handler(CommandHandler("stats", comando_stats))
    app.add_handler(CommandHandler("estatisticas", comando_stats))
    app.add_handler(CommandHandler("user", comando_user))
    app.add_handler(CommandHandler("detalhes", comando_user))
    app.add_handler(CommandHandler("buscar", comando_buscar))
    app.add_handler(CommandHandler("pagamentos", comando_pagamentos))
    app.add_handler(CommandHandler("chamados", comando_chamados))
    app.add_handler(CommandHandler("regulacao", comando_regulacao))
    app.add_handler(CommandHandler("historico", comando_historico))
    app.add_handler(CommandHandler("top10", comando_top10))
    app.add_handler(CommandHandler("assinaturas", comando_assinaturas))
    app.add_handler(CommandHandler("ativos", comando_ativos))

    # ─── Ações administrativas ───
    app.add_handler(CommandHandler("plano", comando_plano))
    app.add_handler(CommandHandler("dar_plano", comando_plano))
    app.add_handler(CommandHandler("cortesia", comando_cortesia))
    app.add_handler(CommandHandler("remover_cortesia", comando_remover_cortesia))
    app.add_handler(CommandHandler("retirar_plano", comando_retirar_plano))
    app.add_handler(CommandHandler("retirar_degustacao", comando_retirar_degustacao))
    app.add_handler(CommandHandler("bloquear", comando_bloquear))
    app.add_handler(CommandHandler("desbloquear", comando_desbloquear))
    app.add_handler(CommandHandler("aviso", comando_aviso))

    # ─── Mídia e Enquete ───
    app.add_handler(CommandHandler("enviar_midia", processar_envio_midia))
    app.add_handler(CommandHandler("enviar_imagem", processar_envio_midia))
    app.add_handler(CommandHandler("enviar_documento", processar_envio_midia))
    app.add_handler(CommandHandler("enviar_enquete", processar_envio_enquete))

    # ─── VS Admin ───
    app.add_handler(CommandHandler("vs", comando_vs))
    app.add_handler(CommandHandler("vs_off", comando_vs_off))

    # ─── Callbacks dos menus ───
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^rel_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^usr_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^pln_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^seg_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^vs_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^top_"))

    # ─── Notificações automáticas ───
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_once(inicializar_state, when=5)
        job_queue.run_repeating(verificar_novidades, interval=30, first=15)
        logger.info("✅ Notificações automáticas ativadas (a cada 30s)")

    # ─── Fallback — qualquer mensagem vai pro VS Admin ───
    async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not eh_admin(update.effective_user.id):
            return
        try:
            await mensagem_vs_admin(update, context)
        except Exception as e:
            logger.error(f"Erro no VS Admin: {e}")
            await update.message.reply_text(
                "❌ Erro ao processar. Use /start para o menu ou tente novamente."
            )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    logger.info("🎛️ Admin Bot iniciado!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()