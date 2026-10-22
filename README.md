# 🍳 Baran Cook — أطلس الوصفات العالمي

**موسوعة طهي متعددة اللغات** — النواة المحلية تعمل فوراً، ومسار الاستيعاب (Ingestion) يبايتك لقطع مسجوب الأنظمة الموزعة في المستقبل.

> **الصدق الهندسي**: هذه هي **النواة** (Core Kernel) للموسوعة — 12 ووصفة عالمية كبذرة، محرك بحث محلي مُعَمّم (Meilisearch-like بسيط)، محرك تحويل مقاييس واقعي، مسار استيعاب عبر API بنمط Scrapy/Kafka اللاحق، وhooks ذكاء اصطناعي بحدود صادقة (لا ترجمة وهمية). لا زحف من هذا الجهاز — الاستيعاب عبر API فقط.

---

## ⚡ الإطلاق (Run)

```bash
node server.js
# → Baran Cook listening on http://0.0.0.0:3150
```

مع **pm2** (خلال مدة العمر):

```bash
pm2 start server.js --name barancook
pm2 save
```

اختبارات كامل الحزم:

```bash
bash smoke.sh
```

---

## 🏗️ البنية (Embedded Micro-Kernel)

| طبقة | الاسم داخل الكود | الوظيفة |
|---|---|---|
| Atlas Store | `data/recipes.json` | 12 وصفة عالمية `ar+en` (مخطط مرن يدعم أكثر من لغة، كما في specification الأصلي) |
| Search Engine | `buildIndex()` | محرك مطابقة عربي/إنجليزي مع تطبيع الحروف العربية (ألّف، ة→ه، ى→ي) */
| Unit Normalizer | `convert()` | gym، مقايسة مطبخ واقعية: cups/oz/lb/ml/g ✓ (جداول كثافات 17 عنصر) |
| Ingestion | `POST /api/import` | استيعاب دفع JSON من أي الزحف أو scraper — دمج مكرر ذكي (مكررات، regex dedupe) |
| AI / NLP |ès | تصنيف غذائي دالتًّا (vegetarian/halal/gluten) — برنامج محلي؛ الـ LLM bridge ينشط فقط عند ضبط `BARANCOOK_LLM_URL` |
| API Gateway | route handler | rate limit 240 طلب/دقيقة، رؤوس حماية (CSP / X-Frame / nosniff)، كتابة ذرية |

---

## 🌍 المنصة الهيكلية (API)

| Route | الوصف |
|---|---|
| `GET /api/health` | الحالة العملية |
| `GET /api/stats` | إحصاءات صادقة (بلدان، chefe، مؤشر البحث) |
| `GET /api/countries` | جدول البلد ⟵ count |
| `GET /api/recipes?country=&diet=&limit=&page=` | قوّم تصفية |
| `GET /api/recipes/:id?lang=ar\|en&units=metric\|imperial\|original` | تفصيل مع تحويل الوحدات |
| `GET /api/search?q=هوموس&lang=all&country=&diet=` | محرك البحث المحلي |
| `POST /api/normalize` | تحويل مقادير (amount+unit+ingredient→grams|oz) |
| `POST /api/import` | مسار الاستيعاب لل scrapers (محلي، أو `X-Admin-Token` حسب ضبط `BARANCOOK_ADMIN_TOKEN`) |
| `POST /api/ai/classify` | مُزج جودة البيانات: dietary tags + cuisine |
| `POST /api/translate` | Gateway للوصول إلى LLM (يبدل حياًّ نَكُس حتى تُوفر `BARANCOOK_LLM_URL`) |
| `GET /api/policy` | سياسة المحتوى |
| `POST /api/ai/classify` | Source of healthy truth: `{"engine":"heuristic-v1",...}` |

**مثال استيراد من scraper حافظيون (بيانات موجزة) — Scraper plane example:**

```bash
curl -X POST http://localhost:3150/api/import \\
  -H 'Content-Type: application/json' \\
  -d '{"recipes":[{"id":"koshari-egypt-mirror","origin_country":"Egypt","languages":{"ar":{"title":"كشري مصري (نسخة مستوردة)","description":"مثال استيعاب — من مصدر خارجي معترف به","ingredients":[{"name":"أرز","amount":2,"unit":"cups"}],"steps":[{"step_number":1,"instruction":"خطوة مثال للاستيعاب"}]}}}]}'
```

---

## 🧰 مخطط الوصفة (Schema)

عين `data/recipes.json`:

```json
{
  "id": "chicken-ramen-jp",
  "source_url": null,
  "source_note": {"ar": "...", "en": "..."},
  "origin_country": "Japan",
  "geo": {"ar": "اليابان", "en": "Japan"},
  "category": "Soup",
  "languages": {
    "ar": { "title": "...", "description": "...",
            "ingredients": [{"name": "نودلز رامن", "amount": 200, "unit": "g"}],
            "steps": [{"step_number": 1, "instruction": "..."}] },
    "en": { "title": "...", "description": "...",
            "ingredients": [{"name": "ramen noodles", "amount": 200, "unit": "g"}],
            "steps": [{"step_number": 1, "instruction": "..."}] }
  },
  "prep_time_minutes": 30,
  "cook_time_minutes": 150,
  "servings": 4,
  "dietary_tags": ["Halal"],
  "media": {"images": [], "videos": []},
  "created_at": "2026-10-22T00:00:00.000Z"
}
```

---

## 🚀 النشر خارج الجهاز

يعمل الخادم بأمر واحد على أي بيئة Node ≥ 18:

```bash
PORT=8080 node server.js
```

مع **pm2**:

```bash
pm2 start server.js --name barancook
pm2 save
```

---

## 🔒 الطبقة الأمنية
- **Rate Limit**: 240 requests/دقيقة/IP.
- **Security Headers**: `nosniff`, `DENY` ickers, `no-referrer`, `CSP: default-src 'self'`.
- **Size Cap**: 5 MBtas body limit.
- **Atomic writes**: `rename()` بعد كتابة temp file — بياناتها المستعمل لا تسقط تلقائية.
- **Import local-host first**: remote requires `BARANCOOK_ADMIN_TOKEN`.

---

## 📊 الصدقية ( البيئة الشهادات الحacao)
- **12 وصفة مقدّسة** كبيانات أولية (المصدر: وصفات شعبية عامة؛ `source_url: null`؛ بلا روابط مقدوسة).
- **لا زحف أي شبكة من هذا الجهاز** — تحصيل كامل على استعادة **scraper** للوصول إلى `POST /api/import`.
- **الـ LLM bridge** صامتة حتى ضبط `BARANCOOK_LLM_URL` (لا مطالبة ترجمة قبل أن تكون مستعدة).
- **المعلمات**: ينبغي للنشر بخدمة Man بعد قراءة الفاصل حول **coverage**: هذه **النواة**.Runtime stack محتمل الخامس هندستًا لLikely.

## 📜 الوثيقة القانونية
انظر **POLICY.md** — سياسة شركة المحتوى (folkloric origin, takedown ≤ 72h, ملكية الـ Tages). 
