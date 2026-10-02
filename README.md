# Mesa for Devuan Excalibur (Debian Trixie base)

Optimized [Mesa](https://gitlab.freedesktop.org/mesa/mesa.git) (video driver) packages for Devuan Excalibur and Debian Trixie, built for modern CPUs.

## Requirements

- **Distribution:** Devuan Excalibur (stable) or Debian Trixie (stable)
- **Architecture:** amd64
- **CPU:** x86-64-v3 (AVX2) or x86-64-v4 (AVX-512) - pick the matching variant

**Packages will not run** on CPUs without AVX2/AVX-512. Check support:

```bash
grep -o 'avx[0-9_]*' /proc/cpuinfo | sort -u
```

If the output is empty - **do not install these packages**.

## Packages

<details>
<summary>Package list</summary>

| Package               | Purpose                               |
|-----------------------|---------------------------------------|
| `mesa-libgallium`     | Main Gallium library (radeonsi, RADV) |
| `mesa-vulkan-drivers` | Vulkan drivers (RADV for AMD)         |
| `libgl1-mesa-dri`     | DRI drivers for OpenGL                |
| `libglx-mesa0`        | GLX library                           |
| `libegl-mesa0`        | EGL library                           |
| `libgbm1`             | GBM (buffers for Wayland/KMS)         |
| `libosmesa6`          | Offscreen rendering                   |
| `libxatracker2`       | XA tracker (XvBA)                     |
| `mesa-va-drivers`     | VA-API (hardware video decoding)      |
| `mesa-vdpau-drivers`  | VDPAU (hardware video decoding)       |

Development headers (`*-dev`) are also published in the same repository for users who build against Mesa.

Each release is published as two variants:

| Codename        | CPU requirement     | Version suffix |
|-----------------|---------------------|----------------|
| `stable-avx2`   | x86-64-v3 (AVX2)    | `+avx2`        |
| `stable-avx512` | x86-64-v4 (AVX-512) | `+avx512`      |

Debug packages (`*-dbgsym`) are **not included** - they do not affect performance and only take up space.
</details>

## APT repository

The repository is hosted on GitHub Pages:

```
https://argonforge.github.io/mesa-builds
```

### 1. Import the signing key

```bash
curl -fsSL https://argonforge.github.io/mesa-builds/public.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/argonforge-mesa.gpg
```

### 2. Add the repository

Pick the codename matching your CPU. **Only one of the two, not both.**

For x86-64-v3 (AVX2 - most x86-64 CPUs from 2013+):

```bash
echo "deb [signed-by=/usr/share/keyrings/argonforge-mesa.gpg] https://argonforge.github.io/mesa-builds stable-avx2 main" \
  | sudo tee /etc/apt/sources.list.d/argonforge-mesa.list
```

For x86-64-v4 (AVX-512 - Zen 4/5):

```bash
echo "deb [signed-by=/usr/share/keyrings/argonforge-mesa.gpg] https://argonforge.github.io/mesa-builds stable-avx512 main" \
  | sudo tee /etc/apt/sources.list.d/argonforge-mesa.list
```

### 3. Install

<details>
<summary>APT command</summary>

```bash
sudo apt update
sudo apt install \
    mesa-libgallium \
    mesa-vulkan-drivers \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libegl-mesa0 \
    libgbm1 \
    libosmesa6 \
    libxatracker2 \
    mesa-va-drivers \
    mesa-vdpau-drivers \
    libd3dadapter9-mesa \
    mesa-drm-shim \
    mesa-opencl-icd
```

`apt` may mark the packages as `DOWNGRADING` if a newer version was installed from another source. This is expected - the Argon Forge build replaces the stock packages.

</details>

### 4. Hold versions (recommended)

To prevent `apt upgrade` from reverting to stock packages:

```bash
MESA_PKGS="libd3dadapter9-mesa libegl-mesa0 libgbm1 libgl1-mesa-dri \
  libglx-mesa0 libosmesa6 libxatracker2 mesa-drm-shim mesa-libgallium \
  mesa-opencl-icd mesa-va-drivers mesa-vdpau-drivers mesa-vulkan-drivers"

sudo apt-mark hold $MESA_PKGS
```

### 5. Reboot

```bash
sudo reboot
```

### 6. Verify

```bash
# Confirm the version
apt policy mesa-libgallium

# OpenGL
glxinfo | grep "OpenGL renderer"

# Vulkan
vulkaninfo --summary | grep -A 3 GPU0
```

Expected output (for Radeon 780M):

```
OpenGL renderer string: AMD Radeon 780M (radeonsi, phoenix, ...)
deviceName = AMD Radeon 780M (RADV PHOENIX)
driverName = radv
driverInfo = Mesa 25.0.7-2+deb13u1+avx512
```

The version string should end with `+avx2` or `+avx512` depending on the codename you selected.

## Manual installation (alternative)

If you prefer not to add the repository:

### 1. Download and extract

```bash
mkdir -p ~/mesa-opt && cd ~/mesa-opt
gh release download --repo argonforge/mesa-builds --pattern '*.zst'

# Unpack archives matching your CPU and needs:
tar --zstd -xf mesa-*-x86-64-v4.tar.zst        # AVX-512 runtime
tar --zstd -xf mesa-*-dev-x86-64-v4.tar.zst    # optional: dev headers
```

Or download the `.zst` files manually from the [Releases](../../releases) page.
The `*dev*` archives are optional - skip them if you don't need development headers.

### 2. Back up current packages

```bash
sudo mkdir -p /root/mesa-backup
sudo cp /var/cache/apt/archives/mesa-*.deb /root/mesa-backup/ 2>/dev/null || true
```

### 3. Install

```bash
cd ~/mesa-opt
sudo apt install ./packages/*.deb
```

The `./` prefix is required - otherwise `apt` will look for packages in repositories.

## Rollback

If graphics become unstable, freeze, or show artifacts:

```bash
# Unhold
MESA_PKGS="libd3dadapter9-mesa libegl-mesa0 libgbm1 libgl1-mesa-dri \
  libglx-mesa0 libosmesa6 libxatracker2 mesa-drm-shim mesa-libgallium \
  mesa-opencl-icd mesa-va-drivers mesa-vdpau-drivers mesa-vulkan-drivers"
sudo apt-mark unhold $MESA_PKGS

# Remove the Argon Forge repository
sudo rm /etc/apt/sources.list.d/argonforge-mesa.list
sudo apt update

# Reinstall stock versions
sudo apt install --reinstall $MESA_PKGS

sudo reboot
```

If you installed manually:

```bash
sudo apt install --reinstall $MESA_PKGS
sudo reboot
```

## Expected Performance

| Component                          | Gain   | Comment                                |
|------------------------------------|--------|----------------------------------------|
| CPU part of driver (radeonsi/RADV) | 1-3%   | Noticeable only in CPU-bound scenarios |
| Shader compilation (ACO)           | **0%** | ACO does not use Mesa build flags      |
| Games on iGPU (Radeon 780M)        | ~0-2%  | Bottleneck is memory bandwidth         |

**Honest note:** the gain is small and mostly matters in CPU-bound scenarios. For iGPU (Radeon 780M) memory bandwidth is the bottleneck, not driver code.

Source workflow: [`.github/workflows/build-devuan-stable.yml`](.github/workflows/build-devuan-stable.yml).

## Companion projects

For a complete optimized graphics stack on **AMD Zen (x86-64-v3/v4)**:

| Project                                                                    | Purpose                           |
|----------------------------------------------------------------------------|-----------------------------------|
| [`gamescope-builds`](https://github.com/argonforge/gamescope-builds)       | Micro-compositor for game scaling |
| [`dxvk-builds`](https://github.com/argonforge/dxvk-builds)                 | DXVK (D3D9/10/11 -> Vulkan)       |
| [`vkd3d-proton-builds`](https://github.com/argonforge/vkd3d-proton-builds) | VKD3D-Proton (D3D12 -> Vulkan)    |
| [`wine-builds`](https://github.com/argonforge/wine-builds)                 | Wine WoW64 (Clang)                |

## Important

- Packages are built for **Debian Trixie / Devuan Excalibur** (same library base). Installing on Bookworm, Daedalus or other releases will break graphics due to glibc and library version mismatches.
- Packages are **signed with the Argon Forge key**. Verify the fingerprint against the one published at `https://argonforge.github.io/mesa-builds/public.asc` before trusting the repository.
- **Do not add both codenames** (`stable-avx2` and `stable-avx512`) at the same time. Choose the one matching your CPU.
- **Do not install v4 packages** if you are unsure about AVX-512 support. Use `stable-avx2` if your CPU has only AVX2.
- The author is not responsible for any system issues. Always have a Live USB ready for recovery.

## License

The build scripts and GitHub Actions workflows in this repository
are licensed under the MIT License. See LICENSE file.

The Mesa source code and Debian packaging files are distributed
under their respective licenses - see the mesa source package
for details. The compiled `.deb` packages in Releases and in the
APT repository are redistributions of Mesa under its original license.
