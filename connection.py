import socket
import threading


class Connection(object):

    def __init__(self):
        """
        Connects to a server at a specific port, and keeps the connection alive.
        """
        self.__socket = None
        self.__is_connection_alive = False
        self.__listen_thread = None
        self.__listeners = set()
    
    def connect(self, ip_address, port, timeout):
        """Connect to to server.

        Parameters
        ----------
        ip_address: str
            The IP address of the server.
        port: int
            The port number to bind to.
        timeout: int
            The number of seconds to wait to stop attempting to connect if a connection has not yet been made.

        Returns
        -------
        bool:
            If the connection was successfully established.

        Throws
        ------
        socket.error:
            If a connection could not be made.
        """
        if not self.__is_connection_alive:
            try:
                self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__socket.settimeout(timeout)
                self.__socket.connect((ip_address, port))
                self.__is_connection_alive = True
                self.__listen_thread = threading.Thread(target=self.__listen)
                self.__listen_thread.start()
            except socket.error as exc:
                print("Caught exception socket.error : " + str(exc))
                self.__is_connection_alive = False
            return self.__is_connection_alive
    
        return False
        
    def disconnect(self):
        """Disconnects from the server.

        Returns
        -------
        bool:
           If the connection was successfully terminated.
        """
        if self.__is_connection_alive:
            self.__socket.close()
            self.__is_connection_alive = False
            return True
        return False
        
    @property
    def is_connection_alive(self):
        """
        Returns
        -------
        bool:
            If the connection is currently connected.
        """
        return self.__is_connection_alive
    
    def send_data(self, data):
        """Sends bytes across the connection.

        Parameters
        ----------
        data: bytes
            The bytes to send.
        """
        self.__socket.send(data)

    def send(self, message, crlf_ending=True):
        """Helper function; sends a string across the connection as bytes.

        Parameters
        ----------
        message: str
            The message to send across the connection.
        crlf_ending: bool
            If the method should ensure the message ends with CR-LF.
            Default value is True.
        """
        self.send_data(bytes(message + "\r\n" if crlf_ending and not message.endswith("\r\n") else message, "utf-8"))
    
    def add_listener(self, listener):
        """Adds a listener to the connection.

        Parameters
        ----------
        listener:
            A function which accepts an object which is created from Connection._process_data(bytes),
            which is called each time data is received from the server.
        """
        self.__listeners.add(listener)

    def remove_listener(self, listener):
        """Removes a listener from the connection.

        Parameters
        ----------
        listener:
            A function which accepts an object which is created from Connection._process_data(bytes),
            which is called each time data is received from the server.
        """
        self.__listeners.remove(listener)

    def _process_data(self, data):
        """Processed the bytes received by the server.

        Parameters
        ----------
        data: bytes
            The bytes received from the server.

        Returns
        -------
        object:
            An object used by the listeners.
        """
        return data

    def __dispatch_listeners(self, obj):
        """Listen to the connection in a loop.

        Parameters
        ----------
        obj: object
            The object to send to the listeners.
        """
        for listener in self.__listeners:
            if listener.accept(obj):
                listener.receive(obj)

    def __listen(self, buffer_size=4096):
        """Listens to incoming data from the socket.

        Parameters
        ----------
        buffer_size: int
            The number of bytes for the socket to receive.
            Default value is 4096.
        """

        while self.__is_connection_alive:
            data = self.__socket.recv(buffer_size)
            if data:
                # Messages are separated by CR-LF. Last element is removed since it will be empty.
                for msg in data.split(b"\r\n")[:1]:
                    self.__dispatch_listeners(self._process_data(msg))
            else:
                # Connection terminated by server: data was empty.
                self.__is_connection_alive = False


class MessageListener(object):

    def __init__(self, message_filter, receive):
        """
        Listens for messages, and uses a filter to determine if the message should be accepted by the listener.
        If the message should be accepted, the implementation should then call MessageListener#receive.

        Parameters
        ----------
        message_filter: (object) -> bool
            A method which takes a message as a parameter, and returns if the message should be accepted or not.
        receive: (object) -> None
            A method which takes a message as a parameter.
            This should typically be called after message_filter returns True.
        """
        self.__filter = message_filter
        self.__receive = receive

    def accept(self, message):
        """
        Calls the <message_filter> parameter passed into the constructor.

        Parameters
        ----------
        message: object
            The message received.

        Returns
        -------
        True if the message should be accepted, otherwise False.
        """
        return self.__filter(message)

    def receive(self, message):
        """
        Calls the <receive> parameter passed into the constructor.

        Parameters
        ----------
        message: object
            The message being received.
        """
        self.__receive(message)
