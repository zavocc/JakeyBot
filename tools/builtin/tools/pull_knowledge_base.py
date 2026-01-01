from tools.builtin._base import BuiltInToolDiscordStateBase
from typing import Literal
import aiofiles

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_pull_knowledge_base(self, kb_name: Literal["utilities_slash_commands", "chat_mgmt_slash_commands"]):
        async with aiofiles.open(f"data/kbdocs/{kb_name}.md", mode="r") as f:
            _kb_contents = await f.read()
        return _kb_contents