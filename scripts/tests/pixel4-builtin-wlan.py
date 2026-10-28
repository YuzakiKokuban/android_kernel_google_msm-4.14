#!/usr/bin/env python3
"""Check the actual built-in WLAN init registers its platform driver."""
from pathlib import Path
import subprocess,tempfile
p=Path(__file__).resolve().parents[2]/'drivers/staging/qcacld-3.0/core/hdd/src/wlan_hdd_main.c'
s=p.read_text(); a=s.index('static int __init hdd_module_init(void)'); start=s.index('{',a); depth=1; end=start+1
while depth:
 depth += (s[end]=='{')-(s[end]=='}'); end+=1
function=s[a:end]
prefix=r'''
#include <stdio.h>
#include <errno.h>
#include <string.h>
#define __init
#define MODULE_INITIALIZED 1
#define hdd_fln(...) ((void)0)
static struct {int loaded_state;} loader, *wlan_loader=&loader;
static int sysret, loadret, syscalls, loads, cleanups;
static int wlan_init_sysfs(void){syscalls++; return sysret;}
static int hdd_driver_load(void){loads++; return loadret;}
static int wlan_deinit_sysfs(void){cleanups++; return 0;}
'''
main=r'''
int main(int argc,char **argv) {
 if(!strcmp(argv[1],"sysfail")) sysret=-12;
 if(!strcmp(argv[1],"loadfail")) loadret=-19;
 int result=hdd_module_init();
 if(sysret) return result==sysret && syscalls==1 && loads==0 ? 0:1;
 if(loadret) return result==loadret && loads==1 && cleanups==1 && loader.loaded_state==0 ? 0:2;
 if(result || syscalls!=1 || loads!=1 || loader.loaded_state!=1) {
  fprintf(stderr,"builtin init: result=%d registrations=%d state=%d\n",result,loads,loader.loaded_state); return 3;
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 c=Path(d)/'wlan.c'; c.write_text(prefix+function+main); e=Path(d)/'wlan'
 subprocess.run(['cc','-std=gnu11',str(c),'-o',str(e)],check=True)
 failed=[case for case in ['success','sysfail','loadfail'] if subprocess.run([str(e),case]).returncode]
 if failed: raise SystemExit('WLAN builtin regression failed: '+', '.join(failed))
 print('WLAN builtin regression: 3/3 passed')
