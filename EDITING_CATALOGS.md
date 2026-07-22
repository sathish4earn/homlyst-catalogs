# Editing an Existing Catalog

Day-to-day maintenance steps for changing what's *already* in a catalog — adding,
removing, or renaming an item; adding or removing a whole category; fixing an
emoji or unit type. No app code, no app release — edit here, push, done.

(Adding a **brand-new country or language** is a different job with its own
sharp edges — see [ROLLOUT_GUIDE.md](ROLLOUT_GUIDE.md) for that instead.)

---

## 0. The one rule you cannot skip

**Every edit needs a version bump, or nobody gets it.**

The app only re-downloads a catalog when its `manifest.json` version number is
higher than what the device already has cached. Edit the file all you want —
if you forget to bump the version, every device that's already synced once
will simply never see your change.

Two version numbers to bump, and they must match:
1. The `"version"` field inside the catalog file itself (top of the file).
2. That catalog's `"version"` field in the matching entry of root `manifest.json`.

```json
// catalogs/india_catalog_v1.json
{ "version": 3, ... }          // was 2, now 3

// manifest.json
{ "code": "IN", ..., "version": 3, ... }   // must match
```

If you're also changing an `l10n` overlay (translated items/categories for one
catalog+language), that file's own `"version"` field *and* its entry in that
catalog's `"l10n"` map in `manifest.json` need the same bump — independent of
the base catalog's version.

---

## 1. Add an item to an existing category

Open `catalogs/<name>_catalog_v1.json`, find the category by its `"key"`, and
add to its `"items"` array.

Two possible item shapes depending on catalog schema version — check what's
already there and match it:

```json
// v1 schema (plain strings) — most catalogs
"items": ["Onion", "Tomato", "New Item Here"]

// v2 schema (stable ids) — newer catalogs, e.g. Malaysia, Brazil
"items": [
  { "id": "onion", "nameEn": "Onion" },
  { "id": "new-item-here", "nameEn": "New Item Here" }
]
```

For v2, the `id` must be a unique kebab-case slug within that file and must
**never change once shipped** — it's the join key for l10n translations and
for a user's already-saved cart/history entries. Renaming the display text
(`nameEn`) later is always safe; changing `id` is not.

Then bump both version numbers (see §0) and see §5 before you save.

## 2. Remove an item

Delete it from the `"items"` array. Bump both version numbers.

If the catalog has an l10n overlay (`catalogs/l10n/<CODE>_<lang>.json`) with a
translation for that item's id, you can leave the stale overlay entry — it's
harmless dead weight, not a bug — or delete it for tidiness. Not required.

## 3. Rename an item

- v1 schema (plain string): just change the string. That's it — v1 items have
  no stable id, so there's nothing else to keep in sync.
- v2 schema (`{id, nameEn}`): change `nameEn` only. **Never change `id`** —
  see §1. If an l10n overlay translates this item, its translation is keyed
  by `id` too, so it keeps working unchanged.

Bump both version numbers.

## 4. Add a brand-new category to an existing catalog

```json
{
  "key": "New Category Name",
  "nameEn": "New Category Name",
  "emoji": "🆕",
  "unitType": "PIECES",
  "items": ["First Item", "Second Item"]
}
```

- `key` and `nameEn` should be identical — `key` is the stable identifier an
  l10n overlay's `"categories"` map would translate against later.
- `unitType` is one of `WEIGHT`, `PIECES`, `LITRES` (exact, all-caps). Match
  the convention already in that file: produce/meat/spices → `WEIGHT`,
  milk/oil/beverages → `LITRES`, everything packaged/countable (snacks,
  personal care, cleaning, health, pet, stationery) → `PIECES`.
- Don't set `nameResKey` unless you're deliberately adding a category-name
  translation to `chrome/*.json` too (see §6) — it's optional and most new
  categories don't need it; an l10n overlay's own `"categories"` map is the
  normal way to translate a category name for one catalog+language.

Bump both version numbers. See §5 before you save.

## 5. ⚠️ Formatting gotcha — read this before saving

Catalog files are **not** uniformly formatted. Some already look like a
standard pretty-printed JSON file (one key per line); others are hand-wrapped
in a denser style (several keys per line, item arrays wrapped across lines
without one-per-line indentation). If your editor or a script reformats the
*whole file* while you're only trying to add one item, the diff balloons from
a few lines to hundreds — pure noise that makes the real change impossible to
review, and it has happened before in this repo.

**Before you save, check**: does the file already look "clean" (one key per
line, standard indentation)? If yes, editing normally is safe. If it looks
"compact" (multiple keys crammed per line), **only touch the lines you mean
to change** — don't run it through a JSON formatter or a script that does
`json.dump()`/re-serializes the whole document, or you'll rewrite everything.

As of this writing, compact-style files needing this care: `australia`,
`canada`, `china`, `france`, `germany`, `india`, `ireland`, `malaysia`,
`newzealand`, `philippines`, `uk`, `usa`. Already clean-style (safe to
re-serialize): `brazil`, `global`, `indonesia`, `mexico`, `thailand`,
`vietnam`. This list can drift as files get touched — the real test is
always: **after editing, run `git diff --stat`. If it shows way more lines
than you actually changed, undo and redo it as a surgical text edit instead.**

## 6. UI chrome strings — only if you added a `nameResKey`

Skip this section unless you set a `nameResKey` on a category in §4.

`chrome/<lang>.json` files nest every string **inside a `"strings"` key** —
not at the file root. Easy to get wrong:

```json
{
  "version": 4,
  "strings": {
    "cat_vegetables": "Vegetables",
    "cat_your_new_key": "Your New Label"   // <- goes in here, not at root
  }
}
```

Add your key + English text to `chrome/en.json`, and (ideally) a translation
to each of the other 14 `chrome/<lang>.json` files. Then bump every touched
language's version in `chrome_manifest.json`'s `"chrome"` map. If you skip a
language, that key just falls back to whatever `nameEn` was set to — not a
crash, just untranslated for that language until someone fills it in.

## 7. If this catalog is one of the 8 bundled into the app

Most catalogs are 100% remote — the CDN copy is the only copy. But **8**
catalogs also ship as a fallback baked directly into the app binary, so a
brand-new install has something to show before its first network fetch:
**India, Australia, Global, Canada, New Zealand, Ireland, UK, US.**

If you're editing one of these, the CDN update alone is enough for every
device that's ever gone online once — but a fresh, never-connected install
will keep showing the old content until you also update the bundled copies,
in the separate `HomLystKMP` app repo (not this one):

- `androidApp/src/main/assets/catalogs/<name>_catalog_v1.json`
- `iosApp/iosApp/<name>_catalog_v1.json`

Copy the same category/item change into both files identically, and bump
their own `"version"` field to match what you just shipped here (matching
numbers isn't functionally required — the app treats any bundled catalog as
version 1 regardless of what's written inside — but keeping them numerically
honest avoids confusion later). Don't touch `manifest_v1.json` in those same
folders — every catalog there is deliberately pinned at `version: 1` forever;
that's the fixed marker the app compares against to know the remote is newer,
not a real content counter.

If you added a `nameResKey` (§6), also add the English string to
`ChromeStringsRegistry.BUNDLED_EN` in
`shared/src/commonMain/kotlin/com/example/homeneeds/data/ChromeStringsRegistry.kt`.

## 8. Commit and push

This repo pushes straight to `main` — no PR, no review gate, no app release:

```bash
cd /Users/home/Sathish/homlyst-catalogs
git add -A
git commit -m "Add <what> to <catalog>"
git push
```

## 9. Verify it's actually live

jsDelivr caches every file **independently** for up to 12h. After pushing,
check the file you changed directly:

```bash
curl -s "https://cdn.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/catalogs/<name>_catalog_v1.json" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['version'])"
```

If it still shows the old version, force a refresh (usually near-instant):

```bash
curl -s "https://purge.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/catalogs/<name>_catalog_v1.json"
curl -s "https://purge.jsdelivr.net/gh/sathish4earn/homlyst-catalogs@main/manifest.json"
```

Purge **both** the specific file and `manifest.json` — they cache separately,
and the app only re-fetches a catalog after it sees the manifest's version
increase. A file can already be updated on the CDN while the manifest still
points devices at the old version, so devices won't pick up the change until
the manifest itself is fresh too.

---

## Quick checklist

- [ ] Edited the item/category
- [ ] Bumped the catalog's internal `"version"`
- [ ] Bumped that catalog's `"version"` in `manifest.json`
- [ ] (v2 schema) never changed an existing item's `id`
- [ ] `git diff --stat` shows roughly the size of change you expected, not a full-file rewrite
- [ ] (only if `nameResKey` added) updated `chrome/*.json` inside `"strings"` + bumped `chrome_manifest.json`
- [ ] (only if one of the 8 bundled catalogs) synced `androidApp/src/main/assets/catalogs/` + `iosApp/iosApp/` in the HomLystKMP repo
- [ ] Pushed
- [ ] Verified live on CDN, purged if still stale
