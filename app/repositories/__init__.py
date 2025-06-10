# app/repositories/__init__.py
# Import JSON repositories (existing)
try:
    from .json_repository import JSONDetectionRepository, JSONEnhancementRepository
except ImportError:
    # If not available, create placeholder classes for type checking
    class JSONDetectionRepository: pass
    class JSONEnhancementRepository: pass

# Import SQL repositories
from .sql_repository import SQLiteDetectionRepository, SQLiteEnhancementRepository, SQLiteVideoRepository

__all__ = [
    'JSONDetectionRepository',
    'JSONEnhancementRepository',
    'SQLiteDetectionRepository', 
    'SQLiteEnhancementRepository',
    'SQLiteVideoRepository'
]