# ComfyCode Infrastructure (Pulumi)

This directory contains the Pulumi project for provisioning Azure Storage resources required by ComfyCode.

## Quickstart

1. Install Pulumi CLI: https://www.pulumi.com/docs/get-started/install/
2. Install Python dependencies: `pip install -r requirements.txt`
3. Configure Pulumi stack settings:
   - `pulumi config set azure:clientId <service-principal-id>`
   - `pulumi config set azure:clientSecret <service-principal-secret> --secret`
   - `pulumi config set azure:tenantId <tenant-id>`
   - `pulumi config set azure:subscriptionId <subscription-id>`
   - `pulumi config set storageAccountName <name>`
   - `pulumi config set containerNames '["artifacts", "images", "outputs"]'`
4. Preview changes: `pulumi preview`
5. Apply changes: `pulumi up`

## Outputs
- Storage account name
- Container URLs

## Runbook
See `runbook.md` for full provisioning and troubleshooting steps.
