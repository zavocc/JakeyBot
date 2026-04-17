from tools.builtin._base import BuiltInToolDiscordStateBase
import discord

# Built-in tools regardless of tool selection unless Disabled
class BuiltInTool(BuiltInToolDiscordStateBase):
    @staticmethod
    def _parse_embed_color(color: str | None) -> discord.Color | None:
        if not color:
            return None

        _raw = color.strip().lower()
        if _raw.startswith("#"):
            _raw = _raw[1:]
        elif _raw.startswith("0x"):
            _raw = _raw[2:]

        try:
            _value = int(_raw, 16)
        except Exception:
            return None

        if _value < 0 or _value > 0xFFFFFF:
            return None

        return discord.Color(_value)

    async def tool_discord_embed_tool(
        self,
        title: str,
        description: str = None,
        color: str = None,
        fields: list[dict] = None,
        footer: dict = None,
        author: dict = None,
        thumbnail_url: str = None,
        image_url: str = None,
    ):
        _embed_color = self._parse_embed_color(color)
        _embed = discord.Embed(
            title=title[:256],
            description=description[:4096] if description else None,
            color=_embed_color,
        )

        if footer and footer.get("text"):
            _embed.set_footer(
                text=footer["text"][:2048],
                icon_url=footer.get("icon_url"),
            )

        if author and author.get("name"):
            _embed.set_author(
                name=author["name"][:256],
                url=author.get("url"),
                icon_url=author.get("icon_url"),
            )

        if thumbnail_url:
            _embed.set_thumbnail(url=thumbnail_url)

        if image_url:
            _embed.set_image(url=image_url)

        if fields:
            _field_count = 0
            for _field in fields:
                if _field_count >= 25:
                    break

                _name = _field.get("name")
                _value = _field.get("value")
                if not _name or not _value:
                    continue

                _embed.add_field(
                    name=str(_name)[:256],
                    value=str(_value)[:1024],
                    inline=bool(_field.get("inline", False)),
                )
                _field_count += 1

        await self.discord_message.channel.send(embed=_embed)
        return "Embed sent successfully"
