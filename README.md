# victoria_cloud_backend
Pulumi project for deploying Victoria cloud backend.

## Required Config
- `azure:location`: The Azure location to deploy into.
- `stack-name:tags`: Dict containing tags to put on resources.
- `stack-name:tenantId` (SECRET): The Azure AD tenant ID to use for Key Vault 
  operations. This can be easily found with Azure CLI by running
  `az account show --query tenantId -o tsv`.
- `stack-name:accessObjectIds` (ARRAY, SECRET): The object IDs of Azure AD service
  principals allowed to access keys in the Key Vault. **Note:** this should include
  the object ID of any service principals being used to run the Pulumi stack, 
  otherwise Pulumi will not be able to create the key.