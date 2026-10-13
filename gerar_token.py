#!/usr/bin/env python3
"""
Gerador de Tokens para a API Auto Cutter / YT Web Analyzer
Gera tokens permanentes e tokens JWT válidos até o ano 2999.
"""

import base64
import datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sys

# Garante suporte a UTF-8 no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def generate_jwt(secret: str, exp_timestamp: int, subject: str = "auto-cutter") -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        "exp": exp_timestamp,
        "valid_until": "2999-12-31"
    }
    
    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    msg = f"{header_b64}.{payload_b64}"
    sig = b64url_encode(hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest())
    return f"{msg}.{sig}"

def main():
    print("=" * 65)
    print("      GERADOR DE TOKENS - AUTO CUTTER / YT WEB ANALYZER")
    print("=" * 65)
    print()

    # Tenta carregar chave do .env se existir
    secret = os.getenv("API_KEY") or os.getenv("AUTH_TOKEN")
    env_file = Path(__file__).parent / ".env"
    if not secret and env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("API_KEY=") or line.startswith("AUTH_TOKEN="):
                    secret = line.split("=", 1)[1].strip().strip("'\"")

    if not secret:
        # Usa a chave mestre padrão integrada ao ecossistema
        secret = "crie_uma_chave_secreta_aqui"
        print(f"[i] Usando chave mestre padrão integrada ao ecossistema: {secret}")
    else:
        print(f"[i] Usando chave secreta encontrada na configuração.")

    # Data de expiração: 31 de Dezembro de 2999 às 23:59:59 UTC
    dt_2999 = datetime.datetime(2999, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
    ts_2999 = int(dt_2999.timestamp())

    jwt_token = generate_jwt(secret, ts_2999)

    print()
    print("-" * 65)
    print("🔑 1. CHAVE MESTRA / API KEY PERMANENTE (Sem expiração)")
    print("-" * 65)
    print(secret)
    print()
    print("ℹ️ Esta chave NÃO tem prazo de validade. É válida para sempre enquanto")
    print("   estiver configurada como API_KEY no servidor (Render / Railway / .env).")
    print()

    print("-" * 65)
    print("🎟️ 2. TOKEN JWT ASSINADO (Com expiração gravada para 31/12/2999)")
    print("-" * 65)
    print(jwt_token)
    print()
    print(f"ℹ️ Validade: {dt_2999.strftime('%d/%m/%Y %H:%M:%S')} UTC (Timestamp: {ts_2999})")
    print(f"   Assinado com a chave mestra acima.")
    print()

    print("=" * 65)
    print("📋 COMO USAR:")
    print("=" * 65)
    print("1. No SERVIDOR (Render / Railway / Docker / .env):")
    print(f"   Defina a variável de ambiente:")
    print(f"   API_KEY={secret}")
    print()
    print("2. No FRONTEND (index.html):")
    print("   Clique em ⚙️ Configurar API e cole no campo 'Chave de Autenticação':")
    print("   - Você pode colar tanto a CHAVE MESTRA (Opção 1)")
    print("   - Quanto o TOKEN JWT VÁLIDO ATÉ 2999 (Opção 2)")
    print("   Ambos serão aceitos com sucesso!")
    print("=" * 65)

if __name__ == "__main__":
    main()
