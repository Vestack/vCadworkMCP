"""
Utility Controller for the vCadworkMCP server
Manages display refresh, output functions and system utilities
"""
from typing import Dict, Any
from .base_controller import BaseController

class UtilityController(BaseController):
    """Controller for utility operations"""
    
    def __init__(self) -> None:
        super().__init__("UtilityController")
    
    async def disable_auto_display_refresh(self) -> Dict[str, Any]:
        """
        Disable automatic display refresh
        
        Important for performance during many consecutive operations.
        Should be re-enabled after operations with enable_auto_display_refresh().
        
        Returns:
            dict: Status of operation
        """
        try:
            # Send command
            return self.send_command("disable_auto_display_refresh", {})
            
        except Exception as e:
            return {"status": "error", "message": f"disable_auto_display_refresh failed: {e}"}
    
    async def enable_auto_display_refresh(self) -> Dict[str, Any]:
        """
        Re-enable automatic display refresh
        
        Should be called after batch operations to reactivate normal
        display updating.
        
        Returns:
            dict: Status of operation
        """
        try:
            # Send command  
            return self.send_command("enable_auto_display_refresh", {})
            
        except Exception as e:
            return {"status": "error", "message": f"enable_auto_display_refresh failed: {e}"}
    
    async def print_error(self, message: str) -> Dict[str, Any]:
        """
        Display error message in Cadwork
        
        Args:
            message: Error message to display in Cadwork
        
        Returns:
            dict: Status of operation
        """
        try:
            # Validation
            if not isinstance(message, str) or not message.strip():
                return {"status": "error", "message": "message must be a non-empty string"}
            
            # Send command
            return self.send_command("print_error", {
                "message": message.strip()
            })
            
        except Exception as e:
            return {"status": "error", "message": f"print_error failed: {e}"}
    
    async def print_warning(self, message: str) -> Dict[str, Any]:
        """
        Display warning message in Cadwork
        
        Args:
            message: Warning message to display in Cadwork
        
        Returns:
            dict: Status of operation
        """
        try:
            # Validation
            if not isinstance(message, str) or not message.strip():
                return {"status": "error", "message": "message must be a non-empty string"}
            
            # Send command
            return self.send_command("print_warning", {
                "message": message.strip()
            })
            
        except Exception as e:
            return {"status": "error", "message": f"print_warning failed: {e}"}
    
    async def get_3d_file_path(self) -> Dict[str, Any]:
        """
        Get path of currently opened 3D file
        
        Returns:
            dict: File path and file information
        """
        try:
            # Send command
            return self.send_command("get_3d_file_path", {})
            
        except Exception as e:
            return {"status": "error", "message": f"get_3d_file_path failed: {e}"}
    
    async def get_project_data(self) -> Dict[str, Any]:
        """
        Get general project data
        
        Returns:
            dict: Project information like name, path, etc.
        """
        try:
            # Send command
            return self.send_command("get_project_data", {})
            
        except Exception as e:
            return {"status": "error", "message": f"get_project_data failed: {e}"}
    
    async def get_cadwork_version_info(self) -> Dict[str, Any]:
        """
        Get Cadwork version information
        
        Returns:
            dict: Version information of Cadwork installation
        """
        try:
            # Send command
            return self.send_command("get_cadwork_version_info", {})
            
        except Exception as e:
            return {"status": "error", "message": f"get_cadwork_version_info failed: {e}"}
