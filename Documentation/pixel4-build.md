# Pixel 4 / Pixel 4 XL

This tree supplies the `bakasu` source branch for the CI Center project
`floral_sm8150`. It supports flame and coral using `floral_defconfig`.
Pushes to `bakasu` dispatch a central build through the repository's `CI_TOKEN`
secret, matching the CI Center's standard trigger template.

## Source and dependencies

BakaSU is fetched at build time from `https://github.com/Baka-SU/BakaSU`,
branch `main`. Before configuring a local build, run its setup script from
this kernel root:

```sh
curl -fLSs https://raw.githubusercontent.com/Baka-SU/BakaSU/main/kernel/setup.sh -o /tmp/bakasu-setup.sh
sh /tmp/bakasu-setup.sh main
```

Do not commit `KernelSU` or `drivers/kernelsu`: they are build dependencies,
not a kernel gitlink. CI runs this setup automatically and logs the BakaSU
revision. The in-tree manual hooks cover exec (including post-exec), access,
stat/fstat, and the reboot control channel. Setuid, init rc, and input hooks
use BakaSU's automatic integration. SUSFS is disabled for this 4.14 tree.

`fs/hybridmount` retains the previous Pixel 4 tree's 4.14 adaptation. Its
`IMPORT` records the upstream revision. CI keeps these in-tree sources;
it must not overwrite them with a GKI module. KEYS and TMPFS_XATTR are required.

## Build and release identity

Use LLVM 12 and GNU AArch64/ARM32 binutils, matching the CI `pixel4-4.14`
profile. LTO and CFI are disabled in this BakaSU configuration. The existing
shadow call stack configuration is retained.

CI forms the release as:

```
<Makefile kernelversion>-Kokuban-Kaltsit-BakaSU-g<12-digit source commit>-openela
```

For this baseline that is `4.14.355-Kokuban-Kaltsit-BakaSU-g<commit>-openela`.
The `openela` identity lives in LOCALVERSION, rather than EXTRAVERSION, so it
appears at the end without changing the numeric source version. Local builds
use `-Kokuban-Kaltsit-BakaSU-openela` by default. To pass a full release
suffix explicitly, clear CONFIG_LOCALVERSION in the output config first
(`scripts/config --file out/.config --set-str LOCALVERSION ""`), then pass
`LOCALVERSION=-Kokuban-Kaltsit-BakaSU-g<commit>-openela` to make. Kbuild
concatenates CONFIG_LOCALVERSION and the make LOCALVERSION argument. Automatic git suffixes are disabled to avoid duplicates.

CI reads the numeric version from the source and does not pin a patch level.
A later move to 5.10+ should preserve this release naming convention while
separately adapting and testing the build profile, hooks, drivers, and boot
format. This change does not implement that kernel migration.

CI packages Image.lz4 for the current A/B slot and retains the ROM's DTB,
DTBO, ramdisk and modules. Building is not a device boot test: validate
module ABI, boot, touch, Wi-Fi, BakaSU authorization and Hybrid Mount before
using a release on a daily device.

## Focused host regression

Run `python3 scripts/tests/pixel4-exec-lifetime.py` with GCC and AddressSanitizer
available. It extracts the actual wrapper, models the exec core consuming its
filename, and checks success, failure, and ERR_PTR paths. This checks ownership
at the integration boundary; it does not replace boot or runtime testing.
