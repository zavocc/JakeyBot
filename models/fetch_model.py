"""
Rather than handling and parsing syntax in generative_chat.py

Relevant snippet:
"""
#############################################
"""
# Set default model
_model = await self.DBConn.get_default_model(guild_id=guild_id)
if _model is None:
    logging.info("No default model found, using default model")
    _model = await self.DBConn.get_default_model(guild_id=guild_id)

_model_provider = _model.split("::")[0]
_model_name = _model.split("::")[-1]
if "/model:" in prompt.content:
    _modelUsed = await prompt.channel.send(f"🔍 Using specific model")
    async for _model_selection in ModelsList.get_models_list_async():
        _model_provider = _model_selection.split("::")[0]
        _model_name = _model_selection.split("::")[-1]

        # In this regex, we are using \s at the end since when using gpt-4o-mini, it will match with gpt-4o at first
        # So, we are using \s|$ to match the end of the string and the suffix gets matched or if it's placed at the end of the string
        if re.search(rf"\/model:{_model_name}(\s|$)", prompt.content):
            await _modelUsed.edit(content=f"🔍 Using model: **{_model_name}**")
            break
    else:
        _model_provider = _model.split("::")[0]
        _model_name = _model.split("::")[-1]
        await _modelUsed.edit(content=f"🔍 Using model: **{_model_name}**")
"""
#############################################
"""
We just create a method here called fetch_provider_caller method
"""