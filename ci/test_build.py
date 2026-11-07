import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("builder", Path(__file__).with_name("build.py"))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Artifacts(unittest.TestCase):
    def test_missing_wlan_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            for f in ("arch/arm64/boot/Image.lz4", "arch/arm64/boot/dtb.img", "arch/arm64/boot/dtbo.img", "include/config/kernel.release"):
                p = out / f; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b"data")
            (out / ".config").write_text("CONFIG_KSU=y\nCONFIG_KSU_SUSFS=y\nCONFIG_LTO_CLANG=y\nCONFIG_CFI_CLANG=y\nCONFIG_QCA_CLD_WLAN=m\n")
            with self.assertRaisesRegex(ValueError, "wlan"):
                builder.validate(out)

    def test_release_must_keep_wireshark_name(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            for f in ("arch/arm64/boot/Image.lz4", "arch/arm64/boot/dtb.img", "arch/arm64/boot/dtbo.img", "wlan.ko"):
                p=out/f; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b"data")
            (out/".config").write_text("CONFIG_KSU=y\nCONFIG_KSU_SUSFS=y\nCONFIG_LTO_CLANG=y\nCONFIG_CFI_CLANG=y\nCONFIG_QCA_CLD_WLAN=m\n")
            p=out/"include/config/kernel.release"; p.parent.mkdir(parents=True); p.write_text("4.14.357-openela")
            with self.assertRaisesRegex(ValueError, "WireShark"):
                builder.validate(out)

if __name__ == "__main__": unittest.main()
