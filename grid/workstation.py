from queue import Queue
from threading import Thread
from time import sleep
from typing import Dict, Optional

import pandas as pd

from extsockets import ServerManager

pending, _open, closed = "pending", "open", "closed"
xonetypes = {pending, _open, closed}

add_subscription, sub_response = "add subscription", "subscription response"
xones = "xones"
spawn, spawn_response = "spawn", "spawn_response"

client, server, meta, data = "client", "server", "meta", "data"

response_template = {"to": client, "from": server, meta: "", data: ""}


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
        global meta, data
        try:
            rcvd_meta = message[meta]
            rcvd_data = message[data]
        except KeyError:
            return 0

        if rcvd_meta.lower() == add_subscription:
            if rcvd_data == xones:
                if client_socket not in self.xone_clients:
                    self.xone_clients.append(client_socket)
                self.broadcast(meta_=sub_response, data_="Loading Xones", client_list=[client_socket])
                if self.dict_of_xonesdf:
                    self.broadcast(meta_=xones, data_=self.dict_of_xonesdf, client_list=[client_socket])

        if rcvd_meta.lower() == spawn:
            if isinstance(rcvd_data, dict):
                if self.manager:
                    retval = self.manager.spawn(rcvd_data)
                    self.broadcast(meta_=spawn_response, data_=retval, client_list=[client_socket])

    def close_handler(self, client_socket):
        if client_socket in self.xone_clients:
            self.xone_clients.remove(client_socket)

    def broadcast(self, meta_, data_, client_list=None):
        global meta, data
        client_list = self.xone_clients if not client_list else client_list

        message = response_template.copy()
        message[meta] = meta_
        message[data] = data_

        self.send_message(client_list, message)

    def update(self):
        while True:
            self.dict_of_xonesdf = self.q.get()
            while not self.q.empty():
                self.dict_of_xonesdf = self.q.get()
            assert set(self.dict_of_xonesdf.keys()) == xonetypes, f"Xone types != {xonetypes}"
            self.broadcast(meta_=xones, data_=self.dict_of_xonesdf)
            sleep(1)
