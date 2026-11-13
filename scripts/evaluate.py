"""Repeatable synthetic routing benchmark; challenge misses remain in the report."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.analysis import recommend

DEPARTMENTS=['infrastructure','security','finance','support','operations']
def main():
    scenarios=json.loads((ROOT/'tests/scenarios.json').read_text())
    rows=[]
    tp=fp=fn=0
    for scenario in scenarios:
        actual={q['department'] for q in recommend(scenario['body'],DEPARTMENTS,'')}
        expected=set(scenario['expected'])
        tp+=len(actual & expected); fp+=len(actual-expected); fn+=len(expected-actual)
        rows.append({'id':scenario['id'],'kind':scenario['kind'],'expected':sorted(expected),
                     'actual':sorted(actual),'exact_match':actual==expected,
                     'missed':sorted(expected-actual),'unnecessary':sorted(actual-expected)})
    report={'dataset':'13 synthetic scenarios; hand-authored expected routes, not real user data',
            'scenario_count':len(rows),'exact_matches':sum(r['exact_match'] for r in rows),
            'micro_precision':round(tp/(tp+fp),4) if tp+fp else None,
            'micro_recall':round(tp/(tp+fn),4) if tp+fn else None,
            'unnecessary_consultations':fp,'missed_dependencies':fn,
            'true_positives':tp,'results':rows}
    destination=ROOT/'docs/evaluation-results.json'
    destination.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
    print('Detailed results: docs/evaluation-results.json')
if __name__=='__main__': main()
