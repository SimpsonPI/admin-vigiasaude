# handlers_relatorios.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import supabase
from helpers import eh_admin, responder, fmt_data, fmt_moeda, emoji_status_plano
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def comando_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    try:
        res = supabase.table("assinaturas").select("chat_id, status, tipo_plano").execute()
        assinaturas = res.data or []

        total_usuarios = len(set(str(a.get("chat_id")) for a in assinaturas))
        ativos = sum(1 for a in assinaturas if str(a.get("status", "")).lower() in ("ativo", "active", "ativa"))
        degustacao = sum(1 for a in assinaturas if str(a.get("tipo_plano", "")).lower() == "degustacao")
        cortesia = sum(1 for a in assinaturas if str(a.get("tipo_plano", "")).lower() == "cortesia")

        res_reg = supabase.table("AlertaSUS_2.0").select("numero_reg").execute()
        total_regs = len(res_reg.data or [])

        res_pag = supabase.table("pagamentos_pix").select("valor, status").execute()
        pagamentos = res_pag.data or []

        def is_aprovado(s):
            s = str(s or "").strip().lower()
            return s in ("approved", "aprovado", "aprovada", "ativo", "pago", "paid", "confirmed")

        pag_aprovados = [p for p in pagamentos if is_aprovado(p.get("status"))]
        pag_pendentes = [p for p in pagamentos if str(p.get("status", "")).lower() in ("pending", "pendente")]
        receita_total = sum(float(p.get("valor", 0) or 0) for p in pag_aprovados)

        res_ch = supabase.table("chamados_suporte").select("status").execute()
        chamados = res_ch.data or []
        ch_abertos = sum(1 for c in chamados if str(c.get("status", "")).lower() in ("aberto", "em_andamento"))

        texto = (
            "📊 <b>ESTATÍSTICAS GERAIS</b>\n\n"
            "👥 <b>USUÁRIOS</b>\n"
            f"• Total: <b>{total_usuarios}</b>\n"
            f"• Ativos: <b>{ativos}</b>\n"
            f"• Degustação: <b>{degustacao}</b>\n"
            f"• Cortesia: <b>{cortesia}</b>\n\n"
            "📋 <b>REGULAÇÕES</b>\n"
            f"• Total cadastradas: <b>{total_regs}</b>\n\n"
            "💳 <b>PAGAMENTOS</b>\n"
            f"• Aprovados: <b>{len(pag_aprovados)}</b>\n"
            f"• Pendentes: <b>{len(pag_pendentes)}</b>\n"
            f"• 💰 Receita total: <b>{fmt_moeda(receita_total)}</b>\n\n"
            "📞 <b>CHAMADOS</b>\n"
            f"• Em aberto: <b>{ch_abertos}</b>\n"
        )
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /stats: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_assinaturas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todas as assinaturas pagas."""
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    try:
        res = (
            supabase.table("assinaturas")
            .select("*")
            .in_("tipo_plano", ["trimestral", "semestral", "pro", "pro_trimestral", "pro_semestral"])
            .order("created_at", desc=True)
            .execute()
        )
        assinaturas = res.data or []

        if not assinaturas:
            await responder(update, "ℹ️ Nenhuma assinatura paga encontrada.")
            return

        res_regs = supabase.table("AlertaSUS_2.0").select("chat_id, nome_paciente").execute()
        nomes = {}
        for r in (res_regs.data or []):
            cid = str(r.get("chat_id"))
            if cid and r.get("nome_paciente"):
                nomes[cid] = r.get("nome_paciente")

        total_geral = len(assinaturas)
        ativos = sum(1 for a in assinaturas if str(a.get("status", "")).lower() in ("ativo", "active", "ativa"))

        valores = {"trimestral": 9.99, "pro_trimestral": 9.99, "semestral": 14.99, "pro_semestral": 14.99, "pro": 0}
        receita = 0
        for a in assinaturas:
            tipo = str(a.get("tipo_plano", "")).lower()
            if str(a.get("status", "")).lower() in ("ativo", "active", "ativa"):
                receita += valores.get(tipo, 0)

        texto = (
            f"📈 <b>ASSINATURAS PAGAS</b>\n\n"
            f"• Total: <b>{total_geral}</b>\n"
            f"• Ativas: <b>{ativos}</b>\n"
            f"• 💰 Receita estimada: <b>{fmt_moeda(receita)}</b>\n\n"
            "───────────────────────\n\n"
        )

        for a in assinaturas[:20]:
            cid = str(a.get("chat_id"))
            nome = nomes.get(cid, "—")
            tipo = str(a.get("tipo_plano", "—")).capitalize()
            status = emoji_status_plano(a.get("status"))
            contratacao = fmt_data(a.get("data_inicio") or a.get("created_at"))
            vencimento = fmt_data(a.get("data_vencimento"))

            texto += (
                f"👤 <b>{nome}</b>\n"
                f"🆔 <code>{cid}</code>\n"
                f"👑 {tipo} — {status}\n"
                f"📅 Contratado: {contratacao}\n"
                f"⏰ Vence: {vencimento}\n\n"
            )

        if len(assinaturas) > 20:
            texto += f"<i>...e mais {len(assinaturas) - 20} assinatura(s)</i>"

        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /assinaturas: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_ativos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    try:
        res = (
            supabase.table("assinaturas")
            .select("chat_id, tipo_plano, status, data_inicio, data_vencimento")
            .eq("status", "ativo")
            .order("data_vencimento", desc=False)
            .limit(30)
            .execute()
        )
        ativos = res.data or []

        if not ativos:
            await responder(update, "ℹ️ Nenhuma assinatura ativa no momento.")
            return

        texto = f"📋 <b>ASSINATURAS ATIVAS</b> ({len(ativos)})\n\n"
        for a in ativos:
            texto += (
                f"🆔 <code>{a.get('chat_id')}</code>\n"
                f"   👑 {a.get('tipo_plano', '?')} — vence {fmt_data(a.get('data_vencimento'))}\n\n"
            )

        if len(texto) > 4000:
            texto = texto[:3990] + "\n\n<i>[...]</i>"

        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /ativos: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_pagamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    try:
        res = supabase.table("pagamentos_pix").select("*").order("created_at", desc=True).limit(15).execute()
        pagamentos = res.data or []

        if not pagamentos:
            await responder(update, "ℹ️ Nenhum pagamento registrado.")
            return

        texto = "💳 <b>ÚLTIMOS PAGAMENTOS</b>\n\n"
        for p in pagamentos:
            status = str(p.get("status", "")).lower()
            emoji = "✅" if status in ("approved", "aprovado", "aprovada", "pago") else "⏳" if status in ("pending", "pendente") else "❌"
            texto += (
                f"{emoji} <b>{fmt_moeda(p.get('valor'))}</b> — {p.get('tipo_plano', '?')}\n"
                f"   🆔 <code>{p.get('chat_id')}</code>\n"
                f"   📅 {fmt_data(p.get('created_at'))}\n\n"
            )

        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /pagamentos: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_chamados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    try:
        res = (
            supabase.table("chamados_suporte")
            .select("*")
            .in_("status", ["aberto", "em_andamento"])
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        chamados = res.data or []

        if not chamados:
            await responder(update, "✅ Nenhum chamado em aberto.")
            return

        texto = f"📋 <b>CHAMADOS EM ABERTO</b> ({len(chamados)})\n\n"
        for c in chamados:
            texto += (
                f"🔔 <b>#{c.get('id')}</b> — {c.get('nome_usuario', '?')}\n"
                f"   🆔 <code>{c.get('chat_id')}</code>\n"
                f"   📝 {str(c.get('mensagem', ''))[:80]}\n"
                f"   📅 {fmt_data(c.get('created_at'))}\n\n"
            )
        texto += "<i>Para responder: use o bot Central</i>"
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /chamados: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_regulacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    if not context.args:
        await responder(update, "⚠️ Uso: <code>/regulacao &lt;numero_reg&gt;</code>")
        return

    num_reg = context.args[0].strip()

    try:
        res = supabase.table("AlertaSUS_2.0").select("*").eq("numero_reg", num_reg).execute()
        dados = res.data or []

        if not dados:
            await responder(update, f"❌ Regulação <code>{num_reg}</code> não encontrada.")
            return

        texto = f"📋 <b>REGULAÇÃO</b> <code>{num_reg}</code>\n\n"
        for r in dados[:5]:
            texto += (
                f"👤 <b>Paciente:</b> {r.get('nome_paciente', '?')}\n"
                f"🆔 <b>Chat ID:</b> <code>{r.get('chat_id')}</code>\n"
                f"📊 <b>Status:</b> {r.get('status_anterior') or '—'}\n"
                f"📈 <b>Posição:</b> {r.get('posicao_anterior') or '—'}\n"
                f"🩺 <b>Especialidade:</b> {r.get('cbo') or '—'}\n"
                f"🏥 <b>Procedimento:</b> {r.get('procedimento') or '—'}\n"
                f"📱 <b>Celular:</b> {r.get('celular') or '—'}\n\n"
                "───\n\n"
            )
        await responder(update, texto)
    except Exception as e:
        logger.error(f"Erro em /regulacao: {e}")
        await responder(update, f"❌ Erro: {e}")


async def comando_resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resumo geral com layout visual aprimorado."""
    if not eh_admin(update.effective_user.id):
        await responder(update, "⛔ Acesso negado.")
        return

    try:
        res_ass = supabase.table("assinaturas").select("chat_id, status, tipo_plano").execute()
        assinaturas = res_ass.data or []

        res_pag = supabase.table("pagamentos_pix").select("valor, status, created_at").execute()
        pagamentos = res_pag.data or []

        res_reg = supabase.table("AlertaSUS_2.0").select("numero_reg, status_anterior, created_at").execute()
        regs = res_reg.data or []

        res_ch = supabase.table("chamados_suporte").select("status").execute()
        chamados = res_ch.data or []

        agora = datetime.now(timezone.utc)
        agora_str = datetime.now().strftime("%d/%m/%Y • %H:%M")

        total_usuarios = len(set(str(a.get("chat_id")) for a in assinaturas))
        ativos = sum(1 for a in assinaturas if str(a.get("status", "")).lower() in ("ativo", "active", "ativa"))
        cortesia = sum(1 for a in assinaturas if str(a.get("tipo_plano", "")).lower() == "cortesia")
        degustacao = sum(1 for a in assinaturas if str(a.get("tipo_plano", "")).lower() == "degustacao")
        bloqueados = sum(1 for a in assinaturas if str(a.get("status", "")).lower() == "bloqueado")

        aprovados = [p for p in pagamentos if str(p.get("status", "")).lower() == "approved"]
        pendentes = [p for p in pagamentos if str(p.get("status", "")).lower() in ("pending", "pendente")]
        receita_total = sum(float(p.get("valor", 0) or 0) for p in aprovados)

        receita_mes = 0
        for p in aprovados:
            try:
                dt = datetime.fromisoformat(str(p.get("created_at")).replace("Z", "+00:00"))
                if dt.year == agora.year and dt.month == agora.month:
                    receita_mes += float(p.get("valor", 0) or 0)
            except Exception:
                pass

        total_regs = len(regs)
        agendadas = sum(1 for r in regs if "agend" in str(r.get("status_anterior") or "").lower())
        em_fila = sum(
            1 for r in regs
            if "informada" in str(r.get("status_anterior") or "").lower()
            or "fila" in str(r.get("status_anterior") or "").lower()
        )
        hoje = 0
        for r in regs:
            try:
                dt = datetime.fromisoformat(str(r.get("created_at")).replace("Z", "+00:00"))
                if dt.date() == agora.date():
                    hoje += 1
            except Exception:
                pass

        total_chamados = len(chamados)
        abertos = sum(1 for c in chamados if str(c.get("status", "")).lower() in ("aberto", "em_andamento"))
        respondidos = sum(1 for c in chamados if str(c.get("status", "")).lower() == "respondido")

        texto = (
            "📊 <b>RESUMO GERAL</b>\n"
            f"🗓️ <i>{agora_str}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"

            "👥 <b>USUÁRIOS</b>\n"
            f"<code>   Total ......... {total_usuarios}</code>\n"
            f"<code>   ✅ Ativos ..... {ativos}</code>\n"
            f"<code>   👑 Cortesia ... {cortesia}</code>\n"
            f"<code>   🎁 Degustação . {degustacao}</code>\n"
            f"<code>   🚫 Bloqueados . {bloqueados}</code>\n\n"

            "💰 <b>PAGAMENTOS</b>\n"
            f"<code>   ✅ Aprovados .. {len(aprovados)}</code>\n"
            f"<code>   ⏳ Pendentes .. {len(pendentes)}</code>\n"
            f"<code>   💵 Receita .... R$ {receita_total:.2f}</code>\n"
            f"<code>   📅 Este mês ... R$ {receita_mes:.2f}</code>\n\n"

            "📋 <b>REGULAÇÕES</b>\n"
            f"<code>   Total ......... {total_regs}</code>\n"
            f"<code>   🟢 Agendadas .. {agendadas}</code>\n"
            f"<code>   🟡 Em fila .... {em_fila}</code>\n"
            f"<code>   🆕 Hoje ....... {hoje}</code>\n\n"

            "🎫 <b>CHAMADOS</b>\n"
            f"<code>   Total ......... {total_chamados}</code>\n"
            f"<code>   🔴 Abertos .... {abertos}</code>\n"
            f"<code>   ✅ Respondidos  {respondidos}</code>\n\n"

            "━━━━━━━━━━━━━━━━━━━━━"
        )

        await responder(update, texto)

    except Exception as e:
        logger.error(f"Erro em /resumo: {e}")
        await responder(update, f"❌ Erro: {e}")