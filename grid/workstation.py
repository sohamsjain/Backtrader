from queue import Queue
from socket import socket
from threading import *
from time import sleep
from typing import Dict, Optional

import pandas as pd

from extsockets import ServerManager

pending, _open, closed = 'pending', 'open', 'closed'
xonetypes = {pending, _open, closed}


class WorkStation(ServerManager):
    def __init__(self, host="", port=2012):
        super(WorkStation, self).__init__(host=host, port=port, call_on_message=self.message_handler,
                                          call_on_close=self.close_handler)
        self.xone_clients = list()
        self.manager = None
        self.dict_of_xonesdf: Optional[Dict[str, pd.DataFrame]] = None
        self.q = Queue()
        self.updater = Thread(target=self.update, daemon=True)
        self.updater.start()

    def set_manager(self, manager):
        self.manager = manager

    def message_handler(self, client_socket, message):
        try:
            meta = message['meta']
            data = message['data']
        except KeyError:
            return 0

        if meta.lower() == 'add subscription':
            if data == 'xones':
                if client_socket not in self.xone_clients:
                    self.xone_clients.append(client_socket)
                message = {"to": "client", "from": "server", 'meta': 'subscription response', 'data': 'Loading Xones'}
                self.send_message(client_socket, message)
                if self.dict_of_xonesdf:
                    self.broadcast(self.dict_of_xonesdf, [client_socket])

        if meta.lower() == 'create xone':
            if isinstance(data, dict):
                if self.manager:
                    response = self.manager.create_xone(data)
                    send_back = {"to": "client", "from": "server", "meta": "xone response", "data": response}
                    self.send_message(client_socket, send_back)

        if meta.lower() == 'exit xone':
            if isinstance(data, dict):
                if self.manager:
                    data = self.manager.exit_xone(data)
                    send_back = {"to": "client", "from": "server", 'meta': 'exit response', 'data': data}
                    self.send_message(client_socket, send_back)

    def close_handler(self, client):
        if client in self.xone_clients:
            self.xone_clients.remove(client)

    def broadcast(self, message, client_list=None):
        client_list = self.clients if not client_list else client_list
        client_list = [client_list] if isinstance(client_list, socket) else client_list
        for client in client_list:
            self.send_message(client, message)

    def update(self):
        while True:
            self.dict_of_xonesdf = self.q.get()
            while not self.q.empty():
                self.dict_of_xonesdf = self.q.get()
            assert set(self.dict_of_xonesdf.keys()) == xonetypes, f"Xone types != {xonetypes}"
            self.broadcast(self.dict_of_xonesdf)
            sleep(1)
