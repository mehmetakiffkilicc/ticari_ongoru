"""Seed only a named test-results directory for advanced research browser tests."""
import json,sys
from pathlib import Path
from contextlib import closing
from analysis import engine
root=Path(sys.argv[1]).resolve()
allowed=(Path(__file__).resolve().parents[1]/'test-results').resolve()
if not root.is_relative_to(allowed): raise SystemExit('Use an isolated test-results directory.')
engine.ROOT=root
rows=[]
def add(p,c,day,cat='Gıda',city='Köln',country='DE',profit=20):
    rows.append({'Fatura Türü':'Satış Faturası','Fatura Tarihi':day,'Fatura No':f'INV-{len(rows)}','Müsteri Kodu':c,'Müsteri Ünvani':f'Müşteri {c}','Malzeme Kodu':p,'Malzeme Aciklamasi':f'Ürün {p}','Malzeme Grubu':cat,'Net Satir Tutari':'100','Satir Kari':str(profit),'Satir Maliyeti':'80','Maliyet Fiyati':'8','Maliyet nach letzter EK RE':'85','Miktar':'10','Birim Fiyati':'10','Birim':'ADET','Sehir':city,'Ülke':country,'Posta Kodu':'50000','Satici':'Ali','Ambar':'Merkez'})
for day in ['2024-10-01','2024-11-01','2024-12-01']:add('P1','C1',day)
for day in ['2024-01-01','2024-02-01']:add('OLD','C1',day)
for i in range(8):
    for p,cat in [('P1','Gıda'),('P2','Gıda'),('P3','İçecek')]:add(p,f'C{i+2}','2024-12-20',cat)
for city,country in [('İstanbul','TR'),('Ankara','TR'),('Paris','FR'),('Berlin','DE'),('New York','US'),('Hayalişehir','TR')]:add('P4',city,'2024-12-30','İçecek',city,country,profit=-10 if city=='Berlin' else 20)
report={'id':'advanced','kind':'movement','name':'advanced.csv','created':'2024-12-30','total':len(rows),'accepted':len(rows),'rejected':0,'warnings':0,'errors':0,'affected':0,'warehouses':['Merkez'],'snapshot':None,'range':['2024-01-01','2024-12-30'],'missing':{},'issues':[]}
with closing(engine.db()) as con:
    con.execute('INSERT INTO batches(id,kind,digest,name,created,rows,accepted,rejected,snapshot,report) VALUES(?,?,?,?,?,?,?,?,?,?)',('advanced','movement','advanced','advanced.csv','2024-12-30',len(rows),len(rows),0,'2024-12-30',json.dumps(report)))
    for i,r in enumerate(rows):con.execute('INSERT INTO records(batch_id,source_line,kind,fingerprint,raw,converted) VALUES(?,?,?,?,?,?)',('advanced',i+1,'movement',str(i),json.dumps(r),json.dumps(r)))
    con.commit()
print('Seeded isolated advanced research fixtures:',len(rows))
