from enum import Enum
class RequestStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    CLOSED = "Closed"
