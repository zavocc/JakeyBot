from pydantic import BaseModel, Field

class ModelProps(BaseModel):
    # model_alias is used as a unique identifier to the model for fetching model from history and parse it
    model_alias: str = Field(..., description="Model alias")
    model_human_name: str = Field(..., description="Human-friendly model name")
    model_description: str = Field(..., description="Model description")
    model_id: str = Field(..., description="Model identifier")
    sdk: str = Field(..., description="Model SDK which will be used to call the model")
    has_reasoning: bool = Field(..., description="Determine if the model is optimized for reasoning")
    thread_name: str = Field(default=None, description="Use the same SDK but use a different thread name for chat separation")
    enable_tools: bool = Field(default=True, description="Enable tools")
    enable_files: bool = Field(default=True, description="Enable files (e.g. Images)")
    enable_threads: bool = Field(default=True, description="Enable chat history")
    reasoning_type: str = Field(default="openai", description="Reasoning type")
    client_name: str = Field(default=None, description="SDK Instance name from discord.Bot subclass")

class ModelParamsOpenAIDefaults(BaseModel):
    temperature: int = Field(default=1)
    max_tokens: int = Field(default=8192)
