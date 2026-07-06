# Rollout Guide — Adding a New Country / Language

This is the end-to-end, copy-pasteable runbook for shipping a new country catalog
(and its language, if new) the same way Malaysia was added: **content only, zero
changes to the HomLystKMP app code, no app release.** Everything the app needs is
fetched from this repo at runtime via jsDelivr.

If you're only translating chrome strings for a language that already has a
catalog, skip to [Part C](#part-c--ui-chrome-translation-buttonslabelspopups).

---

## Mental model — 3 independent content layers

| Layer | File(s) | Controls |
|---|---|---|
| **Catalog** | `catalogs/<country>_catalog_v1.json` + `manifest.json` entry | Which countries exist, their categories/items in English |
| **Catalog l10n** | `catalogs/l10n/<CODE>_<lang>.json` + that catalog's `l10n` map in `manifest.json` | Translated category/item names for one country+language pair |
| **UI chrome** | `chrome/<lang>.json` + `chrome_manifest.json` | Translated buttons/labels/dialogs — same 100 keys, used app-wide, independent of any one country |

A country can exist with **no** l10n (falls back to English item names) and a
language can have chrome translated **without** any catalog using it yet. They're
decoupled on purpose — ship what you have.

---

## Part A — New country (catalog only, no new language)

Use this when the country's shoppers are fine with English UI/labels, or the
language already has l10n/chrome elsewhere.

### 1. Create the catalog file

`catalogs/<country>_catalog_v1.json`:

```json
{
  "version": 2,
  "countryCode": "MY",
  "countryDisplayName": "Malaysia",
  "categories": [
    {
      "key": "Vegetables & Herbs",
      "nameEn": "Vegetables & Herbs",
      "emoji": "🥬",
      "unitType": "WEIGHT",
      "items": [
        { "id": "kangkung", "nameEn": "Kangkung" },
        { "id": "cucumber", "nameEn": "Cucumber" }
      ]
    }
  ]
}
```

Rules:
- `key` is the category's stable identifier — l10n overlays reference it verbatim. Keep it in English, matching `nameEn`.
- `unitType` is one of `WEIGHT`, `PIECES`, `LITRES` (all-caps, exact).
- Each item needs a stable `id` (kebab-case, unique within the file) and `nameEn`. **Never change an existing item's `id` later** — it's the join key for l10n overlays and cart persistence.
- Populate with real, locally-authentic items (not translated English filler) — copy the shape of `catalogs/malaysia_catalog_v1.json` for a fully worked example across ~14 categories.
- `nameResKey` on a category (seen in `india_catalog_v1.json` / `global_catalog_v1.json`) is a **legacy fallback** used only by the original bundled catalogs, for when no l10n overlay supplies a category name — it looks up `cat_<x>` in chrome strings. New catalogs don't need it; just supply category names directly in your l10n overlay instead (Part B).

### 2. Register it in `manifest.json`

Add an entry to the `catalogs` array:

```json
{
  "code": "MY",
  "displayName": "Malaysia",
  "flag": "🇲🇾",
  "fileName": "malaysia_catalog_v1.json",
  "dialCode": "+60",
  "currencyCode": "MYR",
  "version": 1
}
```

- `code` — ISO 3166-1 alpha-2, uppercase.
- `currencyCode` — ISO 4217.
- `flag` — the emoji flag, used directly in the country picker and in the switch-catalog dialog text.
- `version` starts at **1**. Bumping it later is how you signal "re-download this catalog" (see [Part D](#part-d--updating-content-later)).

### 3. Validate JSON before pushing

```bash
python3 -m json.tool catalogs/<country>_catalog_v1.json > /dev/null && echo OK
python3 -m json.tool manifest.json > /dev/null && echo OK
```

### 4. Commit and push

```bash
git add catalogs/<country>_catalog_v1.json manifest.json
git commit -m "Add <Country> catalog"
git push origin main
```

That's it — no l10n, no chrome, no app change. The country appears in the picker
with English item names once the CDN edge the device hits has the new manifest.

---

## Part B — Catalog l10n (translate that country's items/categories)

Do this when shoppers in that country expect the grocery list itself in their
language (not just the app chrome).

### 1. Create the overlay file

`catalogs/l10n/<CODE>_<lang>.json` — file name is `<manifest code>_<ISO 639-1 lang code>.json`:

```json
{
  "version": 1,
  "countryCode": "MY",
  "language": "ms",
  "categories": {
    "Vegetables & Herbs": "Sayur-sayuran & Herba",
    "Fruits": "Buah-buahan"
  },
  "items": {
    "kangkung": "Kangkung",
    "cucumber": "Timun"
  }
}
```

- `categories` keys must exactly match the catalog's `key` values (case-sensitive).
- `items` keys must exactly match item `id`s.
- Coverage can be partial — anything missing falls back to `nameEn` — but aim for 100%. Use `catalogs/l10n/MY_ms.json` as the fully-worked reference.

### 2. Wire it into `manifest.json`

Add the language to that catalog's `l10n` map (create the map if it doesn't exist yet):

```json
{
  "code": "MY",
  ...
  "l10n": {
    "ms": 1
  }
}
```

Version starts at **1**, same bump-to-refresh rule as catalogs.

### 3. New language? Register its display name

If `ms` (or whatever code) has never appeared in this repo before, add it to
`languages.json` so the Settings language picker can show a native name:

```json
"ms": "Bahasa Melayu"
```

This file's *only* job is display names — it is not translation content.

### 4. Validate, commit, push

```bash
python3 -m json.tool catalogs/l10n/<CODE>_<lang>.json > /dev/null && echo OK
python3 -m json.tool manifest.json > /dev/null && echo OK
python3 -m json.tool languages.json > /dev/null && echo OK

git add catalogs/l10n/<CODE>_<lang>.json manifest.json languages.json
git commit -m "Add <lang> l10n for <Country>"
git push origin main
```

At this point: catalog items/categories show in `<lang>`, but app **chrome**
(buttons, dialog titles, "Settings", "Add to Cart", etc.) is still English for
that language until Part C is done too.

---

## Part C — UI chrome translation (buttons/labels/popups)

This is what makes the *entire app* — not just the grocery list — appear in a
language. It's independent of any single country; once `<lang>` has chrome, every
catalog offering that language benefits.

### 1. Get the canonical key set

`chrome/en.json` is the source of truth — **exactly 100 keys**. Never add, remove,
or rename keys per-language; every `chrome/<lang>.json` must have the identical
key set as `en.json`, only values translated. Two keys carry format placeholders
that must be preserved verbatim (they're substituted by the app, not by you):

- `settings_catalog_switch_msg` — contains `%1$s` (gets replaced with a flag+country name)
- `retain_dialog_message` — contains `%d` (gets replaced with an item count)

### 2. Author `chrome/<lang>.json`

```json
{
  "version": 1,
  "strings": {
    "app_name": "HomLyst",
    "nav_search": "Cari",
    "...": "... all 100 keys ...",
    "settings_catalog_switch_msg": "Menukar ke %1$s akan menggantikan katalog item anda dan mengosongkan senarai belanja semasa.",
    "retain_dialog_message": "%d item tidak dibeli. Kekalkan dalam senarai untuk perjalanan seterusnya?"
  }
}
```

`app_name` ("HomLyst") stays untranslated — it's a brand name in every language.

**Recommended: generate + validate programmatically** rather than hand-editing
JSON, to guarantee the key set matches exactly. A small Python script that defines
`KEYS_ORDER` (copy it from `chrome/en.json`'s keys) and a dict per language,
asserts `set(dict.keys()) == set(KEYS_ORDER)`, then writes the file — this is
how the zh/pt/id/es/vi/th/fr/ms batch was done. Catches missing/extra keys before
they ever hit the CDN.

### 3. Register it in `chrome_manifest.json`

```json
{
  "version": 1,
  "chrome": {
    "en": 1,
    "...": 1,
    "ms": 1
  }
}
```

Version starts at **1**. This manifest is refetched unconditionally on every app
refresh (unlike catalogs, it's small and has no per-device cache-gate on itself)
— only the per-language entries inside it are version-gated against what the
device has already cached.

### 4. Validate, commit, push

```bash
python3 -m json.tool chrome/<lang>.json > /dev/null && echo OK
python3 -m json.tool chrome_manifest.json > /dev/null && echo OK

git add chrome/<lang>.json chrome_manifest.json
git commit -m "Add <lang> chrome UI translation"
git push origin main
```

---

## Part D — Updating content later

Editing a file is not enough — the app only re-downloads something when its
**version number increases** past what the device already cached. This is the
one sharp edge of the whole "content-only" model:

| You changed | Bump this |
|---|---|
| A catalog's items/categories | that catalog's `"version"` in `manifest.json` |
| An l10n overlay | that language's version inside the catalog's `"l10n"` map in `manifest.json` |
| A chrome file | that language's version inside `chrome_manifest.json`'s `"chrome"` map |

Forgetting the bump means devices that already synced the old version silently
never see your edit.

---

## Part E — Push checklist (order doesn't matter, but don't skip validation)

```bash
cd /Users/home/Sathish/homlyst-catalogs

# 1. Validate every JSON file you touched
for f in <files you changed>; do python3 -m json.tool "$f" > /dev/null && echo "OK: $f"; done

# 2. Commit + push
git add <files>
git commit -m "<what you added>"
git push origin main
```

---

## Part F — CDN propagation & verification

Content is served through jsDelivr's GitHub CDN:

```
https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/<path>
```

jsDelivr is multi-provider (Cloudflare + Fastly) with independently-caching edge
nodes. A push is usually live within seconds to a couple of minutes, but
individual edges can lag — sometimes considerably — before converging. This is
an infrastructure characteristic, not something wrong with your content.

### Check what's actually live

```bash
curl -s "https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/manifest.json" | python3 -m json.tool
curl -s "https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/chrome_manifest.json"
curl -s "https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/chrome/<lang>.json" | python3 -c "import json,sys; print(json.load(sys.stdin)['strings']['dark_mode'])"
```

### Force a purge if a specific file looks stale

```bash
curl -s "https://purge.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/<path-to-file>"
```

One file per request — jsDelivr does not reliably purge a comma-joined list of
paths as separate entries (it was observed treating a comma-joined string as one
literal path). A `"status": "finished"` response does **not** guarantee every edge
has converged immediately; re-check with `curl` a few times, a couple of seconds
apart, before concluding it's stuck.

### Verify on-device

The app syncs on every launch (`CatalogUpdater.refresh()`, best-effort — any
failure silently keeps the existing cache/bundled seed, so the app never breaks
offline). To force a fresh sync attempt on an emulator/device:

```bash
adb shell am force-stop com.example.homeneeds
adb shell monkey -p com.example.homeneeds -c android.intent.category.LAUNCHER 1
```

Then: Settings → Country Catalog → Change → confirm the new country appears with
correct flag/name → select it → confirm categories/items render → Settings →
Select Language → confirm the new language appears (only for catalogs whose
`l10n` map includes it) → select it → confirm both catalog items *and* chrome
(buttons/labels) render translated.

If chrome/catalog content on-device doesn't match what `curl` shows as live,
that's edge-cache lag on the device's specific network path, not a bug — retry
after a purge, or simply wait; it always converges.

---

## Worked example: Malaysia, start to finish

1. `catalogs/malaysia_catalog_v1.json` — 14 categories, ~230 authentic Malaysian
   grocery items (Kangkung, Sotong, Belacan, Ayam, etc.), `unitType` per category.
2. `manifest.json` — added `{"code": "MY", ..., "l10n": {"ms": 1}}`.
3. `catalogs/l10n/MY_ms.json` — full Malay translation of every category and item.
4. `languages.json` — added `"ms": "Bahasa Melayu"` (new language, never seen before).
5. `chrome/ms.json` — full 100-key Malay UI chrome translation.
6. `chrome_manifest.json` — added `"ms": 1`.
7. Validated all 5 JSON files, committed, pushed.
8. Verified live via `curl`, then on-device: Malaysia appeared in the country
   picker with the 🇲🇾 flag, item screen showed real Malay-market items, switching
   language to Bahasa Melayu translated both the catalog *and* every button/label/
   popup in the app — zero lines of Kotlin touched, zero app release.

That is the complete pattern for every future country/language. If you find
yourself editing anything under `HomLystKMP/androidApp` or `HomLystKMP/shared`
to add a country or language, something has gone wrong — it should never be
necessary.
