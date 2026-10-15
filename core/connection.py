"""
Cadwork connection management
"""
import socket
import json
from typing import Dict, Any, Optional
from .logging import log_info, log_error

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 53002
SOCKET_TIMEOUT = 30.0

class CadworkConnection:
    """Manages connection to Cadwork bridge plugin"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
    
    def send_command(self, operation: str, args: Optional[Dict[str, Any]] = None,
                     timeout: Optional[float] = None) -> Dict[str, Any]:
        """Send command to Cadwork and return response.

        timeout: seconds to wait for the bridge, SOCKET_TIMEOUT when omitted.
        """
        command = {
            "operation": operation,
            "args": args or {}
        }
        
        log_info(f"Sending command: {operation}")
        
        sock = None
        try:
            # Create and configure socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout or SOCKET_TIMEOUT)
            sock.connect((self.host, self.port))
            
            # Send command
            command_bytes = json.dumps(command).encode('utf-8')
            sock.sendall(command_bytes)
            
            # Receive response
            response_data = self._receive_response(sock)
            response: Dict[str, Any] = json.loads(response_data.decode('utf-8'))
            
            log_info(f"Command {operation} completed with status: {response.get('status', 'unknown')}")
            return response
            
        except socket.timeout:
            log_error(f"Timeout waiting for response from Cadwork")
            raise TimeoutError("Timeout waiting for Cadwork response")
            
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            log_error(f"Connection error: {e}")
            raise ConnectionError(f"Connection to Cadwork lost: {e}")
            
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON response: {e}")
            raise ValueError(f"Invalid response format: {e}")
            
        except Exception as e:
            log_error(f"Unexpected error: {e}")
            raise RuntimeError(f"Communication error: {e}")
            
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
    
    def _receive_response(self, sock: socket.socket) -> bytes:
        """Receive the whole response: the bridge closes the connection after it.

        Reads until EOF and leaves parsing to the caller, once. Parsing after
        every chunk instead made a 4 MB response take 30 s. The socket timeout
        still applies to each recv.
        """
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)

        if not chunks:
            raise ConnectionAbortedError("No data received from Cadwork")

        return b''.join(chunks)
    
    def test_connection(self) -> bool:
        """Test if connection to Cadwork works"""
        try:
            response = self.send_command("ping")
            return response.get("status") == "ok"
        except Exception:
            return False

# Global connection instance
_connection: Optional[CadworkConnection] = None

def get_connection() -> CadworkConnection:
    """Get global connection instance"""
    global _connection
    if _connection is None:
        raise ConnectionError("Cadwork connection not initialized")
    return _connection

def initialize_connection(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> CadworkConnection:
    """Initialize global connection"""
    global _connection
    _connection = CadworkConnection(host, port)
    return _connection
