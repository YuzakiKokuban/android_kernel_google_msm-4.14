from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1]
import hashlib
new=(p/'arch/arm64/configs/floral_defconfig').read_text()
nonroot='\n'.join(l for l in new.splitlines() if 'CONFIG_KSU' not in l).encode()
# SHA-256 values from the pinned CNB base; works without fetching its history.
assert hashlib.sha256(nonroot).hexdigest() == '2be5a06df38daced03f171a0de765442531357e6e186b01ffa88cd9238870385', 'non-root defconfig changed'
assert hashlib.sha256((p/'Makefile').read_bytes()).hexdigest() == '2d30ff727b7dd21879e57b248b0b1ef11716eb379f40ce6cc1eea90e25d1821c', 'kernel release changed'
assert subprocess.check_output(['git','-C',str(p/'KernelSU'),'rev-parse','HEAD'],text=True).strip()=='516d3e87fbc986ccefdde2c2765f1700612441a9'
assert 'CONFIG_KSU_SUSFS=y' in (p/'out/.config').read_text()
print('PASS: non-root defconfig and kernel release unchanged; BakaSU pin and SUSFS enabled')
