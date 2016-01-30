import wincertstore
import atexit

certfile = wincertstore.CertFile()
certfile.addstore("CA")
certfile.addstore("ROOT")
atexit.register(certfile.close)
