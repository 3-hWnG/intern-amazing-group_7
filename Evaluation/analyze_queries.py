"""Chấm SƠ BỘ chất lượng truy vấn (không tra web) cho file queries_baseline_*.csv.

Luật heuristic, có báo nhầm — chỉ để ước lượng và lọc ứng viên, không thay cho bước tra thử:
    no_diac       truy vấn mất hết dấu
    off_topic     truy vấn chứa < 50% từ khoá của tên thủ tục (topic)
    facet_ok      câu hỏi dạng facet_* mà truy vấn không giữ khía cạnh (bao lâu / lệ phí / ở đâu ...)
    copy_example  truy vấn chép ví dụ mẫu (thuê trọ, Đà Nẵng ...) dù thủ tục khác
    bad           một trong các lỗi trên

Mặc định chấm cột queries_raw (truy vấn mô hình trả). Thêm --sent để chấm queries_llm
(truy vấn thực sự gửi đi: mô hình không trả thì là câu viết lại + năm).

    .venv\\Scripts\\python.exe Evaluation\\analyze_queries.py Evaluation\\results\\queries_baseline_1.5b_fewshot_off.csv
Ghi ra <file>_scored.csv cạnh file đầu vào.
"""
import pandas as pd, json, re, unicodedata, sys
from collections import Counter
def fold(s):
    s=unicodedata.normalize('NFD',str(s).lower()); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return s.replace('đ','d')
def toks(s): return set(re.findall(r'[a-z0-9]+',fold(s)))
STOP=set('thu tuc cap dang ky giay lai moi va cho cua o tai the nhung gi la co khong'.split())
FACET={'facet_time':r'bao lau|thoi gian|thoi han|may ngay|bao nhieu ngay|mat bao|khi nao',
       'facet_fee':r'le phi|phi|tien|chi phi|mien phi',
       'facet_place':r'o dau|noi nop|co quan|dia diem|dia chi|noi lam|tai dau|nop o',
       'facet_online':r'online|truc tuyen|dich vu cong|vneid|qua mang',
       'facet_docs':r'giay to|ho so|thanh phan|can gi|chuan bi'}
d=pd.read_csv(sys.argv[1]); COL='queries_llm' if '--sent' in sys.argv else 'queries_raw'
d['q']=d[COL].apply(lambda x:' | '.join(json.loads(x)) if isinstance(x,str) else '')
ins=d[d.in_scope==1].copy()
def has_diac(s): return fold(s)!=str(s).lower()
ins['no_diac']=ins.q.apply(lambda s: s!='' and not has_diac(s))
def cover(r):
    t=toks(r.topic)-STOP
    return len(t & toks(r.q))/len(t) if t else 1
ins['topic_cov']=ins.apply(cover,axis=1)
ins['off_topic']=ins.topic_cov<0.5
def facet_ok(r):
    p=FACET.get(r.variant); 
    return None if not p else bool(re.search(p,fold(r.q)))
ins['facet_ok']=ins.apply(facet_ok,axis=1)
ins['copy_example']=ins.apply(lambda r: bool(re.search(r'thue tro|da nang|tre moi sinh',fold(r.q))) and not re.search(r'tam tru|khai sinh',fold(r.topic)),axis=1)
ins['bad']=ins.no_diac|ins.off_topic|(ins.facet_ok==False)|ins.copy_example
print('cột chấm:', COL, '· n', len(ins))
for c in ['no_diac','off_topic','copy_example','bad']: print(c, ins[c].sum(), f"{ins[c].mean():.1%}")
f=ins[ins.facet_ok.notna()]; print('facet_miss', (f.facet_ok==False).sum(),'/',len(f), f"{(f.facet_ok==False).mean():.1%}")
print(ins.groupby('variant').agg(n=('qid','size'),bad=('bad','mean'),off=('off_topic','mean'),nodiac=('no_diac','mean')).round(2).to_string())
print(ins.groupby('topic').bad.mean().sort_values().tail(8).round(2).to_string())
oos=d[d.in_scope==0]; print('OOS route', oos.route.value_counts().to_dict()); print(oos.groupby('oos_kind').route.apply(lambda s:(s!='search').mean()).round(2).to_dict())
print('intent', d.intent.value_counts().head(12).to_dict())
print('clarify variants', ins[ins.route=='clarify'].variant.value_counts().to_dict())
print('gate', d.gate.value_counts().to_dict())
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',70)
if '--examples' in sys.argv: print(ins[ins.off_topic].sample(12,random_state=3)[['question','topic','q']].to_string())
if '--examples' in sys.argv: print(ins[ins.facet_ok==False].sample(6,random_state=3)[['question','variant','q']].to_string())
out=sys.argv[1].rsplit('.',1)[0]+'_scored.csv'; ins.to_csv(out,index=False,encoding='utf-8-sig'); print('Đã lưu', out)
