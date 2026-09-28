- **`x86-64-v3`** - AVX2/BMI/FMA `-mtune=znver3`. Requires x86-64-v3 CPU.
- **`x86-64-v4`** - AVX-512 `-mtune=znver4`. Requires x86-64-v4 CPU.

> [!IMPORTANT]
> `v3` runs on most x86-64 CPUs from 2013+. `v4` requires AVX-512.

Built with `-O3`, `-mtune=znver3/znver4`, `-fno-plt`, `-fomit-frame-pointer`, function/loop/jump alignment.

Install, hold, and rollback instructions are in the [README](https://github.com/argonforge/mesa-builds/blob/main/README.md).
