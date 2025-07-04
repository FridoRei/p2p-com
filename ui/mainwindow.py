from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QDialog,
    QHBoxLayout, QLineEdit, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Slot
import subprocess
import sys
import threading
from PySide6 import QtCore
from PySide6.QtGui import QIcon, QFont
from core.auth_token import validar_token
from core.networking import verificar_conexao_com_host, obter_gateway
from core.hotspot import detectar_interfaces_wifi, criar_hotspot
from ui.chatwindow import ChatWindow
from core.chatclient import ChatClient
from core.chatserver import start_server, broadcast_from_host  # Importa start_server e broadcast_from_host


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conexão Segura")
        self.resize(500, 200)  # Tamanho ideal para exibir os botões sem maximizar

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        vbox = QVBoxLayout(self.central_widget)

        # Espaço acima
        vbox.addSpacerItem(QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))

        label = QLabel("Selecione o modo de conexão:")
        label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(label)

        # Layout horizontal centralizado
        hbox = QHBoxLayout()

        btn_host = QPushButton("Hospedar Rede")
        btn_host.setIcon(QIcon.fromTheme("network-wireless"))
        btn_host.setIconSize(QtCore.QSize(32, 32))
        btn_host.setFixedSize(200, 80)
        btn_host.clicked.connect(self.on_host_clicked)

        btn_join = QPushButton("Juntar-se à Rede")
        btn_join.setIcon(QIcon.fromTheme("contact-new"))
        btn_join.setIconSize(QtCore.QSize(32, 32))
        btn_join.setFixedSize(200, 80)
        btn_join.clicked.connect(self.on_join_clicked)

        hbox.addStretch()
        hbox.addWidget(btn_host)
        hbox.addSpacing(50)
        hbox.addWidget(btn_join)
        hbox.addStretch()

        vbox.addLayout(hbox)

        # Espaço abaixo
        vbox.addSpacerItem(QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))

    @Slot()
    def on_host_clicked(self):
        self.selecionar_interface_wifi()

    @Slot()
    def on_join_clicked(self):
        if verificar_conexao_com_host(validar_token):
            print("Você está conectado ao host correto!")
            self.juntar_se_ao_hotspot()
        else:
            self.mostrar_dialogo("Erro", "Não foi possível verificar a autenticidade do host.")

    def selecionar_interface_wifi(self):
        interfaces = detectar_interfaces_wifi()
        if not interfaces:
            self.mostrar_dialogo("Erro", "Nenhuma interface Wi-Fi encontrada.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Escolher Interface Wi-Fi")
        layout = QVBoxLayout(dialog)

        for iface in interfaces:
            # Layout horizontal para cada interface e botão
            hbox_item = QHBoxLayout()

            item_label = QLabel(iface)
            item_label.setFont(QFont("Arial", 14))  # Fonte maior para os itens

            # Botão "Selecionar" à direita do item
            btn_selecionar = QPushButton("Selecionar")
            btn_selecionar.clicked.connect(lambda checked, iface=iface: self.selecionar_interface(iface, dialog))

            # Adiciona o label e o botão no layout horizontal
            hbox_item.addWidget(item_label)
            hbox_item.addStretch()  # Para empurrar o botão para a direita
            hbox_item.addWidget(btn_selecionar)

            # Adiciona o layout horizontal à janela de diálogo
            layout.addLayout(hbox_item)

        dialog.exec()

    def selecionar_interface(self, iface, dialog):
        dialog.accept()  # Fecha o diálogo
        self.exibir_configuracao_hotspot(iface)

    def exibir_configuracao_hotspot(self, interface):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Hotspot")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Nome da rede (SSID):"))
        ssid_entry = QLineEdit("SecureComunication")
        layout.addWidget(ssid_entry)

        layout.addWidget(QLabel("Senha:"))
        senha_entry = QLineEdit("12345678")
        senha_entry.setEchoMode(QLineEdit.Password)
        layout.addWidget(senha_entry)

        btn_criar = QPushButton("Criar Hotspot")
        layout.addWidget(btn_criar)

        def criar():
            ssid = ssid_entry.text()
            senha = senha_entry.text()

            if len(senha) < 8:
                self.mostrar_dialogo("Erro", "A senha deve ter pelo menos 8 caracteres.")
                return

            dialog.accept()

            # Cria o hotspot e inicia o servidor de autenticação
            criar_hotspot(interface, ssid, senha)
            self.mostrar_dialogo("Hotspot criado", f"SSID: {ssid}\nSenha: {senha}")

            threading.Thread(target=self.iniciar_servidor_autenticacao, daemon=True).start()

            # Cria a instância do ChatWindow para o host, passando a função broadcast_from_host
            self.chat_window = ChatWindow(
                client=None,
                is_host=True,
                broadcast_func=broadcast_from_host  # Passa a função diretamente
            )
            self.chat_window.show()

            # Inicia o servidor de chat em uma thread
            threading.Thread(target=self.iniciar_servidor_chat, daemon=True).start()

            # Esconde a janela principal
            self.hide()

        btn_criar.clicked.connect(criar)

        dialog.exec()

    def mostrar_dialogo(self, titulo, mensagem):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(mensagem)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def iniciar_servidor_autenticacao(self):
        subprocess.run(["python3", "server.py"])

    def iniciar_servidor_chat(self):
        """Inicia o servidor de chat em thread separada"""
        try:
            # Limpa handlers residuais antes de iniciar
            from core.globals import handlers, clientes_lock
            with clientes_lock:
                handlers.clear()
                
            threading.Thread(
                target=start_server,
                args=(self.chat_window,),
                daemon=True
            ).start()
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            if hasattr(self, 'chat_window'):
                self.chat_window.add_message_to_chat(f"Erro ao iniciar servidor: {e}")

    def juntar_se_ao_hotspot(self):
        gateway = obter_gateway()
        if not gateway:
            self.mostrar_dialogo("Erro", "Não foi possível obter o gateway da rede.")
            return
        
        # Cria a janela primeiro
        self.chat_window = ChatWindow(is_host=False)
        
        # Cria o cliente passando a janela já criada
        client = ChatClient(gateway, 20557, self.chat_window)
        
        # Atualiza a referência do cliente na janela
        self.chat_window.client = client
        
        # Conecta os sinais
        if client.worker:
            client.worker.message_received.connect(self.chat_window.add_message_to_chat)
            client.worker.connection_error.connect(self.chat_window.add_message_to_chat)
        
        # Faz a conexão
        client.connect()
        
        self.chat_window.show()
        self.hide()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
