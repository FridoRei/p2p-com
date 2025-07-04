import subprocess
import socket

def obter_gateway():
    try:
        result = subprocess.run(["ip", "route"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith("default"):
                partes = line.split()
                if "via" in partes:
                    return partes[partes.index("via") + 1]
    except Exception as e:
        print(f"[ERRO] ao obter gateway: {e}")
    return None

def verificar_conexao_com_host(validar_token_func, porta=20556):
    gateway = obter_gateway()
    if not gateway:
        print("Gateway não encontrado.")
        return False

    try:
        with socket.create_connection((gateway, porta), timeout=3) as sock:
            token = sock.recv(1024).decode()
            return validar_token_func(token)
    except Exception as e:
        print(f"[ERRO] Falha na conexão com o host: {e}")
    return False
