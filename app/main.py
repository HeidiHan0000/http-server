import socket, os, sys
from pathlib import Path

def build_response(string, protocol_version="HTTP/1.1", code="200 OK", content_type="text/plain", content_encoding=None):
    encoding = "" if not content_encoding else f"Content-Encoding: {content_encoding}"
    print(string)
    response = (
        f"{protocol_version} {code}\r\n"
        f"{encoding}"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {str(len(string))}\r\n\r\n"
        f"{string}"
    )
    return response

def parse_header_user_agent(header_list):
    for h in header_list:
        # headers are case insensitive
        if h.lower().startswith("user-agent"):
            s = h[12:]
            return build_response(s)
    print("User Agent not in header")
    return build_response("", code="400 Bad Request")

def get_file(filename):
    filepath = Path(sys.argv[2]) / filename
    if os.path.exists(filepath) and os.path.isfile(filepath):
        with open(filepath, "r") as file:
            file_contents = file.read()
        return build_response(file_contents, content_type="application/octet-stream")
    else:
        return build_response("", code="404 Not Found")

def post_to_file(req_body, filename):
    filepath = Path(sys.argv[2]) / filename
    try:
        with open(filepath, "w") as file:
            file.write(req_body)
    except Exception as e:
        print("Error writing to file", e)
    return build_response("", code="201 Created")

def get_echo(echo_str, header_list):
    print(echo_str)
    for h in header_list:
        if h.lower() == "accept-encoding": #17 char long
            encoding = h[17:]
            print(encoding)
            if encoding == "gzip":
                return build_response(echo_str, content_encoding="gzip")
    return build_response(echo_str)

def handle_request(client_socket):
    received_msg = client_socket.recv(1024)
    if not received_msg:
        return False
    # Parse the request
    header_body_split = received_msg.decode().split("\r\n\r\n")
    req_body = header_body_split[1]
    start_header_split = header_body_split[0].split("\r\n")
    req_start_line, req_headers = start_header_split[0], start_header_split[1:]
    req_line = req_start_line.split(" ")
    response = ""

    if len(req_line) >= 3: # not sure if it is even valid to have request lines shorter than this, just in case..
        http_method = req_line[0]
        req_target = req_line[1] # the path
        http_version = req_line[2] 
        if http_method == "GET":
            if req_target == "/":
                response = "HTTP/1.1 200 OK\r\n\r\n"
            elif req_target.startswith("/echo/"):
                response = get_echo(req_target[6:], req_headers)
            elif req_target.startswith("/user-agent"):
                response = parse_header_user_agent(req_headers)
            elif req_target.startswith("/files/"):
                filename = req_target.replace("/files/", "")
                response = get_file(filename)
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
        elif http_method == "POST":
            if req_target.startswith("/files/"):
                filename = req_target.replace("/files/", "")
                response = post_to_file(req_body, filename)
    
    client_socket.send(response.encode())
    return True

def main():
    # reuse_port not avail on Windows
    server_socket = socket.create_server(("localhost", 4221), reuse_port=False)
    print("Server running on port 4221...")
    # added timeout because CTLR-C will not work
    server_socket.settimeout(1.0)
    
    try:
        client_socket = None
        while True:
            try:
                client_socket, client_addr = server_socket.accept()
                handle_request(client_socket)
            except socket.timeout:
                pass
            except IOError as msg:
                print(msg)
                server_socket.close()
                print("Server shut down")
                break
            finally:
                if client_socket:
                    client_socket.close()
    except KeyboardInterrupt:
        server_socket.close()
        print("Server shut down")

if __name__ == "__main__":
    main()
