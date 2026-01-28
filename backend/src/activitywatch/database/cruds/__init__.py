from ..db_manager import DatabaseManager

from .users import UsersCRUD
from .devices import DevicesCRUD
from .tokens import ApiTokensCRUD


class CommonCRUD:
    __slots__ = ("db_manager", "users", "devices", "tokens")

    users: UsersCRUD

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.users = UsersCRUD(self.db_manager, self)
        self.devices = DevicesCRUD(self.db_manager, self)
        self.tokens = ApiTokensCRUD(self.db_manager, self)
