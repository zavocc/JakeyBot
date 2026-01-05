from typing import List, Literal
from pydantic import BaseModel, Field

class TextTaskModelProps(BaseModel):
    model_id: str = Field(..., description="Model identifier")
    sdk: str = Field(..., description="Model SDK which will be used to call the model")
    client_name: str = Field(default=None, description="SDK Instance name from discord.Bot subclass")
    default: bool = Field(default=False, description="Set the model as default text generation model")
    model_human_name: str = Field(default=None, description="Human-friendly model name")
    model_specific_params: dict = Field(default={"temperature": 1}, description="Model specific parameters")

class ModelProps(BaseModel):
    # model_alias is used as a unique identifier to the model for fetching model from history and parse it
    model_alias: str = Field(..., description="Model alias")
    model_human_name: str = Field(..., description="Human-friendly model name")
    model_description: str = Field(..., description="Model description")
    model_id: str = Field(..., description="Model identifier")
    sdk: str = Field(..., description="Model SDK which will be used to call the model")
    additional_params: dict = Field(default={}, description="Additional config parameters for the model")
    client_name: str = Field(default=None, description="SDK Instance name from discord.Bot subclass")
    default: bool = Field(default=False, description="Set the model as default chat model")
    enable_tools: bool = Field(default=True, description="Enable tools")
    enable_files: bool = Field(default=True, description="Enable files (e.g. Images)")
    enable_threads: bool = Field(default=True, description="Enable chat history")
    enable_system_instruction: bool = Field(default=True, description="Enable system instructions")
    thread_name: str = Field(default=None, description="Use the same SDK but use a different thread name for chat separation")
    or_beta_file_uploads: bool = Field(default=False, description="Enable PDF and video uploads using LiteLLM/OpenAI SDK for OpenAI and OpenRouter-served models")

class ModelParamsOpenAIDefaults(BaseModel):
    temperature: int = Field(default=1)
    max_tokens: int = Field(default=16000)

class GeminiSafetySetting(BaseModel):
    category: Literal[
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT"
    ]
    threshold: Literal["BLOCK_MEDIUM_AND_ABOVE"]

class ModelParamsGeminiDefaults(BaseModel):
    candidate_count: int = Field(default=1)
    max_output_tokens: int = Field(default=8192)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.95)
    top_k: int = Field(default=40)
    safety_settings: List[GeminiSafetySetting] = Field(
        default=[
            GeminiSafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
            GeminiSafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_MEDIUM_AND_ABOVE"),
            GeminiSafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
            GeminiSafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
        ]
    )