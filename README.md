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

### 2. Add the release workflow to your project repository

Copy [`example/build.yml`](example/build.yml) from this repository into your Godot project at `.github/workflows/build.yml`.

Push a commit — GitHub Actions builds the editor and both export templates for every combination of OS (Linux, macOS, Windows) and cipher (AES-256, Camellia-256, ARIA-256), runs integration tests, and produces three release zips only when all tests pass.

### 3. Download and use a release zip

After the workflow succeeds, download the zip for your chosen cipher from the **Actions** tab:

```
godot-4.6-stable-aes-release.zip
  linux/     godot.linuxbsd.editor.x86_64
             godot.linuxbsd.template_debug.x86_64
             godot.linuxbsd.template_release.x86_64
  macos/     Godot.app  (universal fat binary)
             godot.macos.template_debug.universal
             godot.macos.template_release.universal
  windows/   godot.windows.editor.x86_64.exe
             godot.windows.template_debug.x86_64.exe
             godot.windows.template_release.x86_64.exe
```

Run the editor for your platform to export your project. Distribute the templates alongside your game — all three platforms are encrypted with the same key.

### 4. Minimal single-job example

If you only need one platform and one cipher:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: emabrey/GodotSecureAction@v1
        with:
          godot-version:  '4.6-stable'
          algorithm:      aes
          encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}
          target:         all
```

---

## Provided workflows

This repository ships two workflows. Both call `GodotSecureAction@v1` internally and run the same four integration tests before producing any release artifacts.

### `release.yml` — distributable release zips

**Trigger:** tag push (`v*`) or manual `workflow_dispatch` with an optional `godot-version` input.

Produces one zip per cipher containing the editor and both export templates for all three operating systems. These are the files end users download to build and distribute their Godot project.

| Artifact | Contents |
|----------|----------|
| `godot-{version}-aes-release.zip` | `linux/` `macos/` `windows/` — editor + template_debug + template_release |
| `godot-{version}-camellia-release.zip` | same layout |
| `godot-{version}-aria-release.zip` | same layout |

To build for a specific Godot version, go to **Actions → Build and Release Godot Secure → Run workflow** and enter the version (e.g. `4.5-stable`, `master`).

### `build.yml` — CI on every push to `main`

**Trigger:** push to `main` or manual `workflow_dispatch`.

Runs the same 9-job build matrix and integration tests to verify that the action works after every change. Also produces per-cipher packages on success, keyed to the version configured in `env.GODOT_VERSION`.

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
| `algorithm` | `aes` | Cipher: `aes`, `camellia`, or `aria`. All three use a 256-bit key. Every platform binary in a distribution must use the same cipher. See [Choosing a cipher](#choosing-a-cipher). |
| `encryption-key` | *(empty — random)* | 64-character hex encryption key. Pass your secret: `encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}`. When omitted a random key is generated and recorded in the log artifact. |
| `advanced-kdf` | `true` | Enable the advanced key derivation function for additional key hardening. |

### Build

| Input | Default | Description |
|-------|---------|-------------|
| `target` | `all` | Build targets: `editor`, `template_debug`, `template_release`, or `all`. |
| `platform` | *(auto)* | SCons platform name. Auto-detected from the runner OS when omitted. |
| `arch` | *(auto)* | Target architecture (e.g. `x86_64`, `arm64`, `universal`). Auto-detected when omitted. |
| `precision` | `single` | Floating-point precision: `single` or `double`. |
| `lto` | `full` | Link-time optimisation: `none` or `full`. `full` produces smaller, faster binaries at the cost of longer link time. |
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

Architecture defaults: `x86_64` on Linux and Windows, `universal` (fat binary) on macOS.

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

## Usage examples

### Build all targets on all platforms

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
          target:         all

      - uses: actions/upload-artifact@v4
        with:
          name: godot-${{ matrix.cipher }}-${{ runner.os }}
          path: godot-source/bin/
```

### Use the output paths in a downstream step

```yaml
- name: Build Godot Secure
  id: build
  uses: emabrey/GodotSecureAction@v1
  with:
    godot-version:  '4.6-stable'
    algorithm:      aes
    encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}
    target:         editor

- name: Smoke test
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
    target:           all
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
    target:            all
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

### Use a pre-checked-out source tree

Omit `godot-version` when the source is already in the workspace.

```yaml
- uses: actions/checkout@v4
  with:
    repository: godotengine/godot
    ref:        '4.6-stable'
    path:       godot-source

- uses: emabrey/GodotSecureAction@v1
  with:
    godot-source:   godot-source
    algorithm:      aes
    encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}
    target:         all
```

---

## Choosing a cipher

All three ciphers use a 256-bit key and accept the same `SCRIPT_AES256_ENCRYPTION_KEY` environment variable and Godot project key setting. The difference is the internal algorithm used to encrypt the pack file — choose the one that fits your distribution requirements.

| Cipher | `algorithm` value | Standard | Notes |
|--------|-------------------|----------|-------|
| AES-256 | `aes` | NIST FIPS 197 | Default. Widest adoption and hardware acceleration on most platforms. |
| Camellia-256 | `camellia` | ISO/IEC 18033-3, RFC 3713 | Co-designed by NTT and Mitsubishi; approved for Japanese government use. |
| ARIA-256 | `aria` | Korean KSDS, RFC 5794 | South Korean national standard; mandatory for Korean government systems. |

> **Every platform binary in a project distribution must use the same cipher.**
> A Linux build compiled with `algorithm: camellia` cannot open a pack file exported with an `algorithm: aes` build.

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
9. **Runs SCons** for each requested target across all available CPU cores, with `--implicit-cache` to skip unchanged dependency scans.
10. **Locates the compiled binaries** under `bin/` and writes their absolute paths to the step outputs.

---

## Integration tests

Both `build.yml` and `release.yml` run four automated tests against the Linux AES build before producing any release artifacts. The package job is skipped entirely if any test fails.

| # | Test | What it checks |
|---|------|---------------|
| 1 | Smoke test | The editor's `--version` output contains `(With Godot Secure)` |
| 2 | Headless export | A test Godot project exports successfully in headless mode |
| 3 | Magic header | The exported PCK does not carry the default Godot pack magic (`0x43504447`) |
| 4 | Anti-RE | `gdsdecomp` cannot recover an embedded canary secret from the encrypted PCK |

---

## Requirements

- Godot 4.x source. Tested against `4.5-stable`, `4.6-stable`, and `master`.
- A repository secret named `GODOT_ENCRYPTION_KEY` containing a 64-character hex string. The same key must be entered in your Godot project's export encryption settings.
- All platform binaries in a project distribution must be built with the same `algorithm`.
