from pydantic import BaseModel, Field, field_validator


class StorageConfig(BaseModel):
    name: str = Field(..., description="Storage backend plugin module name")
    enabled: bool = Field(default=False, description="If disabled, it will use Discord CDN instead but not recommended due to TTL.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        _normalized = value.strip().lower()
        if not _normalized:
            raise ValueError("Storage plugin name cannot be empty")
        return _normalized


class PluginsConfig(BaseModel):
    storage: StorageConfig