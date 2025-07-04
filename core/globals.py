# core/globals.py
import threading

clientes_lock = threading.Lock()
handlers = []  # Lista global de ClientHandlers