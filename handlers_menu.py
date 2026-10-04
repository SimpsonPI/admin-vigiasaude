# handlers_menu.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from helpers import eh_admin, responder

logger = logging.getLogger(__name__)


async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Relatórios", callback_data="menu_relatorios"),
            InlineKeyboardButton("👥 Usuários", callback_data="menu_usuarios"),
        ],
        [
            InlineKeyboardButton("👑 Planos", callback_data="menu_planos"),
            InlineKeyboardButton("🛡️ Segurança", callback_data="menu_seguranca"),
        ],
        [
            InlineKeyboardButton("🤖 VS Admin (IA)", callback_data="menu_vs_admin"),
            InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda"),
        ],
    ])

    texto = (
        "🎛️ <b>PAINEL ADMIN — VigiaSaúde</b>\n\n"
        f"🆔 <b>Seu ID:</b> <code>{update.effective_user.id}</code>\n\n"
        "Escolha uma categoria abaixo ou digite sua pergunta para o VS Admin:"
    )
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=teclado)


async def callback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler unificado de todos os callbacks dos menus."""
    query = update.callback_query
    await query.answer()

    if not eh_admin(query.from_user.id):
        await query.edit_message_text("⛔ Acesso negado.")
        return

    data = query.data

    # Imports locais para evitar circular
    from handlers_relatorios import (
        comando_stats, comando_assinaturas, comando_ativos,
        comando_pagamentos, comando_chamados,
    )
    from handlers_usuarios import (
        comando_top10, _top_regulacoes, _top_pagadores, _top_procedimentos,
    )

    # ─── MENUS ───
    if data == "menu_relatorios":
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Estatísticas", callback_data="rel_stats"),
                InlineKeyboardButton("📈 Assinaturas pagas", callback_data="rel_assinaturas"),
            ],
            [
                InlineKeyboardButton("✅ Ativos", callback_data="rel_ativos"),
                InlineKeyboardButton("💳 Pagamentos", callback_data="rel_pagamentos"),
            ],
            [InlineKeyboardButton("📞 Chamados", callback_data="rel_chamados")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu_home")],
        ])
        await query.edit_message_text("📊 <b>RELATÓRIOS</b>\n\nEscolha o relatório:", parse_mode="HTML", reply_markup=teclado)

    elif data == "menu_usuarios":
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 Buscar por ID", callback_data="usr_buscar_id"),
                InlineKeyboardButton("🔎 Buscar termo", callback_data="usr_buscar_termo"),
            ],
            [
                InlineKeyboardButton("📜 Histórico", callback_data="usr_historico"),
                InlineKeyboardButton("🏆 Top 10", callback_data="usr_top10"),
            ],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu_home")],
        ])
        await query.edit_message_text("👥 <b>USUÁRIOS</b>\n\nO que deseja fazer?", parse_mode="HTML", reply_markup=teclado)

    elif data == "menu_planos":
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⭐ Dar Plano", callback_data="pln_dar"),
                InlineKeyboardButton("👑 Cortesia VIP", callback_data="pln_cortesia"),
            ],
            [
                InlineKeyboardButton("❌ Remover Cortesia", callback_data="pln_rem_cortesia"),
                InlineKeyboardButton("🚫 Retirar Plano", callback_data="pln_retirar"),
            ],
            [InlineKeyboardButton("🎁 Retirar Degustação", callback_data="pln_ret_degust")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu_home")],
        ])
        await query.edit_message_text("👑 <b>GESTÃO DE PLANOS</b>\n\nEscolha uma ação:", parse_mode="HTML", reply_markup=teclado)

    elif data == "menu_seguranca":
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔴 Bloquear", callback_data="seg_bloquear"),
                InlineKeyboardButton("🟢 Desbloquear", callback_data="seg_desbloquear"),
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="seg_broadcast"),
                InlineKeyboardButton("📤 Enviar Mídia", callback_data="seg_midia"),
            ],
            [InlineKeyboardButton("📊 Enviar Enquete", callback_data="seg_enquete")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu_home")],
        ])
        await query.edit_message_text("🛡️ <b>SEGURANÇA E COMUNICAÇÃO</b>\n\nEscolha uma ação:", parse_mode="HTML", reply_markup=teclado)

    elif data == "menu_vs_admin":
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Fazer Pergunta", callback_data="vs_pergunta")],
            [
                InlineKeyboardButton("📊 Resumo Geral", callback_data="vs_resumo"),
                InlineKeyboardButton("💰 Faturamento", callback_data="vs_faturamento"),
            ],
            [
                InlineKeyboardButton("🆕 Novos Hoje", callback_data="vs_novos"),
                InlineKeyboardButton("📞 Chamados", callback_data="vs_chamados"),
            ],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="menu_home")],
        ])
        await query.edit_message_text("🤖 <b>VS ADMIN — Assistente IA</b>\n\nEscolha um atalho ou digite sua pergunta:", parse_mode="HTML", reply_markup=teclado)

    elif data == "menu_home":
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Relatórios", callback_data="menu_relatorios"),
                InlineKeyboardButton("👥 Usuários", callback_data="menu_usuarios"),
            ],
            [
                InlineKeyboardButton("👑 Planos", callback_data="menu_planos"),
                InlineKeyboardButton("🛡️ Segurança", callback_data="menu_seguranca"),
            ],
            [
                InlineKeyboardButton("🤖 VS Admin (IA)", callback_data="menu_vs_admin"),
                InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda"),
            ],
        ])
        await query.edit_message_text("🎛️ <b>PAINEL ADMIN — VigiaSaúde</b>\n\nEscolha uma categoria:", parse_mode="HTML", reply_markup=teclado)

    # ─── AÇÕES: RELATÓRIOS ───
    elif data == "rel_stats":
        await comando_stats(update, context)
    elif data == "rel_assinaturas":
        await comando_assinaturas(update, context)
    elif data == "rel_ativos":
        await comando_ativos(update, context)
    elif data == "rel_pagamentos":
        await comando_pagamentos(update, context)
    elif data == "rel_chamados":
        await comando_chamados(update, context)

    # ─── AÇÕES: USUÁRIOS ───
    elif data == "usr_buscar_id":
        await query.edit_message_text(
            "🔍 <b>Buscar por ID</b>\n\nEnvie:\n<code>/user &lt;ID&gt;</code>\n\n<i>Exemplo:</i> <code>/user 5444152614</code>",
            parse_mode="HTML",
        )
    elif data == "usr_buscar_termo":
        await query.edit_message_text(
            "🔎 <b>Buscar por termo</b>\n\nEnvie:\n<code>/buscar &lt;termo&gt;</code>",
            parse_mode="HTML",
        )
    elif data == "usr_historico":
        await query.edit_message_text(
            "📜 <b>Histórico</b>\n\nEnvie:\n<code>/historico &lt;ID&gt;</code>",
            parse_mode="HTML",
        )
    elif data == "usr_top10":
        await comando_top10(update, context)

    # ─── AÇÕES: PLANOS ───
    elif data == "pln_dar":
        await query.edit_message_text(
            "⭐ <b>Dar Plano</b>\n\nEnvie:\n<code>/plano &lt;ID&gt; &lt;tipo&gt; &lt;dias&gt;</code>",
            parse_mode="HTML",
        )
    elif data == "pln_cortesia":
        await query.edit_message_text("👑 <b>Cortesia VIP</b>\n\nEnvie:\n<code>/cortesia &lt;ID&gt;</code>", parse_mode="HTML")
    elif data == "pln_rem_cortesia":
        await query.edit_message_text("❌ <b>Remover Cortesia</b>\n\nEnvie:\n<code>/remover_cortesia &lt;ID&gt;</code>", parse_mode="HTML")
    elif data == "pln_retirar":
        await query.edit_message_text("🚫 <b>Retirar Plano</b>\n\nEnvie:\n<code>/retirar_plano &lt;ID&gt;</code>", parse_mode="HTML")
    elif data == "pln_ret_degust":
        await query.edit_message_text("🎁 <b>Retirar Degustação</b>\n\nEnvie:\n<code>/retirar_degustacao &lt;ID&gt;</code>", parse_mode="HTML")

    # ─── AÇÕES: SEGURANÇA ───
    elif data == "seg_bloquear":
        await query.edit_message_text("🔴 <b>Bloquear</b>\n\nEnvie:\n<code>/bloquear &lt;ID&gt;</code>", parse_mode="HTML")
    elif data == "seg_desbloquear":
        await query.edit_message_text("🟢 <b>Desbloquear</b>\n\nEnvie:\n<code>/desbloquear &lt;ID&gt;</code>", parse_mode="HTML")
    elif data == "seg_broadcast":
        await query.edit_message_text("📢 <b>Broadcast</b>\n\nEnvie:\n<code>/aviso &lt;mensagem&gt;</code>", parse_mode="HTML")
    elif data == "seg_midia":
        await query.edit_message_text("📤 <b>Enviar Mídia</b>\n\nResponda uma foto com:\n<code>/enviar_midia todos</code>", parse_mode="HTML")
    elif data == "seg_enquete":
        await query.edit_message_text("📊 <b>Enviar Enquete</b>\n\n<code>/enviar_enquete todos | Pergunta | Op1 | Op2</code>", parse_mode="HTML")

        # ─── AÇÕES: VS ADMIN ───
    elif data == "vs_pergunta":
        await query.edit_message_text(
            "💬 <b>VS Admin — Pergunte qualquer coisa</b>\n\nDigite sua pergunta direto no chat.",
            parse_mode="HTML",
        )

    elif data == "vs_resumo":
        from handlers_relatorios import comando_resumo
        await comando_resumo(update, context)
        return

    elif data == "vs_faturamento":
        await query.edit_message_text("💰 Consultando...", parse_mode="HTML")
        from ia_admin import processar_consulta_admin
        from handlers_vs_admin import _limpar_html_ia
        resposta = await processar_consulta_admin("Qual o faturamento total e do mês atual?")
        resposta_limpa = _limpar_html_ia(resposta)
        try:
            await query.edit_message_text(resposta_limpa, parse_mode="HTML")
        except Exception:
            await query.edit_message_text(resposta_limpa)

    elif data == "vs_novos":
        await query.edit_message_text("🆕 Consultando...", parse_mode="HTML")
        from ia_admin import processar_consulta_admin
        from handlers_vs_admin import _limpar_html_ia
        resposta = await processar_consulta_admin("Quantos usuários novos se cadastraram hoje?")
        resposta_limpa = _limpar_html_ia(resposta)
        try:
            await query.edit_message_text(resposta_limpa, parse_mode="HTML")
        except Exception:
            await query.edit_message_text(resposta_limpa)

    elif data == "vs_chamados":
        await query.edit_message_text("📞 Consultando...", parse_mode="HTML")
        from ia_admin import processar_consulta_admin
        from handlers_vs_admin import _limpar_html_ia
        resposta = await processar_consulta_admin("Há chamados pendentes? Quantos?")
        resposta_limpa = _limpar_html_ia(resposta)
        try:
            await query.edit_message_text(resposta_limpa, parse_mode="HTML")
        except Exception:
            await query.edit_message_text(resposta_limpa)

    # ─── TOP 10 ───
    elif data == "top_regs":
        await _top_regulacoes(update)
    elif data == "top_pagadores":
        await _top_pagadores(update)
    elif data == "top_procedimentos":
        await _top_procedimentos(update)

    # ─── AJUDA ───
    elif data == "menu_ajuda":
        texto = (
            "❓ <b>AJUDA — Comandos disponíveis</b>\n\n"
            "📊 <b>Relatórios:</b>\n"
            "• /stats • /assinaturas • /ativos\n"
            "• /pagamentos • /chamados\n\n"
            "👥 <b>Usuários:</b>\n"
            "• /user &lt;id&gt; • /historico &lt;id&gt;\n"
            "• /buscar &lt;termo&gt; • /top10\n\n"
            "👑 <b>Planos:</b>\n"
            "• /plano • /cortesia • /remover_cortesia\n"
            "• /retirar_plano • /retirar_degustacao\n\n"
            "🛡️ <b>Segurança:</b>\n"
            "• /bloquear • /desbloquear • /aviso\n"
            "• /enviar_midia • /enviar_enquete\n\n"
            "🤖 <b>VS Admin (IA):</b>\n"
            "Digite qualquer pergunta direto no chat!"
        )
        teclado = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data="menu_home")]])
        await query.edit_message_text(texto, parse_mode="HTML", reply_markup=teclado)