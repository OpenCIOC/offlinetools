import httplib
import socket
import ssl
from backports.ssl_match_hostname import match_hostname

def install_validating_https(cert_file):
    def validating_connect(self):
        "Connect to a host on a given (SSL) port."

        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, cert_reqs=ssl.CERT_REQUIRED, ca_certs=cert_file)
        match_hostname(self.sock.getpeercert(), self.host)



    httplib.HTTPSConnection.connect = validating_connect
