# HomLyst Catalogs

Country grocery catalogs for the [HomLyst](https://github.com/sathish4earn) shopping-list app.
The app downloads these files at runtime, so **adding or updating a country needs no app release** —
edit the JSON, push, done.

## Structure

```
manifest.json          ← registry: which countries exist, with currency/dial-code metadata
catalogs/
  india_catalog_v1.json
  usa_catalog_v1.json
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
re-downloads a catalog when its manifest version increases.

No user data, secrets, or app logic live in this repository — content only.
