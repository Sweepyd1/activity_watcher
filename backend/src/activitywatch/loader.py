from src.activitywatch.config import cfg
from src.activitywatch.database.cruds import CommonCRUD
from src.activitywatch.database.db_manager import DatabaseManager


db_manager = DatabaseManager(cfg.database.async_url)
db = CommonCRUD(db_manager)




