#!/usr/bin/env python3
"""Compile the actual PDR registration code and test early/late subscribers."""
from pathlib import Path
import subprocess, tempfile
root = Path(__file__).resolve().parents[2]
source = (root / 'techpack/audio/dsp/audio_pdr.c').read_text()
source = source[source.index('static struct pd_qmi_client_data audio_pdr_services'):source.index('void *audio_pdr_service_register')]
stub = r'''
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <pthread.h>
#define pr_err(...) ((void)0)
#define pr_debug(...) ((void)0)
#define EXPORT_SYMBOL(x)
#define AUDIO_PDR_DOMAIN_ADSP 0
#define AUDIO_PDR_DOMAIN_MAX 1
#define AUDIO_PDR_FRAMEWORK_DOWN 0
#define AUDIO_PDR_FRAMEWORK_UP 1
#define LOCATOR_DOWN 0
#define LOCATOR_UP 1
#define NOTIFY_OK 0
#define DEFINE_MUTEX(x) pthread_mutex_t x = PTHREAD_MUTEX_INITIALIZER
#define mutex_lock(x) pthread_mutex_lock(x)
#define mutex_unlock(x) pthread_mutex_unlock(x)
struct notifier_block { int (*notifier_call)(struct notifier_block *, unsigned long, void *); int priority; };
struct pd_qmi_client_data { char *client_name; char *service_name; int total_domains; };
struct srcu_notifier_head { struct notifier_block *nb; };
static int registration_error;
static int srcu_notifier_chain_register(struct srcu_notifier_head *h, struct notifier_block *n) { if (registration_error) return registration_error; h->nb=n; return 0; }
static int srcu_notifier_chain_unregister(struct srcu_notifier_head *h, struct notifier_block *n) { h->nb=NULL; return 0; }
static int srcu_notifier_call_chain(struct srcu_notifier_head *h, unsigned long s, void *d) { return h->nb ? h->nb->notifier_call(h->nb,s,d) : 0; }
'''
main = r'''
static int calls, last_state=-1;
static int observe(struct notifier_block *n, unsigned long s, void *d) { calls++; last_state=s; return 0; }
int main(int argc, char **argv) {
 struct notifier_block n={.notifier_call=observe};
 struct pd_qmi_client_data data={.client_name="test",.service_name="avs/audio",.total_domains=1};
 if (!strcmp(argv[1],"null")) return audio_pdr_register(NULL)==-EINVAL ? 0:1;
 if (!strcmp(argv[1],"early")) {
  if (audio_pdr_register(&n) || calls) return 2;
  audio_pdr_locator_callback(NULL,LOCATOR_UP,&data);
 } else {
  audio_pdr_locator_callback(NULL,!strcmp(argv[1],"down")?LOCATOR_DOWN:LOCATOR_UP,&data);
  if (!strcmp(argv[1],"failed")) { registration_error=-ENOMEM; return audio_pdr_register(&n)==-ENOMEM && calls==0 ? 0:3; }
  if (audio_pdr_register(&n)) return 4;
 }
 if (calls!=1 || last_state!=(!strcmp(argv[1],"down")?0:1)) { fprintf(stderr,"%s: calls=%d state=%d\n",argv[1],calls,last_state); return 5; }
 if (audio_pdr_deregister(&n)) return 6;
 audio_pdr_locator_callback(NULL,LOCATOR_DOWN,NULL);
 return calls==1 ? 0:7;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'pdr.c'; p.write_text(stub+source+main)
 exe=Path(d)/'pdr'
 subprocess.run(['cc','-std=gnu11','-pthread',str(p),'-o',str(exe)],check=True)
 failed=[]
 for case in ['early','late','down','failed','null']:
  r=subprocess.run([str(exe),case])
  if r.returncode: failed.append(case)
 if failed: raise SystemExit('PDR regression failed: '+', '.join(failed))
 print('PDR regression: 5/5 passed')
