import hashlib,json,os,pathlib,subprocess,datetime
PREFERRED=['/generate','/chat','/predict','/respond','/infer','/run']

def run(cmd,timeout=240):
    return subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)

def payload_for(spec,prompt):
    p={}; set_prompt=False
    for x in spec.get('parameters',[]):
        n=x.get('parameter_name') or x.get('name',''); l=n.lower()
        req=bool(x.get('required',False)); default=x.get('default')
        typ=(x.get('type') or {}).get('type') if isinstance(x.get('type'),dict) else x.get('type')
        if l in {'message','prompt','text','query','input','instruction','user_message'}:
            p[n]=prompt; set_prompt=True
        elif l in {'chat_history','history','messages'}: p[n]=[]
        elif l in {'max_new_tokens','max_tokens','maximum_new_tokens'}: p[n]=600
        elif l=='temperature': p[n]=0.1
        elif l=='top_p': p[n]=0.9
        elif l=='top_k': p[n]=40
        elif l in {'system','system_prompt'}: p[n]='CLAIM<=EVIDENCE. ROUTING!=REASONING. UNKNOWN REMAINS UNKNOWN.'
        elif req and default is None:
            if typ=='string' and not set_prompt:
                p[n]=prompt; set_prompt=True
            else: return None
    return p if set_prompt else None

def extract(raw):
    raw=raw.strip()
    try:
        o=json.loads(raw)
        if isinstance(o,dict):
            for k in ('Response','response','text','output','message'):
                if isinstance(o.get(k),str): return o[k].strip()
    except Exception:
        pass
    return raw

def invoke(space,prompt):
    info=run(['hf-gradio','info',space],120)
    if info.returncode!=0: return False,'',{'error':info.stderr[-4000:]}
    api=json.loads(info.stdout)
    if 'named_endpoints' in api: api=api['named_endpoints']
    elif 'endpoints' in api: api=api['endpoints']
    elif 'api' in api: api=api['api']
    eps=list(api.items())
    eps.sort(key=lambda kv:(PREFERRED.index(kv[0]) if kv[0] in PREFERRED else 99,kv[0]))
    errors=[]
    for ep,spec in eps:
        payload=payload_for(spec,prompt)
        if payload is None: continue
        pred=run(['hf-gradio','predict',space,ep,json.dumps(payload,ensure_ascii=False)],240)
        if pred.returncode==0 and pred.stdout.strip():
            text=extract(pred.stdout)
            if text:
                return True,text,{'endpoint':ep,'sha256':hashlib.sha256(text.encode()).hexdigest()}
        errors.append((ep,(pred.stderr or pred.stdout)[-2000:]))
    return False,'',{'errors':errors}

role=os.environ['ROLE']; focus=os.environ.get('FOCUS',''); model=os.environ['MODEL']
prompt=f'''You are {role} in CÉRÉBRON Ω FARM44 AI Platform Routing. Focus: {focus}. Analyze provider/model/tool routing with explicit criteria: capability evidence, availability, quota, cost, latency, safety, provenance, schema compatibility, fallback behavior, observability, and failure handling. Distinguish routing success from answer correctness. Produce concise findings, risks, tests, and unknowns. CLAIM<=EVIDENCE.'''
ok,text,meta=invoke(model,prompt)
out={
 'farm':44,'role':role,'focus':focus,'model':model,'provider':'huggingface-space',
 'inference_success':ok,'status':'UNREVIEWED_EXTERNAL_AGENT_OUTPUT' if ok else 'EXTERNAL_INFERENCE_FAILED',
 'api_name':meta.get('endpoint'),'output':text if ok else None,'error':None if ok else meta,
 'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'output_sha256':meta.get('sha256') if ok else None
}
pathlib.Path('results').mkdir(exist_ok=True)
pathlib.Path(f'results/{role}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))