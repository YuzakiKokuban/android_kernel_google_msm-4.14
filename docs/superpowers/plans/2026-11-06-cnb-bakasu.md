# CNB BakaSU migration design

Approved scope: use CNB aaaa03e40200825133d21402cad8f2a86939a778 for the matching PixelOS ROM. Replace KernelSU-Next with BakaSU 516d3e87fbc986ccefdde2c2765f1700612441a9. Preserve CNB driver and module configuration, release string and SUSFS v2.3.0. Work only in WSL Linux filesystem. No flashing or upstream branch replacement.

# Implementation plan

- [x] Create isolated WSL branch from exact CNB revision; inspect existing hooks and build baseline configuration.
- [x] Verify BakaSU identity check fails before replacement. Replace root gitlink, adapt only incompatible root/SUSFS hooks and Kconfig. Keep non-root config identical.
- [x] Run full ARM64 Image.lz4 and modules build. Check linked BakaSU/SUSFS symbols and unchanged non-root configuration.
- [x] Review diff and record build commands, source pins, output checksums and runtime limitations. Export patch and build artifacts.

Review focus: duplicate hook execution, exec filename ownership, SUSFS ABI compatibility, module vermagic, build toolchain differences. Compile/link validation cannot prove phone boot or root runtime.

Review: independent reviewer found boot-event gating regression; reproduced by exec test, fixed, regression passed. Full Image.lz4 + modules build exited 0, 27/27 modules. No device runtime testing.
