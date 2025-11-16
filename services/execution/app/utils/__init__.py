"""
Utilities for Execution Service
"""
from .cloudwatch_logger import log_to_cloudwatch, setup_cloudwatch_logging

__all__ = ['log_to_cloudwatch', 'setup_cloudwatch_logging']
