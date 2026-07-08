# Azure AD and Google Workspace SSO Providers

Milestone 18 adds real enterprise SSO provider scaffolding.

## Added providers

- Azure AD / Microsoft Entra ID
- Google Workspace
- Generic OIDC base provider

## Endpoints

```text
POST /api/v1/sso/{provider_name}/callback
```

Supported provider names:

```text
mock
azure_ad
google_workspace
```

## Required environment variables

### Azure AD / Entra ID

```text
AZURE_AD_TENANT_ID=
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_DEFAULT_ORG=
```

### Google Workspace

```text
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_WORKSPACE_DOMAIN=
GOOGLE_DEFAULT_ORG=
```

## Security note

Secrets must never be committed. Use environment variables, secret managers, or Kubernetes secrets.

## Important limitation

Milestone 18 provides provider scaffolding and claim mapping. Full production SSO still needs:

- state parameter validation
- nonce validation
- PKCE
- tenant-specific IdP configuration
- refresh-token handling
- group overage handling for Azure AD
- audit logging for authentication events
