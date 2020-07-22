# victoria_cloud_backend
Pulumi project for deploying Victoria cloud backend.

## Required Config
- `azure:location`: The Azure location to deploy into.
- `victoria-cloud-backend-azure:tags`: Dict containing tags to put on resources.
- `victoria-cloud-backend-azure:tenantId` (SECRET): The Azure AD tenant ID to use for Key Vault 
  operations. This can be easily found with Azure CLI by running
  `az account show --query tenantId -o tsv`.
- `victoria-cloud-backend-azure:keyVaultName`: The name of the Azure Key Vault.

You also need to add service principal object IDs you want to be able to
access the key vault and storage account to a JSON file with the same name as your stack. For
an example of this please see `victoria-cloud-azure.json` (note it has the
same name as the stack `Pulumi.victoria-cloud-azure.yaml`). As a minimum, the
object ID of the service principal Pulumi is running under will need to have
access to the key vault, so it can create a key in the key vault.

## Deploying config files to your cloud storage backend
It's good practice to keep your Victoria common config files in source control
and deploy them with CI/CD. This way you can version them.

You can do this in a GitHub action like so (using `./config_files` here as
an example):
```yaml
- name: Log in to Azure CLI
  uses: azure/login@v1
  with:
    creds: ${{ secrets.azure_credentials }}
- name: Upload config files to blob storage
  uses: azure/CLI@v1
  with:
    inlineScript: |
      az storage blob upload-batch -d $(pulumi stack output container_name) \
        --account-name $(pulumi stack output storage_account_name) \
        --auth-mode login \
        -s ./config_files
```

This just uses the Azure CLI to upload them, so similar approaches will work
for other CI/CD methods. At Glasswall we deploy ours with Azure Pipelines.

The config files in `./config_files` are the ones we actually use, complete
with encrypted sensitive data.