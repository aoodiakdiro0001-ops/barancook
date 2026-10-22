#!/usr/bin/env bash
# Baran Cook — smoke tests (12 checks against the local API)
set -u
BASE="${BASE:-http://127.0.0.1:3150}"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "PASS: $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL: $1"; }

# python JSON helpers
pyget() { python3 -c "import sys,json; d=json.load(sys.stdin); print(eval('d'+sys.argv[1]))" "$1"; }

# 1) health
H=$(curl -s "$BASE/api/health")
[ "$(echo "$H" | pyget "['ok']")" = "True" ] && ok "health" || bad "health -> $H"

# 2) recipes list total=12
T=$(curl -s "$BASE/api/recipes?limit=1" | pyget "['total']")
[ "$T" = "12" ] && ok "recipes total=12" || bad "recipes total=$T"

# 3) countries include Japan
J=$(curl -s "$BASE/api/countries" | python3 -c "import sys,json; d=json.load(sys.stdin); print(any(c['code']=='Japan' for c in d['countries']))")
[ "$J" = "True" ] && ok "countries include Japan" || bad "countries missing Japan"

# 4) country filter Egypt → koshari
K=$(curl -s "$BASE/api/recipes?country=Egypt" | python3 -c "import sys,json; d=json.load(sys.stdin); print(any(i['id']=='koshari-egypt' for i in d['items']))")
[ "$K" = "True" ] && ok "country filter Egypt" || bad "country filter Egypt"

# 5) search arabic هوموس
S1=$(curl -s "$BASE/api/search?q=%D8%AD%D9%85%D8%B5" | python3 -c "import sys,json; d=json.load(sys.stdin); print(any(i['id']=='hummus-levant' for i in d['items']))")
[ "$S1" = "True" ] && ok "search ar حمص" || bad "search ar حمص"

# 6) search english ramen
S2=$(curl -s "$BASE/api/search?q=ramen" | python3 -c "import sys,json; d=json.load(sys.stdin); print(any(i['id']=='chicken-ramen-jp' for i in d['items']))")
[ "$S2" = "True" ] && ok "search en ramen" || bad "search en ramen"

# 7) diet=Vegetarian nonempty
V=$(curl -s "$BASE/api/recipes?diet=Vegetarian&limit=1" | pyget "['total']")
[ "$V" != "0" ] && [ "$V" != "None" ] && ok "diet Vegetarian nonempty" || bad "diet Vegetarian -> $V"

# 8) detail hummus units=metric (2 cups chickpeas → 400-440 g)
M=$(curl -s "$BASE/api/recipes/hummus-levant?lang=ar&units=metric" | python3 -c "
import sys,json; d=json.load(sys.stdin)['recipe']
g=[i for i in d['ingredients'] if i['name']=='حمّص'][0]['amount']
print('OK' if 400<=g<=440 and g>0 else 'BAD:'+str(g))")
[ "$M" = "OK" ] && ok "humus metric conversion (~417.6 g)" || bad "humus metric -> $M"

# 9) detail units=imperial (volume → fl oz)
I=$(curl -s "$BASE/api/recipes/hummus-levant?lang=ar&units=imperial" | python3 -c "
import sys,json; d=json.load(sys.stdin)['recipe']
u=[i for i in d['ingredients'] if i.get('converted')][0]['unit']
print('OK' if u in ('fl oz','oz') else 'BAD:'+u)")
[ "$I" = "OK" ] && ok "humus imperial (fl oz/oz)" || bad "humus imperial -> $I"

# 10) POST /api/normalize 2 cups flour → ~254.4 g
N=$(curl -s -X POST "$BASE/api/normalize" -H 'Content-Type: application/json' -d '{"amount":2,"unit":"cups","ingredient":"flour","target":"metric"}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
o=d.get('output',{})
print('OK' if o.get('unit')=='g' and 250<=o.get('value',0)<=260 else 'BAD:'+json.dumps(d,ensure_ascii=False))")
[ "$N" = "OK" ] && ok "normalize 2 cups flour → 254.4 g" || bad "normalize -> $N"

# 11) POST /api/import duplicate detection
D=$(curl -s -X POST "$BASE/api/import" -H 'Content-Type: application/json' -d '{"recipes":[{"id":"hummus-levant","origin_country":"Levant","languages":{"en":{"title":"Hummus with Tahini","ingredients":[],"steps":[]}}}]}')
DA=$(echo "$D" | pyget "['added']" | tr -d "[]' ")
DD=$(echo "$D" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['duplicates'])>=1 and len(d['added'])==0)")
[ "$DD" = "True" ] && ok "import duplicate detect (added=0)" || bad "import duplicate -> $D"

# 12) stats + policy
ST=$(curl -s "$BASE/api/stats" | pyget "['recipes']")
PO=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/policy")
[ "$ST" = "12" ] && [ "$PO" = "200" ] && ok "stats=12 + policy 200" || bad "stats=$ST policy=$PO"

echo "----"
echo "smoke: $PASS passed, $FAIL failed"
[ "$FAIL" = "0" ]
