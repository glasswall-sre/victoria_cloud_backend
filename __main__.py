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
import json
from typing import List

import pulumi
from pulumi_azure import core, storage, keyvault, authorization

stack_name = pulumi.get_stack()

config = pulumi.Config()
tags = config.require_object("tags")

# the service principals in the JSON file are given access to Victoria
# cloud backend resources
object_ids = []
with open(f"{stack_name}.json", 'r') as json_file:
    object_ids = json.load(json_file)

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

# make sure the service principals have access to the Azure Blob Storage
for obj_id in object_ids:
    role_assignment = authorization.Assignment(
        f"blob-assignment-{obj_id}",
        scope=storage_account.id,
        role_definition_name="Storage Blob Data Contributor",
        principal_id=obj_id)

storage_container = storage.Container(
    "victoria",
    storage_account_name=storage_account.name,
    container_access_type="private",
    opts=pulumi.ResourceOptions(parent=storage_account))
pulumi.export("container_name", storage_container.name)

# now, the key vault
tenant_id = config.require_secret("tenantId")
keyvault_name = config.require("keyVaultName")
key_vault = keyvault.KeyVault(
    keyvault_name,
    resource_group_name=resource_group.name,
    sku_name="standard",
    tenant_id=tenant_id,
    tags=tags,
    opts=pulumi.ResourceOptions(parent=resource_group))
pulumi.export("key_vault_name", key_vault.name)
pulumi.export("key_vault_url", key_vault.vault_uri)

# create the access policy on the key vault to give the principals access
access_policies = []
for obj_id in object_ids:
    access_policy_name = f"access-policy-{obj_id}"
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
