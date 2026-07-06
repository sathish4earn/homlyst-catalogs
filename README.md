# HomLyst Catalogs

Country grocery catalogs for the [HomLyst](https://github.com/sathish4earn) shopping-list app.
The app downloads these files at runtime, so **adding or updating a country needs no app release** —
edit the JSON, push, done.

## Structure

```
manifest.json          ← registry: which countries exist, with currency/dial-code metadata
languages.json         ← display names for language codes (e.g. "es" -> "Español")
catalogs/
  india_catalog_v1.json
  usa_catalog_v1.json
  ...
  l10n/
    IN_hi.json          ← item/category translations for one catalog + language
    ...
```

## How the app consumes this

Files are served through the jsDelivr CDN (free, global, cached ~12h):

```
https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/manifest.json
https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/catalogs/<fileName>
```

The app checks `manifest.json` on launch, downloads changed catalogs (compared by `version`),
and caches everything locally — it works fully offline after first fetch, and ships with a
bundled seed so it works offline on first install too.

## Adding a country

1. Create `catalogs/<country>_catalog_v1.json` (copy an existing one as a template).
2. Add an entry to `manifest.json`:
   `{ "code": "DE", "displayName": "Germany", "flag": "🇩🇪", "fileName": "germany_catalog_v1.json", "dialCode": "+49", "currencyCode": "EUR", "version": 1 }`
   - `code` — ISO 3166-1 alpha-2
   - `currencyCode` — ISO 4217
3. Push. The country appears in the app's picker within the CDN cache window.

## Updating an existing catalog

Edit the catalog file **and bump its `version` number in `manifest.json`** — the app only
re-downloads a catalog when its manifest version increases. A device that's already synced
an older version will otherwise never see your edit — this is the one sharp edge of the
"content-only, no app release" model, so don't forget it.

## Adding a language (translating a catalog's items and categories)

1. Create `catalogs/l10n/<CODE>_<lang>.json`:
   ```json
   { "version": 1, "categories": { "Vegetables": "Verduras" }, "items": { "onion": "Cebolla" } }
   ```
   `categories` keys are the catalog's category `key` values; `items` keys are item `id`s.
   Coverage can be partial — anything missing falls back to English — but aim for 100%.
2. Add the language to that catalog's `l10n` map in `manifest.json`:
   `"l10n": { "es": 1 }` (version starts at 1, same bump rule as catalogs above).
3. If this is a language the app has never shown before, add its native display name to
   `languages.json` (e.g. `"es": "Español"`) — this is the *only* reason that file exists:
   supplying the text shown in the Settings language picker. It's separate from the
   translation content itself.
4. Push. No app code or release is needed for any of this.

## Updating a language's translations

Edit the `l10n/<CODE>_<lang>.json` file **and bump that language's version number** in the
catalog's `l10n` map in `manifest.json` — same re-fetch rule as catalogs.

## What still requires an app release

Only the app's own UI chrome (button labels, dialog titles, static screen text — not catalog
content) is compiled into the app and needs a release to translate. Most languages here run
with English chrome and translated catalog content only, which is expected and fine.

No user data, secrets, or app logic live in this repository — content only.
