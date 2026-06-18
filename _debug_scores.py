#!/usr/bin/env python3
"""Debug score breakdown for ranker_v3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ranker_v3 as rv
from multiprocessing import Pool, cpu_count

jd_text = rv.read_jd_text('job_description_data_scientist.docx')
jd = rv.extract_jd_features(jd_text)
candidates = rv.load_candidates('candidates_data_scientist.json')

sample = candidates[0]
generic_mode = not any(k in sample for k in ['career','headline','summary'])
print(f'Schema: generic={generic_mode}')

args = [(c, jd) for c in candidates]
with Pool(processes=1) as pool:
    raw = pool.map(rv._score_worker, args, chunksize=1)
results = [r for r in raw if r is not None]
results.sort(key=lambda x: (-x['score'], x['candidate_id']))

pool_cands = [c for c in candidates if rv._extract_id(c) in {r['candidate_id'] for r in results[:15]}]
sem_scores  = rv.compute_semantic_scores(pool_cands, jd)
bm25_scores = rv.compute_bm25_scores(pool_cands, jd)

id_to_result = {r['candidate_id']: r for r in results[:15]}

print(f'{"Rank":>4} {"ID":>14} {"Rule":>6} {"Sem":>6} {"BM25":>6} {"Hybrid":>7} {"Exp":>3} {"Skills":>25}')
print('-' * 100)
for i, c in enumerate(pool_cands):
    cid = rv._extract_id(c)
    r = id_to_result[cid]
    rule = r['score']
    sem = sem_scores[i]
    bm = bm25_scores[i]
    hybrid = rule * 0.30 + sem * 0.50 + bm * 0.20
    exp = c.get('experience_years', c.get('yoe', '?'))
    skills = str(c.get('skills', c.get('skillnames', [])))[:24]
    print(f'{i+1:>4} {cid:>14} {rule:.4f} {sem:.4f} {bm:.4f} {hybrid:.4f} {exp:>3} {skills}')
