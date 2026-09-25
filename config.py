# config.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

TELEGRAM_ADMIN_TOKEN = os.getenv("TELEGRAM_ADMIN_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NOME_ADMIN = os.getenv("NOME_ADMIN", "Sr. Lincoln")

if not TELEGRAM_ADMIN_TOKEN or not SUPABASE_URL or not SUPABASE_KEY or not ADMIN_ID:
    raise ValueError("❌ Variáveis de ambiente faltando no .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logger = logging.getLogger(__name__)