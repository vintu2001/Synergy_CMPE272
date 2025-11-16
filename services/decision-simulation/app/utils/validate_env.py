"""
Environment Configuration Validator
Validates that all required RAG environment variables are loaded correctly.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv


class EnvValidator:
    """Validates environment configuration for RAG setup."""
    
    # Required RAG environment variables with their expected types
    REQUIRED_VARS = {
        "RAG_ENABLED": bool,
        "EMBEDDING_MODEL": str,
        "EMBEDDING_DIMENSION": int,
        "VECTOR_STORE_TYPE": str,
        "VECTOR_STORE_PATH": str,
        "KB_BASE_PATH": str,
        "RAG_TOP_K": int,
        "RAG_SIMILARITY_THRESHOLD": float,
    }
    
    OPTIONAL_VARS = {
        "EMBEDDING_DEVICE": str,
        "CHROMA_COLLECTION_NAME": str,
        "RAG_MAX_TOKENS_PER_CHUNK": int,
        "RAG_CHUNK_OVERLAP": int,
        "RAG_CONTEXT_WINDOW": int,
        "RAG_CONTEXT_TEMPLATE": str,
        "RAG_CACHE_ENABLED": bool,
        "RAG_LOG_RETRIEVALS": bool,
    }
    
    def __init__(self, env_file: str = ".env"):
        """Initialize validator and load environment file."""
        self.env_file = Path(env_file)
        if self.env_file.exists():
            load_dotenv(self.env_file)
            print(f"✅ Loaded environment file: {self.env_file}")
        else:
            print(f"⚠️  Environment file not found: {self.env_file}")
    
    def _convert_value(self, value: str, expected_type: type) -> any:
        """Convert string value to expected type."""
        if expected_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        return value
    
    def validate_required(self) -> Tuple[bool, List[str]]:
        """Validate all required environment variables."""
        missing = []
        invalid = []
        
        for var_name, expected_type in self.REQUIRED_VARS.items():
            value = os.getenv(var_name)
            
            if value is None:
                missing.append(var_name)
                continue
            
            try:
                self._convert_value(value, expected_type)
            except (ValueError, TypeError) as e:
                invalid.append(f"{var_name} (expected {expected_type.__name__}, got '{value}')")
        
        success = len(missing) == 0 and len(invalid) == 0
        errors = missing + invalid
        
        return success, errors
    
    def validate_paths(self) -> Tuple[bool, List[str]]:
        """Validate that configured paths exist."""
        errors = []
        
        # Check KB base path
        kb_base = os.getenv("KB_BASE_PATH", "./kb")
        kb_path = Path(kb_base)
        if not kb_path.exists():
            errors.append(f"KB_BASE_PATH does not exist: {kb_path}")
        
        # Check vector store path (parent directory should exist)
        vector_store = os.getenv("VECTOR_STORE_PATH", "./vector_stores/chroma_db")
        vector_path = Path(vector_store).parent
        if not vector_path.exists():
            errors.append(f"Vector store parent directory does not exist: {vector_path}")
        
        return len(errors) == 0, errors
    
    def validate_ranges(self) -> Tuple[bool, List[str]]:
        """Validate that numeric values are in acceptable ranges."""
        errors = []
        
        # Similarity threshold should be between 0 and 1
        threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
        if not 0.0 <= threshold <= 1.0:
            errors.append(f"RAG_SIMILARITY_THRESHOLD must be 0.0-1.0, got {threshold}")
        
        # Top K should be positive
        top_k = int(os.getenv("RAG_TOP_K", "5"))
        if top_k <= 0:
            errors.append(f"RAG_TOP_K must be positive, got {top_k}")
        
        # Embedding dimension should be reasonable (typical: 384, 768, 1536)
        embed_dim = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        if embed_dim < 100 or embed_dim > 2000:
            errors.append(f"EMBEDDING_DIMENSION seems unusual: {embed_dim}")
        
        return len(errors) == 0, errors
    
    def get_config_summary(self) -> Dict[str, any]:
        """Get summary of current RAG configuration."""
        config = {}
        
        for var_name, expected_type in {**self.REQUIRED_VARS, **self.OPTIONAL_VARS}.items():
            value = os.getenv(var_name)
            if value is not None:
                try:
                    config[var_name] = self._convert_value(value, expected_type)
                except:
                    config[var_name] = value
        
        return config
    
    def validate_all(self) -> bool:
        """Run all validations and print results."""
        print("\n" + "="*60)
        print("RAG Environment Configuration Validation")
        print("="*60 + "\n")
        
        all_valid = True
        
        # Check required variables
        print("1. Checking required variables...")
        success, errors = self.validate_required()
        if success:
            print("   ✅ All required variables present and valid")
        else:
            print("   ❌ Issues with required variables:")
            for error in errors:
                print(f"      - {error}")
            all_valid = False
        
        # Check paths
        print("\n2. Checking paths...")
        success, errors = self.validate_paths()
        if success:
            print("   ✅ All paths exist")
        else:
            print("   ⚠️  Path issues:")
            for error in errors:
                print(f"      - {error}")
            all_valid = False
        
        # Check value ranges
        print("\n3. Checking value ranges...")
        success, errors = self.validate_ranges()
        if success:
            print("   ✅ All values in acceptable ranges")
        else:
            print("   ⚠️  Range issues:")
            for error in errors:
                print(f"      - {error}")
            all_valid = False
        
        # Print configuration summary
        print("\n4. Current RAG Configuration:")
        config = self.get_config_summary()
        for key, value in sorted(config.items()):
            print(f"   {key}: {value}")
        
        print("\n" + "="*60)
        if all_valid:
            print("✅ Environment configuration is VALID")
        else:
            print("❌ Environment configuration has ISSUES")
        print("="*60 + "\n")
        
        return all_valid


if __name__ == "__main__":
    validator = EnvValidator()
    is_valid = validator.validate_all()
    exit(0 if is_valid else 1)
