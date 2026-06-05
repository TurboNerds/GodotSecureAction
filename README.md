# GodotSecureAction

A GitHub Action that downloads the Godot Engine source, optionally downloads and applies [Godot Secure](https://github.com/emilymabrey93/Godot-Secure), then compiles the editor and/or export templates from source.

This is the build-from-source counterpart to [appsinacup/action_setup_godot](https://github.com/appsinacup/action_setup_godot), which downloads pre-built binaries. Use this action when you need to compile a patched or customised Godot build.

---

## Inputs

### Godot source

| Input | Default | Description |
|-------|---------|-------------|
| `godot-version` | `4.6-stable` | Godot version tag or branch to download (e.g. `4.6-stable`, `master`). The source is downloaded automatically. Leave empty if the source is already present in the workspace. |
| `godot-repo` | `godotengine/godot` | GitHub repository to download Godot source from. |
| `godot-source` | `godot-source` | Path where the Godot source root is, or will be downloaded to, relative to the workspace. |
| `cache-godot-source` | `true` | Cache the downloaded Godot source between runs, keyed by `godot-repo` and `godot-version`. Has no effect when `godot-version` is empty. |

### Godot Secure script

| Input | Default | Description |
|-------|---------|-------------|
| `godot-secure-repo` | `emabrey/Godot-Secure` | GitHub repository to download the Godot Secure release artifact from. Leave empty to skip downloading the script. |
| `godot-secure-tag` | `v1.0.0-alpha` | Release tag to download `godot_secure.py` from. Example: `v1.0.0-alpha`, `v1.2.0`. |

### Build

| Input | Default | Description |
|-------|---------|-------------|
| `target` | `editor` | Build target(s): `editor`, `template_debug`, `template_release`, or `all`. |
| `platform` | *(auto)* | Target platform. Auto-detected from runner OS when omitted. |
| `arch` | *(auto)* | Target architecture (e.g. `x86_64`, `arm64`, `universal`). Auto-detected when omitted. |
| `precision` | `single` | Floating-point precision: `single` or `double`. |
| `use-lto` | `false` | Enable link-time optimisation. Recommended only for release template builds. |
| `extra-scons-args` | *(empty)* | Additional SCons arguments appended verbatim to every build invocation. |
| `scons-cache` | `false` | Cache the SCons build cache between runs to speed up incremental builds. |
| `scons-cache-path` | `.scons-cache` | Directory used for the SCons build cache. |
| `python-version` | `3.x` | Python version to set up for running SCons. |

### Platform auto-detection

When `platform` is not specified the action maps the runner OS to the SCons platform name:

| Runner OS | SCons platform |
|-----------|----------------|
| Linux | `linuxbsd` |
| macOS | `macos` |
| Windows | `windows` |

### Architecture auto-detection

When `arch` is not specified the action uses `x86_64` on Linux and Windows runners, and `universal` (fat binary) on macOS runners.

---

## Outputs

| Output | Description |
|--------|-------------|
| `godot-source-path` | Absolute path to the Godot source tree used for the build. |
| `godot-secure-script` | Absolute path to the downloaded `godot_secure.py` in the workspace root. Empty when `godot-secure-repo` was not set. |
| `editor-path` | Absolute path to the compiled editor binary. Empty if not built. |
| `template-debug-path` | Absolute path to the compiled debug export template. Empty if not built. |
| `template-release-path` | Absolute path to the compiled release export template. Empty if not built. |

---

## Usage

### Auto-download Godot source and build the editor

The action downloads and caches the source automatically when `godot-version` is set.

```yaml
- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    target: editor
```

### Download the default Godot Secure release (v1.0.0-alpha)

`godot-secure-repo` defaults to `emabrey/Godot-Secure` and `godot-secure-tag` defaults to `v1.0.0-alpha`, so no extra inputs are needed to use the current stable release.

```yaml
- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    target: editor
```

### Pin to a specific Godot Secure release

```yaml
- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    godot-secure-repo: emabrey/Godot-Secure
    godot-secure-tag: v1.2.0
    target: editor
```

### Use a fork or alternate repo

```yaml
- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    godot-secure-repo: my-org/my-godot-secure-fork
    godot-secure-tag: v2.0.0
    target: editor
```

### Build all targets with caching and LTO

```yaml
- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    target: all
    use-lto: true
    scons-cache: true
    cache-godot-source: true
```

### Pass custom SCons arguments

```yaml
- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    target: editor
    extra-scons-args: use_llvm=yes linker=mold
```

### Use the output paths in a downstream step

```yaml
- name: Build Godot
  id: godot-build
  uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-version: 4.6-stable
    target: editor

- name: Run headless tests
  run: |
    "${{ steps.godot-build.outputs.editor-path }}" \
      --headless --path my_project --quit
```

### Use a pre-checked-out source tree (no auto-download)

Set `godot-source` to the path of your existing checkout and omit `godot-version`.

```yaml
- uses: actions/checkout@v4
  with:
    repository: godotengine/godot
    ref: 4.6-stable
    path: godot-source

- uses: emilymabrey93/godot_secure_action@v1
  with:
    godot-source: godot-source
    target: editor
```

---

## Full workflow example — Godot Secure + build

This is the intended end-to-end workflow. The action downloads both the Godot source and `godot_secure.py`, then you patch and build in a single job.

```yaml
name: Build Godot Secure Engine

on:
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout workflow repo
        uses: actions/checkout@v4

      - name: Download Godot source and Godot Secure script
        id: setup
        uses: emilymabrey93/godot_secure_action@v1
        with:
          godot-version: 4.6-stable
          cache-godot-source: true
          # godot-secure-repo and godot-secure-tag use their defaults:
          # emabrey/Godot-Secure @ v1.0.0-alpha
          target: all
          scons-cache: true
          use-lto: true

      - name: Apply Godot Secure patch
        env:
          SCRIPT_AES256_ENCRYPTION_KEY: ${{ secrets.GODOT_ENCRYPTION_KEY }}
        run: |
          python "${{ steps.setup.outputs.godot-secure-script }}" \
            "${{ steps.setup.outputs.godot-source-path }}" \
            --mode apply \
            --algorithm aes \
            --advanced-kdf \
            --non-interactive

      - name: Upload Godot Secure log
        uses: actions/upload-artifact@v4
        with:
          name: godot-secure-log
          path: godot_secure_*.log
          if-no-files-found: warn

      - name: Upload editor binary
        uses: actions/upload-artifact@v4
        with:
          name: godot-editor-linux
          path: ${{ steps.setup.outputs.editor-path }}

      - name: Upload debug template
        uses: actions/upload-artifact@v4
        with:
          name: godot-template-debug-linux
          path: ${{ steps.setup.outputs.template-debug-path }}

      - name: Upload release template
        uses: actions/upload-artifact@v4
        with:
          name: godot-template-release-linux
          path: ${{ steps.setup.outputs.template-release-path }}
```

Store `GODOT_ENCRYPTION_KEY` as an [encrypted Actions secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets). The Godot Secure log uploaded as an artifact contains the security token — store it in secure external storage immediately.

---

## How it works

1. **Sets up Python** using `actions/setup-python`, then installs SCons via pip.
2. **Restores the Godot source cache** (if `cache-godot-source` is true and `godot-version` is set). On a cache hit the download is skipped entirely.
3. **Downloads the Godot source** as a tarball from GitHub when `godot-version` is set and no cached copy exists. Release tags and branch names are both supported — the action tries the tag URL first and falls back to the branch URL automatically.
4. **Downloads the Godot Secure release artifact** from `https://github.com/{godot-secure-repo}/releases/download/{godot-secure-tag}/{godot-secure-asset}` when `godot-secure-repo` is set. Defaults to the `godot_secure.py` asset from `emabrey/Godot-Secure` at `v1.0.0-alpha`.
5. **Validates the source tree** by checking for `SConstruct` and fails fast with a clear error if it is missing.
6. **Installs system dependencies** appropriate for the runner OS:
   - Linux: X11, OpenGL, audio, and input headers via `apt-get`
   - macOS: yasm via Homebrew (Xcode command-line tools are pre-installed)
   - Windows: no extra steps required — MSVC is pre-installed on GitHub-hosted runners
7. **Restores the SCons build cache** (optional) to speed up incremental rebuilds.
8. **Runs SCons** for each requested target, parallelising across all available CPU cores.
9. **Locates the compiled binaries** under the `bin/` directory and writes their absolute paths to the action outputs.

---

## Requirements

- Godot 4.x source is supported.
- When using `godot-version`, no pre-existing source checkout is needed — the action handles it.
- When `godot-version` is omitted, the Godot source must already be present at `godot-source`.
- For Godot Secure builds, run the patch script **after** this action downloads the source and **before** the build step invocation (or use a two-step approach as shown in the workflow example above).
