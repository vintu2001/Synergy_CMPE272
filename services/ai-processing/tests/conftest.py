"""
Pytest configuration and fixtures for AI Processing Service tests.
Mocks numpy/pandas/xgboost to avoid Windows access violations.
"""
import sys
from unittest.mock import MagicMock

# Mock problematic libraries BEFORE any other imports
# This prevents NumPy 2.0 access violations on Windows
sys.modules['numpy'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['xgboost'] = MagicMock()
sys.modules['joblib'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.ensemble'] = MagicMock()
