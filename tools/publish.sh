#!/usr/bin/env bash
# Publish this folder as your GitHub profile page: makes the repository if it is missing, commits, pushes.
#
#   mkdir -p ~/shivrajtode-upload && cd ~/shivrajtode-upload && unzip -o "$(ls -t ~/storage/downloads/shivrajtode-repo*.zip | head -n 1)" && cd shivrajtode && bash tools/publish.sh
#
# GitHub shows the README of the repository that is named exactly like your user name (shivrajtode/shivrajtode)
# on your profile page, and only while that repository is public. This script takes care of both.
# It needs git, and gh (pkg install git gh) or a token in ~/.git-credentials.
# Optional: GH_USER=you   FORCE=1 (replace what is on GitHub instead of joining it)
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
BRANCH=main
say()  { printf '\033[1;36m==> %s\033[0m\n' "$*"; }
note() { printf '    %s\n' "$*"; }
die()  { printf '\033[1;31m!! %s\033[0m\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is missing (Termux: pkg install git)"
[ -f README.md ] && [ -f tools/build.py ] || die "run this from inside the shivrajtode folder:  bash tools/publish.sh"
case "$(pwd -P)" in
  /storage/* | /sdcard/*)
    die "git does not work on Android's shared storage (this folder is $(pwd -P)).
   Run it from Termux's own home instead:
   mkdir -p ~/shivrajtode-upload && cd ~/shivrajtode-upload && unzip -o \"\$(ls -t ~/storage/downloads/shivrajtode-repo*.zip | head -n 1)\" && cd shivrajtode && bash tools/publish.sh" ;;
esac

have_gh() { command -v gh >/dev/null 2>&1; }
gh_ok()   { have_gh && gh auth status >/dev/null 2>&1; }
token()   { [ -f "$HOME/.git-credentials" ] && sed -n 's#^https://[^:]*:\([^@]*\)@github\.com.*#\1#p' "$HOME/.git-credentials" | head -n1; }

# A GitHub user name is letters, digits and single hyphens, at most 39 long. Anything else (an error message that a
# broken login prints, say) is never taken for a name.
valid_login() { case "$1" in '' | -* | *[!A-Za-z0-9-]*) return 1 ;; esac; [ "${#1}" -le 39 ]; }

from_remote()      { [ -d .git ] && git remote get-url origin | sed -n 's#.*github\.com[:/]\([^/]*\)/.*#\1#p'; }
from_gh()          { have_gh && gh api user -q .login; }
from_gitconfig()   { git config --global github.user; }
from_credentials() { [ -f "$HOME/.git-credentials" ] && sed -n 's#^https://\([^:@/]*\)[:@].*github\.com.*#\1#p' "$HOME/.git-credentials" | head -n1; }
from_hosts()       { [ -f "$HOME/.config/gh/hosts.yml" ] && sed -n 's/^ *user: *//p' "$HOME/.config/gh/hosts.yml" | head -n1; }

detect_user() {
  local u c
  [ -n "${GH_USER:-}" ] && { printf '%s' "$GH_USER"; return; }
  for c in from_remote from_gh from_gitconfig from_credentials from_hosts; do
    u="$($c 2>/dev/null)"
    if valid_login "$u"; then printf '%s' "$u"; return; fi
  done
  printf '%s' shivrajtode
}

# ---- who, and logged in ------------------------------------------------------------------------------------------
USER_NAME="$(detect_user)"
REPO_NAME="${REPO_NAME:-$USER_NAME}"   # a profile repository has to carry your user name
say "Publishing github.com/$USER_NAME/$REPO_NAME"

if ! gh_ok && [ -z "$(token)" ]; then
  have_gh || die "Termux is not connected to GitHub yet. Run:  pkg install gh && gh auth login   then run this again."
  [ -t 0 ] || die "not logged in to GitHub. Run:  gh auth login   then run this again."
  say "Logging in to GitHub (a code is shown: type it on https://github.com/login/device)"
  gh auth login --web --git-protocol https || die "the GitHub login did not finish"
fi
gh_ok && gh auth setup-git >/dev/null 2>&1 || true

# ---- git: branch, identity, remote -------------------------------------------------------------------------------
[ -d .git ] || { git init -q && git symbolic-ref HEAD "refs/heads/$BRANCH"; }
[ "$(git symbolic-ref -q --short HEAD 2>/dev/null)" = "$BRANCH" ] || git checkout -q "$BRANCH" 2>/dev/null || git checkout -q -b "$BRANCH"

# Termux has no git identity until one is set: without it the commit stops with "Author identity unknown".
if [ -z "$(git config user.email)" ]; then
  id=""
  if gh_ok; then v="$(gh api user -q .id 2>/dev/null)" && case "$v" in '' | *[!0-9]*) ;; *) id="$v" ;; esac; fi
  git config user.email "${id:+$id+}$USER_NAME@users.noreply.github.com"
fi
[ -n "$(git config user.name)" ] || git config user.name "$USER_NAME"

REMOTE="https://github.com/$USER_NAME/$REPO_NAME.git"
if git remote get-url origin >/dev/null 2>&1; then git remote set-url origin "$REMOTE"; else git remote add origin "$REMOTE"; fi

# ---- the repository on GitHub ------------------------------------------------------------------------------------
repo_exists() { GIT_TERMINAL_PROMPT=0 git ls-remote origin >/dev/null 2>&1; }
if ! repo_exists; then
  say "Creating the public repository $USER_NAME/$REPO_NAME"
  out=""
  if gh_ok; then
    out="$(GH_PROMPT_DISABLED=1 gh repo create "$USER_NAME/$REPO_NAME" --public --description "My GitHub profile" 2>&1)"
  elif [ -n "$(token)" ]; then
    out="$(curl -sS --max-time 30 -H "Authorization: token $(token)" https://api.github.com/user/repos \
      -d "{\"name\":\"$REPO_NAME\",\"description\":\"My GitHub profile\",\"private\":false}" 2>&1)"
  fi
  for _ in 1 2 3 4; do repo_exists && break; sleep 2; done   # a new repository can take a moment to show up
  repo_exists || { [ -n "$out" ] && note "$out"
    die "could not reach or create github.com/$USER_NAME/$REPO_NAME. Check the login (gh auth status) and the connection,
   or make an EMPTY PUBLIC repository called $REPO_NAME on github.com by hand and run this again."; }
fi

# ---- commit ------------------------------------------------------------------------------------------------------
git add -A
if git diff --cached --quiet; then
  say "Nothing new to commit"
else
  if git rev-parse --verify -q HEAD >/dev/null; then msg="Update profile"; else msg="Profile: Material 3 Expressive README"; fi
  git commit -q -m "$msg" || die "the commit failed"
  say "Committed: $msg"
fi
git rev-parse --verify -q HEAD >/dev/null || die "there is nothing to publish (no commit)"

# ---- push, joining what GitHub already has -----------------------------------------------------------------------
# The branch GitHub shows is the one its HEAD points to. That is main unless the repository was made long ago.
RB="$BRANCH"
def="$(GIT_TERMINAL_PROMPT=0 git ls-remote --symref origin HEAD 2>/dev/null | sed -n 's#^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$#\1#p')"
[ -n "$def" ] && RB="$def"
OR="refs/remotes/origin/$RB"

if [ -n "${FORCE:-}" ]; then
  say "FORCE: replacing $RB on GitHub"
  git push -u -f origin "HEAD:refs/heads/$RB" || die "the push failed"
else
  if git fetch -q origin "+refs/heads/$RB:$OR" 2>/dev/null && ! git merge-base --is-ancestor "$OR" HEAD 2>/dev/null; then
    if git merge-base HEAD "$OR" >/dev/null 2>&1; then
      say "GitHub has newer changes (an edit made on github.com?). Joining them with this update:"
      git log --format='    %h %an: %s' "HEAD..$OR"
      git merge --no-edit -q "$OR" >/dev/null 2>&1 || { git merge --abort 2>/dev/null
        die "GitHub has a change that cannot be joined by itself. Nothing was pushed and nothing was changed.
   To replace what is on GitHub with this folder, run:  FORCE=1 bash tools/publish.sh"; }
    else
      say "That repository already has its own history (an older README?)."
      note "Your new profile wins where files clash. The old version stays in the history, nothing is lost."
      git merge --no-edit -q --allow-unrelated-histories -X ours "$OR" >/dev/null 2>&1 || { git merge --abort 2>/dev/null
        die "could not join the old history. Nothing was pushed and nothing was changed.
   To replace what is on GitHub with this folder, run:  FORCE=1 bash tools/publish.sh"; }
    fi
  fi
  git push -u origin "HEAD:refs/heads/$RB" || die "the push failed. Check that Termux is logged in to GitHub (gh auth status)."
fi

# ---- did it land? ------------------------------------------------------------------------------------------------
here="$(git rev-parse HEAD)"
there="$(GIT_TERMINAL_PROMPT=0 git ls-remote origin "refs/heads/$RB" 2>/dev/null | cut -f1)"
[ "$here" = "$there" ] || die "the push finished but GitHub does not show the new commit yet. Run this script once more."
note "GitHub is now at $(git rev-parse --short HEAD) on branch $RB"

code="$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' "https://api.github.com/repos/$USER_NAME/$REPO_NAME" 2>/dev/null || true)"
if [ "$code" = "404" ]; then
  note "!! The repository is PRIVATE, so GitHub will not show it on your profile. Make it public with:"
  note "   gh repo edit $USER_NAME/$REPO_NAME --visibility public --accept-visibility-change-consequences"
fi

say "Done. Your profile: https://github.com/$USER_NAME"
note "(the repository: https://github.com/$USER_NAME/$REPO_NAME)  If the page looks the same, refresh it once."
