from tools.builtin._base import BuiltInToolDiscordStateBase
from zoneinfo import ZoneInfo
import datetime

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_fetch_date_time(self, timezone: str = "UTC") -> str:
        # Return current time in the requested timezone, defaulting to UTC.
        try:
            _tzinfo = ZoneInfo(timezone)
        except Exception:
            _tzinfo = ZoneInfo("UTC")

        _now = datetime.datetime.now(_tzinfo)
        return {
            "guidelines": "NOTE: it is formatted as YYYY-MM-DD for date and HH:MM:SS for time.",
            "timezone": _tzinfo.key,
            "date": _now.strftime("%Y-%m-%d"),
            "time": _now.strftime("%H:%M:%S"),
            "iso": _now.isoformat()
        }