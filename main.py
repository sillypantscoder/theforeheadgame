# A basic Python web server that will serve files in "public_files/".
# Also serves the list of sets, and the "sets" JSON files.

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import datetime

hostName = "0.0.0.0"
serverPort = 7298 # chosen at random

def read_file(filename):
	f = open(filename, "r")
	t = f.read()
	f.close()
	return t

def bin_read_file(filename):
	f = open(filename, "rb")
	t = f.read()
	f.close()
	return t

def write_file(filename, content):
	f = open(filename, "w")
	f.write(content)
	f.close()

def file_mod_date(filename):
	stamp = os.path.getmtime(filename)
	date = datetime.datetime.fromtimestamp(stamp)
	return date

def get(path):
	qpath = path.split("?")[0]
	if path == "/sets": # LIST OF SETS
		sets = [
			{"filename": f[:-5], "displayname": json.loads(read_file(os.path.join("sets", f)))["name"]}
			for f in os.listdir("sets")
			if (True if "deleted" in json.loads(read_file(os.path.join("sets", f))).keys() else print("aaaaa! Set does not contain 'deleted' parameter", f)) and not json.loads(read_file(os.path.join("sets", f)))["deleted"]
		]
		sets = sorted(sets, key=lambda x: os.path.getmtime("sets/" + x["filename"] + ".json"))
		return {
			"status": 200,
			"headers": {
				"Content-Type": "application/json"
			},
			"content": json.dumps(sets)
		}
	elif qpath.startswith("/set/"):
		setname = qpath[5:] + ".json"
		set = json.loads(read_file(os.path.join("sets", setname)))
		return {
			"status": 200,
			"headers": {
				"Content-Type": "application/json"
			},
			"content": json.dumps(set)
		}
	elif os.path.isfile("public_files/" + qpath): # SERVING DIRECT FILES
		return {
			"status": 200,
			"headers": {
				"Content-Type": {
					"html": "text/html",
					"json": "application/json",
					"js": "text/javascript"
				}[qpath.split(".")[-1]]
			},
			"content": bin_read_file("public_files/" + qpath)
		}
	elif qpath.endswith("/"): # INDEX.HTML
		if os.path.isdir("public_files/" + qpath) and os.path.isfile("public_files/" + qpath + "/index.html"):
			return {
				"status": 200,
				"headers": {
					"Content-Type": "text/html"
				},
				"content": read_file("public_files/" + qpath + "/index.html")
			}
		else:
			return {
				"status": 404,
				"headers": {
					"Content-Type": "text/html"
				},
				"content": f""
			}
	else: # 404 page
		return {
			"status": 404,
			"headers": {
				"Content-Type": "text/html"
			},
			"content": f""
		}

def post(path, body):
	if path.startswith("/edit"):
		setname = path[6:]
		setdata = json.loads(body.decode("UTF-8"))
		if os.path.exists("sets/" + setname + ".json"): return {
			"status": 404,
			"headers": {},
			"content": f""
		}
		write_file("sets/" + setname + ".json", json.dumps(setdata, indent='\t'))
		return {
			"status": 200,
			"headers": {},
			"content": f""
		}
	if path.startswith("/delete"):
		setname = path[8:]
		if not os.path.exists("sets/" + setname + ".json"): return {
			"status": 404,
			"headers": {},
			"content": f""
		}
		setdata = json.loads(read_file("sets/" + setname + ".json"))
		setdata["deleted"] = True
		write_file("sets/" + setname + ".json", json.dumps(setdata, indent='\t'))
		return {
			"status": 200,
			"headers": {},
			"content": f""
		}
	else:
		return {
			"status": 404,
			"headers": {},
			"content": f""
		}

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		global running
		res = get(self.path)
		self.send_response(res["status"])
		for h in res["headers"]:
			self.send_header(h, res["headers"][h])
		self.end_headers()
		c = res["content"]
		if type(c) == str: c = c.encode("utf-8")
		self.wfile.write(c)
	def do_POST(self):
		res = post(self.path, self.rfile.read(int(self.headers["Content-Length"])))
		self.send_response(res["status"])
		for h in res["headers"]:
			self.send_header(h, res["headers"][h])
		self.end_headers()
		self.wfile.write(res["content"].encode("utf-8"))
	def log_message(self, format: str, *args) -> None:
		return;
		if 400 <= int(args[1]) < 500:
			# Errored request!
			print(u"\u001b[31m", end="")
		print(args[0].split(" ")[0], "request to", args[0].split(" ")[1], "(status code:", args[1] + ")")
		print(u"\u001b[0m", end="")
		# don't output requests

if __name__ == "__main__":
	running = True
	webServer = HTTPServer((hostName, serverPort), MyServer)
	webServer.timeout = 1
	print("Server started http://%s:%s" % (hostName, serverPort))
	while running:
		try:
			webServer.handle_request()
		except KeyboardInterrupt:
			running = False
	webServer.server_close()
	print("Server stopped")
