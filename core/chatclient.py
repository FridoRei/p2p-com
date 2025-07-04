import socket
import threading
import subprocess
from PySide6.QtCore import QObject, Signal, Slot

class ChatClientWorker(QObject):
    message_received = Signal(str)
    connection_error = Signal(str)
    
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self._running = True

    def stop(self):
        self._running = False

    @Slot()
    def listen_for_messages(self):
        """Escuta mensagens do servidor e emite sinais"""
        while self._running:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    self.message_received.emit(message)
                else:
                    self.message_received.emit("Servidor desconectou.")
                    break
            except Exception as e:
                if self._running:
                    self.connection_error.emit(f"Erro de conexão: {e}")
                break
        
        self.client_socket.close()
        print("Thread de escuta encerrada.")

class ChatClient:
    @staticmethod
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

    def __init__(self, host, port, chat_window=None, nome_usuario="Usuário"):
        self.host = host
        self.port = port
        self.chat_window = chat_window
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nome_usuario = nome_usuario
        self.worker = None
        self.thread = None

    def connect(self):
        if not self.host:
            print("Gateway não encontrado.")
            return
        
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Conectado ao servidor em {self.host}:{self.port}")
            
            # Configura worker e thread
            self.worker = ChatClientWorker(self.client_socket)
            self.thread = threading.Thread(target=self.worker.listen_for_messages, daemon=True)
            
            # Conecta sinais
            if self.chat_window:
                self.worker.message_received.connect(self.chat_window.add_message_to_chat)
                self.worker.connection_error.connect(self.chat_window.add_message_to_chat)
            
            self.thread.start()
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            if self.chat_window:
                self.chat_window.add_message_to_chat(f"Erro ao conectar: {e}")

    def send_message(self, message):
        try:
            if not self.client_socket:
                raise Exception("Socket não inicializado")
            
            # Adiciona quebra de linha para facilitar a leitura no servidor
            self.client_socket.sendall((message + "\n").encode())
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            if self.chat_window:
                self.chat_window.add_message_to_chat(f"Erro ao enviar: {e}")
            raise  # Re-lança a exceção para ser tratada pelo chamador

    def disconnect(self):
        if self.worker:
            self.worker.stop()
        if self.client_socket:
            self.client_socket.close()
        print("Cliente desconectado.")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from ui.chatwindow import ChatWindow
    import sys

    app = QApplication(sys.argv)
    window = ChatWindow()
    gateway = ChatClient.obter_gateway()
    
    if gateway:
        client = ChatClient(gateway, 20557, window)
        client.connect()
        window.show()
        sys.exit(app.exec())
    else:
        print("Não foi possível obter o gateway.")
