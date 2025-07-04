import sys
from PySide6.QtWidgets import QApplication
from ui.mainwindow import MainWindow  # Sua janela principal com PySide6

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Inicializa o app Qt
    win = MainWindow()            # Cria a janela principal
    win.show()                    # Exibe a janela
    sys.exit(app.exec())         # Executa o loop principal
