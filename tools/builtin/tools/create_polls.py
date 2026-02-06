from tools.builtin._base import BuiltInToolDiscordStateBase
from typing import Literal
import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    async def tool_create_polls(self, question: str, multi_select: bool, choices: dict, poll_duration_hours: int = 24):
        # Create, send, and parse poll
        _poll = discord.Poll(
            question=question,
            allow_multiselect=multi_select,
            duration=poll_duration_hours
        )

        # Add answers and must limit upto 10
        _answer_count_limit = 0
        for _answer in choices:
            if _answer_count_limit >= 10:
                break

            _poll.add_answer(text=_answer["text"][:55], emoji=_answer.get("emoji", None))
            _answer_count_limit += 1

        # Send poll
        await self.discord_message.channel.send(poll=_poll)

        return "Poll created successfully."