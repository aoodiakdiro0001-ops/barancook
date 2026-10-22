#!/usr/bin/env node
/**
 * Baran Cook — Global Recipe Atlas (Multilingual Cooking Encyclopedia)
 * Zero-dependency Node.js HTTP server.
 *
 * Layers / services (embedded micro-kernel):
 *   1) Atlas Store          — recipes.json (multilingual schema, ar+en now, extensible)
 *   2) Search Engine        — local inverted index (Arabic-normalized + English) ranked
 *   3) Unit Normalizer      — cups/tbsp/tsp/oz/lb/ml ⇄ grams/ml metric or imperial
 *   4) Ingestion (Import)   — POST /api/import JSON batch, deduped, atomic writes
 *   5) AI / NLP hooks       — dietary classifier (heuristic) + optional LLM bridge (env)
 *
 * Honesty notes:
 *   - Seed recipes are traditional folk recipes seeded locally (source_url: null).
 *   - No live scraping runs on this device; ingestion is API-driven (scrapers call /api/import).
 *   - Translation bridge stays dormant until an LLM endpoint is configured via env.
 *
 * Security: rate limiting, security headers, size-capped bodies, local-only import
 * (or BARANCOOK_ADMIN_TOKEN for remote), atomic writes.
 */

'use strict';

const http = require('http');
const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const crypto = require('crypto');
const { URL } = require('url');

/* ================= CONFIG ================= */
const PORT = Number(process.env.PORT || 3150);
const HOST = process.env.HOST || '0.0.0.0';
const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, 'public');
const DATA_DIR = path.join(ROOT, 'data');
const RECIPES_FILE = path.join(DATA_DIR, 'recipes.json');
const HISTORY_FILE = path.join(DATA_DIR, 'import-history.json');
const POLICY_FILE = path.join(ROOT, 'POLICY.md');
const ADMIN_TOKEN = process.env.BARANCOOK_ADMIN_TOKEN || '';
const LLM_URL = process.env.BARANCOOK_LLM_URL || '';
const MAX_BODY = 5 * 1024 * 1024; // 5MB
const RATE_LIMIT = 240;           // requests
const RATE_WINDOW_MS = 60 * 1000; // per minute per IP

/* ================= RATE LIMITER ================= */
const rateMap = new Map();
function rateLimited(ip) {
  const now = Date.now();
  const rec = rateMap.get(ip);
  if (!rec || now - rec.t > RATE_WINDOW_MS) {
    rateMap.set(ip, { t: now, n: 1 });
    return false;
  }
  rec.n += 1;
  if (rec.n > RATE_LIMIT) return true;
  return false;
}
setInterval(() => {
  const now = Date.now();
  for (const [ip, rec] of rateMap) if (now - rec.t > RATE_WINDOW_MS * 2) rateMap.delete(ip);
}, RATE_WINDOW_MS).unref();

/* ================= ARABIC / TEXT NORMALIZATION ================= */
const AR_DIACRITICS = /[\u064B-\u0652\u0640]/g;
function normText(s) {
  return String(s || '')
    .toLowerCase()
    .replace(AR_DIACRITICS, '')
    .replace(/أ|إ|آ/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/ى/g, 'ي')
    .replace(/[^\p{L}\p{N}\s-]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}
const STOP = new Set(['the','a','an','of','and','or','with','in','to','for','on','by','from',
  'في','من','مع','الى','إلى','على','عن','و','ه','ا','ال','الى','ثم','او','أو']);

function tokenize(s) {
  const n = normText(s);
  return n.split(' ').filter(Boolean).filter(w => w.length > 1 && !STOP.has(w));
}

/* ================= SEARCH / INDEX ================= */
let recipes = [];
let idx = new Map(); // token -> Set of recipe ids (Map keeps insertion; rank via count)
function idfLet() {
  // simple BM25-lite: shorter docs win, match density ranks
}
function addToIndex(r) {
  const fields = [
    [3, r.languages && r.languages.ar && r.languages.ar.title],
    [3, r.languages && r.languages.en && r.languages.en.title],
    [2, r.category], [2, r.origin_country],
    [1, r.dietary_tags && r.dietary_tags.join(' ')],
    [2, r.languages && r.languages.ar && r.languages.ar.description],
    [2, r.languages && r.languages.en && r.languages.en.description],
  ];
  // ingredients + steps
  for (const lang of ['ar', 'en']) {
    const L = r.languages && r.languages[lang];
    if (!L) continue;
    for (const ing of L.ingredients || []) fields.push([2, ing.name]);
    for (const s of L.steps || []) fields.push([1, s.instruction]);
  }
  for (const [w, text] of fields) {
    for (const tok of tokenize(text || '')) {
      if (!idx.has(tok)) idx.set(tok, new Map());
      const m = idx.get(tok);
      m.set(r.id, (m.get(r.id) || 0) + w);
    }
  }
}
function buildIndex() {
  idx = new Map();
  for (const r of recipes) addToIndex(r);
}
function searchRecipes(q, { lang, country, diet, limit }) {
  const tokens = tokenize(q);
  const scores = new Map();
  for (const tok of tokens) {
    const m = idx.get(tok);
    if (!m) continue;
    for (const [id, w] of m) scores.set(id, (scores.get(id) || 0) + w);
  }
  let list = [...scores.entries()]
    .map(([id, s]) => ({ r: recipes.find(x => x.id === id), s }))
    .filter(x => x.r)
    .sort((a, b) => b.s - a.s || a.r.id.localeCompare(b.r.id));
  if (country) list = list.filter(x => x.r.origin_country === country);
  if (diet) list = list.filter(x => x.r.dietary_tags && x.r.dietary_tags.includes(diet));
  const lim = Math.max(1, Math.min(50, Number(limit) || 10));
  return list.slice(0, lim).map(x => x.r);
}

/* ================= UNIT NORMALIZER (Metric ⬄ Imperial) ================= */
// densities: grams per milliliter (approximate, cooking-grade)
const DENSITIES = {
  water: 1.0, milk: 1.03, broth: 1.0, stock: 1.0, oil: 0.92, 'olive oil': 0.92,
  butter: 0.96, ghee: 0.94, honey: 1.42, sugar: 0.85, 'brown sugar': 0.85,
  salt: 1.27, rice: 0.85, bulgur: 0.78, couscous: 0.75, flour: 0.53,
  semolina: 0.65, lentils: 0.84, chickpeas: 0.87, beans: 0.85, pasta: 0.75,
  'yogurt': 1.03, 'tomato paste': 1.1, tahini: 1.35, 'cream': 1.0, cocoa: 0.6,
  // Arabic keys (both sides run through normText — diacritics/ة/ى normalized)
  'حمص': 0.87, 'طحينة': 1.35, 'ملح': 1.27, 'زيت': 0.92, 'ارز': 0.85,
  'زبدة': 0.96, 'سكر': 0.85, 'سمولينا': 0.65, 'زبادي': 1.03, 'كريما': 1.0,
  'مرق': 1.0, 'دقيق': 0.53, 'دقيق حمص': 0.8, 'عسل': 1.42, 'ماء': 1.0,
  'عدس': 0.84, 'مكرونة': 0.75, 'فاصوليا': 0.85, 'جبن': 1.05,
}; // fallback for unknown ingredient: 1.0 (water-like)
const VOL_TO_ML = {
  cup: 240, cups: 240, tbsp: 15, tablespoon: 15, tablespoons: 15,
  tsp: 5, teaspoon: 5, teaspoons: 5, 'fl oz': 29.57, ml: 1, liter: 1000, liters: 1000, l: 1000,
};
const WT_TO_G = {
  g: 1, gram: 1, grams: 1, kg: 1000, oz: 28.35, ounce: 28.35, ounces: 28.35,
  lb: 453.59, pound: 453.59, pounds: 453.59,
};
const UNIT_ALIASES = {
  'گرام': 'g', 'غرام': 'g', 'مل': 'ml', 'ملليلتر': 'ml', 'مليلتر': 'ml',
  'كوب': 'cup', 'أوقية': 'oz', 'رقاقة': 'lbs', 'كلغ': 'kg',
};
const IMPERIAL_FMT = { g: 'oz', ml: 'fl oz' };
function normalizeIngredient(s) {
  return normText(String(s || '')).replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه');
}
function densityFor(ingredient) {
  const n = normalizeIngredient(ingredient);
  for (const k of Object.keys(DENSITIES)) {
    if (n === normText(k)) return DENSITIES[k];
  }
  // longer names: oil with modifiers e.g. "زيت زيتون" — check substring either way
  for (const k of Object.keys(DENSITIES)) {
    const kk = normText(k);
    if (n.includes(kk) || kk.includes(n)) return DENSITIES[k];
  }
  return 1.0;
}
function parseUnit(unitRaw) {
  let u = String(unitRaw || '').trim().toLowerCase();
  u = UNIT_ALIASES[u] || u;
  if (VOL_TO_ML[u] != null) return { sys: 'volume_ml', to_ml: VOL_TO_ML[u], key: u };
  if (WT_TO_G[u] != null) return { sys: 'weight_g', to_g: WT_TO_G[u], key: u };
  if (u === 'count' || u === 'pc' || u === 'piece' || u === 'pieces' || u === 'قطعة') return { sys: 'count', key: 'count' };
  return null;
}
function convert({ amount, unit, ingredient, target }) {
  const a = Number(amount);
  if (!Number.isFinite(a) || a < 0) return { ok: false, error: 'amount must be a finite number >= 0' };
  const p = parseUnit(unit);
  if (!p) return { ok: false, error: 'unsupported unit' };
  const d = densityFor(ingredient);
  let grams = null, ml = null;
  if (p.sys === 'volume_ml') { ml = a * p.to_ml; grams = ml * d; }
  else if (p.sys === 'weight_g') { grams = a * p.to_g; ml = d > 0 ? grams / d : grams; }
  else return { ok: false, error: 'count units are not convertible' };
  let outValue, outUnit, display;
  const r1 = (x) => Math.round(x * 10) / 10;
  if (target === 'imperial') {
    // convert canonical grams/ml → imperial picking oz / fl oz
    if (p.sys === 'volume_ml') { outValue = r1(ml / 29.57); outUnit = 'fl oz'; }
    else { outValue = r1(grams / 28.35); outUnit = ozUnit(grams); }
    display = `${outValue} ${outUnit}`;
  } else {
    // target metric: prefer grams for weight-ish, ml for water-like
    if (p.sys === 'volume_ml') {
      if (d >= 0.95) { outValue = r1(ml); outUnit = 'ml'; }
      else { outValue = r1(grams); outUnit = densityGood(ingredient) ? 'g' : 'ml'; }
    } else {
      outValue = r1(grams); outUnit = 'g';
    }
    display = `${outValue} ${outUnit}`;
  }
  return { ok: true, input: { amount: a, unit: p.key }, output: { value: outValue, unit: outUnit, display }, density_g_per_ml: d, note: densityGood(ingredient) ? undefined : 'unknown density — water-like default applied' };
}
function ozUnit(grams) { return grams >= 453.59 ? 'lb' : 'oz'; }
function densityGood(i) { return Object.keys(DENSITIES).some(k => {
  const n = normalizeIngredient(i); const kk = normText(k);
  return n === kk || n.includes(kk) || kk.includes(n);
}); }
function recipetoLocale(r, lang, units) {
  // returns a localized view (depth: title/desc/ingredients/steps), optionally unit-converted
  const L = (r.languages && (r.languages[lang] || r.languages.ar)) || null;
  if (!L) return null;
  const view = { id: r.id, title: L.title, description: L.description, country: r.origin_country, category: r.category, dietary_tags: r.dietary_tags, origin_note: L.source_note };
  view.ingredients = (L.ingredients || []).map(i => {
    const ing = { name: i.name, original: String((i.amount == null ? '' : i.amount) + (i.unit ? ' ' + i.unit : '')).trim() };
    if (units && units !== 'original' && i.amount != null && i.unit) {
      const conv = convert({ amount: i.amount, unit: i.unit, ingredient: i.name, target: units });
      if (conv.ok) ing.amount = conv.output.value, ing.unit = conv.output.unit, ing.converted = true;
      else { ing.amount = i.amount; ing.unit = i.unit; ing.converted = false; }
    } else { ing.amount = i.amount; ing.unit = i.unit; }
    return ing;
  });
  view.steps = (L.steps || []).map(s => ({ step_number: s.step_number, instruction: s.instruction }));
  view.prep_time_minutes = r.prep_time_minutes;
  view.cook_time_minutes = r.cook_time_minutes;
  view.servings = r.servings;
  view.media = r.media || {};
  return view;
}

/* ================= /AI/ DIETARY CLASSIFIER (heuristic, honest) ================= */
const MEAT_WORDS = ['chicken', 'beef', 'lamb', 'pork', 'meat', 'fish', 'shrimp', 'salmon', 'turkey', 'duck', 'دجاج', 'لحم', 'سمك', 'روبيان', 'خروف', 'لحمه'];
function classifyDietary(r) {
  const tags = [];
  const texts = [];
  for (const lang of ['ar', 'en']) {
    const L = r.languages && r.languages[lang];
    if (!L) continue;
    for (const ing of L.ingredients || []) texts.push(ing.name);
  }
  const blob = normText(texts.join(' '));
  const words = tokenize(blob);
  const meatHit = MEAT_WORDS.some(m => words.includes(normText(m)) || blob.includes(normText(m)));
  if (!meatHit) tags.push('Vegetarian');
  const pork = /pork|bacon|ham\b|خنزير|لحم خنزير/.test(blob);
  if (pork) {
    // note: not halal
    tags.push('Not-Halal');
    return tags;
  }
  const gelatin = /gelatin|جيلا?تين/.test(blob);
  const alcohol = /wine|rum|beer|نبيذ|خمر|كحول/.test(blob);
  if (!pork && !gelatin && !alcohol) tags.push('Halal');
  if (/(gluten|wheat|flour|semolina|pasta|بسملة|دقيق|سمولينا|مكرونة|فتة)/.test(blob)) tags.push('May-Contain-Gluten');
  return tags;
}
function guessCuisine(r) {
  return r.origin_country || 'Unknown';
}

/* ================= HTTP HELPERS ================= */
function json(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  });
  res.end(body);
}
function readBody(req, cap) {
  return new Promise((resolve) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > cap) { req.destroy(); resolve(null); return; }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', () => resolve(null));
  });
}
const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon' };
function serveStatic(res, filePath) {
  fs.stat(filePath, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, {
      'Content-Type': MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'no-referrer',
      'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'",
    });
    fs.createReadStream(filePath).pipe(res);
  });
}

/* ================= ATOMIC WRITES ================= */
async function atomicWrite(file, obj) {
  const tmp = file + '.' + crypto.randomBytes(6).toString('hex') + '.tmp';
  const data = JSON.stringify(obj, null, 2);
  await fsp.writeFile(tmp, data, 'utf8');
  await fsp.rename(tmp, file);
}

/* ================= INGESTION (IMPORT) ================= */
function slugify(s) {
  return normText(s).replace(/[^a-z0-9- ]/g, '').trim().replace(/\s+/g, '-').slice(0, 60);
}
async function importRecipes(payload, meta) {
  const out = { added: [], duplicates: [], rejected: [] };
  const list = Array.isArray(payload && payload.recipes) ? payload.recipes : [];
  let dirty = false;
  for (const r of list) {
    if (!r || typeof r !== 'object') { out.rejected.push({ reason: 'not an object' }); continue; }
    const hasAr = r.languages && r.languages.ar && r.languages.ar.title;
    const hasEn = r.languages && r.languages.en && r.languages.en.title;
    if (!hasAr && !hasEn) { out.rejected.push({ reason: 'missing title in ar/en' }); continue; }
    if (!r.origin_country) { out.rejected.push({ reason: 'missing origin_country' }); continue; }
    // dedupe: source_url OR id-slug OR (title_en + country)
    const dupe = recipes.find(x =>
      (r.source_url && x.source_url && r.source_url === x.source_url) ||
      (r.id && x.id === r.id) ||
      (r.languages && r.languages.en && x.languages && x.languages.en &&
        normText(r.languages.en.title) === normText(x.languages.en.title) &&
        String(r.origin_country) === String(x.origin_country))
    );
    if (dupe) { out.duplicates.push(dupe.id); continue; }
    if (!r.id) r.id = slugify((hasEn && r.languages.en.title) || (hasAr && r.languages.ar.title));
    if (recipes.some(x => x.id === r.id)) r.id = r.id + '-' + crypto.randomBytes(3).toString('hex');
    const rec = {
      id: r.id,
      source_url: r.source_url || null,
      source_note: r.source_note || { ar: 'وصفة مستوردة', en: 'Imported recipe' },
      origin_country: String(r.origin_country),
      recipe_id_schema_note: r.recipe_id_schema_note || { ar: 'معرّف نصي بديل عن uuid_v4 صالح للاستخدام البشري', en: 'Human-readable id (uuid_v4 kept optional in import schema)' },
      category: r.category || 'Main Course',
      languages: r.languages,
      prep_time_minutes: r.prep_time_minutes || 0,
      cook_time_minutes: r.cook_time_minutes || 0,
      servings: r.servings || 4,
      dietary_tags: r.dietary_tags || classifyDietary(r),
      media: r.media || { images: [], videos: [] },
      created_at: r.created_at || new Date().toISOString(),
    };
    // ensure structure
    for (const lang of ['ar', 'en']) {
      if (!rec.languages[lang]) continue;
      rec.languages[lang].ingredients = rec.languages[lang].ingredients || [];
      rec.languages[lang].steps = rec.languages[lang].steps || [];
      for (const s of rec.languages[lang].steps) if (!s.step_number) s.step_number = 1;
      for (const [si, s] of rec.languages[lang].steps.entries()) s.step_number = si + 1;
    }
    if (!rec.dietary_tags.includes('Vegetarian') && !meatHit(rec)) Object.assign(rec, { dietary_tags: classifyDietary(rec) });
    recipes.push(rec);
    addToIndex(rec);
    out.added.push(rec.id);
    dirty = true;
  }
  if (dirty) {
    await atomicWrite(RECIPES_FILE, { version: 1, updated_at: new Date().toISOString(), recipes });
  }
  let hist = [];
  try { hist = JSON.parse(await fsp.readFile(HISTORY_FILE, 'utf8')); } catch {}
  hist.push({ at: new Date().toISOString(), meta: meta || {}, added: out.added, duplicates: out.duplicates, rejected: out.rejected });
  try { await atomicWrite(HISTORY_FILE, hist); } catch {}
  return out;
}
function meatHit(r) {
  const texts = [];
  for (const lang of ['ar', 'en']) {
    const L = r.languages && r.languages[lang];
    if (!L) continue;
    for (const ing of L.ingredients || []) texts.push(ing.name);
  }
  const b = normText(texts.join(' '));
  return MEAT_WORDS.some(m => b.includes(normText(m)));
}

/* ================= BOOT ================= */
async function boot() {
  try {
    const raw = await fsp.readFile(RECIPES_FILE, 'utf8');
    const j = JSON.parse(raw);
    recipes = Array.isArray(j.recipes) ? j.recipes : [];
  } catch (e) {
    console.error('[barancook] recipes load failed:', e.message);
    recipes = [];
  }
  buildIndex();
  console.log(`[barancook] boot: ${recipes.length} recipes, index tokens: ${idx.size}`);
}

/* ================= ROUTER ================= */
async function route(req, res) {
  const u = new URL(req.url, 'http://x');
  const p = u.pathname;
  const q = u.searchParams;
  const ip = (req.socket.remoteAddress || 'x').replace('::ffff:', '');

  // security headers for all responses (API + static)
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Permissions-Policy', 'geolocation=(), camera=(), microphone=()');

  if (rateLimited(ip)) return json(res, 429, { ok: false, error: 'rate limit exceeded' });

  // ---------- static ----------
  if (req.method === 'GET' || req.method === 'HEAD') {
    if (p === '/' || p === '/index.html') return serveStatic(res, path.join(PUBLIC_DIR, 'index.html'));
    if (p === '/css/styles.css') return serveStatic(res, path.join(PUBLIC_DIR, 'css', 'styles.css'));
    if (p === '/js/app.js') return serveStatic(res, path.join(PUBLIC_DIR, 'js', 'app.js'));
    if (p === '/favicon.ico') { res.writeHead(204); return res.end(); }
  }

  // ---------- health ----------
  if (p === '/api/health') return json(res, 200, { ok: true, service: 'barancook', version: '1.0.0', recipes: recipes.length, index_tokens: idx.size, time: new Date().toISOString(), llm_bridge: LLM_URL ? 'configured' : 'dormant', admin: ADMIN_TOKEN ? 'token_required_for_remote_import' : 'local_only_import' });

  // ---------- stats (honesty) ----------
  if (p === '/api/stats') {
    const byCountry = {};
    for (const r of recipes) byCountry[r.origin_country] = (byCountry[r.origin_country] || 0) + 1;
    const byDiet = {};
    for (const r of recipes) for (const t of r.dietary_tags || []) byDiet[t] = (byDiet[t] || 0) + 1;
    const langs = {};
    for (const r of recipes) for (const k of Object.keys(r.languages || {})) langs[k] = (langs[k] || 0) + 1;
    return json(res, 200, { ok: true, recipes: recipes.length, countries: Object.keys(byCountry).length, by_country: byCountry, by_diet: byDiet, by_language: langs, index_tokens: idx.size, note: { ar: 'النواة تعمل الآن محلياً — الزحف الموزع يبدأ عبر /api/import عند توفير مصادر', en: 'Core live locally NOW — distributed scraping begins via /api/import as sources are provided' } });
  }

  // ---------- countries ----------
  if (p === '/api/countries') {
    const map = {};
    for (const r of recipes) {
      const c = r.origin_country;
      if (!map[c]) map[c] = { code: c, count: 0, country_ar: (r.geo && r.geo.ar) || '', country_en: (r.geo && r.geo.en) || c };
      map[c].count++;
    }
    return json(res, 200, { ok: true, countries: Object.values(map).sort((a, b) => b.count - a.count) });
  }

  // ---------- recipes (list) ----------
  if (p === '/api/recipes' && req.method === 'GET') {
    let list = recipes.slice();
    const country = q.get('country'); if (country) list = list.filter(r => r.origin_country === country);
    const diet = q.get('diet'); if (diet) list = list.filter(r => r.dietary_tags && r.dietary_tags.includes(diet));
    const page = Math.max(1, Number(q.get('page')) || 1);
    const limit = Math.min(50, Math.max(1, Number(q.get('limit')) || 12));
    const start = (page - 1) * limit;
    const items = list.slice(start, start + limit).map(r => ({
      id: r.id,
      title_ar: r.languages && r.languages.ar && r.languages.ar.title,
      title_en: r.languages && r.languages.en && r.languages.en.title,
      country: r.origin_country,
      category: r.category,
      dietary_tags: r.dietary_tags,
      prep_time_minutes: r.prep_time_minutes,
      cook_time_minutes: r.cook_time_minutes,
      servings: r.servings,
    }));
    return json(res, 200, { ok: true, total: list.length, page, limit, items });
  }

  // ---------- recipes (detail) ----------
  let m;
  if ((m = p.match(/^\/api\/recipes\/([^/]+)$/))) {
    const r = recipes.find(x => x.id === m[1]);
    if (!r) return json(res, 404, { ok: false, error: 'recipe not found' });
    const lang = q.get('lang') || 'ar';
    const units = q.get('units') || 'metric'; // metric | imperial | original
    const view = recipetoLocale(r, lang, units);
    if (!view) return json(res, 404, { ok: false, error: 'language not available for this recipe' });
    return json(res, 200, { ok: true, recipe: view });
  }

  // ---------- search ----------
  if (p === '/api/search' && req.method === 'GET') {
    const q0 = q.get('q') || '';
    const lang = q.get('lang') || 'all';
    const country = q.get('country');
    const diet = q.get('diet');
    const limit = q.get('limit');
    const found = searchRecipes(q0, { lang, country, diet, limit: Number(limit) || 12 });
    return json(res, 200, { ok: true, q: q0, count: found.length, items: found.map(r => ({ id: r.id, title_ar: r.languages && r.languages.ar && r.languages.ar.title, title_en: r.languages && r.languages.en && r.languages.en.title, country: r.origin_country, dietary_tags: r.dietary_tags, snippet_ar: r.languages && r.languages.ar && r.languages.ar.description ? r.languages.ar.description.slice(0, 90) : '', snippet_en: r.languages && r.languages.en && r.languages.en.description ? r.languages.en.description.slice(0, 90) : '' })) });
  }

  // ---------- normalize ----------
  if (p === '/api/normalize' && req.method === 'POST') {
    const raw = await readBody(req, 65536);
    let body; try { body = JSON.parse(raw || '{}'); } catch { return json(res, 400, { ok: false, error: 'invalid JSON' }); }
    const r = convert(body);
    return json(res, r.ok ? 200 : 400, r);
  }

  // ---------- AI: dietary classifier ----------
  if (p === '/api/ai/classify' && req.method === 'POST') {
    const raw = await readBody(req, 262144);
    let body; try { body = JSON.parse(raw || '{}'); } catch { return json(res, 400, { ok: false, error: 'invalid JSON' }); }
    const stub = { languages: { ar: { ingredients: (body.ingredients_ar || []).map(n => ({ name: n })) }, en: { ingredients: (body.ingredients_en || []).map(n => ({ name: n })) } } };
    const tags = classifyDietary(stub);
    return json(res, 200, { ok: true, engine: 'heuristic-v1', dietary_tags: tags, cuisine: body.country || guessCuisine(body) || 'Unknown', llm_bridge: LLM_URL ? { status: 'configured', url_env: true } : { status: 'dormant' }, note: 'Resource-Friendly: deterministic local classifier — LLM bridge turns on when BARANCOOK_LLM_URL is set' });
  }

  // ---------- AI: translation bridge (dormant until env configured) ----------
  if (p === '/api/translate' && req.method === 'POST') {
    const raw = await readBody(req, 262144);
    let body; try { body = JSON.parse(raw || '{}'); } catch { return json(res, 400, { ok: false, error: 'invalid JSON' }); }
    if (!LLM_URL) return json(res, 501, { ok: false, reason: 'dormant: no BARANCOOK_LLM_URL configured — set it to activate the LLM bridge', honesty: 'translation stays manual until an AI endpoint is wired' });
    try {
      const resp = await fetch(LLM_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: body.text, from: body.from, to: body.to }) });
      const j = await resp.json();
      return json(res, resp.ok ? 200 : 502, j);
    } catch (e) {
      return json(res, 502, { ok: false, error: 'LLM bridge failed', detail: String(e.message).slice(0, 200) });
    }
  }

  // ---------- import (ingestion entrypoint for scrapers) ----------
  if (p === '/api/import' && req.method === 'POST') {
    const local = ['127.0.0.1', '::1'].includes(ip);
    if (!local && !ADMIN_TOKEN) return json(res, 403, { ok: false, error: 'remote import disabled — run locally or set BARANCOOK_ADMIN_TOKEN' });
    if (!local) {
      const tok = req.headers['x-admin-token'];
      if (!ADMIN_TOKEN || tok !== ADMIN_TOKEN) return json(res, 401, { ok: false, error: 'invalid admin token' });
    }
    const raw = await readBody(req, MAX_BODY);
    let body; try { body = JSON.parse(raw || '{}'); } catch { return json(res, 400, { ok: false, error: 'invalid JSON' }); }
    const out = await importRecipes(body, { ip, ua: String(req.headers['user-agent'] || '').slice(0, 100) });
    return json(res, 200, { ok: true, ...out });
  }

  // ---------- policy ----------
  if (p === '/api/policy') {
    const t = await fsp.readFile(POLICY_FILE, 'utf8');
    return json(res, 200, { ok: true, policy_md: t });
  }

  return json(res, 404, { ok: false, error: 'not found' });
}

/* ================= SERVER ================= */
(async () => {
  await boot();
  const server = http.createServer((req, res) => {
    route(req, res).catch(e => {
      console.error('[barancook] route error:', e);
      try { json(res, 500, { ok: false, error: 'internal error' }); } catch {}
    });
  });
  server.listen(PORT, HOST, () => {
    console.log(`[barancook] Baran Cook — Global Recipe Atlas listening on http://${HOST}:${PORT}`);
  });
})();
