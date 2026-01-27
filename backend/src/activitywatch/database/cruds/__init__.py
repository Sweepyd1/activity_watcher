from ..db_manager import DatabaseManager

from .users import UsersCRUD

class CommonCRUD:
    __slots__ = (
        "db_manager",
        "users",

    )

    users: UsersCRUD

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.users = UsersCRUD(self.db_manager, self)

