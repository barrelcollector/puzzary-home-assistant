# Puzzary for Home Assistant

This custom integration connects Home Assistant to a Puzzary server. It provides
account statistics, a latest-printable-puzzle image, browsable puzzle media, and
actions for refreshing, generating, publishing, archiving, and restoring puzzles.

## Install

### HACS custom repository

1. In HACS, add `https://github.com/barrelcollector/puzzary-home-assistant` as a
   custom **Integration** repository.
2. Install **Puzzary** and restart Home Assistant.
3. Open **Settings -> Devices & services -> Add integration**, select **Puzzary**,
   and enter the URL Home Assistant uses to reach Puzzary plus a Puzzary API token.

### Manual

Copy `custom_components/puzzary` into Home Assistant's
`config/custom_components/puzzary` directory and restart Home Assistant.

`localhost` refers to Home Assistant itself. When the two applications run on
different hosts or containers, use a Puzzary address reachable from Home Assistant.

## Features

- Sensors for played, completed, in-progress, attempted, and correct puzzles
- Latest printable puzzle image entity
- Media folders organized by state and puzzle type
- `puzzary.refresh`, `puzzary.generate_puzzle`, `puzzary.publish_puzzle`,
  `puzzary.archive_puzzle`, and `puzzary.unarchive_puzzle` actions

Generation and administration actions require the matching Puzzary permission.
Statistics, media, and refresh work with a normal API-enabled account.

## Upgrade or remove

Upgrade through HACS, or replace the manual `custom_components/puzzary` folder,
then restart Home Assistant. To remove the integration, delete its entry from
**Settings -> Devices & services**, remove the folder if installed manually, and
restart Home Assistant.

## Compatibility and distribution

Version 0.2.2 supports the Puzzary 0.1.0 public beta API and Home Assistant
2025.1 or newer. Puzzary must be reachable from Home Assistant over HTTP or
HTTPS, and the configured Puzzary account must have API access plus any
permissions required by the enabled actions.

The supported public-beta installation paths are a HACS custom repository and
manual installation. Submission to the default HACS repository is not part of
the first public beta and can be considered after the integration has broader
real-world testing.

## Branding

Puzzary's icon is bundled in the integration's `brand` directory for Home
Assistant 2026.3 and newer and for compatible HACS marketplace surfaces. The
same high-contrast mark is used by Puzzary core and remains legible on light and
dark themes. Home Assistant versions before local custom-integration branding
support continue to use their normal placeholder behavior.

The editable SVG master, palette, rationale, and reproducible export steps are
in [`branding/`](branding/README.md). This integration does not expose a
standalone web interface, so it does not include unused favicon or web-manifest
assets.

## License

Puzzary for Home Assistant is licensed under the
[Apache License 2.0](LICENSE). Copyright 2026 Puzzary contributors. See
[NOTICE](NOTICE) for attribution. Home Assistant and its trademarks belong to
their respective owners; this is an independent integration.

