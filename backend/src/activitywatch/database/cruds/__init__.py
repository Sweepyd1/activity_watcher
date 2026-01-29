from ..db_manager import DatabaseManager

from .users import UsersCRUD
from .devices import DevicesCRUD
from .tokens import ApiTokensCRUD
from .activity import ActivityEventsCRUD
from .sync import SyncSessionsCRUD
from .statistics import StatisticsCRUD
class CommonCRUD:
    __slots__ = ("db_manager", "users", "devices", "tokens", "activity", "sync", "statistics")

    users: UsersCRUD
    devices: DevicesCRUD
    tokens: ApiTokensCRUD
    activity: ActivityEventsCRUD
    sync: SyncSessionsCRUD
    statistics: StatisticsCRUD

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.users = UsersCRUD(self.db_manager, self)
        self.devices = DevicesCRUD(self.db_manager, self)
        self.tokens = ApiTokensCRUD(self.db_manager, self)
        self.activity = ActivityEventsCRUD(self.db_manager, self)
        self.sync = SyncSessionsCRUD(self.db_manager, self)
        self.statistics = StatisticsCRUD(self.db_manager, self)
