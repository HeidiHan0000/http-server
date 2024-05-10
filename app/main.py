import socket

def handle_request(client_socket):
    received_msg = client_socket.recv(1024)
    if not received_msg:
        return False
    response = "HTTP/1.1 200 OK\r\n\r\n"
    client_socket.send(response.encode())
    print("Sent 200")
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
