import socket, os, sys
from pathlib import Path

CLRF = "\r\n"

# for cleanup, lets create a request and response class
# have default 404 error


def echo_response(string):
    status_line = "HTTP/1.1 200 OK"
    headers = f"Content-Type: text/plain{CLRF}Content-Length: "
    len_body = str(len(string))
    return f"{status_line}{CLRF}{headers}{len_body}{CLRF}{CLRF}{string}"

def parse_header_user_agent(header_list):
    for h in header_list:
        # headers are case insensitive
        # USE STARTSWITH
        if "user-agent" in h.lower():
            s = h[12:]
            return echo_response(s)
    print("no User Agent")
    return "uhoh"

def get_file(filename):
    file_path = Path(sys.argv[2]) / filename
    print(file_path)
    file_path = str(file_path).replace("\\", "/")
    # dirlist = os.listdir(some)
    # print(dirlist)
    file_path = Path(file_path)
    if file_path.exists():
        print("pls")
    else:
        print("SDfjlk")
    if os.path.exists(file_path) and os.path.isfile(file_path):
    # try:
        print("in try")
        with open(file_path, "r") as file:
            file_contents = file.read()
            print("in read")
        msg = f"HTTP/1.1 200 OK{CLRF}Content-Type: application/octet-stream{CLRF}Content-Length: {len(file_contents)}{CLRF}{CLRF}{file_contents}{CLRF}"
    else:
    # except Exception:
        print("SDflkjflskgjlfkj")
        msg = f"HTTP/1.1 404 NOT FOUND{CLRF}Content-Length: 0{CLRF}{CLRF}"
    return msg
            
def handle_request(client_socket):
    received_msg = client_socket.recv(1024)
    if not received_msg:
        return False
    # Parse the request
    request = received_msg.decode().split(CLRF)
    req_start_line, req_headers = request[0], request[1:] # there whould be a body here too.. 
    req_line = req_start_line.split(" ")
    response = ""

    if len(req_line) >= 3: # not sure if it is valid to have request lines shorter than this, just in case..
        http_method = req_line[0]
        req_target = req_line[1] # the path
        http_version = req_line[2] 
        if http_method == "GET":
            if req_target == "/":
                response = "HTTP/1.1 200 OK\r\n\r\n"
            elif len(req_target) >= 6 and req_target[:6] == "/echo/":
                response = echo_response(req_target[6:])
            elif len(req_target) >= 11 and req_target[:11] == "/user-agent":
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
