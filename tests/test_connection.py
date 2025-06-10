# test_connection.py
import socket

def check_connection(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"Success: Connection to {host}:{port} succeeded")
            return True
        else:
            print(f"Failed: Connection to {host}:{port} failed with error code {result}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# Test connection to the server
check_connection("localhost", 8001)