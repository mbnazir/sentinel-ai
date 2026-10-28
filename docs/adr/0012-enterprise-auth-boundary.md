# ADR 0012: Authentication and authorization are separate boundaries

Status: Accepted

Sentinel authorizes API calls through validated identity claims and explicit roles. Production authentication must be federated to the enterprise identity provider. The application must not become a password store. Connector credentials and signing secrets must be injected from an approved secret manager.
