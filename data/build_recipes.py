#!/usr/bin/env python3
"""
Baran Cook — seed data builder (source of truth).
Writes data/recipes.json via json.dump (guaranteed-valid JSON).
12 traditional folk recipes across 10+ regions, Arabic + English.
Honesty: source_url = None (no invented external links).
"""
import json, os

def ing(name, amount=None, unit=None):
    return {"name": name, "amount": amount, "unit": unit}

def steps(*pairs):
    out = []
    for i, (ar, en) in enumerate(pairs, start=1):
        out.append({"step_number": i, "instruction_ar": ar, "instruction_en": en})
    return out

SRC = {"ar": "وصفة شعبية معروفة عاماً — زُرعت كبذرة محلية بلا رابط خارجي",
       "en": "Traditional folk recipe — locally seeded, no external URL"}

RECIPES = [
    dict(
        id="hummus-levant", source_url=None, source_note=SRC,
        origin_country="Levant", geo={"ar": "بلاد الشام", "en": "Levant"},
        category="Appetizer",
        prep=15, cook=40, servings=4,
        tags=["Vegetarian", "Halal"],
        ar=dict(
            title="حمّص بالطحينة",
            description="صحن شامي أيقوني — للحمص الحريري يجب تقشير الحمّص بعد سلق طويل.",
            ingredients=[
                ing("حمّص", 2, "cups"), ing("طحينة", 4, "tbsp"),
                ing("عصير ليمون", 3, "tbsp"), ing("ثوم", 2, "count"),
                ing("ملح", 1, "tsp"), ing("زيت زيتون", 2, "tbsp")],
            steps_steps=["انقع الحمّص الجاف في ماء بارد ليلة كاملة (أو استخدم معلّباً مصفّى).",
                         "اسلقه مع رشّة بيكربونات الصودا 40 دقيقة حتى يفصخ القشر.",
                         "أزل القشرة ثم اخفقه في الخالط مع الطحينة والليمون والثوم والملح.",
                         "أضف ماء السلق تدريجياً حتى القوام الحريري — قدمه بالزيت والبابريكا."]),
        en=dict(
            title="Hummus with Tahini",
            description="Iconic Levantine dish — silky hummus requires peeling the chickpeas after a long simmer.",
            ingredients=[
                ing("chickpeas", 2, "cups"), ing("tahini", 4, "tbsp"),
                ing("lemon juice", 3, "tbsp"), ing("garlic", 2, "count"),
                ing("salt", 1, "tsp"), ing("olive oil", 2, "tbsp")],
            steps_en=["Soak dried chickpeas in cold water overnight (or use well-drained canned).",
                      "Simmer with a pinch of baking soda for 40 minutes until skins loosen.",
                      "Peel the skins then blend with tahini, lemon juice, garlic and salt.",
                      "Add cooking water gradually to a silky texture; finish with olive oil and paprika."])
    ),
    dict(
        id="koshari-egypt", source_url=None, source_note=SRC,
        origin_country="Egypt", geo={"ar": "مصر", "en": "Egypt"},
        category="Main Course",
        prep=25, cook=50, servings=4,
        tags=["Vegetarian", "Halal", "May-Contain-Gluten"],
        ar=dict(
            title="كشري مصري",
            description="الطعام الوطني المصري: طبقات رز وعدس ومكرونة وبصل مقلي وصلصة حارصة وحمّص مسلوق.",
            ingredients=[
                ing("أرز", 2, "cups"), ing("عدس بني", 1, "cup"),
                ing("مكرونة", 2, "cups"), ing("بصل", 3, "count"),
                ing("صلصة طماطم", 1, "cup"), ing("حمّص مسلوق", 1, "cup")],
            steps_steps=["اسلقه العدس حتى ينضج دون أن يتفكك، ثم صفّه.",
                         "اطبخ الرز بنسبة 1:2 مع الماء والملح.",
                         "اسلق المكرونة، ثم اقلي البصل حتى يتحمّر ذهبياً.",
                         "قدّم بالطبقات: رز، عدس، مكرونة، ثم صلصة الطماطم والحمّص والبصل المقلي على القمة."],
            ),
        en=dict(
            title="Egyptian Koshari",
            description="Egypt's national dish — layered rice, lentils, pasta, crisp onions, tomato sauce and chickpeas.",
            ingredients=[
                ing("rice", 2, "cups"), ing("brown lentils", 1, "cup"),
                ing("pasta", 2, "cups"), ing("onions", 3, "count"),
                ing("tomato sauce", 1, "cup"), ing("chickpeas", 1, "cup")],
            steps_en=["Boil lentils until just tender; drain.",
                      "Cook rice with a 2:1 water-to-rice ratio and salt.",
                      "Boil pasta; fry thin onion slices until deep golden crisp.",
                      "Layer rice, lentils, pasta; top with tomato sauce, chickpeas and onions."])
    ),
    dict(
        id="turkish-pilav", source_url=None, source_note=SRC,
        origin_country="Turkey", geo={"ar": "تركيا", "en": "Turkey"},
        category="Side",
        prep=25, cook=25, servings=4,
        tags=["Vegetarian", "Halal"],
        ar=dict(
            title="بيلاف تركي بالصنوبر",
            description="أرز تركي: كل حبة مختومة بالزبدة، مع صنوبر مُحمص وعنب مجفف.",
            ingredients=[
                ing("أرز", 2, "cups"), ing("زبدة", 3, "tbsp"),
                ing("صنوبر", 2, "tbsp"), ing("عنب مجفف", 2, "tbsp"),
                ing("مرق دجاج", 4, "cups")],
            steps_steps=["انقع الأرز في ماء ساخن 20 دقيقة ثم صفّه.",
                         "حمص الصنوبر في الزبدة حتى الذهب.",
                         "أضف الأرز وقلّبه لحفظ كل حبة بالزبدة.",
                         "أضف مرق الدجاج الحار، أغلق الغطاء، اطبخ 20 دقيقة على نار هادئة.",
                         "أضف العنب المجفف قبيل التقديم."]),
        en=dict(
            title="Turkish Pilav with Pine Nuts",
            description="Turkish rice — every grain coated in butter and studded with pine nuts and currants.",
            ingredients=[
                ing("rice", 2, "cups"), ing("butter", 3, "tbsp"),
                ing("pine nuts", 2, "tbsp"), ing("currants", 2, "tbsp"),
                ing("chicken broth", 4, "cups")],
            steps_en=["Soak rice in hot water for 20 minutes; drain well.",
                      "Toast pine nuts in butter until golden.",
                      "Add the rice and stir to coat every grain.",
                      "Pour hot chicken broth, cover, simmer 20 minutes on low.",
                      "Fold in currants right before serving."])
    ),
    dict(
        id="chicken-ramen-jp", source_url=None, source_note=SRC,
        origin_country="Japan", geo={"ar": "اليابان", "en": "Japan"},
        category="Soup",
        prep=30, cook=150, servings=4,
        tags=["Halal"],
        ar=dict(
            title="رامن دجاج تقليدي",
            description="وصفة يابانية أصيلة: مرقة دجاج تمرد شقت ثلاث ساعات مع نودلز رامن.",
            ingredients=[
                ing("نودلز رامن", 200, "g"),
                ing("عظام دجاج", 1, "kg"), ing("صلصة صويا", 4, "tbsp"),
                ing("زنجبيل", 20, "g"), ing("بصل أخضر", 3, "count"),
                ing("بيض", 2, "count")],
            steps_steps=["اغلي عظام الدجاج مع الزنجبيل في قدر كبير 2.5 ساعة ثم رفِ.",
                         "تبمّر المرقة بصلصة الصويا والملح.",
                         "اسلق النودلز في قدر منفصل.",
                         "قدّم: نودلز ثم مرق ثم بيض مسلوق وبصل أخضر مقطع."]),
        en=dict(
            title="Traditional Chicken Ramen",
            description="Authentic Japanese recipe — long-simmered chicken broth with delicate noodles.",
            ingredients=[
                ing("ramen noodles", 200, "g"),
                ing("chicken bones", 1, "kg"), ing("soy sauce", 4, "tbsp"),
                ing("ginger", 20, "g"), ing("green onions", 3, "count"),
                ing("eggs", 2, "count")],
            steps_en=["Simmer bones with ginger in a large pot 2.5 hours, then strain.",
                      "Season the broth with soy sauce and salt.",
                      "Cook ramen noodles in a separate pot.",
                      "Assemble: noodles first, hot broth, soft-boiled egg, sliced green onion."],
            )
    ),
    dict(
        id="bibimbap-kr", source_url=None, source_note=SRC,
        origin_country="Korea", geo={"ar": "كوريا", "en": "Korea"},
        category="Main Course",
        prep=20, cook=25, servings=2,
        tags=["Vegetarian", "Halal"],
        ar=dict(
            title="بيمباب كوري نباتي",
            description="وعاء الأرز الكوري: خضار مُقشّة كل نوع مع السمسم وجوجنغنغ (فلفل حار) على القمة.",
            ingredients=[
                ing("أرز", 2, "cups"), ing("سباناخ", 100, "g"),
                ing("جزر", 1, "count"), ing("فطر شيتاكي", 100, "g"),
                ing("جوجنغان (فلفل حار)", 2, "tbsp"),
                ing("بذور سمسم", 1, "tbsp")],
            steps_steps=["اطبخ الأرز وتمّه بلوحة خشب من زيت السمسم.",
                         "شوّه كل خضار منفرداً مع ملح خفيف.",
                         "ترتّب الخضار على الرز في كتل ملوّنة.",
                         "أضف جوجنغان وامزج قبل الأكل."]),
        en=dict(
            title="Korean Bibimbap (Vegetarian)",
            description="Korean rice bowl with seasoned vegetables, sesame oil and gochujang chili paste.",
            ingredients=[
                ing("rice", 2, "cups"), ing("spinach", 100, "g"),
                ing("carrot", 1, "count"), ing("shiitake mushrooms", 100, "g"),
                ing("gochujang", 2, "tbsp"), ing("sesame seeds", 1, "tbsp")],
            steps_en=["Cook rice and season with a spoon of sesame oil.",
                      "Sauté each vegetable separately with a pinch of salt.",
                      "Arrange the vegetables in colour blocks on the rice.",
                      "Add gochujang chili paste and mix right before eating."])
    ),
    dict(
        id="butter-chicken-in", source_url=None, source_note=SRC,
        origin_country="India", geo={"ar": "الهند", "en": "India"},
        category="Main Course",
        prep=70, cook=35, servings=4,
        tags=["Halal", "Gluten-Free"],
        ar=dict(
            title="دجاج بالزبدة (مرغ ماخاني)",
            description="طبق دلهي الأسطوري: دجاج متبّل بالزبادي، يصير في صلصة طماطم كريميّة.",
            ingredients=[
                ing("صدر دجاج", 800, "g"), ing("زبادي", 200, "g"),
                ing("زبدة", 60, "g"), ing("كريما", 200, "ml"),
                ing("طماطم", 400, "g"), ing("جارام مصلا", 2, "tsp")],
            steps_steps=["انقع الدجاج في الزبادي مع الزنجبيل والثوم والبهارات لمدة ساعة.",
                         "شيّ الدجان في مقلاة حارّة حتى حد الأسود.",
                         "دب الكريم زبدة مع الطماطم وجارام مصلا بحلاوة سلسة.",
                         "أضفُ الكريما، اطبخ 10 دقيقة، ثم انضمام الدجان؛ اطبخ 10 دقيقة أخيرة."]),
        en=dict(
            title="Butter Chicken (Murgh Makhani)",
            description="Iconic Delhi dish — yogurt-marinated chicken finished in a creamy tomato sauce.",
            ingredients=[
                ing("chicken breast", 800, "g"), ing("yogurt", 200, "g"),
                ing("butter", 60, "g"), ing("cream", 200, "ml"),
                ing("tomatoes", 400, "g"), ing("garam masala", 2, "tsp")],
            steps_en=["Marinate chicken in yogurt, ginger-garlic and garam masala for 1 hour.",
                      "Char the chicken in a hot pan (or under the broiler).",
                      "Melt butter, cook tomatoes with garam masala to a smooth sauce.",
                      "Stir in cream, simmer 10 minutes; fold in the chicken and simmer 10 more."])
    ),
    dict(
        id="black-bean-tacos-mx", source_url=None, source_note=SRC,
        origin_country="Mexico", geo={"ar": "المكسيك", "en": "Mexico"},
        category="Street Food",
        prep=15, cook=15, servings=4,
        tags=["Vegetarian", "Gluten-Free"],
        ar=dict(
            title="تاكو الفاصوليا السوداء (نباتي)",
            description="طعام شوارع المكسيكي بلا لحم: فاصوليا سوداء بالكومين، ذرة، أفوكادو وليمون.",
            ingredients=[
                ing("فاصوليا سوداء", 400, "g"), ing("تورتيا ذرة", 8, "count"),
                ing("ذرة", 2, "cups"), ing("أفوكادو", 1, "count"),
                ing("ليمون", 1, "count"), ing("كزبرة طازجة", 2, "tbsp")],
            steps_steps=["سخّن الفاصوليا مع الكومين وطلب من عصير الليمون.",
                         "حمّب التورتيات على لهب.",
                         "هرس الأفوكادو مع الليمون والملح حتى جواهل.",
                         "قدّم: فاصوليا، ذرة، أفوكادو، كيلي كُوبّي وأسباق ليمون."]),
        en=dict(
            title="Black Bean Tacos (Vegetarian)",
            description="Mexican street food, meat-free — black beans with corn, avocado, lime and cilantro.",
            ingredients=[
                ing("black beans", 400, "g"), ing("corn tortillas", 8, "count"),
                ing("corn kernels", 2, "cups"), ing("avocado", 1, "count"),
                ing("lime", 1, "count"), ing("fresh cilantro", 2, "tbsp")],
            steps_en=["Warm beans with cumin and a splash of lime juice.",
                      "Char the corn tortillas briefly over a flame.",
                      "Mash avocado with lime and salt into quick guacamole.",
                      "Assemble: beans, corn, guacamole, cilantro and lime wedges."])
    ),
    dict(
        id="caprese-it", source_url=None, source_note=SRC,
        origin_country="Italy", geo={"ar": "إيطاليا", "en": "Italy"},
        category="Salad",
        prep=10, cook=0, servings=2,
        tags=["Vegetarian", "Gluten-Free", "Halal"],
        ar=dict(
            title="سلطة كابريزي",
            description="ألوان علم إيطاليا على طبق: طماطم، موزاريلا طازجة وريحان.",
            ingredients=[
                ing("طماطم", 3, "count"), ing("موزاريلا طازجة", 250, "g"),
                ing("ريحان", 20, "g"), ing("زيت زيتون", 3, "tbsp"),
                ing("ملح", 0.5, "tsp")],
            steps_steps=["قطّع الطماطم والموزاريلا في دوائير السمك نفسه.",
                         "رتّب بالتبادل: طماطم، موزاريلا، ورقة ريحان.",
                         "ترش بزيت الزيتون والملح السماقي."]),
        en=dict(
            title="Caprese Salad",
            description="Italian tricolore on a plate — tomatoes, fresh mozzarella and basil.",
            ingredients=[
                ing("tomatoes", 3, "count"), ing("fresh mozzarella", 250, "g"),
                ing("basil", 20, "g"), ing("olive oil", 3, "tbsp"),
                ing("salt", 0.5, "tsp")],
            steps_en=["Slice tomatoes and mozzarella into equal rounds.",
                      "Alternate tomato, mozzarella and a basil leaf on the plate.",
                      "Drizzle with olive oil and flaky salt."],
            )
    ),
    dict(
        id="french-onion-soup", source_url=None, source_note=SRC,
        origin_country="France", geo={"ar": "فرنسا", "en": "France"},
        category="Soup",
        prep=15, cook=70, servings=4,
        tags=[],  # contains beef broth — NOT vegetarian; has baguette — gluten
        ar=dict(
            title="شوربة البصل الفرنسية",
            description="بصل كرملي في مرقة لحم، مغطى بخبز بغيت وجبن غرويير مذاب.",
            ingredients=[
                ing("بصل", 6, "count"), ing("زبدة", 50, "g"),
                ing("مرق لحم البقر", 1.5, "liter"), ing("خبز بغيت", 1, "count"),
                ing("جبن غرويير", 150, "g")],
            steps_steps=["كرمل البصل في الزبدة 40 دقيقة على نار هادئة حتى يصبح ذهبياً كراميلياً.",
                         "أضف المرق; اغلي 20 دقيقة.",
                         "اسكب في أكواب آمنة للفرن؛ ضع شرائح البغيت على السطح.",
                         "أضف الغرويير; اشوي 10 دقائق حتى الذهب."]),
        en=dict(
            title="French Onion Soup",
            description="Caramelized onions in a rich beef broth topped with baguette and melted cheese.",
            ingredients=[
                ing("onions", 6, "count"), ing("butter", 50, "g"),
                ing("beef broth", 1.5, "liter"), ing("baguette", 1, "count"),
                ing("gruyère cheese", 150, "g")],
            steps_en=["Caramelize onions in butter for 40 minutes over low heat.",
                      "Add beef broth, simmer 20 minutes.",
                      "Ladle into oven-safe bowls, top with baguette slices.",
                      "Add gruyère and broil 10 minutes until golden."])
    ),
    dict(
        id="shiro-injera-et", source_url=None, source_note=SRC,
        origin_country="Ethiopia", geo={"ar": "إثيوبيا", "en": "Ethiopia"},
        category="Main Course",
        prep=30, cook=40, servings=4,
        tags=["Vegetarian", "Halal", "Gluten-Free"],
        ar=dict(
            title="شيرو مع إنجيرا",
            description="الأساس النباتي الإثيوبي: يست بدقيق الحمص مع الثوم وبربري، يؤكل مع إنجيرا إسفنجية.",
            ingredients=[
                ing("دقيق حمص", 2, "cups"), ing("دقيق تيف", 3, "cups"),
                ing("زيت نيجيلا", 2, "tbsp"), ing("ثوم", 3, "count"),
                ing("بهار بربري", 2, "tbsp")],
            steps_steps=["تخمير عجينة دقيق تيف بالماء لمدة ثلاثة أيام.",
                         "اسكب العجينة على ملاعق حارّة (مِتَط) حتى تفقّر منكّ الإنجيرا.",
                         "قلّب زيت النيجيلا مع الثوم والبربري.",
                         "أقُم في دقيق الحمص مع الماء، اطبخ حتى القوام الرسوء؛ قدّم مع إنجيرا."],
            ),
        en=dict(
            title="Shiro with Injera",
            description="Ethiopian vegan staple — a garlicky chickpea-flour stew with berbere on spongy injera.",
            ingredients=[
                ing("chickpea flour", 2, "cups"), ing("teff flour", 3, "cups"),
                ing("nigella seed oil", 2, "tbsp"), ing("garlic", 3, "count"),
                ing("berbere spice", 2, "tbsp")],
            steps_en=["Ferment a teff batter with water for three days.",
                      "Pour the batter onto a hot mitad (griddle); it bubbles into injera.",
                      "Sauté nigella oil with garlic and berbere spice.",
                      "Whisk in chickpea flour with water; simmer until silky; serve on injera."])
    ),
    dict(
        id="uzbek-plov", source_url=None, source_note=SRC,
        origin_country="Uzbekistan", geo={"ar": "أوزبكستان", "en": "Uzbekistan"},
        category="Main Course",
        prep=30, cook=80, servings=6,
        tags=["Halal", "Gluten-Free"],
        ar=dict(
            title="بلوف أوزبكي (أوشي)",
            description="البلوف في آسيا الوسطى: خروف مع جزر وبصل، في كبزان المقشور.",
            ingredients=[
                ing("لحم خروف", 700, "g"), ing("بصل", 3, "count"),
                ing("جزر", 600, "g"), ing("أرز ديزرا", 700, "g"),
                ing("زيت بذور الشمس", 200, "ml"), ing("كمون", 1, "tbsp")],
            steps_steps=["سخّن الزيت في الكازان وّوّن الخروف حتى البني.",
                         "أضف البصل ثم جزرشيك طويق: اطبخ حتى الليّن.",
                         "صرب الماء الحار الغمسة، أضف الكمون و الثوم؛ اطبخ 40 دقيقة (زرباك).",
                         "أضف الأرز، غطّه بالماء; اطبخ باكبر حتى الماص.",
                         "غطّ محكّم، طبخ 20 دقيقة على نار جيدة جداً، راحة قبل 10 دقائق."]),
        en=dict(
            title="Uzbek Plov (Oshi)",
            description="Central Asian pilaf — lamb, carrots and onions built in a kazan with devzira rice.",
            ingredients=[
                ing("lamb", 700, "g"), ing("onions", 3, "count"),
                ing("carrots", 600, "g"), ing("devzira rice", 700, "g"),
                ing("sunflower oil", 200, "ml"), ing("cumin", 1, "tbsp")],
            steps_en=["Heat oil in a kazan; sear lamb chunks until brown.",
                      "Add onions then thick carrot matchsticks; cook until soft.",
                      "Pour hot water to cover; add cumin and garlic heads; simmer 40 min (zirvak).",
                      "Add rice, cover with water; cook uncovered until absorbed.",
                      "Cover tightly, steam 20 minutes on very low heat; rest 10 minutes before fluffing."])
    ),
    dict(
        id="basbousa-levant", source_url=None, source_note=SRC,
        origin_country="Levant", geo={"ar": "بلاد الشام", "en": "Levant"},
        category="Dessert",
        prep=20, cook=30, servings=8,
        tags=["Vegetarian", "Halal", "May-Contain-Gluten"],
        ar=dict(
            title="بسبوسة",
            description="حلوى سموليما شامية مقيّدة بالشربات، مقصوصة بماسل ذهبي مع لوز.",
            ingredients=[
                ing("سمولينا", 2.5, "cups"), ing("زبادي", 200, "g"),
                ing("سكر", 1, "cup"), ing("سمن", 0.5, "cup"),
                ing("بيكنج بودر", 1, "tbsp")],
            steps_steps=["امزج السمولينا مع الزبادي والسمن؛ اتركها ساعة.",
                         "افرد في صينية مدهونة، نقّش معيّنات، ضع لوزة في كل معيّن.",
                         "اطبخ 30 دقيقة على 180\u00b0C حتى الذهب.",
                         "اسكب الشربات الباردة على الكعكة الساخنة؛ 1 ساعة قبل التقديم."]),
        en=dict(
            title="Basbousa (Semolina Cake)",
            description="Syrup-soaked Levantine semolina cake — scored diamonds topped with almonds.",
            ingredients=[
                ing("semolina", 2.5, "cups"), ing("yogurt", 200, "g"),
                ing("sugar", 1, "cup"), ing("clarified butter (samna)", 0.5, "cup"),
                ing("baking powder", 1, "tbsp")],
            steps_en=["Mix semolina with yogurt and ghee; rest 1 hour.",
                      "Spread in a greased pan, score diamonds, drop an almond on each.",
                      "Bake at 180°C for 30 minutes until golden.",
                      "Pour cold syrup over the hot cake; rest 1 hour before serving."])
    ),
]

def build():
    out = {"version": 1, "updated_at": "2026-10-22T00:00:00.000Z", "recipes": []}
    for r in RECIPES:
        langs = {}
        for L in ("ar", "en"):
            key_desc = "description"
            ingredients = r[L]["ingredients"]
            steps_list = []
            raw = r[L].get("steps_steps") or r[L].get("steps_en") or []
            for i, t in enumerate(raw, start=1):
                steps_list.append({"step_number": i, "instruction": t})
            # support bilingual steps list for ar/en separately
            steps_bi = None
            for s in r.get("steps", []):
                steps_bi = s  # take last; not used for these recipes
            if steps_bi is None and L == "en":
                raw2 = r["ar"].get("steps_steps") or []
                if not raw and raw2:
                    pass  # en step list present above; fallback to ar text if not provided
            languages = {
                "title": r[L]["title"],
                "description": r[L][key_desc],
                "ingredients": ingredients,
                "steps": [{"step_number": i, "instruction": (r[L].get("steps_steps") or r[L].get("steps_en") or [])[i-1]}
                          for i in range(1, len(raw) + 1)]
            }
            LANGS = {"ar": {"title": r["ar"]["title"], "description": r["ar"]["description"],
                             "ingredients": r["ar"]["ingredients"],
                             "steps": [{"step_number": i+1, "instruction": s} for i, s in enumerate(r["ar"]["steps_steps"])],
                             "source_note": r["source_note"]["ar"]},
                     "en": {"title": r["en"]["title"], "description": r["en"]["description"],
                             "ingredients": r["en"]["ingredients"],
                             "steps": [{"step_number": i+1, "instruction": s} for i, s in enumerate(r["en"]["steps_en"])],
                             "source_note": r["source_note"]["en"]}}
            langs[L] = LANGS[L]
        out["recipes"].append({
            "id": r["id"], "source_url": r["source_url"], "source_note": r["source_note"],
            "origin_country": r["origin_country"], "geo": r["geo"], "category": r["category"],
            "languages": langs,
            "prep_time_minutes": r["prep"], "cook_time_minutes": r["cook"],
            "servings": r["servings"], "dietary_tags": r["tags"],
            "media": {"images": [], "videos": []},
            "created_at": "2026-10-22T00:00:00.000Z",
        })
    # safety: circular extra vars cleanup
    for key in ("ingredients", "steps_steps", "steps_en", "title", "description"):
        for r in out["recipes"]:
            pass
    return out

if __name__ == "__main__":
    data = build()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[build_recipes] wrote {len(data['recipes'])} recipes -> {path}")
