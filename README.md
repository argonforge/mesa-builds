# Mesa for Devuan Excalibur (Debian Trixie base)

Optimized Mesa (video driver) packages for Devuan Excalibur, built for modern CPUs.

Packages are built automatically via GitHub Actions inside a clean `devuan/devuan:excalibur` Docker container and published in the [Releases](../../releases) section.

## Requirements

- **Distribution:** Devuan Excalibur (stable)
- **Architecture:** amd64
- **CPU:** x86-64-v3 (AVX2) or x86-64-v4 (AVX-512) — pick the matching variant

**Packages will not run** on CPUs without AVX2/AVX-512. Check support:

```bash
grep -o 'avx[0-9_]*' /proc/cpuinfo | sort -u
```

If the output is empty — **do not install these packages**.

## Packages

<details>
<summary>Package list</summary>

| Package | Purpose |
|---|---|
| `mesa-libgallium` | Main Gallium library (radeonsi, RADV) |
| `mesa-vulkan-drivers` | Vulkan drivers (RADV for AMD) |
| `libgl1-mesa-dri` | DRI drivers for OpenGL |
| `libglx-mesa0` | GLX library |
| `libegl-mesa0` | EGL library |
| `libgbm1` | GBM (buffers for Wayland/KMS) |
| `libosmesa6` | Offscreen rendering |
| `libxatracker2` | XA tracker (XvBA) |
| `mesa-va-drivers` | VA-API (hardware video decoding) |
| `mesa-vdpau-drivers` | VDPAU (hardware video decoding) |

Debug packages (`*-dbgsym`) are **not included** in releases — they do not affect performance and only take up space.
</details>

## Installation

### 1. Download and extract

```bash
mkdir -p ~/mesa-opt && cd ~/mesa-opt
gh release download --repo argonforge/mesa-optimized --pattern '*.zst'

# Pick ONE:
tar --zstd -xf mesa-*-x86-64-v4.tar.zst   # AVX-512 (Zen 4/5)
# or
tar --zstd -xf mesa-*-x86-64-v3.tar.zst   # AVX2 (Zen 1/2/3)
```

Or download the `.zst` files manually from the [Releases](../../releases) page.
You can exclude `*dev*` packages if you don't need them.

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

The `./` prefix is required — otherwise `apt` will look for packages in repositories.

`apt` may mark some packages as `DOWNGRADING` even though the version is the same. This is a replacement of the stock build with a local one, not an actual downgrade.

### 4. Hold versions

To prevent `apt upgrade` from reverting to stock packages. See [Hold & Rollback](#hold--rollback)

### 5. Reboot

```bash
sudo reboot
```

## Verification

```bash
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
driverInfo = Mesa 25.0.7-2+deb13u1
```

## Hold & Rollback

```bash
MESA_PKGS="libd3dadapter9-mesa libegl-mesa0 libgbm1 libgl1-mesa-dri \
  libglx-mesa0 libosmesa6 libxatracker2 mesa-drm-shim mesa-libgallium \
  mesa-opencl-icd mesa-va-drivers mesa-vdpau-drivers mesa-vulkan-drivers"

# Hold
sudo apt-mark hold $MESA_PKGS

# If graphics become unstable, freeze, or show artifacts:
# Unhold
sudo apt-mark unhold $MESA_PKGS

# Reinstall stock versions
sudo apt install --reinstall $MESA_PKGS

sudo reboot
```

## Expected Performance

| Component | Gain | Comment |
|---|---|---|
| CPU part of driver (radeonsi/RADV) | 1–3% | Noticeable only in CPU-bound scenarios |
| Shader compilation (ACO) | **0%** | ACO does not use Mesa build flags |
| Games on iGPU (Radeon 780M) | ~0–2% | Bottleneck is memory bandwidth |

**Honest note:** the gain is small and mostly matters in CPU-bound scenarios. For iGPU (Radeon 780M) memory bandwidth is the bottleneck, not driver code.

Source workflow: [`.github/workflows/build-mesa.yml`](.github/workflows/build-mesa.yml).

## Companion projects

For a complete optimized graphics stack on **AMD Zen (x86-64-v3/v4)**:

| Project | Purpose |
|---|---|
| [`gamescope-builds`](https://github.com/argonforge/gamescope-builds) | Micro-compositor for game scaling |
| [`dxvk-builds`](https://github.com/argonforge/dxvk-builds) | DXVK (D3D9/10/11 → Vulkan) |
| [`vkd3d-proton-builds`](https://github.com/argonforge/vkd3d-proton-builds) | VKD3D-Proton (D3D12 → Vulkan) |
| [`wine-builds`](https://github.com/argonforge/wine-builds) | Wine WoW64 (Clang) |

## Important

- Packages are built **only for Devuan Excalibur**. Installing on Daedalus (oldstable) or other releases may break graphics.
- Packages are **not signed**. Verify integrity using SHA-256 from the release description.
- **Do not install v4 packages** if you are unsure about AVX-512 support. Use v3 if your CPU has only AVX2.
- The author is not responsible for any system issues. Always have a Live USB ready for recovery.

## License

The build scripts and GitHub Actions workflows in this repository
are licensed under the MIT License. See LICENSE file.

The Mesa source code and Debian packaging files are distributed
under their respective licenses — see the mesa source package
for details. The compiled .deb packages in Releases are
redistributions of Mesa under its original license.
