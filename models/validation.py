from enum import Enum
from pydantic import BaseModel, Field

class ReasoningType(Enum):
    SIMPLE = "simple" # OpenAI and Grok models that accepts reasoning values to "minimal", "low", "medium", "high"
    ADVANCED = "advanced" # int-based from 128-32000

class ModelProps(BaseModel):
    model_id: str = Field(..., description="Model identifier")
    has_reasoning: bool = Field(..., description="Determine if the model is optimized for reasoning")
    enable_tools: bool = Field(default=True, description="Enable tools")
    enable_files: bool = Field(default=True, description="Enable files (e.g. Images)")
    enable_threads: bool = Field(default=True, description="Enable chat history")
    reasoning_type: ReasoningType = Field(default=ReasoningType.SIMPLE, description="Reasoning type")

class ModelParamsOpenAIDefaults(BaseModel):
    temperature: int = Field(default=1)
    max_output_tokens: int = Field(default=8192)
