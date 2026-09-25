# ia_admin.py
import os
import logging
import httpx
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_IA = "openai/gpt-oss-120b"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

NOME_ADMIN = os.getenv("NOME_ADMIN", "Sr. Lincoln")


# ═══════════════════════════════════════════════════════════
# COLETA DE CONTEXTO
# ═══════════════════════════════════════════════════════════

async def coletar_contexto() -> str:
    """Coleta um snapshot completo do sistema para a IA."""
    linhas = []
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    linhas.append(f"DATA/HORA ATUAL: {agora}\n")

    # ─── ASSINATURAS ───
    try:
        res = supabase.table("assinaturas").select("chat_id, tipo_plano, status, data_vencimento, usou_degustacao").execute()
        assinaturas = res.data or []

        total = len(set(str(a.get("chat_id")) for a in assinaturas))
        ativos = [a for a in assinaturas if str(a.get("status", "")).lower() in ("ativo", "active", "ativa")]
        degustacao = [a for a in assinaturas if str(a.get("tipo_plano", "")).lower() == "degustacao"]
        cortesia = [a for a in assinaturas if str(a.get("tipo_plano", "")).lower() == "cortesia"]
        bloqueados = [a for a in assinaturas if str(a.get("status", "")).lower() == "bloqueado"]

        linhas.append(f"USUÁRIOS:")
        linhas.append(f"• Total: {total}")
        linhas.append(f"• Ativos: {len(ativos)}")
        linhas.append(f"• Degustação: {len(degustacao)}")
        linhas.append(f"• Cortesia: {len(cortesia)}")
        linhas.append(f"• Bloqueados: {len(bloqueados)}")
    except Exception as e:
        logger.error(f"Erro assinaturas: {e}")
        linhas.append("USUÁRIOS: erro ao carregar")

    # ─── PAGAMENTOS ───
    try:
        res = supabase.table("pagamentos_pix").select("valor, status, tipo_plano, created_at").execute()
        pagamentos = res.data or []

        aprovados = [p for p in pagamentos if str(p.get("status", "")).lower() == "approved"]
        pendentes = [p for p in pagamentos if str(p.get("status", "")).lower() == "pending"]

        receita_total = sum(float(p.get("valor", 0) or 0) for p in aprovados)

        # Receita do mês atual
        agora_dt = datetime.now(timezone.utc)
        receita_mes = 0
        for p in aprovados:
            try:
                dt = datetime.fromisoformat(str(p.get("created_at")).replace("Z", "+00:00"))
                if dt.year == agora_dt.year and dt.month == agora_dt.month:
                    receita_mes += float(p.get("valor", 0) or 0)
            except Exception:
                pass

        linhas.append(f"\nPAGAMENTOS:")
        linhas.append(f"• Total aprovados: {len(aprovados)}")
        linhas.append(f"• Pendentes: {len(pendentes)}")
        linhas.append(f"• Receita total: R$ {receita_total:.2f}")
        linhas.append(f"• Receita do mês: R$ {receita_mes:.2f}")
    except Exception as e:
        logger.error(f"Erro pagamentos: {e}")

    # ─── REGULAÇÕES ───
    try:
        res = supabase.table("AlertaSUS_2.0").select("numero_reg, nome_paciente, chat_id, status_anterior, procedimento, created_at").execute()
        regs = res.data or []

        # Contagem por status
        status_count = {}
        for r in regs:
            s = str(r.get("status_anterior") or "Sem status").strip()
            status_count[s] = status_count.get(s, 0) + 1

        # Cadastradas hoje
        agora_dt = datetime.now(timezone.utc).date()
        hoje = 0
        for r in regs:
            try:
                dt = datetime.fromisoformat(str(r.get("created_at")).replace("Z", "+00:00"))
                if dt.date() == agora_dt:
                    hoje += 1
            except Exception:
                pass

        linhas.append(f"\nREGULAÇÕES:")
        linhas.append(f"• Total: {len(regs)}")
        linhas.append(f"• Cadastradas hoje: {hoje}")
        linhas.append(f"• Por status:")
        for s, qtd in sorted(status_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            linhas.append(f"   - {s}: {qtd}")
    except Exception as e:
        logger.error(f"Erro regulações: {e}")

    # ─── CHAMADOS ───
    try:
        res = supabase.table("chamados_suporte").select("id, nome_usuario, status, created_at").execute()
        chamados = res.data or []

        abertos = [c for c in chamados if str(c.get("status", "")).lower() in ("aberto", "em_andamento")]
        respondidos = [c for c in chamados if str(c.get("status", "")).lower() == "respondido"]

        linhas.append(f"\nCHAMADOS:")
        linhas.append(f"• Total: {len(chamados)}")
        linhas.append(f"• Abertos/em andamento: {len(abertos)}")
        linhas.append(f"• Respondidos: {len(respondidos)}")

        if abertos:
            linhas.append("• Detalhes dos abertos:")
            for c in abertos[:3]:
                linhas.append(f"   - #{c.get('id')} — {c.get('nome_usuario', '?')} ({c.get('created_at', '')[:10]})")
    except Exception as e:
        logger.error(f"Erro chamados: {e}")

    return "\n".join(linhas)


async def coletar_detalhes_usuario(chat_id: str) -> str:
    """Coleta dados completos de um usuário específico."""
    linhas = [f"USUÁRIO: {chat_id}"]

    try:
        res = supabase.table("assinaturas").select("*").eq("chat_id", chat_id).execute()
        if res.data:
            a = res.data[0]
            linhas.append(f"• Plano: {a.get('tipo_plano') or '—'}")
            linhas.append(f"• Status: {a.get('status') or '—'}")
            linhas.append(f"• Início: {a.get('data_inicio') or '—'}")
            linhas.append(f"• Vencimento: {a.get('data_vencimento') or '—'}")
            linhas.append(f"• Limite: {a.get('limite_ids') or 'Ilimitado'}")
            linhas.append(f"• Usou degustação: {a.get('usou_degustacao')}")
    except Exception as e:
        linhas.append(f"Erro assinatura: {e}")

    try:
        res = supabase.table("pagamentos_pix").select("valor, tipo_plano, status, created_at").eq("chat_id", chat_id).execute()
        pagamentos = res.data or []
        linhas.append(f"• Total de pagamentos: {len(pagamentos)}")
        total = sum(float(p.get("valor", 0) or 0) for p in pagamentos if str(p.get("status", "")).lower() == "approved")
        linhas.append(f"• Total pago: R$ {total:.2f}")
    except Exception as e:
        linhas.append(f"Erro pagamentos: {e}")

    try:
        res = supabase.table("AlertaSUS_2.0").select("numero_reg, nome_paciente, procedimento, status_anterior").eq("chat_id", chat_id).execute()
        regs = res.data or []
        linhas.append(f"• Regulações: {len(regs)}")
        for r in regs[:5]:
            linhas.append(f"   - {r.get('numero_reg')} — {r.get('procedimento')} — {r.get('status_anterior')}")
    except Exception as e:
        linhas.append(f"Erro regulações: {e}")

    return "\n".join(linhas)


# ═══════════════════════════════════════════════════════════
# CHAMADA À IA
# ═══════════════════════════════════════════════════════════

async def chamar_groq(system_prompt: str, user_message: str) -> str:
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY não configurada no .env"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODELO_IA,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Erro Groq: {e}")
        return f"❌ Erro na IA: {e}"


async def processar_consulta_admin(mensagem: str) -> str:
    """Processa uma consulta do admin em linguagem natural."""
    contexto = await coletar_contexto()

    system_prompt = (
        f"Você é o VS Admin, assistente executivo do {NOME_ADMIN} no sistema VigiaSaúde.\n\n"
        "Você tem acesso a TODOS os dados do sistema em tempo real (veja abaixo).\n\n"
        "REGRAS:\n"
        "1. Responda SEMPRE em português, de forma clara e objetiva.\n"
        "2. Use os dados do CONTEXTO para responder. NUNCA invente números.\n"
        "3. Se o admin perguntar sobre um usuário específico, use o comando /user <ID> se não tiver os dados.\n"
        "4. Seja profissional, mas amigável. Trate o admin como 'você'.\n"
        "5. Não use markdown complexo. Use HTML simples do Telegram (<b>, <i>, <code>).\n"
        "6. Se não tiver certeza, diga o que você sabe e sugira o comando certo.\n\n"
        f"=== CONTEXTO ATUAL DO SISTEMA ===\n{contexto}\n=== FIM DO CONTEXTO ==="
    )

    return await chamar_groq(system_prompt, mensagem)


async def processar_consulta_usuario(chat_id: str, mensagem: str) -> str:
    """Processa consulta sobre um usuário específico."""
    contexto = await coletar_detalhes_usuario(chat_id)

    system_prompt = (
        f"Você é o VS Admin, assistente executivo do {NOME_ADMIN}.\n\n"
        f"O admin está perguntando sobre um usuário específico.\n\n"
        f"=== DADOS DO USUÁRIO ===\n{contexto}\n=== FIM ===\n\n"
        "Responda de forma clara e objetiva, usando APENAS os dados acima."
    )

    return await chamar_groq(system_prompt, mensagem)