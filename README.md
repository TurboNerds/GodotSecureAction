# GodotSecureAction

A GitHub Action that builds a cryptographically hardened Godot Engine from source.
It downloads the Godot Engine C++ source, applies the [Godot Secure](https://github.com/emabrey/Godot-Secure) patch to replace the default pack encryption with a uniquely keyed cipher, and compiles the editor and export templates — all in a single step.

The produced binaries are drop-in replacements for the official Godot editor and export templates and work with any Godot 4.x project.

---

## Quick start

### 1. Add an encryption key secret

Generate a 64-character hex key and store it as a repository secret named `GODOT_ENCRYPTION_KEY`:

```sh
python -c "import secrets; print(secrets.token_hex(32))"
```

Go to **Settings → Secrets and variables → Actions → New repository secret** and paste the output.

Set the same key in your Godot project under **Project → Export → Encryption → Script encryption key**.

### 2. Create the build workflow

Create `.github/workflows/build.yml` in your Godot project repository:

```yaml
name: Build Godot Secure

on:
  workflow_dispatch:
  push:
    branches: [main]

jobs:
  build:
    name: ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - name: Build Godot Secure
        id: godot-secure
        uses: emabrey/GodotSecureAction@v1
        with:
          godot-version:  '4.6-stable'
          algorithm:      aes              # aes · camellia · aria — pick one, use it everywhere
          encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}

      - name: Upload binaries
        uses: actions/upload-artifact@v4
        with:
          name: godot-secure-${{ steps.godot-secure.outputs.algorithm }}-${{ runner.os }}
          path: godot-source/bin/
```

Push a commit. The workflow builds the editor and both export templates for Linux, macOS, and Windows in parallel. When all three jobs finish, download the artifact for your platform and use the editor to export your project.

### 3. Pick up your binaries

After the workflow succeeds, go to **Actions → your run → Artifacts** and download the zip for your OS:

```
godot-secure-aes-Linux.zip     → editor + template_debug + template_release (ELF x86_64)
godot-secure-aes-macOS.zip     → editor + template_debug + template_release (arm64)
godot-secure-aes-Windows.zip   → editor + template_debug + template_release (.exe x86_64)
```

Run the editor on your machine to export your project.

---

## Choosing a cipher

Pick one algorithm and use it for **every** OS build. A pack file exported with an AES editor cannot be opened by a Camellia template.

| Cipher | `algorithm` value | Standard | Notes |
|--------|-------------------|----------|-------|
| AES-256 | `aes` | NIST FIPS 197 | Default. Widest adoption; hardware acceleration on most platforms. |
| Camellia-256 | `camellia` | ISO/IEC 18033-3, RFC 3713 | Co-designed by NTT and Mitsubishi; approved for Japanese government use. |
| ARIA-256 | `aria` | Korean KSDS, RFC 5794 | South Korean national standard; mandatory for Korean government systems. |

All three use a 256-bit key and accept the same `SCRIPT_AES256_ENCRYPTION_KEY` environment variable and Godot project key setting.

---

## Inputs

### Godot source

| Input | Default | Description |
|-------|---------|-------------|
| `godot-version` | `4.6-stable` | Godot version tag or branch (e.g. `4.6-stable`, `master`). Downloaded and cached automatically. Leave empty only if the source is already in the workspace. |
| `godot-repo` | `godotengine/godot` | GitHub repository to download Godot source from. |
| `godot-source` | `godot-source` | Path where the Godot source root is, or will be downloaded to, relative to the workspace. |
| `cache-godot-source` | `true` | Cache the downloaded Godot source between runs. The cached copy is always the clean unpatched source — safe to share across cipher combinations and concurrent jobs. |

### Godot Secure patch

| Input | Default | Description |
|-------|---------|-------------|
| `godot-secure-repo` | `emabrey/Godot-Secure` | GitHub repository to download the Godot Secure script from. Leave empty to skip patching. |
| `godot-secure-tag` | `v1.0.2-alpha` | Release tag to download `godot_secure.py` from. |
| `algorithm` | `aes` | Cipher: `aes`, `camellia`, or `aria`. Every platform binary in a distribution must use the same cipher. |
| `encryption-key` | *(empty — random)* | 64-character hex encryption key. Pass your repository secret here. When omitted a random key is generated and recorded in the log artifact. |
| `advanced-kdf` | `true` | Enable the advanced key derivation function for additional key hardening. |

### Build

| Input | Default | Description |
|-------|---------|-------------|
| `target` | `all` | Build targets: `editor`, `template_debug`, `template_release`, or `all`. |
| `platform` | *(auto)* | SCons platform name. Auto-detected from the runner OS when omitted. |
| `arch` | *(auto)* | Target architecture (e.g. `x86_64`, `arm64`). Auto-detected when omitted. |
| `precision` | `single` | Floating-point precision: `single` or `double`. |
| `lto` | `auto` | Link-time optimisation: `none`, `auto`, or `full`. `auto` skips LTO on editor/debug builds and enables thin LTO on release templates — the best default for most workflows. Use `full` when building release distributions. |
| `extra-scons-args` | *(empty)* | Additional SCons arguments appended to every build invocation. Example: `use_llvm=yes linker=mold`. |
| `scons-cache` | `true` | Cache compiled SCons objects between runs. A warm cache reduces build time by 60–90 %. |
| `scons-cache-path` | `.scons-cache` | Directory used for the SCons object cache. |
| `python-version` | `3.x` | Python version used to run SCons and Godot Secure. |

### Platform auto-detection

| Runner OS | SCons platform | Extra SCons args injected automatically |
|-----------|----------------|----------------------------------------|
| Linux | `linuxbsd` | *(none)* |
| macOS | `macos` | `vulkan_sdk_path=<molten-vk prefix>` |
| Windows | `windows` | `d3d12=yes` |

Architecture defaults: `x86_64` on Linux and Windows, auto-detected on macOS (arm64 on Apple Silicon runners).

---

## Outputs

| Output | Description |
|--------|-------------|
| `godot-source-path` | Absolute path to the Godot source tree used for the build. |
| `godot-secure-script` | Absolute path to the downloaded `godot_secure.py`. Empty when `godot-secure-repo` was not set. |
| `editor-path` | Absolute path to the compiled editor binary. Empty if not built. |
| `template-debug-path` | Absolute path to the compiled debug export template. Empty if not built. |
| `template-release-path` | Absolute path to the compiled release export template. Empty if not built. |

---

## More examples

### Trigger on a release tag and produce fully optimised binaries

```yaml
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - name: Build Godot Secure
        id: godot-secure
        uses: emabrey/GodotSecureAction@v1
        with:
          godot-version:  '4.6-stable'
          algorithm:      aes
          encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}
          lto:            full          # maximum optimisation for a release build

      - uses: actions/upload-artifact@v4
        with:
          name: godot-secure-${{ steps.godot-secure.outputs.algorithm }}-${{ runner.os }}
          path: godot-source/bin/
```

### Run the editor in a downstream step

```yaml
- name: Build Godot Secure
  id: build
  uses: emabrey/GodotSecureAction@v1
  with:
    godot-version:  '4.6-stable'
    algorithm:      aes
    encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}
    target:         editor

- name: Headless version check
  run: |
    "${{ steps.build.outputs.editor-path }}" --headless --version
```

### Pin to a specific Godot Secure release

```yaml
- uses: emabrey/GodotSecureAction@v1
  with:
    godot-version:    '4.6-stable'
    godot-secure-tag: 'v1.2.0'
    algorithm:        camellia
    encryption-key:   ${{ secrets.GODOT_ENCRYPTION_KEY }}
```

### Use a fork of Godot Secure

```yaml
- uses: emabrey/GodotSecureAction@v1
  with:
    godot-version:     '4.6-stable'
    godot-secure-repo: 'my-org/my-godot-secure-fork'
    godot-secure-tag:  'v2.0.0'
    algorithm:         aes
    encryption-key:    ${{ secrets.GODOT_ENCRYPTION_KEY }}
```

### Pass custom SCons arguments

```yaml
- uses: emabrey/GodotSecureAction@v1
  with:
    godot-version:    '4.6-stable'
    algorithm:        aes
    encryption-key:   ${{ secrets.GODOT_ENCRYPTION_KEY }}
    extra-scons-args: 'use_llvm=yes linker=mold'
    target:           editor
```

### Build all three ciphers at once

Only needed when you want to support multiple cipher options for different distribution contexts (e.g. one build for general users and one for a regulatory region).

```yaml
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os:     [ubuntu-latest, macos-latest, windows-latest]
        cipher: [aes, camellia, aria]
    steps:
      - name: Build Godot Secure
        id: godot-secure
        uses: emabrey/GodotSecureAction@v1
        with:
          godot-version:  '4.6-stable'
          algorithm:      ${{ matrix.cipher }}
          encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}

      - uses: actions/upload-artifact@v4
        with:
          name: godot-secure-${{ steps.godot-secure.outputs.algorithm }}-${{ runner.os }}
          path: godot-source/bin/
```

---

## Provided workflows

This repository ships two workflows used for developing and releasing GodotSecureAction itself. They are not needed for typical project use — the quick start workflow above is all most projects need.

### `build.yml` — CI on every push to `main`

Verifies the action works across all cipher and OS combinations after every change. Runs the full 9-job build matrix (3 ciphers × 3 OSes) and four integration tests before producing any artifacts.

### `release.yml` — distributable release zips

Triggered by a tag push (`v*`) or manually from the Actions tab. Produces one zip per cipher containing the editor and both export templates for all three platforms.

| Artifact | Contents |
|----------|----------|
| `godot-{version}-aes-release.zip` | `linux/` `macos/` `windows/` — editor + template_debug + template_release |
| `godot-{version}-camellia-release.zip` | same layout |
| `godot-{version}-aria-release.zip` | same layout |

---

## How it works

1. **Sets up Python** and installs SCons via pip.
2. **Restores the Godot source cache** (read-only). On a cache hit the download is skipped. The cached copy is always the clean unpatched source — safe to share across jobs that apply different ciphers.
3. **Downloads the Godot Engine source** as a tarball from GitHub when `godot-version` is set and no cached copy exists. Tag URLs are tried first; branch URLs are used as a fallback.
4. **Saves the clean source cache** immediately after download and before any patching.
5. **Downloads `godot_secure.py`** from the configured release tag.
6. **Applies the Godot Secure patch** with the chosen `algorithm`. The encryption key is masked in logs and passed exclusively via the `SCRIPT_AES256_ENCRYPTION_KEY` environment variable.
7. **Installs system dependencies** for the runner OS:
   - **Linux** — X11, OpenGL, audio, Wayland, and input headers via `apt-get`
   - **macOS** — MoltenVK (Vulkan) and yasm via Homebrew
   - **Windows** — D3D12 Agility SDK via the Godot-bundled install script
8. **Restores the SCons object cache** to reuse compiled objects from previous runs (when `scons-cache` is `true`).
9. **Runs SCons** for each requested target across all available CPU cores, with `--implicit-cache` to skip unchanged dependency scans across runs.
10. **Locates the compiled binaries** under `bin/` and writes their absolute paths to the step outputs.

---

## Requirements

- Godot 4.x source. Tested against `4.5-stable`, `4.6-stable`, and `master`.
- A repository secret named `GODOT_ENCRYPTION_KEY` containing a 64-character hex string. The same key must be entered in your Godot project's export encryption settings.
- All platform binaries in a project distribution must be built with the same `algorithm`.
