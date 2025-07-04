from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QCheckBox, QLabel, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt
from core.chatclient import ChatClient
import subprocess


class ChatWindow(QWidget):
    def __init__(self, client: ChatClient = None, is_host: bool = False, broadcast_func=None):
        super().__init__()
        self.setWindowTitle("Chat Seguro")
        self.resize(600, 400)  # Tamanho inicial da janela

        self.client = client  # Instância do cliente de chat
        self.is_host = is_host  # Se for o host, habilitar configurações
        self.broadcast_func = broadcast_func  # Função de broadcast (apenas para host)
        self.server_process = None  # Referência para o processo do servidor

        layout = QVBoxLayout(self)

        # Criar o QTabWidget para alternar entre as abas
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        # Aba de Chat
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)

        # Área de mensagens (readonly)
        self.textview = QTextEdit()
        self.textview.setReadOnly(True)
        self.textview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chat_layout.addWidget(self.textview)

        # Linha de entrada e botão enviar
        input_layout = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Digite sua mensagem...")
        input_layout.addWidget(self.entry)

        send_button = QPushButton("Enviar")
        send_button.clicked.connect(self.on_send_clicked)
        input_layout.addWidget(send_button)

        self.chat_layout.addLayout(input_layout)

        # Adiciona a aba de chat ao QTabWidget
        self.tabs.addTab(self.chat_widget, "Chat")

        # Aba de Configurações (apenas se for o host)
        if self.is_host:
            self.settings_widget = QWidget()
            self.settings_layout = QVBoxLayout(self.settings_widget)

            self.add_server_settings()

            # Adiciona a aba de configurações ao QTabWidget
            self.tabs.addTab(self.settings_widget, "Configurações")

        # Mostrar a janela maximizada
        self.showMaximized()

    def add_server_settings(self):
        """Adiciona as configurações do servidor na aba de configurações"""
        settings_label = QLabel("Configurações do servidor:")
        self.settings_layout.addWidget(settings_label)

        self.server_checkbox = QCheckBox("Servidor de autenticação ativado")
        self.server_checkbox.setChecked(False)
        self.server_checkbox.stateChanged.connect(self.on_server_checkbox_changed)
        self.settings_layout.addWidget(self.server_checkbox)

    def on_server_checkbox_changed(self):
        """Ativa ou desativa o servidor de autenticação dependendo do checkbox"""
        if self.server_checkbox.isChecked():
            self.start_authentication_server()
        else:
            self.stop_authentication_server()

    def start_authentication_server(self):
        """Inicia o servidor de autenticação"""
        if not self.server_process:
            self.server_process = subprocess.Popen(["python3", "server.py"])
            self.add_message_to_chat("Servidor de autenticação iniciado.")
        else:
            self.add_message_to_chat("Servidor de autenticação já está em execução.")

    def stop_authentication_server(self):
        """Para o servidor de autenticação"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            self.add_message_to_chat("Servidor de autenticação parado.")
        else:
            self.add_message_to_chat("Nenhum servidor de autenticação em execução.")

    def on_send_clicked(self):
        mensagem = self.entry.text().strip()

        if mensagem:
            self.add_message_to_chat(f"Você: {mensagem}")
            self.entry.clear()
            if self.is_host:
                if self.broadcast_func:
                    self.broadcast_func(mensagem, self)
            else:
                if self.client:
                    try:
                        # Envia diretamente usando o cliente, sem dispatcher
                        self.client.send_message(mensagem)
                    except Exception as e:
                        self.add_message_to_chat(f"Erro ao enviar: {str(e)}")
                else:
                    self.add_message_to_chat("Erro: Conexão não disponível")

    def add_message_to_chat(self, mensagem: str):
        """Adiciona uma mensagem à área de chat"""
        self.textview.append(mensagem)
