import os
from datetime import datetime, timezone

def now() -> datetime:
    """
    Trả về thời điểm hiện tại.
    Nếu biến môi trường CSV_GIO được đặt (ISO 8601), dùng giá trị đó để hỗ trợ mock time khi test.
    """
    gio_mock = os.environ.get("CSV_GIO")
    if gio_mock:
        return datetime.fromisoformat(gio_mock)
    return datetime.now(timezone.utc)
