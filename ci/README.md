# PixelOS 17 flame kernel source

This is the kernel from PixelOS flame 20261107-1111: CNB 4.14.357 + BakaSU + SUSFS 2.3. The original kernel and BakaSU commits are recorded in pixelos17.json. BakaSU is vendored, including its out-of-tree UAPI headers fix; source-version.mk preserves the original driver identity without requiring an unpublished submodule commit.

Build on Ubuntu 24.04 x86_64:

    sudo apt-get install build-essential bc bison flex libssl-dev libelf-dev lz4 python3 binutils-aarch64-linux-gnu binutils-arm-linux-gnueabi gcc-arm-linux-gnueabi
    python3 ci/build.py --artifact-dir artifacts

The builder downloads the ROM's immutable AOSP clang-r596125 revision and checksum-pinned Android dtc/mkdtimg tools. Set KOKUBAN_CLANG_DIR or --clang-dir to reuse that compiler. Set --jobs or KOKUBAN_MAKE_JOBS to cap build parallelism. Its default config preserves LTO/CFI, BakaSU SUSFS hooks and the WireShark release string.

The artifact ZIP contains Image.lz4, concatenated base DTBs, dtbo.img, matching external modules, config, symbols and SHA256 checksums. It is NOT an AnyKernel/recovery installer. Integrate these outputs into the matching ROM/device/vendor tree. Compiling this kernel does not prove compatibility with other ROMs.

CI Center detects ci/pixelos17.json and invokes this builder without downloading a different root driver or applying its old 4.14 hook patches. Automatic root-source updates skip this pinned baseline until its hook compatibility is reviewed.
