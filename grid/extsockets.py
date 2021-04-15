import errno
import pickle
import select
import socket
import threading

from extlogger import *

logcat = LogCat(__name__)


class Server(socket.socket):
    HOST = ""
    PORT = 9999

    def __init__(self, host=None, port=None):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.HOST = host if host is not None else self.HOST
        self.PORT = port if port is not None else self.PORT
        self.bind((self.HOST, self.PORT))
        print(f"Binding {self.HOST} with {self.PORT}")
        self.listen(5)


class ServerManager:
    HEADER_LENGTH = 10

    def __init__(self, host=None, port=None, call_on_message=None, call_on_close=None):
        self.server = Server(host=host, port=port)
        self.sockets = [self.server]
        self.client_dict = {}
        self.clients = []
        self.on_message = None
        self.on_close = None
        if call_on_message:
            self.set_on_message(call_on_message)
        if call_on_close:
            self.set_on_close(call_on_close)
        self.name = "Server {}:{}".format(host, port)
        self.logcat = logcat.get_logger(self.name, "server.log")
        self.logcat.info("Initialising {}\n{}".format(self.name, time.ctime()))
        self.main_thread = threading.Thread(target=self.mainloop, daemon=True)
        self.main_thread.start()

    def set_on_message(self, call_on_message):
        self.on_message = call_on_message

    def set_on_close(self, call_on_close):
        self.on_close = call_on_close

    def add_client(self, client_socket, client_address):
        self.sockets.append(client_socket)
        self.clients.append(client_socket)
        self.client_dict.update({client_socket: client_address})
        self.logcat.debug("Added New client to socket list and client list")

    def remove_client(self, client):
        self.sockets.remove(client)
        self.client_dict.pop(client)
        self.clients.remove(client)
        self.logcat.debug("Removed: {}".format(client))

    def receive_message(self, socket):
        try:

            # Receive our "header" containing message length, it's size is defined and constant
            message_header = socket.recv(self.HEADER_LENGTH)

            # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(message_header):
                return False

            # Convert header to int value
            message_length = int(message_header.decode('utf-8').strip())

            # Receiving and converting the message
            chunks = []
            bytes_recd = 0
            while bytes_recd < message_length:
                chunk = socket.recv(min(message_length - bytes_recd, 2048))
                if chunk == b'':
                    return False
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            message = b''.join(chunks)

            data = pickle.loads(message)
            return data

        except:

            # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
            # or just lost his connection
            # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
            # and that's also a cause when we receive an empty message
            return False

    def pack_message(self, message):
        message = pickle.dumps(message)
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode('utf-8')
        return message_header + message

    def send_message(self, _socket, message):
        pickle_message = self.pack_message(message)
        message_length = len(pickle_message)
        if type(_socket) != list:
            _socket = [_socket]
        for sock in _socket:
            totalsent = 0
            while totalsent < message_length:
                sent = sock.send(pickle_message[totalsent:])
                totalsent = totalsent + sent

    def close(self):
        self.server.close()

    def mainloop(self):
        while True:
            self.logcat.debug("New Iteration")
            read_sockets, write_sockets, exception_sockets = select.select(self.sockets, [], self.sockets)
            self.logcat.debug("read: {}, write: {}, exception: {}".format(len(read_sockets), len(write_sockets),
                                                                          len(exception_sockets)))
            for notified_socket in read_sockets:

                if notified_socket == self.server:
                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    client_socket, client_address = self.server.accept()
                    self.logcat.debug(f'New Connection Recieved from {client_address}')
                    self.add_client(client_socket, client_address)
                    print(f'New Connection Recieved from {client_address}')
                # Else existing socket is sending a message
                else:

                    # Receive message
                    message = self.receive_message(notified_socket)
                    self.logcat.debug('Message Received')
                    # If False, client disconnected, cleanup
                    if message is False:
                        self.logcat.debug(f'Connection closed {self.client_dict[notified_socket]}')
                        print(f'Connection closed {self.client_dict[notified_socket]}')
                        if self.on_close:
                            self.on_close(notified_socket)
                        self.remove_client(notified_socket)
                        continue

                    if self.on_message:
                        self.on_message(notified_socket, message)

            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                self.logcat.debug("Removing Exception Socket: " + notified_socket)
                self.remove_client(notified_socket)


class Client(socket.socket):
    HOST = "127.0.0.1"
    PORT = 9999

    def __init__(self, host=None, port=None, blocking=False):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.HOST = host if host is not None else self.HOST
        self.PORT = port if port is not None else self.PORT
        self.connect((self.HOST, self.PORT))
        print(f"Connecting to {self.HOST}:{self.PORT}")
        if not blocking:
            self.setblocking(False)


class ClientManager:
    HEADER_LENGTH = 10

    def __init__(self, host=None, port=None, call_on_message=None, call_on_close=None):
        self.client = Client(host=host, port=port, blocking=True)
        self.on_message = None
        self.on_close = None
        if call_on_message:
            self.set_on_message(call_on_message)
        if call_on_close:
            self.set_on_close(call_on_close)
        self.main_thread = threading.Thread(target=self.mainloop, daemon=True)
        self.stop_mainloop = False
        self.main_thread.start()

    def set_on_message(self, call_on_message):
        self.on_message = call_on_message

    def set_on_close(self, call_on_close):
        self.on_close = call_on_close

    def receive_message(self):
        try:

            # Receive our "header" containing message length, it's size is defined and constant
            message_header = self.client.recv(self.HEADER_LENGTH)

            # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(message_header):
                return "Connection Closed"

            # Convert header to int value
            message_length = int(message_header.decode('utf-8').strip())
            # Receiving and converting the message

            chunks = []
            bytes_recd = 0
            while bytes_recd < message_length:
                chunk = self.client.recv(min(message_length - bytes_recd, 2048))
                if chunk == b'':
                    return "Connection Closed"
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            message = b''.join(chunks)

            # message = self.client.recv(message_length)
            data = pickle.loads(message)
            return data


        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading IOError: {}'.format(str(e)))
            if e.errno == errno.WSAECONNRESET:
                return "Connection Closed"
            return False

    def pack_message(self, message):
        message = pickle.dumps(message)
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode('utf-8')
        return message_header + message

    def send_message(self, message):
        pickle_message = self.pack_message(message)
        message_length = len(pickle_message)
        totalsent = 0
        while totalsent < message_length:
            sent = self.client.send(pickle_message[totalsent:])
            totalsent = totalsent + sent

    def close(self):
        self.client.close()
        self.stop_mainloop = True

    def mainloop(self):
        while not self.stop_mainloop:
            try:
                # Receive message
                message = self.receive_message()

                if message is not False:
                    if message == "Connection Closed":
                        if self.on_close:
                            self.on_close()
                        break

                    if self.on_message:
                        self.on_message(message)

            except Exception as e:
                # Any other exception - something happened, exit
                print('Reading error: {}'.format(str(e)))


if __name__ == '__main__':
    s = Server()
