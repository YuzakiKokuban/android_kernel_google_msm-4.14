#!/usr/bin/env python3
"""Build the PixelOS 17 CNB kernel without changing its root driver or config."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

CLANG_REV = '29182889399818f97baa65ea238c80e8117981eb'
CLANG_URL = f'https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/{CLANG_REV}/clang-r596125.tar.gz'


def validate(out):
    out = Path(out)
    required = ['arch/arm64/boot/Image.lz4', 'arch/arm64/boot/dtb.img',
                'arch/arm64/boot/dtbo.img', 'include/config/kernel.release']
    for name in required:
        p = out / name
        if not p.is_file() or not p.stat().st_size:
            raise ValueError('Missing kernel output: ' + name)
    config = (out / '.config').read_text().splitlines()
    for name in ('KSU', 'KSU_SUSFS', 'LTO_CLANG', 'CFI_CLANG'):
        if 'CONFIG_' + name + '=y' not in config:
            raise ValueError('Required config disabled: ' + name)
    if 'CONFIG_KSU_MANUAL_HOOK=y' in config:
        raise ValueError('Conflicting KSU manual hook')
    if 'CONFIG_QCA_CLD_WLAN=m' in config and not list(out.rglob('wlan.ko')):
        raise ValueError('Missing wlan module')
    release = (out / 'include/config/kernel.release').read_text().strip()
    if 'WireShark' not in release or 'Kokuban-Kaltsit-BakaSU' not in release:
        raise ValueError('Kernel release must retain Kokuban and WireShark naming')
    return release


def compiler(directory):
    if directory:
        p = Path(directory).resolve()
        if not (p / 'bin/clang').is_file():
            raise ValueError('Missing clang in ' + str(p))
        return p
    p = Path(os.environ.get('KOKUBAN_CLANG_CACHE', '~/.cache/kokuban/clang-r596125')).expanduser().resolve()
    if not (p / 'bin/clang').is_file():
        p.mkdir(parents=True, exist_ok=True)
        archive = p.with_suffix('.tar.gz')
        print('Downloading pinned AOSP clang-r596125', flush=True)
        urllib.request.urlretrieve(CLANG_URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(p, filter='data')
        archive.unlink()
    version = subprocess.check_output([str(p / 'bin/clang'), '--version'], text=True)
    if 'r596125' not in version:
        raise ValueError('Unexpected compiler: ' + version)
    return p


def dtc_binary():
    # The Android DTC accepts this tree's overlays; distro DTC 1.7 asserts on them.
    dest = Path('~/.cache/kokuban/dtc-android').expanduser().resolve()
    expected = '46b5bf79dee40514a4877878ce9a8fd3f2dd0396a16c6f54a9572ae0bf9a7ead'
    if not dest.is_file() or hashlib.sha256(dest.read_bytes()).hexdigest() != expected:
        url = 'https://android.googlesource.com/platform/prebuilts/misc/+/be7c3a630b5dc5eb3260035d77a81b2f322754f8/linux-x86/dtc/dtc?format=TEXT'
        data = base64.b64decode(urllib.request.urlopen(url, timeout=120).read())
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Android DTC checksum mismatch')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        dest.chmod(0o755)
    return str(dest)


def mkdtimg_binary():
    dest = Path('~/.cache/kokuban/bin/mkdtimg').expanduser().resolve()
    expected = '32ed014e05e653c22f43d53f412041330ea3631e0c376808aaa51a379f0efe8a'
    if not dest.is_file() or hashlib.sha256(dest.read_bytes()).hexdigest() != expected:
        url = 'https://android.googlesource.com/kernel/prebuilts/build-tools/+/811c6e2938d53b3c318d7635b03931601a68c765/linux-x86/bin/mkdtimg?format=TEXT'
        data = base64.b64decode(urllib.request.urlopen(url, timeout=120).read())
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('mkdtimg checksum mismatch')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        dest.chmod(0o755)
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--artifact-dir', type=Path, default=Path.cwd())
    parser.add_argument('--clang-dir')
    parser.add_argument('--dtc')
    parser.add_argument('--jobs', type=int, default=int(os.environ.get('KOKUBAN_MAKE_JOBS', os.cpu_count() or 1)))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    subprocess.run(['python3', str(Path(__file__).with_name('test_build.py'))], check=True)
    source = args.source.resolve()
    out = (args.out or source / 'out').resolve()
    tc = compiler(args.clang_dir or os.environ.get('KOKUBAN_CLANG_DIR'))
    env = os.environ.copy()
    env['PATH'] = str(tc / 'bin') + ':' + str(mkdtimg_binary().parent) + ':' + env['PATH']
    # These inherited variables belong to the caller's kernel build, if any.
    for name in ('KBUILD_SRC', 'KBUILD_OUTPUT', 'LOCALVERSION'):
        env.pop(name, None)
    command = ['make', '-C', str(source), 'O=' + str(out), 'ARCH=arm64', 'LLVM=1', 'LLVM_IAS=1',
               'CC=clang', 'HOSTCC=clang', 'HOSTCFLAGS=-fcommon', 'HOSTLDFLAGS=-fuse-ld=lld',
               'CLANG_TRIPLE=aarch64-linux-gnu-', 'CROSS_COMPILE=aarch64-linux-gnu-',
               'CROSS_COMPILE_ARM32=arm-linux-gnueabi-']
    dtc = args.dtc or os.environ.get('KOKUBAN_DTC') or dtc_binary()
    if not dtc:
        raise ValueError('Install device-tree-compiler or pass --dtc')
    command.append('DTC_EXT=' + str(Path(dtc).resolve()))
    subprocess.run(command + ['floral_defconfig'], env=env, check=True)
    subprocess.run(command + ['-j' + str(args.jobs), 'Image.lz4', 'dtbs', 'dtbo.img', 'modules'], env=env, check=True)
    # Android's device build concatenates the generated base DTBs separately.
    dtbs = sorted((out / 'arch/arm64/boot/dts').rglob('*.dtb'))
    if not dtbs:
        raise ValueError('Missing base DTBs')
    (out / 'arch/arm64/boot/dtb.img').write_bytes(b''.join(path.read_bytes() for path in dtbs))
    release = validate(out)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    dest = args.artifact_dir.resolve() / ('Pixel4_Kernel-' + release + '-images-modules.zip')
    files = {name: out / name for name in ('.config', 'System.map', 'Module.symvers', 'include/config/kernel.release')}
    for name in ('Image.lz4', 'dtb.img', 'dtbo.img'):
        files[name] = out / 'arch/arm64/boot' / name
    for path in out.rglob('*.ko'):
        files['modules/' + str(path.relative_to(out))] = path
    sums = ''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + name + '\n' for name, path in sorted(files.items()))
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, path in files.items():
            z.write(path, name)
        z.write(source / 'ci/pixelos17.json', 'source-provenance.json')
        z.writestr('SHA256SUMS', sums)
        z.writestr('README.txt', 'Pixel 4 PixelOS 17 kernel build outputs.\nThis is NOT a recovery-flashable AnyKernel ZIP.\nUse the matching ROM device tree to package boot and its vendor modules.\n')
    with zipfile.ZipFile(dest) as z:
        if z.testzip() is not None:
            raise ValueError('Archive CRC failed')
    print('Kernel build verified: ' + release, flush=True)
    print('Artifact: ' + str(dest), flush=True)


if __name__ == '__main__':
    main()
