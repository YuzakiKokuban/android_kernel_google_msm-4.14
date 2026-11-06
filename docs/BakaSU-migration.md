# CNB BakaSU integration

Base: its-hecker/infinity_cnb_kernel_google_msm-4.14 at aaaa03e40200825133d21402cad8f2a86939a778.
Root: Baka-SU/BakaSU at 516d3e87fbc986ccefdde2c2765f1700612441a9.
Existing CNB SUSFS v2.3.0, release definition and non-root floral_defconfig entries are preserved.

Clone submodules recursively. Select floral_defconfig. CONFIG_KSU_SUSFS is the hook mode; CONFIG_KSU_MANUAL_HOOK must remain disabled because these are mutually exclusive BakaSU modes.

Validation commands:

    python3 tests/test-bakasu-exec.py
    python3 tests/test-bakasu-config.py
    make O=out ARCH=arm64 CC=clang CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- floral_defconfig
    make O=out ARCH=arm64 CC=clang LD=ld.lld CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabi- -j12 Image.lz4 modules

Local validation uses LLVM 12.0.1 and host OpenSSL 3 (via PKG_CONFIG_LIBDIR and LD_LIBRARY_PATH); no host compatibility workaround changes kernel source or device config.
The exec regression harness compiles the actual wrapper with test doubles. It verifies boot events remain enabled when su compatibility is disabled, error handling, post hooks and filename lifetime. It does not simulate Android userspace.

This source is for the matching CNB-based ROM. No standalone driver built-ins or vendor modifications are introduced. Build success does not establish phone boot, BakaSU manager operation, SUSFS concealment or binary compatibility with modules from a different compiler/build. Rebuild ROM modules with this tree where needed. Device validation remains required.

## Verified local result (2026-11-06)

Full Image.lz4 and modules build exited 0. All 27 modules listed in modules.order were produced. Linked symbols include ksu_handle_execveat, ksu_handle_post_execveat, ksu_handle_sys_reboot and susfs_init. BakaSU version string: 35257-516d3e87. Local kernel release: 4.14.357-WireShark+. Both Python checks pass. No device was flashed.
