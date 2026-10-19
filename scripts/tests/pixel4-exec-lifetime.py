#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# Host-side regression for the actual exec wrapper's filename ownership.
from pathlib import Path
import subprocess
import os
import tempfile
root = Path(__file__).resolve().parents[2]
s = (root / 'fs/exec.c').read_text()
start=s.index('static int do_execveat_common(')
end=s.index('\nint do_execve(', start)
wrapper=s[start:end]
harness=r'''
#include <stdint.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#define CONFIG_KSU_MANUAL_HOOK 1
#define IS_ERR(p) ((uintptr_t)(p) > (uintptr_t)-4096)
struct filename { const char *name; int refcnt; };
struct user_arg_ptr { void *ptr; };
static int result;
static int posts;
static int frees;
static void putname(struct filename *name) {
    if (--name->refcnt == 0) { frees++; free(name); }
}
static int ksu_handle_execveat(int *fd, struct filename **name, void *argv, void *envp, int *flags) { return 0; }
static int __do_execveat_common(int fd, struct filename *name, struct user_arg_ptr argv, struct user_arg_ptr envp, int flags) {
    if (!IS_ERR(name)) putname(name);
    return result;
}
static int ksu_handle_post_execveat(int *fd, struct filename **name, void *argv, void *envp, int *flags, int *retval) {
    if (!IS_ERR(*name)) assert(strcmp((*name)->name, "/system/bin/sh") == 0);
    posts++;
    return 0;
}
'''+wrapper+r'''
int main(void) {
    struct user_arg_ptr args = {0};
    for (int i = 0; i < 2; i++) {
        struct filename *name = malloc(sizeof(*name));
        *name = (struct filename){"/system/bin/sh", 1};
        result = i ? -13 : 0;
        assert(do_execveat_common(-100, name, args, args, 0) == result);
    }
    result = -14;
    assert(do_execveat_common(-100, (void *)(intptr_t)-14, args, args, 0) == -14);
    assert(posts == 3);
    assert(frees == 2);
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="pixel4-exec-lifetime-") as directory:
    source = Path(directory) / "test.c"
    binary = Path(directory) / "test"
    source.write_text(harness)
    subprocess.run(["gcc", "-g", "-fsanitize=address", "-o", str(binary), str(source)], check=True)
    # LSan cannot operate under the sandbox's ptrace; frees are asserted above.
    result = subprocess.run([str(binary)], capture_output=True, text=True,
                            env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"})
    print("exec lifetime regression:", "PASS" if result.returncode == 0 else "FAIL")
    if result.returncode:
        print(result.stderr)
    raise SystemExit(result.returncode)
