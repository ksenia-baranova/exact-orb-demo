from pathlib import Path
import datetime,json,sys
B=Path(__file__).parent
final='--final'in sys.argv
p=B/('experiment_stop_final.json'if final else'experiment_stop.json');assert not p.exists(),'immutable stop record'
start=json.loads((B/'execution_start.json').read_text(encoding='utf-8'))
run='run04-delivery'if final else'run04'
idx=json.loads((B/run/'index.json').read_text(encoding='utf-8'))
assert len(idx['records'])==24 and not idx.get('failure')
assert all(x['pass']for x in idx['controls'])and all(x['pass']for x in idx['boundary']['controls'])
now=datetime.datetime.now(datetime.timezone.utc);t0=datetime.datetime.fromisoformat(start['started_at'])
data={'author':'Codex / Developer','task':'TASK-D-005','stop_condition':'sufficient bounded evidence: explicit construction counterexamples + independent positive controls; no further tuning','stopped_utc':now.isoformat(),'stopped_MSK':now.astimezone(datetime.timezone(datetime.timedelta(hours=3))).isoformat(),'started_to_stop_wall_hours':(now-t0).total_seconds()/3600,'wall_within_12h_from_STARTED':(now-t0).total_seconds()<=12*3600,'browser_started':idx['meta']['started'],'browser_ended':idx['meta']['ended'],'browser_wall_seconds':idx['meta']['browserWallSeconds'],'effort_note':'Wall envelope includes interruptions and tool approval waits, is NOT measured effort/timesheet or a basis for reconstructing D003/remaining budget. Assessment preparation already included once in estimate. No extra experiment allowed after this stop.','actual_effort_hours':None,'browser_cells':24,'browser_controls':len(idx['controls']),'boundary_controls':len(idx['boundary']['controls']),'experiment_hours_cap':12,'browser_harness_cap':4,'analytics_cap':4}
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if final:
 data['authoritative_run']=run
 data['initial_stop_preserved']='experiment_stop.json'
 data['post_audit_correction']='10 misses had no activation event in first run. Same model/inputs repeated with global capture in run04-delivery; no parameter tuning, no budget extension. Both runs and original sources retained. This is final experiment stop.'
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('D005_EXPERIMENT_STOP '+json.dumps({k:data[k]for k in ['stopped_MSK','started_to_stop_wall_hours','wall_within_12h_from_STARTED','browser_wall_seconds']}))
