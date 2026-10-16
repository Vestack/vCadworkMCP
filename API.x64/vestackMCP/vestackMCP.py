"""
vestackMCP plugin (vCadworkMCP bridge launcher)

This file lives in the Cadwork user profile, away from the repository, so it has
to be told where the repository is. See resolve_mcp_home() for how it decides.

Launching the plugin (a click in Cadwork, or `ci_start.exe ... /PLUGIN=vestackMCP`)
starts the bridge with no window when nothing listens on port 53002, and opens
the status window when a bridge already listens. See launch().
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

# Cadwork imports
import utility_controller as uc

# Fallback for installations that follow the original instructions.
LEGACY_HOME = r'C:\cadworkMCP'

# Global variables
bridge_running = False

def resolve_mcp_home() -> str:
    """Locate the vCadworkMCP checkout.

    In order:
      1. the CADWORK_MCP_HOME environment variable,
      2. a file named mcp_home.txt next to this plugin, holding the path,
      3. C:\\cadworkMCP, the original hard-coded location.

    The first candidate that contains cadwork_bridge.py wins, so a stale
    environment variable does not shadow a working mcp_home.txt.
    """
    candidates = []

    from_env = os.environ.get('CADWORK_MCP_HOME', '').strip()
    if from_env:
        candidates.append(from_env)

    pointer = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mcp_home.txt')
    if os.path.isfile(pointer):
        try:
            with open(pointer, 'r', encoding='utf-8') as handle:
                for line in handle:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        candidates.append(line)
                        break
        except OSError as exc:
            uc.print_to_console(f"Could not read {pointer}: {exc}")

    candidates.append(LEGACY_HOME)

    for candidate in candidates:
        if os.path.isfile(os.path.join(candidate, 'cadwork_bridge.py')):
            return candidate

    raise FileNotFoundError(
        "vCadworkMCP checkout not found. Looked in: "
        + ", ".join(candidates)
        + ". Set CADWORK_MCP_HOME, or put the path in mcp_home.txt next to "
        + "vestackMCP.py."
    )

def is_listening(port: int = 53002, attempts: int = 5) -> bool:
    """Whether something accepts connections on the bridge port.

    cadwork_bridge.main() starts a daemon thread and returns whether or not the
    bind succeeded, so the only honest way to report "Running" is to connect.
    """
    import socket
    import time

    for attempt in range(attempts):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                return True
        except OSError:
            if attempt < attempts - 1:
                time.sleep(0.2)
    return False

def start_bridge() -> bool:
    """Start the MCP bridge socket server inside Cadwork."""
    global bridge_running

    if bridge_running:
        return False

    try:
        home = resolve_mcp_home()
        if home not in sys.path:
            sys.path.insert(0, home)

        # Imported here, not at module level: the path is only known now.
        import cadwork_bridge

        cadwork_bridge.main()

        bridge_running = is_listening()
        if bridge_running:
            uc.print_to_console(f"vestackMCP: bridge listening on 53002, from {home}")
        else:
            uc.print_to_console(
                "vestackMCP: bridge did not come up on port 53002. Another bridge or "
                "Cadwork instance may already hold it; restart Cadwork.")
        return bridge_running

    except Exception as e:
        uc.print_to_console(f"vestackMCP: failed to start bridge: {e}")
        return False

def stop_bridge() -> None:
    """Mark the bridge as stopped.

    The socket server runs in a daemon thread that this plugin has no handle on,
    so the port stays bound until Cadwork exits. Restart Cadwork to release it or
    to reload changed bridge code.
    """
    global bridge_running

    bridge_running = False
    uc.print_to_console(
        "vestackMCP: bridge marked as stopped. The socket stays open until Cadwork exits.")

class BridgeGUI:
    """Simple GUI for bridge control"""
    
    def __init__(self) -> None:
        self.root: Optional[tk.Tk] = None
        self.status_label: Optional[ttk.Label] = None
        self.start_btn: Optional[ttk.Button] = None
        self.stop_btn: Optional[ttk.Button] = None
    
    def create_gui(self) -> None:
        """Create the GUI"""
        self.root = tk.Tk()
        self.root.title("vestackMCP")
        self.root.geometry("380x260")
        self.root.resizable(False, False)
        
        # Title
        title_label = ttk.Label(self.root, text="vestackMCP", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=15)
        
        # Status
        self.status_label = ttk.Label(self.root, text="Status: Stopped", 
                                     font=("Arial", 11), foreground="red")
        self.status_label.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="Start Bridge", 
                                   command=self.on_start, width=12)
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Bridge", 
                                  command=self.on_stop, width=12, state="disabled")
        self.stop_btn.pack(side="left", padx=10)
        
        # Info: the port, and which checkout the bridge will run from
        try:
            location = resolve_mcp_home()
        except Exception as exc:
            location = f"NOT FOUND - {exc}"
        info_label = ttk.Label(self.root, text=f"Port: 53002\n{location}",
                               font=("Arial", 9), foreground="gray",
                               wraplength=330, justify="center")
        info_label.pack(pady=5)
        
        # Center window
        self.center_window()
    
    def center_window(self) -> None:
        """Center window on screen"""
        if self.root is None:
            return
            
        self.root.update_idletasks()
        width, height = 380, 260
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_start(self) -> None:
        """Handle start button"""
        success = start_bridge()
        if success:
            messagebox.showinfo("Bridge", "Bridge listening on port 53002.")
        else:
            messagebox.showerror("Error", "Bridge did not start. See the Cadwork console for the reason.")
        self.update_status()
    
    def on_stop(self) -> None:
        """Handle stop button"""
        stop_bridge()
        messagebox.showinfo("Bridge", "Marked as stopped. The socket stays open until Cadwork exits.")
        self.update_status()
    
    def update_status(self) -> None:
        """Update status display"""
        if self.status_label is None or self.start_btn is None or self.stop_btn is None:
            return
            
        if bridge_running:
            self.status_label.config(text="Status: Running", foreground="green")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            self.status_label.config(text="Status: Stopped", foreground="red")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
    
    def show(self) -> None:
        """Show the GUI"""
        self.create_gui()
        self.update_status()
        if self.root is not None:
            self.root.mainloop()

def launch(listening: Callable[[], bool],
           start: Callable[[], bool],
           show_window: Callable[[], None]) -> str:
    """Decide what a click on the plugin (or the /PLUGIN= shortcut) does.

    Cadwork may run this script afresh on every click, so module globals say
    nothing about an earlier click: only the port does.

    Returns "started" or "failed" when nothing listened and the bridge was
    started with no window, and "window" when a bridge already listens and the
    status window was opened instead.
    """
    if listening():
        show_window()
        return "window"
    return "started" if start() else "failed"

def show_status_window() -> None:
    """Open the Start/Stop window for a bridge that already listens."""
    global bridge_running

    # The port answered, whatever this process remembers.
    bridge_running = True
    gui = BridgeGUI()
    gui.show()

def main() -> None:
    """Main plugin entry point"""
    try:
        launch(lambda: is_listening(attempts=1), start_bridge, show_status_window)
    except Exception as e:
        uc.print_to_console(f"vestackMCP: plugin error: {e}")
        messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    main()
