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

### 2. Copy the example workflow into your project repository

Create `.github/workflows/build.yml` in your Godot project repository. A complete
ready-to-use example is provided at [`example/build.yml`](example/build.yml) in this
repository.

The workflow builds the editor and both export templates for every combination of
OS (Linux, macOS, Windows) and cipher (AES-256, Camellia-256, ARIA-256), runs
integration tests, and produces merged per-cipher release artifacts only when all
tests pass.

### 3. Minimal single-job example

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

## Inputs

### Godot source

| Input | Default | Description |
|-------|---------|-------------|
| `godot-version` | `4.6-stable` | Godot version tag or branch to download (e.g. `4.6-stable`, `master`). The source is downloaded and cached automatically. Leave empty only if the source is already present in the workspace. |
| `godot-repo` | `godotengine/godot` | GitHub repository to download Godot source from. |
| `godot-source` | `godot-source` | Path where the Godot source root is, or will be downloaded to, relative to the workspace. |
| `cache-godot-source` | `true` | Cache the downloaded Godot source between runs, keyed by `godot-repo` and `godot-version`. The cached copy is always the clean unpatched source so it is safe to share across cipher combinations and concurrent jobs. |

### Godot Secure patch

| Input | Default | Description |
|-------|---------|-------------|
| `godot-secure-repo` | `emabrey/Godot-Secure` | GitHub repository to download the Godot Secure release artifact from. Leave empty to skip downloading and applying the patch. |
| `godot-secure-tag` | `v1.0.2-alpha` | Release tag to download `godot_secure.py` from. |
| `algorithm` | `aes` | Cipher algorithm: `aes`, `camellia`, or `aria`. All three use a 256-bit key. You must use the same algorithm for every platform binary in a project distribution. See [Choosing a cipher](#choosing-a-cipher). |
| `encryption-key` | *(empty — random)* | 64-character hex AES-256 encryption key. Pass your secret here: `encryption-key: ${{ secrets.GODOT_ENCRYPTION_KEY }}`. When omitted, Godot Secure generates a random key for the build (recorded in the log artifact). |
| `advanced-kdf` | `true` | Enable the advanced key derivation function for additional key hardening. |

### Build

| Input | Default | Description |
|-------|---------|-------------|
| `target` | `all` | Build target(s): `editor`, `template_debug`, `template_release`, or `all` (compiles all three). |
| `platform` | *(auto)* | SCons platform name. Auto-detected from the runner OS when omitted. See [Platform auto-detection](#platform-auto-detection). |
| `arch` | *(auto)* | Target architecture (e.g. `x86_64`, `arm64`, `universal`). Auto-detected when omitted. |
| `precision` | `single` | Floating-point precision: `single` or `double`. |
| `lto` | `full` | Link-time optimisation: `none` or `full`. `full` produces smaller, faster binaries at the cost of longer link time. Recommended for release distributions. |
| `extra-scons-args` | *(empty)* | Additional SCons arguments appended verbatim to every build invocation. Example: `use_llvm=yes linker=mold`. |
| `scons-cache` | `true` | Cache compiled SCons objects between runs. A warm cache reduces build time by 60–90 %. |
| `scons-cache-path` | `.scons-cache` | Directory used for the SCons object cache. |
| `python-version` | `3.x` | Python version used to run SCons and Godot Secure. |

### Platform auto-detection

When `platform` is not specified the action maps the runner OS to the SCons platform name:

| Runner OS | SCons platform | Extra SCons args added automatically |
|-----------|----------------|--------------------------------------|
| Linux | `linuxbsd` | *(none)* |
| macOS | `macos` | `vulkan_sdk_path=<molten-vk prefix>` |
| Windows | `windows` | `d3d12=yes` |

Architecture defaults are `x86_64` on Linux and Windows, and `universal` (fat binary) on macOS.

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

Run this matrix across `ubuntu-latest`, `macos-latest`, and `windows-latest` to get
a complete set of binaries. See [`example/build.yml`](example/build.yml) for the full
workflow including integration tests and artifact packaging.

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
          path: |
            ${{ steps.godot-secure.outputs.editor-path }}
            ${{ steps.godot-secure.outputs.template-debug-path }}
            ${{ steps.godot-secure.outputs.template-release-path }}
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

### Use a pre-checked-out source tree (no auto-download)

Omit `godot-version` if you have already checked out the source yourself.

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

All three ciphers use a 256-bit key and produce binaries that accept the same
`SCRIPT_AES256_ENCRYPTION_KEY` environment variable and Godot project key setting.
The difference is the internal cipher used to encrypt the pack file — choose the
one that best fits your distribution requirements.

| Cipher | `algorithm` value | Standard | Notes |
|--------|-------------------|----------|-------|
| AES-256 | `aes` | NIST FIPS 197 | Default. Widest adoption and hardware acceleration. |
| Camellia-256 | `camellia` | ISO/IEC 18033-3, RFC 3713 | Co-designed by NTT and Mitsubishi; approved for Japanese government use. |
| ARIA-256 | `aria` | Korean KSDS, RFC 5794 | South Korean national standard; mandatory for Korean government systems. |

Every binary in a project distribution **must use the same cipher**. A Linux build
compiled with `algorithm: camellia` cannot read a pack file encrypted by a Windows
build compiled with `algorithm: aes`.

---

## How it works

1. **Sets up Python** and installs SCons via pip.
2. **Restores the Godot source cache** (read-only). If the source is already cached, the download is skipped entirely. The cache always holds the clean unpatched source so it is safe to share across jobs that apply different ciphers.
3. **Downloads the Godot Engine source** as a tarball from GitHub when `godot-version` is set and no cached copy exists. Release tags and branch names are both supported — the action tries the tag URL first and falls back to the branch URL automatically.
4. **Saves the clean source cache** immediately after download, before any patching, so the cached copy is always unmodified.
5. **Downloads `godot_secure.py`** from the specified release of `godot-secure-repo`.
6. **Applies the Godot Secure patch** with the chosen `algorithm`. The encryption key is masked in logs and passed to the script exclusively via the `SCRIPT_AES256_ENCRYPTION_KEY` environment variable.
7. **Installs system dependencies** for the runner OS:
   - **Linux** — X11, OpenGL, audio, Wayland, and input headers via `apt-get`
   - **macOS** — MoltenVK (Vulkan) and yasm via Homebrew
   - **Windows** — D3D12 Agility SDK via the Godot-bundled install script
8. **Restores the SCons object cache** (when `scons-cache` is `true`) to reuse compiled objects from previous runs.
9. **Runs SCons** for each requested target, parallelising across all available CPU cores, with `--implicit-cache` to skip unchanged dependency scans.
10. **Locates the compiled binaries** under `bin/` and writes their absolute paths to the action outputs.

---

## Requirements

- Godot 4.x source. Tested against `4.5-stable`, `4.6-stable`, and `master`.
- A repository secret named `GODOT_ENCRYPTION_KEY` containing a 64-character hex string. The same key must be set in your Godot project's export encryption settings.
- All platform binaries in a project distribution must be built with the same `algorithm`.
