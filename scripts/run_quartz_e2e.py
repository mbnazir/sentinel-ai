#!/usr/bin/env python3
import argparse, json, time, urllib.request, urllib.error, uuid

def call(base,token,method,path,body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(base.rstrip("/")+path,data=data,method=method,headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=120) as r:
            raw=r.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} failed: {e.code} {e.read().decode()}")

ap=argparse.ArgumentParser()
ap.add_argument("--sentinel",default="http://localhost:8000")
ap.add_argument("--token",required=True)
ap.add_argument("--quartz-url",required=True)
ap.add_argument("--from-date",required=True)
ap.add_argument("--to-date",required=True)
ap.add_argument("--poll-seconds",type=int,default=5)
args=ap.parse_args()

print("1. Registering Quartz connector")
connector=call(args.sentinel,args.token,"POST","/api/v1/connectors",{
    "name":"Quartz Local",
    "connector_type":"quartz",
    "mode":"rest-api",
    "enabled":True,
    "base_url":args.quartz_url,
    "config":{"sessions_path":"/api/sentinel/v1/login-sessions","activities_path":"/api/sentinel/v1/activities","page_size":500,"verify_tls":True}
})
cid=connector["id"]; print("   connector_id:",cid)

print("2. Testing Quartz connection")
print("  ",call(args.sentinel,args.token,"POST",f"/api/v1/connectors/{cid}/test"))

print("3. Ingesting immutable Quartz snapshots")
run=call(args.sentinel,args.token,"POST","/api/v1/ingestion-runs",{
    "connector_id":cid,"shift_date_from":args.from_date,"shift_date_to":args.to_date,
    "idempotency_key":"local-"+uuid.uuid4().hex
})
rid=run["id"]; print("   ingestion_run_id:",rid,"sessions:",run["session_count"],"activities:",run["activity_count"])

print("4. Starting background integrity scan")
scan=call(args.sentinel,args.token,"POST","/api/v1/scans",{
    "ingestion_run_id":rid,"date_from":args.from_date,"date_to":args.to_date,
    "requested_by":"local.e2e","scope":"employee_day"
})
sid=scan["id"]; print("   scan_id:",sid)

print("5. Polling scan")
while True:
    s=call(args.sentinel,args.token,"GET",f"/api/v1/scans/{sid}")
    print("  ",s["status"],"employee_days:",s["employee_days_processed"],"findings:",s["finding_count"])
    if s["status"] in {"completed","failed","cancelled"}: break
    time.sleep(args.poll_seconds)

print("6. Findings")
items=call(args.sentinel,args.token,"GET",f"/api/v1/scans/{sid}/findings")
print("   total:",len(items))
for f in items[:20]:
    print(f'   {f["severity"]:8} {f["rule_id"]:10} agent={f.get("agent_id")} date={f.get("shift_date")} {f["reason"]}')
print("\\nDashboard: http://localhost:8080")
