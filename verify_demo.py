import analysis.decision_cases as dc
result = dc.seed({'scope':'demo','reset':True})
cases = result['cases']
print(f'Toplam {len(cases)} demo vaka:')
for c in cases:
    eid = c['id']
    cat = c['category']
    ent = c['entity'][:35]
    state = c.get('state','?')
    print(f'  {eid:35} {cat:10} {ent:35} [{state}]')
