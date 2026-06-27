# Releasing Breadcrumbs to PyPI

The package is build-clean: `python -m build` produces a wheel + sdist that pass
`twine check`, with all template files bundled as package data. This doc covers
how to publish it.

There are two supported paths. **Trusted Publishing (recommended)** stores no
secrets; **manual token upload** is the fallback if you want to publish by hand.

---

## Path A — Trusted Publishing via GitHub Actions (recommended)

No API tokens are stored anywhere. GitHub mints a short-lived OIDC token per run.
The workflow lives at [`.github/workflows/release.yml`](.github/workflows/release.yml).

### One-time setup (per index)

1. Go to **https://pypi.org/manage/account/publishing/** (and, for the dry-run,
   the twin at **https://test.pypi.org/manage/account/publishing/**).
2. Add a **pending publisher** with:
   - **PyPI project name:** `crumb-kit`
   - **Owner:** `jumbodaddystack`
   - **Repository:** `breadcrumbs`
   - **Workflow name:** `release.yml`
   - **Environment:** `pypi` (on PyPI) / `testpypi` (on TestPyPI)
3. (Optional but recommended) In the GitHub repo, create matching
   **Environments** named `pypi` and `testpypi` under
   *Settings → Environments*, and add required reviewers if you want a manual
   approval gate before each publish.

No secrets to add. That's the whole setup.

### Dry-run on TestPyPI first

Trigger the workflow manually (*Actions → release → Run workflow*). It builds,
runs the same checks CI does, and publishes to **TestPyPI**. Verify the install:

```bash
pipx install --index-url https://test.pypi.org/simple/ \
             --pip-args="--extra-index-url https://pypi.org/simple/" crumb-kit
crumb --version
```

(The extra index lets pip resolve any real deps; crumb-kit itself has none.)

### Publish to real PyPI

1. Bump `version` in `pyproject.toml` — and keep `breadcrumbs/__init__.py`
   (`__version__`) and `breadcrumbs/cli.py` (`_FALLBACK_VERSION`) in sync. Add a
   `CHANGELOG.md` entry. (Current released version: `0.1.2`.)
2. Tag and create a **GitHub Release** (e.g. `v0.1.2`). Publishing the release
   triggers the `publish-pypi` job automatically. (Alternatively, *Actions →
   release → Run workflow* via `workflow_dispatch` also publishes to real PyPI.)

```bash
git tag v0.1.2
git push origin v0.1.2
# then publish the release in the GitHub UI (or `gh release create v0.1.2`)
```

After it runs, confirm:

```bash
pipx install crumb-kit
crumb --version
```

---

## Path B — Manual upload with an API token (fallback)

If you'd rather not use Actions:

1. Create a token at **https://pypi.org/manage/account/token/** (scope it to the
   `breadcrumbs` project after the first upload; before that, an account-wide
   token is required for the initial publish).
2. Build and upload from a source checkout:

```bash
cd breadcrumbs
python -m build                      # writes dist/*.whl and dist/*.tar.gz
python -m twine check dist/*         # must PASS
python -m twine upload dist/*        # username: __token__   password: <your token>
```

To dry-run on TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

> **Note on `twine check`:** it needs a current `packaging` (≥24.1) to recognize
> Metadata-Version 2.4's `License-File` field. If you see a spurious
> `unrecognized or malformed field 'license-file'` error, upgrade in a clean
> venv: `python -m venv .venv && .venv/bin/pip install -U twine packaging`.

---

## Versioning reminder

`pyproject.toml` `version` is the **package** version (semver). It is independent
of the on-disk **record `schema_version`** (manifest `schema_version: 1`).
`crumb --version` prints both. Bump the package MAJOR only alongside a
breaking record-schema change.

A PyPI version is **permanent** — once `0.1.0` is uploaded it cannot be replaced,
only yanked. Always dry-run on TestPyPI before the first real publish.
