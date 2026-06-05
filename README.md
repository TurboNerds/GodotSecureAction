# GodotSecureAction

A GitHub Action that compiles the Godot Engine editor and export templates from a C++ source tree.

This action is the build-from-source counterpart to [appsinacup/action_setup_godot](https://github.com/appsinacup/action_setup_godot), which downloads pre-built binaries. Use this action when you need to compile a patched or customised Godot build — for example, a source tree modified by [Godot Secure](https://github.com/emilymabrey93/Godot-Secure).

---

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `godot-source` | No | `.` | Path to the Godot C++ source root, relative to the workspace. |
| `target` | No | `editor` | Build target(s): `editor`, `template_debug`, `template_release`, or `all`. |
| `platform` | No | *(auto)* | Target platform. Auto-detected from runner OS when omitted. |
| `arch` | No | *(auto)* | Target architecture (e.g. `x86_64`, `arm64`, `universal`). Auto-detected when omitted. |
| `precision` | No | `single` | Floating-point precision: `single` or `double`. |
| `use-lto` | No | `false` | Enable link-time optimisation. Recommended only for release template builds. |
| `extra-scons-args` | No | *(empty)* | Additional SCons arguments appended verbatim to every build invocation. |
| `scons-cache` | No | `false` | Enable caching of the SCons build cache between runs. |
| `scons-cache-path` | No | `.scons-cache` | Directory used for the SCons build cache. |
| `python-version` | No | `3.x` | Python version to set up for running SCons. |

### Platform auto-detection

When `platform` is not specified the action maps the GitHub Actions runner OS to the SCons platform name:

| Runner OS | SCons platform |
|-----------|---------------|
| Linux | `linuxbsd` |
| macOS | `macos` |
| Windows | `windows` |

### Architecture auto-detection

When `arch` is not specified the action uses `x86_64` on Linux and Windows runners, and `universal` (fat binary) on macOS runners.

---

## Outputs

| Output | Description |
|--------|-------------|
| `editor-path` | Absolute path to the compiled editor binary. Empty if not built. |
| `template-debug-path` | Absolute path to the compiled debug export template. Empty if not built. |
| `template-release-path` | Absolute path to the compiled release export template. Empty if not built. |

---

## Usage

### Build the Godot editor on the current runner OS

```yaml
- uses: emilymabrey93/action_godot_engine@v1
  with:
    godot-source: vendored/godot
    target: editor
```

### Build all targets with caching and LTO

```yaml
- uses: emilymabrey93/action_godot_engine@v1
  with:
    godot-source: vendored/godot
    target: all
    use-lto: true
    scons-cache: true
```

### Pass custom SCons arguments

```yaml
- uses: emilymabrey93/action_godot_engine@v1
  with:
    godot-source: vendored/godot
    target: editor
    extra-scons-args: use_llvm=yes linker=mold
```

### Use the output paths in a downstream step

```yaml
- name: Build Godot editor
  id: godot-build
  uses: emilymabrey93/action_godot_engine@v1
  with:
    godot-source: vendored/godot
    target: editor

- name: Run headless tests
  run: |
    "${{ steps.godot-build.outputs.editor-path }}" \
      --headless --path my_project --quit
```

---

## Full workflow example — Godot Secure + build

This is the intended end-to-end workflow when using Godot Secure to produce a cryptographically unique Godot build.

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

      - name: Checkout Godot source
        uses: actions/checkout@v4
        with:
          repository: godotengine/godot
          ref: 4.4-stable
          path: godot-source

      - name: Checkout Godot Secure
        uses: actions/checkout@v4
        with:
          repository: emilymabrey93/Godot-Secure
          path: godot-secure

      - name: Patch Godot source with Godot Secure
        env:
          SCRIPT_AES256_ENCRYPTION_KEY: ${{ secrets.GODOT_ENCRYPTION_KEY }}
        run: |
          python godot-secure/godot_secure.py godot-source \
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

      - name: Build Godot editor and export templates
        id: godot-build
        uses: emilymabrey93/action_godot_engine@v1
        with:
          godot-source: godot-source
          target: all
          scons-cache: true
          use-lto: true

      - name: Upload editor binary
        uses: actions/upload-artifact@v4
        with:
          name: godot-editor-linux
          path: ${{ steps.godot-build.outputs.editor-path }}

      - name: Upload debug template
        uses: actions/upload-artifact@v4
        with:
          name: godot-template-debug-linux
          path: ${{ steps.godot-build.outputs.template-debug-path }}

      - name: Upload release template
        uses: actions/upload-artifact@v4
        with:
          name: godot-template-release-linux
          path: ${{ steps.godot-build.outputs.template-release-path }}
```

Store `GODOT_ENCRYPTION_KEY` as an [encrypted Actions secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets). The Godot Secure log uploaded as an artifact contains the security token — store it in secure external storage immediately.

---

## How it works

1. **Sets up Python** using `actions/setup-python`, then installs SCons via pip.
2. **Installs system dependencies** appropriate for the runner OS:
   - Linux: X11, OpenGL, audio, and input headers via `apt-get`
   - macOS: yasm via Homebrew (Xcode command-line tools are pre-installed)
   - Windows: no extra steps required — MSVC is pre-installed on GitHub-hosted runners
3. **Restores the SCons cache** (optional) to speed up incremental rebuilds.
4. **Runs SCons** for each requested target, parallelising across all available CPU cores.
5. **Locates the compiled binaries** under the `bin/` directory and writes their absolute paths to the action outputs.

---

## Requirements

- The Godot C++ source tree must already be present in the workspace before this action runs.
- Godot 4.x source is supported.
- For Godot Secure builds, run the Godot Secure patch script **before** this action.
