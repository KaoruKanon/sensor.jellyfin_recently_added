# Jellyfin Recently Added Component

Home Assistant component to feed [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) with
Jellyfin's recently added media.</br>
This component does not require, nor conflict with, the default Jellyfin components.</br></br>

### Issues
Read through these two resources before posting issues to GitHub or the forums.
 - [upcoming-media-card troubleshooting guide](https://github.com/custom-cards/upcoming-media-card/blob/master/troubleshooting.md)
 - [@thomasloven's lovelace guide](https://github.com/thomasloven/hass-config/wiki/Lovelace-Plugins).

## Installation:
1. Install this component by copying [these files](https://github.com/kaorukanon/sensor.jellyfin_recently_added/tree/master/custom_components/jellyfin_recently_added) to `custom_components/jellyfin_recently_added/`.
2. Install the card: [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card)
3. Add the code for the card to your `ui-lovelace.yaml`.
4. **You will need to restart after installation for the component to start working.**

### Before you start: getting your Jellyfin API key and User ID
- **API key**: In Jellyfin, go to *Administration > Dashboard > Advanced > API Keys* and create a new key. This authenticates the request, it does not by itself say whose library/watch-state to read.
- **User ID**: this identifies which Jellyfin account's library access and watch-state to use. It's required even when the API key belongs to an admin account: "recently added" respects per-user library access, and "continue watching" (`on_deck`) is inherently tied to one user's playback history — Jellyfin has no server-wide equivalent of either.
  - **Via the UI (Option B below)**: no need to look it up — step 2 of the setup wizard shows a dropdown of every account on the server, as long as your API key belongs to an admin account (`GET /Users` requires admin rights to list everyone). If it doesn't, the dropdown is empty and you fall back to the manual entry below.
  - **Manually (needed for Option A/YAML, or if the dropdown is empty)**: either open *Administration > Dashboard > Users*, select the account, and copy the `userId` value from the page URL, or query the API directly: `curl -H "X-Emby-Token: YOUR_API_KEY" http://jellyfin.local:8096/Users` — the response lists every account with its `Id`, and `Policy.IsAdministrator` / `Policy.EnableAllFolders` to help you spot the admin one.
  - The User ID is not a secret, it's just an identifier, but you can still keep it in `secrets.yaml` alongside the API key if you'd rather have all the sensitive-looking values in one place.

### Adding device
You can set this integration up either through the UI, or through `configuration.yaml` — both work, and can be used interchangeably.

<details><summary style="list-style: none"><h3><b style="cursor: pointer">Option A: configuration.yaml + secrets.yaml</b></h3></summary>

Add your API key (and any other value you'd rather not have in plain text) to `secrets.yaml`:

```yaml
# secrets.yaml
jellyfin_api_key: "0123456789abcdef0123456789abcdef"
jellyfin_user_id: "0123456789abcdef0123456789abcdef"
```

Then reference it from `configuration.yaml`:

```yaml
# configuration.yaml
jellyfin_recently_added:
  - host: jellyfin.local
    port: 8096
    ssl: false
    api_key: !secret jellyfin_api_key
    user_id: !secret jellyfin_user_id
    max: 5
    on_deck: false
    section_types:
      - movies
      - tvshows
    # section_libraries: []       # optional, defaults to all matching libraries
    # exclude_keywords: []        # optional
```

`configuration.yaml` accepts a list under `jellyfin_recently_added:`, so you can declare more than one server. On every Home Assistant restart, each block is imported into a config entry; an entry previously imported this way (matched by `api_key`) is refreshed with the current YAML values rather than duplicated, so `configuration.yaml`/`secrets.yaml` stays the source of truth for entries set up this way. Entries added through the UI are left untouched. You'll still need to restart Home Assistant after adding or editing a block for the change to take effect.

#### `configuration.yaml` reference

Each item in the `jellyfin_recently_added:` list accepts the same values as the UI form:

| Key                 | Required | Type          | Default                | Description                                                                                                   |
| -------------------- | -------- | ------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| `host`               | Yes      | string        | —                        | Jellyfin server hostname or IP.                                                                                  |
| `api_key`            | Yes      | string        | —                        | Jellyfin API key (*Dashboard > API Keys*).                                                                       |
| `user_id`            | Yes      | string        | —                        | Jellyfin User ID whose library access and watch-state to use — see [above](#before-you-start-getting-your-jellyfin-api-key-and-user-id). |
| `port`               | No       | integer       | `8096`                   | Jellyfin server port.                                                                                            |
| `ssl`                | No       | boolean       | `false`                  | Use `https` to reach the server.                                                                                 |
| `name`               | No       | string        | `''`                     | Prefix added to entity names/`unique_id` — set this if you're configuring more than one Jellyfin server.        |
| `max`                | No       | integer       | `5`                      | Max number of items kept per sensor.                                                                            |
| `on_deck`            | No       | boolean       | `false`                  | Show "continue watching" items instead of "recently added".                                                     |
| `section_types`      | No       | list of string | `[movies, tvshows]`     | Which library types to expose, any of: `movies`, `tvshows`, `music`, `photos`.                                  |
| `section_libraries`  | No       | list of string | `[]` (all matching)     | Restrict to specific library names (must match the names shown in Jellyfin exactly). Leave empty for all libraries matching `section_types`. |
| `exclude_keywords`   | No       | list of string | `[]`                     | Reserved for a future title-filtering feature; accepted for schema/UI parity but not currently applied.        |

</details>

<details><summary style="list-style: none"><h3><b style="cursor: pointer">Option B: UI (My button)</b></h3></summary>

The wizard is two steps: server connection first (host/port/SSL/API key), then account and sensor settings — where `user_id` is a dropdown of every Jellyfin account (populated via the API key you just entered) instead of a field you fill in by hand.

To add the **Jellyfin Recently added** integration to your Home Assistant, use this My button:

<a href="https://my.home-assistant.io/redirect/config_flow_start?domain=jellyfin_recently_added" class="my badge" target="_blank"><img src="https://my.home-assistant.io/badges/config_flow_start.svg"></a>

<details><summary style="list-style: none"><h3><b style="cursor: pointer">Manual configuration steps</b></h3></summary>

If the above My button doesn’t work, you can also perform the following steps manually:

- Browse to your Home Assistant instance.

- Go to [Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations/).

- In the bottom right corner, select the [Add Integration button].(https://my.home-assistant.io/redirect/config_flow_start?domain=jellyfin_recently_added)

- From the list, select **Jellyfin Recently added**.

- Follow the instructions on screen to complete the setup.
</details>

</details>

The number of items in the sensor, library types, libraries in general, excluded words, and show "continue watching" options can be changed later.

**Do not just copy examples, please use config options above to build your own!**

## FAQ:
### When I tried it said *"User already configured"*
This is because the integration uses the Jellyfin API key as part of its *unique_id*, so it does not collide with other instances of the same integration.

### I want to change the config of the integration, how do I do it?
This is very simple, when you go to the *'Settings/Devices & services/Jellyfin Recently Added'* you will see your instance of the Jellyfin Recently Added integration and on the right side you will see **Configure** button, when you press it you can change all necessary config you might need to change and click submit, the instance then should restart and show new values based on your new settings.
</br><small>(If you want to change Jellyfin address, API key, User ID or sensors prefix name you will need to readd the integration with your new parameters)</small>

### The number of items in the sensor is not the amount I set it to be
The sensor you most likely mean is the merged sensor which shows all the data (also sorted) that are in the other sensors, meaning if you've set your max number of values to 7 and you've got 3 section types (movies, tvshows, music) the total number of items in the merged sensor will be 21 (7 *<small>(for max)</small>* * 3 *<small>(for section types)</small>*)

### My sensor is not showing any values, but there are no errors
This may be caused by an incorrectly set *Libraries to consider*, you can change them in [Config](#i-want-to-change-the-config-of-the-integration-how-do-i-do-it), where if you've configured your Jellyfin API key, User ID and address right will now show all libraries in the dropdown selection.

### Card Content Defaults

| key   | default                      | example                                             |
| ----- | ----------------------------- | --------------------------------------------------- |
| title | $title                       | "The Walking Dead"                                  |
| line1 | $episode                     | "What Comes After"                                  |
| line2 | $day, $date $time            | "Monday, 10/31 10:00 PM" Displays time of download. |
| line3 | $number - $rating - $runtime | "S01E12 - ★ 9.8 - 01:30"                            |
| line4 | $genres                      | "Action, Adventure, Comedy"                         |
| icon  | mdi:eye-off                  | https://materialdesignicons.com/icon/eye-off        |
