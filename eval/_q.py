import sys,re
sys.path.insert(0,'D:/Finale_architect/repo')
from Database.pipeline import retrieval as R
from Database.pipeline.textutil import fold
c=R.connect('D:/Finale_architect/repo/Database/runtime/procedures.db')
def grep(*kws,dom=None,lim=30):
    q="select proc_id,name,domain,province from procedures where status='active'"
    n=0
    for r in c.execute(q):
        f=fold(r['name'])
        if all(fold(k) in f for k in kws) and (not dom or dom in r['domain']):
            print(r['proc_id'],'|',r['name'][:110],'|',r['domain'][:25],'|',r['province']);n+=1
            if n>=lim:break
def show(pid):
    r=R.build_record(c,pid)
    print('==',pid,r['name'][:100],'| prov',r['province'],'| domain',r['domain'])
    print(' fees_raw',[(f['fee_type'],f['amount_value'],f['amount_text'][:70]) for f in r['fees']][:6],'status',r['status_fees'])
    print(' fees_clean',[(f['amount_value'],f['amount_text'][:80]) for f in r['fees_clean']][:5])
    print(' time',r['processing_time_text'][:80],'| methods',[(m['submission_method'],m['processing_time_qty'],m['processing_time_unit']) for m in r['methods']][:5])
    print(' addr',r['receiving_address'][:80],'| online',r['has_online_submission'],r['online_url'][:40],'| agency',r['executing_agency'][:50])
    print(' comps',len(r['components']),[x['name'][:40] for x in r['components']][:3],'| cases',[x['case_name'][:50] for x in r['cases']][:4])
    print(' files',len(r['files_clean']),'steps',len(r['steps_clean']),'legal',[l['doc_code'] for l in r['legal_basis']][:3],'dec',r['decision_number'],'subj',r['subjects'][:2])
if __name__=='__main__':
    if sys.argv[1]=='g': grep(*sys.argv[2:])
    else:
        for p in sys.argv[1:]: show(p)
