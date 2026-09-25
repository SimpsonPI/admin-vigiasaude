# handlers_usuarios.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import supabase
from helpers import eh_admin, responder, fmt_data, fmt_moeda, emoji_status_plano

logger = logging.getLogger(__name__)


async def comando_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/user &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        res = supabase.table("assinaturas").select("*").eq("chat_id", target_id).execute()
        dados = res.data or []

        if not dados:
            await responder(update, f"❌ Nenhum registro para ID <code>{target_id}</code>.")
            return

        user = dados[0]
        tipo = str(user.get("tipo_plano") or "—").strip().lower()
        nomes = {
            "trimestral": "Pro Trimestral",
            "semestral": "Pro Semestral",
            "pro": "Pro",
            "degustacao": "Degustação 🎁",
            "cortesia": "Cortesia VIP 👑",
        }
        tipo_fmt = nomes.get(tipo, tipo.capitalize())

        limite = user.get("limite_ids")
        limite_txt = "Ilimitado" if not limite else str(limite)

        texto = (
            f"👤 <b>USUÁRIO</b> <code>{target_id}</code>\n\n"
            f"👑 <b>Plano:</b> {tipo_fmt}\n"
            f"📊 <b>Status:</b> {emoji_status_plano(user.get('status'))}\n"
            f"📅 <b>Início:</b> {fmt_data(user.get('data_inicio'))}\n"
            f"⏰ <b>Vencimento:</b> {fmt_data(user.get('data_vencimento'))}\n\n"
            f"🎁 <b>Já usou degustação:</b> {'✅ Sim' if user.get('usou_degustacao') else '❌ Não'}\n"
            f"📈 <b>Limite IDs:</b> {limite_txt}\n"
            f"🔔 <b>Último aviso:</b> {user.get('ultimo_aviso') or '—'}\n"
            f"💳 <b>ID MP:</b> <code>{user.get('mp_payment_id') or '—'}</code>\n"
        )
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /user: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/buscar &lt;termo&gt;</code>")
        return

    termo = " ".join(context.args).strip()
    termo_lower = termo.lower()

    try:
        resultados = []

        if termo.isdigit():
            res = supabase.table("assinaturas").select("chat_id, tipo_plano, status, data_vencimento").eq("chat_id", termo).execute()
            for r in (res.data or []):
                resultados.append(("assinatura", r))

        res_regs = supabase.table("AlertaSUS_2.0").select("chat_id, numero_reg, nome_paciente, celular, procedimento, status_anterior").execute()
        for r in (res_regs.data or []):
            nome = str(r.get("nome_paciente") or "").lower()
            num_reg = str(r.get("numero_reg") or "").lower()
            cel = str(r.get("celular") or "").lower()
            if termo_lower in nome or termo_lower in num_reg or termo_lower in cel:
                resultados.append(("regulacao", r))

        if not resultados:
            await responder(update, f"❌ Nenhum resultado para: <b>{termo}</b>")
            return

        usuarios = {}
        for tipo, r in resultados:
            cid = str(r.get("chat_id") or "?")
            usuarios.setdefault(cid, {"assinatura": None, "regulacoes": []})
            if tipo == "assinatura":
                usuarios[cid]["assinatura"] = r
            else:
                usuarios[cid]["regulacoes"].append(r)

        texto = f"🔍 <b>Resultados para:</b> {termo}\n"
        texto += f"<i>{len(usuarios)} usuário(s) encontrado(s)</i>\n\n"

        for cid, dados in list(usuarios.items())[:10]:
            a = dados.get("assinatura") or {}
            regs = dados.get("regulacoes") or []
            plano = a.get("tipo_plano") or "—"
            texto += f"🆔 <code>{cid}</code> — <b>{plano}</b>\n"
            if regs:
                for r in regs[:3]:
                    nome = r.get("nome_paciente") or "?"
                    num = r.get("numero_reg") or "?"
                    texto += f"   📋 <code>{num}</code> — {nome}\n"
                if len(regs) > 3:
                    texto += f"   <i>...e mais {len(regs) - 3} regulações</i>\n"
            texto += "\n"

        if len(usuarios) > 10:
            texto += f"\n<i>...e mais {len(usuarios) - 10} usuário(s)</i>"

        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /buscar: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Timeline completa de um usuário."""
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/historico &lt;ID&gt;</code>")
        return

    target_id = context.args[0].strip()

    try:
        res_ass = supabase.table("assinaturas").select("*").eq("chat_id", target_id).execute()
        assinatura = res_ass.data[0] if res_ass.data else None

        res_pag = (
            supabase.table("pagamentos_pix")
            .select("id, valor, tipo_plano, status, created_at")
            .eq("chat_id", target_id)
            .order("created_at", desc=True)
            .execute()
        )
        pagamentos = res_pag.data or []

        res_reg = (
            supabase.table("AlertaSUS_2.0")
            .select("numero_reg, nome_paciente, procedimento, cbo, status_anterior, posicao_anterior, created_at")
            .eq("chat_id", target_id)
            .order("created_at", desc=True)
            .execute()
        )
        regulacoes = res_reg.data or []

        res_ch = (
            supabase.table("chamados_suporte")
            .select("id, mensagem, status, created_at")
            .eq("chat_id", target_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        chamados = res_ch.data or []

        texto = f"📜 <b>HISTÓRICO COMPLETO</b>\n🆔 <code>{target_id}</code>\n\n"

        if assinatura:
            tipo = str(assinatura.get("tipo_plano") or "—").capitalize()
            limite = assinatura.get("limite_ids") or "Ilimitado"
            texto += (
                "━━━ 👑 <b>ASSINATURA ATUAL</b> ━━━\n"
                f"• Plano: <b>{tipo}</b>\n"
                f"• Status: {emoji_status_plano(assinatura.get('status'))}\n"
                f"• Limite: {limite} regulações\n"
                f"• Início: {fmt_data(assinatura.get('data_inicio'))}\n"
                f"• Vence: {fmt_data(assinatura.get('data_vencimento'))}\n"
                f"• Usou degustação: {'✅ Sim' if assinatura.get('usou_degustacao') else '❌ Não'}\n\n"
            )
        else:
            texto += "━━━ 👑 <b>ASSINATURA</b> ━━━\n❌ Nenhuma assinatura encontrada.\n\n"

        if pagamentos:
            total = sum(float(p.get("valor", 0) or 0) for p in pagamentos if str(p.get("status", "")).lower() == "approved")
            texto += f"━━━ 💳 <b>PAGAMENTOS</b> ({len(pagamentos)}) ━━━\n"
            texto += f"💰 <b>Total pago: {fmt_moeda(total)}</b>\n\n"
            for p in pagamentos[:5]:
                status_emoji = "✅" if str(p.get("status", "")).lower() == "approved" else "⏳" if str(p.get("status", "")).lower() == "pending" else "❌"
                texto += (
                    f"{status_emoji} <b>{fmt_moeda(p.get('valor'))}</b> — {p.get('tipo_plano')}\n"
                    f"   📅 {fmt_data(p.get('created_at'))}\n"
                )
            if len(pagamentos) > 5:
                texto += f"\n<i>...e mais {len(pagamentos) - 5} pagamento(s)</i>\n"
            texto += "\n"
        else:
            texto += "━━━ 💳 <b>PAGAMENTOS</b> ━━━\n❌ Nenhum pagamento registrado.\n\n"

        if regulacoes:
            texto += f"━━━ 📋 <b>REGULAÇÕES</b> ({len(regulacoes)}) ━━━\n"
            for r in regulacoes[:5]:
                texto += (
                    f"• <code>{r.get('numero_reg')}</code> — {r.get('nome_paciente', '?')}\n"
                    f"   {r.get('procedimento') or '?'} | {r.get('status_anterior') or 'Sem status'}\n"
                )
            if len(regulacoes) > 5:
                texto += f"<i>...e mais {len(regulacoes) - 5} regulação(ões)</i>\n"
            texto += "\n"
        else:
            texto += "━━━ 📋 <b>REGULAÇÕES</b> ━━━\n❌ Nenhuma regulação cadastrada.\n\n"

        if chamados:
            texto += f"━━━ 📞 <b>ÚLTIMOS CHAMADOS</b> ━━━\n"
            for c in chamados:
                status_emoji = {
                    "aberto": "🟢", "em_andamento": "🟡",
                    "respondido": "🔵", "fechado": "⚫",
                }.get(str(c.get("status", "")).lower(), "⚪")
                texto += (
                    f"{status_emoji} #{c.get('id')} — {str(c.get('mensagem', ''))[:50]}\n"
                    f"   📅 {fmt_data(c.get('created_at'))}\n"
                )
            texto += "\n"

        if len(texto) > 4000:
            texto = texto[:3990] + "\n\n<i>[...]</i>"

        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /historico: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Top 10 rankings."""
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Mais Regulações", callback_data="top_regs")],
            [InlineKeyboardButton("💰 Maiores Pagadores", callback_data="top_pagadores")],
            [InlineKeyboardButton("🏥 Procedimentos", callback_data="top_procedimentos")],
        ])
        await responder(update, "🏆 <b>RANKINGS — TOP 10</b>\n\nEscolha uma categoria:", reply_markup=teclado)
        return

    categoria = context.args[0].strip().lower()
    if categoria in ("regs", "regulacoes"):
        await _top_regulacoes(update)
    elif categoria in ("pagadores", "pagamentos", "pagos"):
        await _top_pagadores(update)
    elif categoria in ("procedimentos", "proced"):
        await _top_procedimentos(update)
    else:
        await responder(update, "❌ Categoria inválida. Use: regs, pagadores ou procedimentos")


async def _top_regulacoes(update: Update):
    try:
        res = supabase.table("AlertaSUS_2.0").select("chat_id, nome_paciente").execute()
        dados = res.data or []
        contagem = {}
        nomes = {}
        for d in dados:
            cid = str(d.get("chat_id") or "?")
            contagem[cid] = contagem.get(cid, 0) + 1
            if d.get("nome_paciente") and cid not in nomes:
                nomes[cid] = d.get("nome_paciente")

        top = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
        texto = "🏆 <b>TOP 10 — MAIS REGULAÇÕES</b>\n\n"
        for i, (cid, qtd) in enumerate(top, 1):
            medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
            nome = nomes.get(cid, "—")
            texto += f"{medalha} {nome}\n    🆔 <code>{cid}</code> — <b>{qtd}</b> regulação(ões)\n\n"
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em _top_regulacoes: {e}")
        await responder(update, f"❌ Erro: {e}")


async def _top_pagadores(update: Update):
    try:
        res = supabase.table("pagamentos_pix").select("chat_id, valor, status").execute()
        dados = res.data or []
        total = {}
        qtd = {}
        for d in dados:
            if str(d.get("status", "")).lower() != "approved":
                continue
            cid = str(d.get("chat_id") or "?")
            total[cid] = total.get(cid, 0) + float(d.get("valor", 0) or 0)
            qtd[cid] = qtd.get(cid, 0) + 1

        top = sorted(total.items(), key=lambda x: x[1], reverse=True)[:10]

        res_nomes = supabase.table("AlertaSUS_2.0").select("chat_id, nome_paciente").execute()
        nomes = {}
        for r in (res_nomes.data or []):
            cid = str(r.get("chat_id"))
            if cid and r.get("nome_paciente") and cid not in nomes:
                nomes[cid] = r.get("nome_paciente")

        texto = "🏆 <b>TOP 10 — MAIORES PAGADORES</b>\n\n"
        for i, (cid, valor) in enumerate(top, 1):
            medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
            nome = nomes.get(cid, "—")
            texto += (
                f"{medalha} {nome}\n"
                f"    🆔 <code>{cid}</code>\n"
                f"    💰 <b>{fmt_moeda(valor)}</b> ({qtd.get(cid, 0)} pagamento(s))\n\n"
            )
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em _top_pagadores: {e}")
        await responder(update, f"❌ Erro: {e}")


async def _top_procedimentos(update: Update):
    try:
        res = supabase.table("AlertaSUS_2.0").select("procedimento").execute()
        dados = res.data or []
        contagem = {}
        for d in dados:
            proc = str(d.get("procedimento") or "—").strip().upper()
            contagem[proc] = contagem.get(proc, 0) + 1

        top = sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:10]
        texto = "🏆 <b>TOP 10 — PROCEDIMENTOS</b>\n\n"
        for i, (proc, qtd) in enumerate(top, 1):
            medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}.</b>"
            texto += f"{medalha} {proc} — <b>{qtd}</b>\n"
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em _top_procedimentos: {e}")
        await responder(update, f"❌ Erro: {e}")