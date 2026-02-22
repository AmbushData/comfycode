import pulumi
import pulumi_azure_native as azure
from pydantic import BaseModel, Field
from typing import List

# Pulumi config contract
class InfraConfig(BaseModel):
    storage_account_name: str = Field(..., description="Azure Storage account name")
    container_names: List[str] = Field(..., description="Blob container names")
    resource_group_name: str = Field("comfycode-rg", description="Resource group name")
    location: str = Field("eastus", description="Azure region")

config = pulumi.Config()
settings = InfraConfig(
    storage_account_name=config.require("storageAccountName"),
    container_names=config.require_object("containerNames"),
    resource_group_name=config.get("resourceGroupName") or "comfycode-rg",
    location=config.get("location") or "eastus",
)

# Resource group
resource_group = azure.resources.ResourceGroup(
    settings.resource_group_name,
    resource_group_name=settings.resource_group_name,
    location=settings.location,
)

# Storage account
storage_account = azure.storage.StorageAccount(
    settings.storage_account_name,
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=azure.storage.SkuArgs(name="Standard_LRS"),
    kind="StorageV2",
)

# Blob containers
containers = []
for cname in settings.container_names:
    container = azure.storage.BlobContainer(
        f"{settings.storage_account_name}-{cname}",
        account_name=storage_account.name,
        resource_group_name=resource_group.name,
        public_access="None",
        container_name=cname,
    )
    containers.append(container)

# Export outputs
pulumi.export("storageAccountName", storage_account.name)
pulumi.export("containerNames", [c.name for c in containers])
pulumi.export("resourceGroupName", resource_group.name)
pulumi.export("location", resource_group.location)
