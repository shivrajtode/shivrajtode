# tools

Every image on the profile page is drawn by `build.py`. Change the words or the colours, run it, push.

## Publish from Termux

`publish.sh` puts this folder on GitHub as your profile page. It sets a git identity if Termux has none, makes the public `shivrajtode/shivrajtode` repository if it is missing, commits, and pushes. Run it from Termux's own home, not from `~/storage/downloads`, because git does not work on Android's shared storage:

```sh
mkdir -p ~/shivrajtode-upload && cd ~/shivrajtode-upload && unzip -o "$(ls -t ~/storage/downloads/shivrajtode-repo*.zip | head -n 1)" && cd shivrajtode && bash tools/publish.sh
```

Running it again after an update is safe. It needs `git` and either `gh` (`pkg install git gh`, then `gh auth login`) or a token in `~/.git-credentials`. If someone edited the repo on github.com in the meantime, those changes are joined in first. `FORCE=1 bash tools/publish.sh` replaces what is on GitHub with this folder instead.

## Regenerate

Run these from the repo root:

```sh
pip install -r tools/requirements.txt    # just fonttools, pure Python
python3 tools/build.py                   # rebuilds assets/ only
python3 tools/build.py --readme          # also rewrites README.md
```

Without `--readme` your hand edits to `README.md` are left alone.

## What to edit

All of it is in the CONTENT block at the top of `build.py`.

| Name | What it controls |
| --- | --- |
| `NAME`, `TAGLINE`, `TELEGRAM` | hero text and the contact button |
| `SEED` | the Material colour seeds as `(hue, chroma)`. Change one number and the whole page re-themes, light and dark |
| `PROJECTS` | the four cards: title, link, description, chips, icon, shape, colour roles, corner radii |
| `ABOUT_ROWS` | the rows in the "About phone" card |

Shapes you can use in `PROJECTS` (`shape=`): circle, cookie7, cookie9, cookie12, clover4, flower8, sunny, burst, pentagon, triangle, diamond, squircle, pill, pillv, gem, rose6.

Icons (`icon=`): bolt, phones, shield, chip, person, phone, flask, terminal, arrow, back, plane.

## Files

- `build.py` draws the images and the README.
- `publish.sh` pushes the folder to GitHub (see above).
- `m3.py` is a small Material 3 toolkit: HCT colour (CAM16) and tonal palettes, the M3 colour roles for light and dark, expressive shapes that can morph into one another, text turned into outlines with kerning, and the SMIL animation helpers.
- `fonts/` holds Outfit (headings and body) and Red Hat Mono (the command chips). Both are SIL Open Font License 1.1, and the licence files sit next to the fonts.

## Good to know

- The images are plain SVG: no scripts, no external requests, no tracking. Text is converted to outlines, so it looks the same on every device.
- `assets/static/` has still copies of the animated images. The README serves them to viewers who have "reduce motion" turned on.
- Light and dark versions are switched with `<picture>` and `prefers-color-scheme`.
- GitHub caches raw files for a few minutes, so after a push a hard refresh may be needed before a change shows up.
- This is an unofficial take on the Material 3 Expressive look. It is not made by or affiliated with Google.
