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

