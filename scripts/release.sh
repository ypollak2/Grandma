#!/usr/bin/env bash
# Release script for grandma — runs all checks before publishing to PyPI.
# Usage: ./scripts/release.sh
set -Eeuo pipefail

PROJECT_NAME="grandma"
EXPECTED_REMOTE="ypollak2/Grandma"
PYPI_JSON_URL="https://pypi.org/pypi/${PROJECT_NAME}/json"
TEST_PYPI_REPOSITORY="testpypi"

FORBIDDEN_SDIST_PATHS=(
  ".env"
  "CLAUDE.md"
  "MONETIZATION.md"
  "STRATEGY.md"
  "PRICING.md"
  "ROADMAP.md"
  ".claude/"
)

die() { echo "❌ ERROR: $*" >&2; exit 1; }

confirm() {
  local answer
  read -r -p "👉 $1 — type 'yes' to continue: " answer
  [[ "$answer" == "yes" ]] || die "Aborted."
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

# ── 1. Required tools ──────────────────────────────────────────────────────────
echo "==> Checking required tools"
require_cmd git
require_cmd uv
require_cmd curl
require_cmd tar

# ── 2. Git sanity ──────────────────────────────────────────────────────────────
echo "==> Checking git state"
origin_url="$(git remote get-url origin)"
[[ "$origin_url" == *"$EXPECTED_REMOTE"* ]] \
  || die "Unexpected origin: ${origin_url}. Expected to contain ${EXPECTED_REMOTE}"

git diff --quiet         || die "Working tree has unstaged changes — commit or stash first."
git diff --cached --quiet || die "Staged but uncommitted changes exist."

current_branch="$(git rev-parse --abbrev-ref HEAD)"
git fetch --tags origin
git fetch origin "$current_branch"

local_head="$(git rev-parse HEAD)"
remote_head="$(git rev-parse "origin/${current_branch}")"
[[ "$local_head" == "$remote_head" ]] || die "Local HEAD differs from origin/${current_branch} — push first."

# ── 3. Read version ────────────────────────────────────────────────────────────
echo "==> Reading version"
VERSION="$(grep -E '^__version__\s*=' src/grandma/__init__.py | head -1 | sed 's/.*"\(.*\)".*/\1/')"
[[ -n "$VERSION" ]] || die "Could not parse __version__ from src/grandma/__init__.py"
TAG="v${VERSION}"
echo "    Version: ${VERSION}  →  Tag: ${TAG}"

# ── 4. Tag must not exist ──────────────────────────────────────────────────────
echo "==> Validating tag uniqueness"
git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null && die "Tag ${TAG} already exists locally."
git ls-remote --tags origin "refs/tags/${TAG}" | grep -q . && die "Tag ${TAG} already exists on origin."

# Version must be greater than latest tag
latest_tag="$(git tag --sort=-v:refname | head -n 1 || true)"
if [[ -n "$latest_tag" ]]; then
  uv run python - "$latest_tag" "$VERSION" <<'PY'
import re, sys
from packaging.version import Version
latest_tag, version = sys.argv[1], sys.argv[2]
latest_ver = re.sub(r"^v", "", latest_tag)
if Version(version) <= Version(latest_ver):
    raise SystemExit(f"Version {version} is not bumped above latest tag {latest_tag}")
PY
fi

# ── 5. PyPI duplicate check ────────────────────────────────────────────────────
echo "==> Checking PyPI for existing release"
http_status="$(curl -fsS -o /tmp/grandma-pypi.json -w "%{http_code}" "$PYPI_JSON_URL" || true)"
if [[ "$http_status" == "200" ]]; then
  uv run python - "$VERSION" /tmp/grandma-pypi.json <<'PY'
import json, sys
from pathlib import Path
version = sys.argv[1]
data = json.loads(Path(sys.argv[2]).read_text())
if version in data.get("releases", {}):
    raise SystemExit(f"Version {version} is already published on PyPI")
PY
elif [[ "$http_status" == "404" ]]; then
  echo "    Package not on PyPI yet — first release."
else
  die "Could not query PyPI (HTTP ${http_status})."
fi

# ── 6. Lint ────────────────────────────────────────────────────────────────────
echo "==> Running ruff lint"
uvx ruff check .
uvx ruff format --check .

# ── 7. Tests ───────────────────────────────────────────────────────────────────
echo "==> Running tests"
uv sync --all-extras
uv run pytest -x --tb=short

# ── 8. Build ───────────────────────────────────────────────────────────────────
echo "==> Building sdist + wheel"
rm -rf dist build
uv build

sdist_count="$(find dist -maxdepth 1 -name "*.tar.gz" | wc -l | tr -d ' ')"
wheel_count="$(find dist -maxdepth 1 -name "*.whl"    | wc -l | tr -d ' ')"
[[ "$sdist_count" == "1" ]] || die "Expected 1 sdist, found ${sdist_count}."
[[ "$wheel_count"  == "1" ]] || die "Expected 1 wheel, found ${wheel_count}."

SDIST="$(find dist -maxdepth 1 -name "*.tar.gz" | head -1)"

# ── 9. Sdist content audit ─────────────────────────────────────────────────────
echo "==> Auditing sdist contents for secrets / internal docs"
sdist_listing="$(tar -tzf "$SDIST")"
for forbidden in "${FORBIDDEN_SDIST_PATHS[@]}"; do
  if printf '%s\n' "$sdist_listing" | grep -Eq "(^|/)${forbidden//./\\.}($|/)"; then
    die "Forbidden path found in sdist: ${forbidden}"
  fi
done
echo "    Sdist clean ✅"

# ── 10. Twine check ────────────────────────────────────────────────────────────
echo "==> Running twine check"
uvx twine check dist/*

# ── 11. TestPyPI (optional — skipped if [testpypi] not in ~/.pypirc) ──────────
echo
echo "All checks passed. Ready to release ${PROJECT_NAME} ${VERSION}."

if grep -q '^\[testpypi\]' ~/.pypirc 2>/dev/null; then
  echo "TestPyPI: https://test.pypi.org/project/${PROJECT_NAME}/${VERSION}/"
  confirm "Upload to TestPyPI first?"
  uvx twine upload --repository "$TEST_PYPI_REPOSITORY" dist/*
  echo
  echo "Verify: https://test.pypi.org/project/${PROJECT_NAME}/${VERSION}/"
  confirm "Looks good? Upload ${VERSION} to production PyPI?"
else
  echo "  (TestPyPI skipped — no [testpypi] section in ~/.pypirc)"
  confirm "Upload ${VERSION} to production PyPI?"
fi

# ── 12. Production PyPI ────────────────────────────────────────────────────────
uvx twine upload dist/*

# ── 13. Tag and push ──────────────────────────────────────────────────────────
echo "==> Creating and pushing git tag ${TAG}"
git tag -a "$TAG" -m "Release ${VERSION}"
git push origin "$TAG"

echo
echo "✅ Released ${PROJECT_NAME} ${VERSION} → https://pypi.org/project/${PROJECT_NAME}/${VERSION}/"
