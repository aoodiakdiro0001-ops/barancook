# 🍳 Baran Cook — أطلس الوصفات العالمي

**موسوعة طهي متعددة اللغات — v1.2.0** — **831 وصفة حقيقية من 76 بلداً**، بصور ومحرك بحث عربي/إنجليزي وتحويل مقاييس.

> **الصدق عن المصادر (v1.2.0)**: لم يُزحَف «كل ما على الإنترنت» — ذلك مستحيل من جهاز واحد قانونياً وتقنياً. بدلاً من ذلك:
> 1. **قاعدة TheMealDB المفتوحة — 793 وصفة** مستوردة كاملة عبر 77 بلداً (strCountry حقيقي من الـAPI)، كل وصفة تحمل `source_url` حقيقي لصفحتها + `source_note` يصرّح أن المحتوى الأصلي إنجليزي.
> 2. **26 وصفة عربية أصيلة** مكتوبة يدوياً (منسف، كبسة، مقلوبة، مسخن، فتة حمص، دولمة، قوزي، ملوخية، حواوشي، محشي كرنب، طاجين برقوق، كسكس مغربي، حريرة، بسطيلة، شكشوكة، كسكس جزائري، مرقوق، هريس، مشكك، شوربة عدس، بازين، عصيدة، زربيان...) — بلا ادعاء روابط خارجية.
> 3. **التوسيع لاحقاً**: عبر `POST /api/import` (محلياً أو بـBARANCOOK_ADMIN_TOKEN) — يمكن استيراد أي ملف بنفس المخطط (مثلاً dump ضخم مستقبلاً).
> - عناوين عربية للأطباق المشهورة فقط حيث الاسم موثوق (حقل عِرقَيّ `ar_title` في القائمة)، والتفصيلة تعرض الأصل ببهات `language_fallback` صادقة.
> - البحث العربي للكلمات المشهورة (برياني/رامن/بيتزا...) يُوسَّع عبر قاموس استعلامات صادق (AR_QUERY_ALIASES) — بلا ترجمة وهمية للمحتوى.

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
| `POST /api/contribute` | **إضافة وصفة من الجمهور** — نموذج الموقع، بلا رموز ولا حاجات: حدّ 10 وصفات/دقيقة لكل IP |
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

## 🤝 إضافة وصفة من الموقع (الجميع يستطيع)

أي زائر يضغط «➕ أضف وصفة» فيرتفع نموذج بسيط: الاسم، البلد (مع اقتراحات)، تصنيف، وصف قصير،
وقت/طبخ/عدد الأفراد، ثم **المكونات والخطوات سطرًا سطرًا** — والباقي يعمله المحرك:

- يفكك `«2 cups حمّص» / «1/2 كوب سكر» / «ملعقة كبيرة طحينة»` إلى name/amount/unit تلقائياً (أنظمة متري وعربي وإنجليزي).
- يصنّف الوسوم الغذائية (نباتي/حلال/Jewish-free...) آلياً من المكونات صراحة وبلا مزاعم.
- ينشر مباشرة‌ وبعلم `community: true` + ملاحظة «أضافها مستخدم عبر نموذج الموقع»، وتظهر فوراً في البحث.
- منع التكرار (نفس الاسم+البلد → `added=0`، لا مكتب ويُحسب duplicate)، وحدّ 10 مساهمات/دقيقة لكل IP، ورفض 400 صريح للحقول الناقصة.

مثال حيّ (أُضيف فعلًا بنفس الطريقة — وصفة المسقعة المصرية):

```bash
curl -X POST http://127.0.0.1:3150/api/contribute \
  -H 'Content-Type: application/json' \
  -d '{"lang":"ar","title":"مسقعة مصرية (نباتي)","country":"مصر","category":"Main Course",
       "description":"طبق شعبي نباتي: باذنجان وصلصة طماطم وبصل.","prep":20,"cook":45,"servings":4,
       "ingredients":["3 count باذنجان","1.5 cup صلصة طماطم","0.25 cup زيت زيتون","0.5 tsp كمون","1 tsp ملح"],
       "steps":["شيّ شرائح الباذنجان حتى الذهبية","شوّح البصل والثوم","أضف الصلصة وعلّق 10 دقائق","رصّ الطبقات وصينية واحفظها بالفرن 30–35 دقيقة على 180"]}'
# → {"ok":true,"added":["rcad1f224"],"duplicates":[],"rejected":[]}
```

إضافة إن غاب النص الكامل بالعربية (يُبنى المعرّف `r-…` سداسي عشوائي بدل slug فارغ — صندق معروض بالمصدر).

---

## 📱 PWA — تثبيت على كل الأجهزة

- `public/manifest.webmanifest` + `public/service-worker.js` + أيقونات (192/512/maskable).
- تعمل كتطبيق مثبّت (standalone) على أندرويد و iOS (مشاركة ← إضافة إلى الشاشة الرئيسية) و سطح المكتب (زر التثبيت في العنوان).
- **العمل بلا إنترنت بعد أول زيارة**: القشرة تخزَّن، وأول بيانات APIِ تُنسبر لاستعراضها أوفلاين؛ انقطاع صريح يعطي 503 JSON صادق بلا كذب.
- تحديث آلي ذكي: الملفات الثابتة تعمل بكاش ثم تُنسبر في الخلفية (stale-while-revalidate) — أي تعديل يصل المستخدم من ثاني فتح بلا يد.

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
