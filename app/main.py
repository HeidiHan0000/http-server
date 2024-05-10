import socket, os, sys
from pathlib import Path

CLRF = "\r\n"

def build_response(string, protocol_version="HTTP/1.1", code="200 OK", content_type="text/plain"):
    response = (
        f"{protocol_version} {code}\r\n"
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
    file_path = str(Path(sys.argv[2]) / filename).replace("\\", "/") # was causing weird error
    file_path = Path(file_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, "r") as file:
            file_contents = file.read()
        return build_response(file_contents, content_type="application/octet-stream")
    else:
        return build_response("", code="404 Not Found")
            
def handle_request(client_socket):
    received_msg = client_socket.recv(1024)
    if not received_msg:
        return False
    # Parse the request
    request = received_msg.decode().split(CLRF)
    req_start_line, req_headers = request[0], request[1:] # there whould be a body here too.. 
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
                response = build_response(req_target[6:])
            elif req_target.startswith("/user-agent"):
                response = parse_header_user_agent(req_headers)
            elif req_target.startswith("/files/"):
                filename = req_target.replace("/files/", "")
                response = get_file(filename)
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
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
