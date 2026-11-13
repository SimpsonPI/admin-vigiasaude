import os
import subprocess
import httpx
from datetime import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PASTA_PREMIUM = r"C:\Users\User\Pictures\Bot_VigiaSaude"
LOG_PREMIUM = os.path.join(PASTA_PREMIUM, "servidor.log")


async def gerar_laudo_sistema():
    """Coleta dados reais do sistema para a IA analisar."""
    laudo = []
    laudo.append("=== LAUDO DE DIAGNÓSTICO DO SISTEMA ===")
    laudo.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # 1. Verifica se os processos Python estão rodando
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq python.exe"],
            text=True,
            encoding="cp850",  # Evita o erro de caracteres estranhos do Windows
            errors="replace",
        )
        qtd_python = output.lower().count("python.exe")
        laudo.append(f"\n1. Processos Python ativos nesta máquina: {qtd_python}")
        if qtd_python == 0:
            laudo.append("   ALERTA: Nenhum bot Python rodando nesta máquina!")
    except Exception as e:
        laudo.append(f"\n1. Erro ao checar processos: {e}")

    # 2. Testa conexão com o Supabase (usando credenciais do Admin)
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            sb = create_client(url, key)
            sb.table("assinaturas").select("id").limit(1).execute()
            laudo.append("\n2. Banco de Dados (Supabase) do Admin: ONLINE.")
        else:
            laudo.append(
                "\n2. Banco de Dados: Credenciais não encontradas no .env do Admin."
            )
    except Exception as e:
        laudo.append(f"\n2. Banco de Dados (Supabase): FALHA DE CONEXÃO. Erro: {e}")

    # 3. Testa API do Telegram (Usando a variável correta TELEGRAM_ADMIN_TOKEN)
    try:
        token = os.getenv("TELEGRAM_ADMIN_TOKEN")

        if not token:
            try:
                from config import TELEGRAM_ADMIN_TOKEN as token
            except:
                pass

        if token:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"https://api.telegram.org/bot{token}/getMe", timeout=10
                )
                if r.status_code == 200 and r.json().get("ok"):
                    laudo.append(
                        "\n3. API do Telegram (Admin): ONLINE (Bot autenticado com sucesso)."
                    )
                else:
                    laudo.append(
                        f"\n3. API do Telegram: FALHA. Status HTTP: {r.status_code}"
                    )
        else:
            laudo.append(
                "\n3. API do Telegram: Não testado (TELEGRAM_ADMIN_TOKEN não encontrado)."
            )
    except Exception as e:
        laudo.append(f"\n3. API do Telegram: FALHA DE REDE. Erro: {e}")

    # 4. Lê as últimas linhas de erro do log do Premium
    laudo.append("\n4. Status do Bot VS Premium (via Log):")
    try:
        if os.path.exists(LOG_PREMIUM):
            with open(LOG_PREMIUM, "r", encoding="utf-8", errors="replace") as f:
                linhas = f.readlines()[-100:]
                erros = [l.strip() for l in linhas if "ERROR" in l or "Traceback" in l]
                if erros:
                    for e in erros[-3:]:
                        laudo.append(f"   - {e}")
                else:
                    laudo.append(
                        "   Nenhum erro recente no log. O bot VS Premium está rodando limpo."
                    )
        else:
            laudo.append("   Log do Premium não encontrado no caminho.")
    except Exception as e:
        laudo.append(f"   Erro ao ler o log do Premium: {e}")

    return "\n".join(laudo)
