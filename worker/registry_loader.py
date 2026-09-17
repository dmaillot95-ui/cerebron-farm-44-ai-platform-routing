import json, urllib.request
from pathlib import Path
RAW='https://raw.githubusercontent.com/dmaillot95-ui/cerebron-omega-encyclopedia/main/'
def load_registry(categories, timeout=20, max_chars=18000):
    meta={'loaded':False,'version':None,'categories':[],'errors':[],'provenance':[]}; chunks=[]
    try:
        local=json.loads(Path('CEREBRON_REGISTRY.json').read_text(encoding='utf-8')); manifest_url=local['registry']
        with urllib.request.urlopen(manifest_url,timeout=timeout) as r: manifest=json.loads(r.read().decode('utf-8'))
        meta['version']=manifest.get('version'); paths=manifest.get('paths',{})
        for cat in categories:
            rel=paths.get(cat)
            if not rel: continue
            url=RAW+rel
            try:
                with urllib.request.urlopen(url,timeout=timeout) as r: text=r.read().decode('utf-8')
                chunks.append(f'\n### {cat.upper()} — source: {url}\n{text[:max_chars]}'); meta['categories'].append(cat); meta['provenance'].append(url)
            except Exception as e: meta['errors'].append({'category':cat,'error':repr(e)})
        meta['loaded']=bool(chunks)
    except Exception as e: meta['errors'].append({'stage':'manifest','error':repr(e)})
    return '\n'.join(chunks),meta
