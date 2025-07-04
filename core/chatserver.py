import socket
import threading
import time
from PySide6.QtCore import QObject, Signal, Slot
from core.globals import clientes_lock, handlers

# Porta do servidor de chat
CHAT_SERVER_PORT = 20557

class ClientHandler(QObject):
    # Sinais para comunicar com a GUI do host
    new_message_for_host = Signal(str)  # Mensagens recebidas de clientes
    client_status_for_host = Signal(str)  # Status de conexão/desconexão de clientes

    def __init__(self, client_socket, addr):
        super().__init__()
        self.client_socket = client_socket
        self.addr = addr
        self._running = True
        # Configura timeout para evitar bloqueios
        self.client_socket.settimeout(1.0)

    def stop(self):
        self._running = False

    @Slot()
    def run(self):
        """Lida com a comunicação de um cliente individual."""
        with clientes_lock:
            handlers.append(self)
            print(f"[Servidor] Novo cliente conectado: {self.addr}")

        try:
            while self._running:
                try:
                    # Recebe a mensagem do cliente
                    mensagem_bytes = self.client_socket.recv(1024)
                    if not mensagem_bytes:
                        print(f"[Servidor] Cliente {self.addr} desconectou")
                        break
                    
                    mensagem = mensagem_bytes.decode('utf-8').strip()
                    print(f"[Servidor] Mensagem recebida de {self.addr}: {mensagem}")
                    
                    # Exibe a mensagem no chat do host
                    self.new_message_for_host.emit(f"[{self.addr[0]}] {mensagem}")
                    
                    # Retransmite a mensagem para outros clientes
                    self.broadcast_message(f"[{self.addr[0]}] {mensagem}", self.client_socket)

                except socket.timeout:
                    continue  # Timeout normal, continua o loop
                except Exception as e:
                    if self._running:
                        print(f"[Servidor] Erro com cliente {self.addr}: {e}")
                        self.new_message_for_host.emit(f"[Servidor] Erro com cliente {self.addr}: {e}")
                    break

        finally:
            with clientes_lock:
                if self in handlers:
                    handlers.remove(self)
                    print(f"[Servidor] Handler removido para {self.addr}")
            
            self.client_socket.close()
            self.client_status_for_host.emit(f"[Servidor] Cliente desconectado: {self.addr}")
            print(f"[Servidor] Conexão encerrada com {self.addr}")

    def send_to_client(self, message: str):
        """Envia uma mensagem para este cliente específico"""
        try:
            if self._running:
                self.client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"[Servidor] Erro ao enviar para {self.addr}: {e}")

    def broadcast_message(self, message: str, sender_socket=None):
        """Envia mensagem para todos os clientes, exceto o remetente"""
        message_bytes = message.encode('utf-8')
        
        with clientes_lock:
            current_handlers = handlers.copy()
        
        for handler in current_handlers:
            if handler != self and handler._running:
                try:
                    handler.client_socket.sendall(message_bytes)
                except Exception as e:
                    print(f"[Servidor] Erro no broadcast para {handler.addr}: {e}")

def broadcast_from_host(message: str, chat_window_instance):
    """Envia mensagem do host para todos os clientes conectados"""
    if not message:
        return

    if chat_window_instance:
        chat_window_instance.add_message_to_chat(f"Você (Host): {message}")
    
    message_with_prefix = f"[Host] {message}"
    print(f"[Servidor] Broadcast do host: {message_with_prefix}")
    
    with clientes_lock:
        current_handlers = handlers.copy()
    
    for handler in current_handlers:
        try:
            if handler._running:
                handler.send_to_client(message_with_prefix)
        except Exception as e:
            print(f"[Servidor] Erro no broadcast para {handler.addr}: {e}")

def start_server(chat_window_instance):
    """Inicia o servidor de chat."""
    print("[Servidor] Iniciando servidor de chat...")
    
    # Limpa handlers residuais
    with clientes_lock:
        handlers.clear()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    host = '0.0.0.0'
    port = CHAT_SERVER_PORT

    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"[Servidor] Servidor de chat escutando em {host}:{port}")
        
        if chat_window_instance:
            chat_window_instance.add_message_to_chat(f"Servidor de chat iniciado em {host}:{port}")

        while True:
            try:
                conn, addr = server_socket.accept()
                print(f"[Servidor] Nova conexão de {addr}")
                
                # Cria handler para o novo cliente
                handler = ClientHandler(conn, addr)
                
                # Configura thread
                thread = threading.Thread(target=handler.run, daemon=True)
                
                # Conecta sinais à interface
                if chat_window_instance:
                    handler.new_message_for_host.connect(chat_window_instance.add_message_to_chat)
                    handler.client_status_for_host.connect(chat_window_instance.add_message_to_chat)
                
                thread.start()
                
            except Exception as e:
                print(f"[Servidor] Erro ao aceitar conexão: {e}")

    except Exception as e:
        print(f"[Servidor] Erro fatal no servidor: {e}")
        if chat_window_instance:
            chat_window_instance.add_message_to_chat(f"Erro no servidor: {e}")
    finally:
        server_socket.close()
        print("[Servidor] Servidor de chat encerrado.")