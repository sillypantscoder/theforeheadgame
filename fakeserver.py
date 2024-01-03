import typing
import os
import json
import sys

class URLQuery:
	def __init__(self, q):
		self.orig = q
		self.fields = {}
		for f in q.split("&"):
			s = f.split("=")
			if len(s) >= 2:
				self.fields[s[0]] = s[1]
	def get(self, key):
		if key in self.fields:
			return self.fields[key]
		else:
			return ''

def read_file(filename: str) -> bytes:
	"""Read a file and return the contents."""
	f = open(filename, "rb")
	t = f.read()
	f.close()
	return t

def write_file(filename: str, content: bytes):
	"""Write data to a file."""
	f = open(filename, "wb")
	f.write(content)
	f.close()

class HttpResponse(typing.TypedDict):
	"""A dict containing an HTTP response."""
	status: int
	headers: dict[str, str]
	content: str | bytes

class HttpResponseStrict(typing.TypedDict):
	"""A dict containing an HTTP response. The content field is required to be bytes and not str."""
	status: int
	headers: dict[str, str]
	content: bytes

def get(path: str, query: URLQuery) -> HttpResponse:
	# playername = query.get("name")
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
	elif path.startswith("/set/"):
		setname = path[5:] + ".json"
		set = json.loads(read_file(os.path.join("sets", setname)))
		return {
			"status": 200,
			"headers": {
				"Content-Type": "application/json"
			},
			"content": json.dumps(set)
		}
	elif os.path.isfile("public_files" + path):
		return {
			"status": 200,
			"headers": {
				"Content-Type": {
					"html": "text/html",
					"js": "text/javascript",
					"css": "text/css",
					"svg": "image/svg+xml",
					"ico": "image/x-icon"
				}[path.split(".")[-1]]
			},
			"content": read_file("public_files" + path)
		}
	elif os.path.isdir("public_files" + path):
		return {
			"status": 200,
			"headers": {
				"Content-Type": "text/html"
			},
			"content": read_file("public_files" + path + "index.html")
		}
	else: # 404 page
		print("404 GET " + path, file=sys.stderr)
		return {
			"status": 404,
			"headers": {
				"Content-Type": "text/html"
			},
			"content": ""
		}

def post(path: str, body: str) -> HttpResponse:
	bodydata = body.split("\n")
	if path.startswith("/edit"):
		setname = path[6:]
		setdata = json.loads(body)
		if os.path.exists("sets/" + setname + ".json"): return {
			"status": 404,
			"headers": {},
			"content": f""
		}
		write_file("sets/" + setname + ".json", json.dumps(setdata, indent='\t').encode("UTF-8"))
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
		write_file("sets/" + setname + ".json", json.dumps(setdata, indent='\t').encode("UTF-8"))
		return {
			"status": 200,
			"headers": {},
			"content": f""
		}
	else:
		print("404 POST " + path, file=sys.stderr)
		return {
			"status": 404,
			"headers": {
				"Content-Type": "text/html"
			},
			"content": ""
		}

class MyServer:
	def read_packet(self) -> bytes:
		headers = b""
		newChar = b""
		while newChar != b".":
			headers += newChar
			newChar = sys.stdin.buffer.read(1)
		length = int(headers)
		content = b""
		for i in range(length):
			content += sys.stdin.buffer.read(1)
		return content
	def handle_request(self):
		method = self.read_packet()
		path = self.read_packet().decode("UTF-8")
		body = self.read_packet().decode("UTF-8")
		res: HttpResponseStrict = {
			"status": 404,
			"headers": {},
			"content": b""
		}
		if method == b"GET":
			res = self.do_GET(path)
		if method == b"POST":
			res = self.do_POST(path, body)
		s: list[bytes] = [
			str(res["status"]).encode("UTF-8"),
			",".join([f"{a}:{b}" for a, b in res["headers"].items()]).encode("UTF-8"),
			res["content"]
		]
		for data in s:
			self.send_packet(data)
			# time.sleep(0.3)
	def send_packet(self, info: bytes):
		sys.stdout.buffer.write(str(len(info)).encode("UTF-8"))
		sys.stdout.buffer.write(b".")
		sys.stdout.buffer.write(info)
		sys.stdout.buffer.flush()
		# try: print("Printed[", str(len(info)), '.', info.decode("UTF-8"), "]", sep="", file=sys.stderr)
		# except UnicodeDecodeError: print("Printed[", str(len(info)), '.', info, "]", sep="", file=sys.stderr)
	def do_GET(self, path) -> HttpResponseStrict:
		splitpath = path.split("?")
		res = get(splitpath[0], URLQuery(''.join(splitpath[1:])))
		c: str | bytes = res["content"]
		if isinstance(c, str): c = c.encode("utf-8")
		return {
			"status": res["status"],
			"headers": res["headers"],
			"content": c
		}
	def do_POST(self, path: str, body: str) -> HttpResponseStrict:
		res = post(path, body)
		c: str | bytes = res["content"]
		if isinstance(c, str): c = c.encode("utf-8")
		return {
			"status": res["status"],
			"headers": res["headers"],
			"content": c
		}

if __name__ == "__main__":
	running = True
	webServer = MyServer()
	print(f"Fake server (the forehead game) started", file=sys.stderr)
	# sys.stdout.flush()
	while running:
		try:
			webServer.handle_request()
		except KeyboardInterrupt:
			running = False
	print("Server stopped", file=sys.stderr)
