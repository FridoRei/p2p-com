import socket
import subprocess
import os
import signal
import time
from core.auth_token import gerar_token

HOST = '0.0.0.0'  # Aceita conexões de qualquer IP
PORT = 20556      # A porta do servidor de autenticação

# Função para verificar e matar o processo que está utilizando a porta
def verificar_porta_em_uso(port):
    try:
        # Obtém o PID do processo que está utilizando a porta
        result = subprocess.check_output(['lsof', '-t', '-i', f':{port}']).decode('utf-8').strip()
        if result:
            pid = int(result)  # ID do processo
            print(f"Processo {pid} está utilizando a porta {port}. Matando o processo...")
            os.kill(pid, signal.SIGTERM)  # Envia um sinal para matar o processo
            print(f"Processo {pid} morto com sucesso.")
            time.sleep(2)
    except subprocess.CalledProcessError:
        print(f"Porta {port} não está sendo utilizada por nenhum processo.")

# Verifica se a porta já está em uso e mata o processo se necessário
verificar_porta_em_uso(PORT)

# Criar o socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

# Gerar token inicial apenas para log (o token muda a cada conexão de qualquer forma)
print("[LOG] Servidor iniciado. Gerando exemplo de token:")
_ = gerar_token()  # Mostra o salt e a palavra base via print do auth_token.py

print(f"Esperando por uma conexão na porta {PORT}...")

try:
    while True:
        conn, addr = server_socket.accept()
        print(f"\nConexão recebida de {addr}")

        # Gerar o token de autenticação
        token = gerar_token()
        print(f"Token enviado: {token}")

        # Enviar o token para o cliente
        conn.sendall(token.encode())
        conn.close()
except KeyboardInterrupt:
    print("\nServidor encerrado manualmente.")
finally:
    server_socket.close()
