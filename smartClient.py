# Author:  Yiming Sun
# Purpose:  CSc 361 - Assignment 1
# Date:  Jan 26 2018

import sys, re, socket, ssl

# Distinct Cookies collected from every response headers.
Cookies = set()

# Refer to Negotiating HTTP/2 (https://python-hyper.org/projects/h2/en/stable/negotiating-http2.html#clients).
def get_http2_ssl_context():
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    ctx.set_alpn_protocols(["h2", "http/1.1"])
    try:
        ctx.set_npn_protocols(["h2", "http/1.1"])
    except NotImplementedError:
        pass
    return ctx


# Refer to Negotiating HTTP/2 (https://python-hyper.org/projects/h2/en/stable/negotiating-http2.html#clients).
def negotiate_tls(tcp_conn, context, host):
    try:
        tls_conn = context.wrap_socket(tcp_conn, server_hostname=host)
        negotiated_protocol = tls_conn.selected_alpn_protocol()
        if negotiated_protocol is None:
            negotiated_protocol = tls_conn.selected_npn_protocol()
        tls_conn.close()
    except:
        negotiated_protocol = None
    # Return "h2" if HTTP2 is supported, None if not.
    return negotiated_protocol


def get_Cookies(resp, host):
	if resp:
		# Find Cookies' keys and domains in the response header using regex.
		temp = re.findall(r"(?:Set-Cookie: (.*?)=.*domain=([^;\r\n]*))|(?:Set-Cookie: (.*?)?=)", resp)
		for i in range(0, len(temp)):
			# Domain is present.
			if not temp[i][0] == "":
				key = temp[i][0]
				domain = temp[i][1]
			# Domain is by default (hostname).
			else:
				key = temp[i][2]
				domain = host
			Cookies.add("name: -, key: " + key + ", domain name: " + host)


def print_result(sup_https, prot, resp, host):
	print("1. Support of HTTPS: ", end="")
	if sup_https:
		print("yes")
	else:
		print("no")

	if not resp:
		prot = "N/A"
	print("2. The newest HTTP versions that the web server supports: " + prot)

	print("3. List of Cookies:", end="")
	if Cookies:
		print("")
		for Cookie in Cookies:
			print(Cookie)
	else:
		print(" none")


def smart_client(host, path, sup_https):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error as e:
		print_result(False, "", "", "")
		print("Failed to create socket: " + e.strerror)
		sys.exit(1)

	# Wrap the socket with SSL and use port 443 if HTTPS is supported, otherwise use port 80.
	if sup_https:
		port = 443
		s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_SSLv23)
	else:
		port = 80

	try:
		s.connect((host, port))
	except socket.error as e:
		print_result(False, "", "", "")
		print("Failed to connect socket to the host: " + e.strerror)
		s.close()
		sys.exit(1)

	# Always send HTTP1.1 message; add path (if exists) to the message.
	msg = "GET /" + path + " HTTP/1.1\r\nHost: " + host + "\r\n\r\n"
	msg = msg.encode()
	s.sendall(msg)
	resp = s.recv(4096).decode()
	# Get HTTP status code using regex.
	stat = re.findall(r"^HTTP/.{3} (.{3})", resp)[0]
	get_Cookies(resp, host)
	s.close()

	# Need redirection.
	if stat == "301" or "302":
		new_host = re.findall(r"Location: https?://([^/]*)", resp)
		path = re.findall(r"Location: https?://[^/]*/(.*)?\r", resp)
		if new_host:
			if path:
				path = path[0]
			else:
				path = ""
			# Determine whether HTTPS is supported or not from protocol name in redirected URL using regex.
			if re.match(r".*Location: http:.*", resp, re.S):
				sup_https = False
			# Call the function recursively with the new information.
			smart_client(new_host[0], path, sup_https)

	# Reach destination.
	if stat == "200" or "404" or "503" or "505":
		# Find protocol the host uses from the response header using regex ("HTTP/1.0" or "HTTP/1.1").
		prot = re.findall(r"^(.{8})", resp)[0]
		# Further more, determine whether the host uses HTTP2 or notif the HTTP version is 1.1 or higher.
		if prot == "HTTP/1.1":
			ctx = get_http2_ssl_context()
			# Recreate and reconnect the socket.
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((host, 443))
			new_prot = negotiate_tls(s, ctx, host)
			if new_prot == "h2":
				prot = "HTTP/2.0"
		# Print out result and exit the program (will not return to higher level of the recurrence).
		print_result(sup_https, prot, resp, host)
		sys.exit()


def main():
	if len(sys.argv) != 2:
		print("Please provide an URL in the argument line.")
		sys.exit(1)
	# Determine whether the hostname input is valid or not using regex.
	if not re.match(r"^([A-Za-z0-9-]{1,63}\.)+[A-Za-z0-9-]{1,63}$", sys.argv[1]):
		print("Please input an valid URL, and do not include protocol or path.")
		sys.exit(1)
	host = sys.argv[1]
	print("website: " + host)

	# Assume the host supports HTTPS in the first call.
	# Will receive a redirecting response ("301" or "302") if HTTPS is actually not supported.
	smart_client(host, "", True)

if __name__ == "__main__":
	main()