# victoria_cloud_backend
Pulumi project for deploying Victoria cloud backend.

## Required Config
- `azure:location`: The Azure location to deploy into.
- `stack-name:tags`: Dict containing tags to put on resources.
- `stack-name:tenantId` (SECRET): The Azure AD tenant ID to use for Key Vault 
  operations. This can be easily found with Azure CLI by running
  `az account show --query tenantId -o tsv`.

You also need to add service principal object IDs you want to be able to
access the key vault to a JSON file with the same name as your stack. For
an example of this please see `victoria-cloud-azure.json` (note it has the
same name as the stack `Pulumi.victoria-cloud-azure.yaml`). As a minimum, the
object ID of the service principal Pulumi is running under will need to have
access to the key vault, so it can create a key.