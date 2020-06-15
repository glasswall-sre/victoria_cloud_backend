"""Pulumi code to deploy Victoria cloud backend.

Deploys:
    - A Resource Group for all the Victoria stuff to reside in
    - A Storage Account and Blob Container to store remote configs
    - A Key Vault and Key to perform envelope encryption
    - Access policies on the Key Vault to give users encrypt/decrypt perms

It's essentially the shell script deployment part of the Victoria User Guide
(https://sre.glasswallsolutions.com/victoria/user-guide.html#azure) converted
to Pulumi.

Author:
    Sam Gibson <sgibson@glasswallsolutions.com>
"""
import hashlib
from typing import List

import pulumi
from pulumi_azure import core, storage, keyvault

config = pulumi.Config()
tags = config.require_object("tags")

# deploy the resource group
resource_group = core.ResourceGroup("rg-victoria", tags=tags)
pulumi.export("rg_name", resource_group.name)

# now, the storage account and container
storage_account = storage.Account(
    "stvictoria",
    resource_group_name=resource_group.name,
    account_replication_type="LRS",
    account_tier="Standard",
    account_kind="StorageV2",
    tags=tags,
    opts=pulumi.ResourceOptions(parent=resource_group))
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("storage_connection_string",
              storage_account.primary_connection_string)

storage_container = storage.Container(
    "victoria",
    storage_account_name=storage_account.name,
    container_access_type="private",
    opts=pulumi.ResourceOptions(parent=storage_account))
pulumi.export("container_name", storage_container.name)

# now, the key vault
tenant_id = config.require_secret("tenantId")
key_vault = keyvault.KeyVault(
    "kv-victoria",
    resource_group_name=resource_group.name,
    sku_name="standard",
    tenant_id=tenant_id,
    tags=tags,
    opts=pulumi.ResourceOptions(parent=resource_group))
pulumi.export("key_vault_name", key_vault.name)
pulumi.export("key_vault_url", key_vault.vault_uri)

# make sure we give relevant service principals access to this key vault's keys
key_access_object_ids = config.require_secret_object("accessObjectIds")

access_policies = []


def create_access_policies(obj_ids: List[str]) -> None:
    """Callback used to create access policies from the 'accessObjectIds'
    config value. This is used because the object from the config is a
    Pulumi Output (basically a future).
    """
    for obj_id in obj_ids:
        # hash the object ID to keep it secret and unique
        obj_id_hash = hashlib.sha256(obj_id.encode("utf-8")).hexdigest()
        access_policy_name = f"access-policy-{obj_id_hash}"
        policy = keyvault.AccessPolicy(
            access_policy_name,
            key_vault_id=key_vault.id,
            object_id=obj_id,
            tenant_id=tenant_id,
            key_permissions=[
                "create", "get", "list", "delete", "encrypt", "decrypt"
            ],
            opts=pulumi.ResourceOptions(parent=key_vault))
        access_policies.append(policy)


key_access_object_ids.apply(create_access_policies)

# finally, create the key encryption key in the vault
encryption_key = keyvault.Key(
    "keyencryptionkey",
    key_opts=["decrypt", "encrypt"],
    key_type="RSA",
    key_size=2048,
    key_vault_id=key_vault.id,
    tags=tags,
    opts=pulumi.ResourceOptions(parent=key_vault, depends_on=access_policies))
pulumi.export("key_name", encryption_key.name)
pulumi.export("key_id", encryption_key.id)
