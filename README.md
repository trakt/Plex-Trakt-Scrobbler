# Trakt.tv (for Plex)
Now compatible with the Native Plex Movie Agent (should also be compatible with the upcoming Native Plex TV Agent). If you use the new agents, you require at least PMS version 1.20.1.3213 or higher, and you have to do a metadata refresh on the entire library after upgrading to this version. This plugin should be fully backwards compatible with the earlier supported agents.

I cannot support other issues with the plugin outside of the new agent support.

[![](https://img.shields.io/badge/license-GPLv3-blue.svg?style=flat-square)][license] [![](https://img.shields.io/requires/github/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)][requires.io] [![](https://img.shields.io/scrutinizer/build/g/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)][scrutinizer] [![](https://img.shields.io/scrutinizer/g/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)][scrutinizer] [![](https://img.shields.io/scrutinizer/coverage/g/fuzeman/Plex-Trakt-Scrobbler.svg?style=flat-square)][scrutinizer]  
[![](https://img.shields.io/gitter/room/trakt/Plex-Trakt-Scrobbler.svg?style=social)][gitter.im]

**Trakt.tv (for Plex)** is a plugin for [Plex Media Server][plex.tv] to synchronize watched history, ratings, playback progress and lists to your [Trakt.tv][trakt.tv] profile.

### Key Features
 - Automatically track every TV show and movie you watch
 - Upload watched history, ratings and playback progress to your [Trakt.tv][trakt.tv] profile
 - Synchronize data between supported applications *([Kodi](https://trakt.tv/a/kodi), [MediaPortal](https://trakt.tv/a/mediaportal), [Emby](https://trakt.tv/a/emby), [Infuse](https://trakt.tv/a/infuse-ios))*
 - Link all your [Plex][plex.tv] users to individual [Trakt.tv][trakt.tv] profiles

*See https://trakt.tv/vip for an overview of other features available on the Trakt.tv website.*

### Navigation

| [Install][install] | [FAQ][faq] | [Settings][settings] | [Support][support] | [KB][knowledge-base] | [Issues][issues] | [Credits][credits] |
|:------------------:|:----------:|:--------------------:|:------------------:|:-------------------:|:----------------:|:------------------:|
| [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/file_download.png)][install] | [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/question_answer.png)][faq] | [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/settings.png)][settings] | [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/help.png)][support] | [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/bug_report.png)][knowledge-base] | [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/message.png)][issues] | [![](https://raw.githubusercontent.com/wiki/fuzeman/Plex-Trakt-Scrobbler/_assets/people.png)][credits] |

[install]: https://github.com/trakt/Plex-Trakt-Scrobbler/wiki/Installation
[faq]: https://github.com/trakt/Plex-Trakt-Scrobbler/wiki/Frequently-asked-questions
[settings]: https://github.com/trakt/Plex-Trakt-Scrobbler/wiki/Configuration
[support]: https://github.com/trakt/Plex-Trakt-Scrobbler/wiki/Support
[knowledge-base]: https://github.com/trakt/Plex-Trakt-Scrobbler/wiki/KB
[issues]: https://github.com/trakt/Plex-Trakt-Scrobbler/issues

[license]: https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/LICENSE.md
[credits]: https://github.com/trakt/Plex-Trakt-Scrobbler/blob/master/Trakttv.bundle/CREDITS.md

[gitter.im]: https://gitter.im/trakt/Plex-Trakt-Scrobbler?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge
[gratipay]: https://gratipay.com/trakt-for-plex
[paypal]: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=853QCH9BP7LE2
[requires.io]: https://requires.io/github/fuzeman/Plex-Trakt-Scrobbler/requirements
[scrutinizer]: https://scrutinizer-ci.com/g/fuzeman/Plex-Trakt-Scrobbler
[trakt.tv]: https://trakt.tv
[plex.tv]: https://www.plex.tv

## Trakt authentication (Device Code Flow)

This plugin uses **Trakt Device Code Flow** to connect a Trakt account. No Client
Secret is required.

### Application configuration

Create a Trakt application, then configure only the Client ID. In Plex plugin
data, create `advanced.ini`:

```ini
[trakt]
client_id = YOUR_CLIENT_ID
```

`TRAKT_CLIENT_ID` may be used instead of `client_id`. Do not add or require a
`client_secret`. The old embedded Client ID/Secret and old `/pin/{app_id}` URL
are no longer used.

### Connect Trakt

1. Open **Preferences**.
2. Use **Connect Trakt** in the main menu, or in **Authentication** if shown.
3. The plugin requests a device code and shows:

```text
Connect Trakt
1. Open: [verification_url]
2. Enter code: ABCD-EFGH

Waiting for authorization...
```

The `verification_url` comes from Trakt; it is not constructed. `user_code` and
device authorization are temporary and are not persisted as account credentials.
Polling respects Trakt's `interval`, `authorization_pending`, `slow_down`,
expired device codes and user denial. An expired device code requests another
code; denial reports failure.

After authorization, the plugin calls `/users/settings`, retrieves username, and
associates authorization with the existing Plex-Trakt account.

### Token refresh and migration

Trakt access tokens expire after 7 days. `TraktAuthenticationManager` refreshes
automatically before authenticated scrobbling/sync requests.

Refresh request body:

```json
{
  "refresh_token": "<current_refresh_token>",
  "client_id": "<client_id>",
  "grant_type": "refresh_token"
}
```

No Client Secret is sent. Refresh-token rotation is atomic: `access_token`,
`refresh_token`, `scope`, `token_type`, `created_at` and `expires_in` are
replaced together. `scope` is preserved exactly as returned. Per-account locks
prevent concurrent refresh requests from consuming the same single-use refresh
token twice.

**Existing installations:** keep existing account records and database. Accounts
with legacy OAuth credentials that cannot be refreshed after Trakt's
authentication migration are marked `authorization_required`; they are not
deleted. Plex username-to-Plex-user association, watched history, sync
preferences and plugin state are preserved. Reconnect once with **Connect
Trakt**. Old refresh tokens cannot be exchanged after Trakt's authentication
migration; `invalid_grant` / `session not found` requires reauthorization.

Authentication state is `connected`, `authorization_required`,
`authorization_in_progress`, or `authentication_error`. Trakt API unavailable
does not delete account state. `invalid_client` is reported as an application
configuration problem. HTTP 429 respects rate-limit instructions. Network
timeout during refresh is not automatically retried with the old token because
Trakt may have consumed it; recovery checks persistent storage or requires
reauthorization.

### Logging

Authentication logs record events such as `[Trakt] Device authorization
initiated`, `[Trakt] Waiting for user authorization`, `[Trakt] Account
authorized`, `[Trakt] Access token refreshed`, `[Trakt] Credentials persisted`,
`[Trakt] Refresh rejected`, and `[Trakt] Account requires reauthorization`.
Tokens, device codes, user codes and authorization payloads are never logged.

### Synology deployment

1. Back up the existing plugin directory and database.
2. Install the modified plugin alongside the backup.
3. Configure `[trakt] client_id`.
4. Connect the Trakt account again once.
5. Verify scrobbling.
6. Force a token refresh in a test environment.
7. Restart Plex and verify authentication persists.
8. Keep the backup until the installation has operated successfully for several
   days.
