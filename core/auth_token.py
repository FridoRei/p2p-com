# core/auth_token.py
import bcrypt
from datetime import datetime

def gerar_salt():
    salt = bcrypt.gensalt(rounds=12)
    return salt

def gerar_token():
    data_atual = datetime.now()
    mes_anterior = data_atual.month - 1 if data_atual.month != 1 else 12
    palavra_base = f"{data_atual.year}-{mes_anterior}-{data_atual.day}"
    
    salt = gerar_salt()
    token = bcrypt.hashpw(palavra_base.encode("utf-8"), salt)
    return token.decode("utf-8")

def validar_token(token_recebido):
    data_atual = datetime.now()
    mes_anterior = data_atual.month - 1 if data_atual.month != 1 else 12
    palavra_base = f"{data_atual.year}-{mes_anterior}-{data_atual.day}"
    # A correção é que bcrypt.checkpw já faz tudo, a linha hash_esperado era o erro
    return bcrypt.checkpw(palavra_base.encode("utf-8"), token_recebido.encode("utf-8"))
