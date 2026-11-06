from pathlib import Path
import subprocess, tempfile, sys
root=Path(__file__).resolve().parents[1]
source=(root/'fs/exec.c').read_text() if len(sys.argv)==1 else subprocess.check_output(['git','show',sys.argv[1]+':fs/exec.c'],cwd=root,text=True)
a=source.index('static int do_execveat_common('); b=source.index('\nint do_execve_file(',a)
wrapper=source[a:b]
stubs=r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#define CONFIG_KSU_SUSFS 1
#define IS_ERR(p) ((long)(p)<0)
#define PTR_ERR(p) ((long)(p))
#define static_branch_likely(p) (*(p))
#define static_branch_unlikely(p) (*(p))
bool ksu_su_compat_enabled=true, susfs_is_sdcard_android_data_not_decrypted=true;
bool no_su; int session, posts, calls, result;
struct filename {int refcnt;};
struct user_arg_ptr {int unused;};
bool susfs_is_current_proc_no_su(void) {return no_su;}
int ksu_handle_execveat(int *f,struct filename **n,void *a,void *e,int *g) {calls++; return session?0:-1;}
int ksu_handle_execveat_sucompat(int *f,struct filename **n,void *a,void *e,int *g) {return ksu_handle_execveat(f,n,a,e,g);}
int ksu_handle_post_execveat_sucompat(int *f,struct filename **n,void *a,void *e,int *g,int *r) {assert((*n)->refcnt>0); posts++; return 0;}
void putname(struct filename *n) {assert(n->refcnt>0); n->refcnt--;}
int __do_execve_file(int f,struct filename *n,struct user_arg_ptr a,struct user_arg_ptr e,int g,void *file) {putname(n);return result;}
'''
main=r'''
int main(void) {
 for(int denied=0;denied<2;denied++) for(int enabled=0;enabled<2;enabled++)
 for(int decrypted=0;decrypted<2;decrypted++) for(int su=0;su<2;su++) for(int fail=0;fail<2;fail++) {
  no_su=denied; ksu_su_compat_enabled=enabled; susfs_is_sdcard_android_data_not_decrypted=!decrypted;
  session=su;posts=calls=0;result=fail?-2:0;
  struct filename n={1};struct user_arg_ptr a={0};
  assert(do_execveat_common(0,&n,a,a,0)==result);
  assert(n.refcnt==0);int active=!decrypted || (!denied&&enabled);
  assert(calls==active); assert(posts==(active&&su));
 }
 struct user_arg_ptr a={0}; assert(do_execveat_common(0,(void *)-2L,a,a,0)==-2);
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(stubs+wrapper+main)
 subprocess.run(['cc','-Werror','-o',str(p/'test'),str(p/'test.c')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS: 32 exec hook combinations, error pointer, filename reference lifetime')
