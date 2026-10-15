import socket
import json
import threading
import traceback
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from bridge.dispatcher import dispatch_command

HOST, PORT = "127.0.0.1", 53002

def socket_server():
    """Main socket server loop"""
    server_address = (str(HOST), int(PORT))
    srv = None
    
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(server_address)
        srv.listen(1)
        print(f"✓ vCadworkMCP bridge listening on {HOST}:{PORT}")
    except Exception as e:
        print(f"!!! Server setup failed: {e}")
        if srv:
            srv.close()
        return
    
    # Main server loop
    while True:
        conn = None
        try:
            conn, addr = srv.accept()
            conn.settimeout(20.0)
            
            # Receive data
            raw_chunks = []
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                raw_chunks.append(chunk)
                
                # Check for complete JSON
                temp_data = b''.join(raw_chunks).strip()
                if temp_data.startswith(b'{') and temp_data.endswith(b'}'):
                    try:
                        json.loads(temp_data.decode('utf-8'))
                        break
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
            
            if not raw_chunks:
                continue
            
            # Process request
            raw = b''.join(raw_chunks)
            try:
                decoded_data = raw.decode('utf-8')
                parsed_msg = json.loads(decoded_data)
                
                # Dispatch to handler
                response = dispatch_command(
                    parsed_msg.get("operation"), 
                    parsed_msg.get("args", {})
                )
                
                # Send response
                response_bytes = json.dumps(response).encode('utf-8')
                conn.sendall(response_bytes)
                
            except Exception as e:
                print(f"Error processing request: {e}")
                traceback.print_exc()
                error_response = {
                    "status": "error", 
                    "message": f"Processing error: {e}"
                }
                try:
                    conn.sendall(json.dumps(error_response).encode('utf-8'))
                except:
                    pass
                
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

def main():
    """Main entry point"""
    print("\n--- Starting vCadworkMCP bridge v2.0 ---")
    
    # Check if port is available
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.bind((HOST, PORT))
        test_sock.close()
    except OSError:
        print(f"!!! Port {PORT} already in use. Is another bridge running?")
        return
    
    # Start server
    server_thread = threading.Thread(target=socket_server, daemon=True)
    server_thread.start()
    print("Bridge running in background...")

if __name__ == "__main__":
    main()
