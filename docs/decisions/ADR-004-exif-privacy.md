# ADR-004: EXIF location privacy by default

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

Field photographs can embed precise GPS coordinates in EXIF metadata. In humanitarian mine-action
contexts those coordinates may reveal hazardous-object locations, personnel movements, affected
communities, or sensitive operational sites. Sending such metadata to storage or a model provider
without an explicit need would create avoidable privacy and security risk.

## Decision

`KEEP_EXIF_GPS` defaults to `false`. The ingest layer does not include GPS in `ImageMetadata` unless
an operator deliberately enables the setting for an approved deployment. Regardless of that
setting, accepted image bytes are re-encoded without EXIF before they may reach storage or a model.
Rejected images stop before sanitized output or downstream processing.

## Consequences

Location does not leave the input boundary by default. Deployments that enable GPS assume the duty
to define access control, retention, audit, and lawful-use policy. Tests explicitly guard the
default non-disclosure and metadata stripping behavior.

