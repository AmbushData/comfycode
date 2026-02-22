# Infrastructure Runbook

## Provisioning Azure Storage

1. Ensure you have an Azure subscription and a service principal with contributor access.
2. Set Pulumi config values for your stack (see README).
3. Run `pulumi preview` to check planned changes.
4. Run `pulumi up` to provision resources.

## Service Principal Setup
- [Azure docs: Create service principal](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal)

## Container Naming
- See `docs/BLOB_CONVENTIONS.md` for naming conventions.

## Destroying Resources
- Run `pulumi destroy` to remove resources from dev/staging.
- For production, review data retention before destroying.
