from typing import Dict, Any, Optional, List
import logging
from polyad.utils.logging import get_logger

class ErrorHandler:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.error_handlers = {
            'api': self._handle_api_error,
            'system': self._handle_system_error,
            'network': self._handle_network_error,
            'validation': self._handle_validation_error
        }

    def add_handler(self, error_type: str, handler: callable):
        """Add a custom error handler"""
        self.error_handlers[error_type] = handler

    def _handle_api_error(self, error: Exception, context: Dict) -> Dict:
        """Handle API-related errors"""
        error_info = {
            'type': 'api_error',
            'message': str(error),
            'service': context.get('service'),
            'endpoint': context.get('endpoint'),
            'status_code': context.get('status_code')
        }
        self.logger.error(f"API Error: {error_info}")
        return error_info

    def _handle_system_error(self, error: Exception, context: Dict) -> Dict:
        """Handle system-related errors"""
        error_info = {
            'type': 'system_error',
            'message': str(error),
            'component': context.get('component'),
            'operation': context.get('operation')
        }
        self.logger.error(f"System Error: {error_info}")
        return error_info

    def _handle_network_error(self, error: Exception, context: Dict) -> Dict:
        """Handle network-related errors"""
        error_info = {
            'type': 'network_error',
            'message': str(error),
            'host': context.get('host'),
            'port': context.get('port')
        }
        self.logger.error(f"Network Error: {error_info}")
        return error_info

    def _handle_validation_error(self, error: Exception, context: Dict) -> Dict:
        """Handle validation errors"""
        error_info = {
            'type': 'validation_error',
            'message': str(error),
            'field': context.get('field'),
            'value': context.get('value')
        }
        self.logger.error(f"Validation Error: {error_info}")
        return error_info

    def handle_error(self, error: Exception, context: Dict) -> Dict:
        """Handle an error using the appropriate handler"""
        error_type = context.get('error_type', 'system')
        handler = self.error_handlers.get(error_type, self._handle_system_error)
        return handler(error, context)

def validate_input(data: Dict, schema: Dict) -> bool:
    """Validate input data against a schema"""
    for field, rules in schema.items():
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        
        value = data[field]
        for rule in rules:
            if rule == 'required' and not value:
                raise ValueError(f"Field '{field}' is required")
            elif rule == 'string' and not isinstance(value, str):
                raise ValueError(f"Field '{field}' must be a string")
            elif rule == 'number' and not isinstance(value, (int, float)):
                raise ValueError(f"Field '{field}' must be a number")
            elif rule == 'list' and not isinstance(value, list):
                raise ValueError(f"Field '{field}' must be a list")

    return True
