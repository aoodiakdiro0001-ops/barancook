#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""import_mealdb.py — push data/mealdb_seed.json into the atlas via POST /api/import
(local loopback only, batches of 40). Idempotent: the server dedupes."""
import json
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(HERE, '..', 'data', 'mealdb_seed.json')
BASE = os.environ.get('BARANCOOK_BASE', 'http://127.0.0.1:3150')


def post(url, payload):
    raw = json.dumps(payload, ensure_ascii=False)
    out = subprocess.run(['curl', '-s', '-X', 'POST', url,
                          '-H', 'Content-Type: application/json',
                          '--data-binary', '@-'],
                         input=raw, capture_output=True, text=True, timeout=120)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {'ok': False, 'error': out.stdout[:200]}


def main():
    seed = json.load(open(os.path.normpath(SEED), encoding='utf-8'))
    meals = seed.get('meals') or []
    total_added, total_dupe, total_reject = 0, 0, 0
    B = 40
    for i in range(0, len(meals), B):
        batch = meals[i:i + B]
        res = post(BASE + '/api/import', {'recipes': batch})
        if not res.get('ok'):
            print('batch', i, 'FAILED:', json.dumps(res, ensure_ascii=False)[:300])
            continue
        total_added += len(res.get('added') or [])
        total_dupe += len(res.get('duplicates') or [])
        total_reject += len(res.get('rejected') or [])
        print('batch %4d: added=%d dupes=%d (running: +%d)' % (i, len(res.get('added') or []), len(res.get('duplicates') or []), total_added))
    print('DONE: added=%d duplicates=%d rejected=%d' % (total_added, total_dupe, total_reject))
    st = post(BASE + '/api/stats', {}) if False else json.loads(subprocess.run(['curl', '-s', BASE + '/api/stats'], capture_output=True, text=True).stdout or '{}')
    print('stats: recipes=%s countries=%s tokens=%s' % (st.get('recipes'), st.get('countries'), st.get('index_tokens')))


if __name__ == '__main__':
    main()
