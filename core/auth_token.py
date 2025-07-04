# core/auth_token.py
import bcrypt
from datetime import datetime

def gerar_salt():
    salt = bcrypt.gensalt(rounds=12)
    return salt

def gerar_token():
    try:
        data_atual = datetime.now()
        mes_anterior = data_atual.month - 1 if data_atual.month != 1 else 12
        palavra_base = f"{data_atual.year}-{mes_anterior}-{data_atual.day}"
        
        salt = gerar_salt()
        token = bcrypt.hashpw(palavra_base.encode("utf-8"), salt)
        return token.decode("utf-8")
    except Exception as e:
        print(f"[ERRO] ao gerar token: {e}")
        return None

def validar_token(token_recebido):
    try:
        data_atual = datetime.now()
        mes_anterior = data_atual.month - 1 if data_atual.month != 1 else 12
        palavra_base = f"{data_atual.year}-{mes_anterior}-{data_atual.day}"
        return bcrypt.checkpw(palavra_base.encode("utf-8"), token_recebido.encode("utf-8"))
    except Exception as e:
        print(f"[ERRO] ao validar token: {e}")
        return False
