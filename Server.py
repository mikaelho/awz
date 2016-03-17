# coding: utf-8
import BaseHTTPServer
import threading

class AWZHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	
	allow_reuse_address = True
	
	def do_GET(s):
		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.end_headers()
		s.wfile.write(s.server.content_func(s.path[1:]))
		#s.wfile.write("<html><head><title>AWZ</title></head>")
		#s.wfile.write("<body><p>This is a test.</p>")
		#s.wfile.write(markdown(AWZHandler.store[s.path[1:]]))
		#s.wfile.write("<p>You accessed path: %s</p>" % s.path)
		#s.wfile.write("<p>Server address is: %s</p>" % s.address_string())
		#s.wfile.write("</body></html>")
		
server_thread = None
server = None
		
def start(content_hook):
	if alive(): return
	server = BaseHTTPServer.HTTPServer(('10.0.1.201', 8000), AWZHandler)
	server.content_func = content_hook
	#server = BaseHTTPServer.HTTPServer(('', 8012), AWZHandler)
	server_thread = threading.Thread(target = server.serve_forever)
	#thread.daemon = True
	server_thread.start()
		
def stop():
	#server.socket.close()
	server.shutdown()
	server.server_close()
	server = None

def alive():
	return (server_thread and server_thread.is_alive())
