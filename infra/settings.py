from pydantic import BaseModel, Field
from typing import List

class InfraConfig(BaseModel):
    storage_account_name: str = Field(..., description="Azure Storage account name")
    container_names: List[str] = Field(..., description="Blob container names")
    resource_group_name: str = Field("comfycode-rg", description="Resource group name")
    location: str = Field("eastus", description="Azure region")
