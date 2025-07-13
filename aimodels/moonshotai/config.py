from core.exceptions import CustomErrorMessage
import importlib
import logging
class ModelParams:
    def __init__(self):
        # Model provider thread
        self._model_provider_thread = "moonshotai"

        self._genai_params = {
            "temperature": 0.7
        }

    # internal function to fetch tool
    async def _fetch_tool(self, db_conn) -> dict:
        # Tools
        _tool_selection_name = await db_conn.get_tool_config(guild_id=self._guild_id)
        try:
            if _tool_selection_name is None:
                _Tool = None
            else:
                _Tool = importlib.import_module(f"tools.{_tool_selection_name}").Tool(
                    method_send=self._discord_method_send,
                    discord_ctx=self._discord_ctx,
                    discord_bot=self._discord_bot
                )
        except ModuleNotFoundError as e:
            logging.error("I cannot import the tool because the module is not found: %s", e)
            raise CustomErrorMessage("⚠️ The feature you've chosen is not available at the moment, please choose another tool using `/feature` command or try again later")

        # Check if tool is code execution
        if _Tool:
            if _tool_selection_name == "CodeExecution":
                raise CustomErrorMessage("⚠️ Code execution is not supported in Moonshot AI model, please use other models that support it.")
            else:
                # Check if the tool schema is a list or not
                # Since a list of tools could be a collection of tools, sometimes it's just a single tool
                # But depends on the tool implementation
                if type(_Tool.tool_schema_openai) == list:
                    _tool_schema = _Tool.tool_schema_openai
                else:
                    _tool_schema = _Tool.tool_schema_openai
        else:
            _tool_schema = None

        return {
            "tool_schema": _tool_schema,
            "tool_human_name": _Tool.tool_human_name if _Tool else None,
            "tool_object": _Tool
        }