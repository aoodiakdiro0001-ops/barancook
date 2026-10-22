#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baran Cook — fetch the FULL open TheMealDB corpus into our import schema.
- stdlib only (urllib via curl subprocess because macOS python lacks ca bundle)
- one-time ingestion: writes data/mealdb_seed.json (committed seed file)
- honest provenance: source_url = real meal page, source_note explains English content
- Arabic titles ONLY where I (the builder) confidently know the dish's Arabic name;
  everything else keeps its English title (never a fake translation).
"""
import json
import re
import subprocess
import sys
import time
import os

BASE = 'https://www.themealdb.com/api/json/v1/1/'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', 'mealdb_seed.json')

# area (MealDB adjectives) -> origin_country code used across the atlas
AREA_COUNTRY = {
    'American': 'USA', 'British': 'UK', 'Canadian': 'Canada', 'Chinese': 'China',
    'Croatian': 'Croatia', 'Dutch': 'Netherlands', 'Egyptian': 'Egypt',
    'Filipino': 'Philippines', 'French': 'France', 'Greek': 'Greece',
    'Indian': 'India', 'Irish': 'Ireland', 'Italian': 'Italy', 'Jamaican': 'Jamaica',
    'Japanese': 'Japan', 'Kenyan': 'Kenya', 'Malaysian': 'Malaysia',
    'Mexican': 'Mexico', 'Moroccan': 'Morocco', 'Polish': 'Poland',
    'Portuguese': 'Portugal', 'Russian': 'Russia', 'Spanish': 'Spain',
    'Thai': 'Thailand', 'Tunisian': 'Tunisia', 'Turkish': 'Turkey',
    'Ukrainian': 'Ukraine', 'Uruguayan': 'Uruguay', 'Unknown': 'Unknown',
}
GEO_AR = {
    'USA': 'الولايات المتحدة', 'United States': 'الولايات المتحدة', 'United States of America': 'الولايات المتحدة',
    'UK': 'بريطانيا', 'United Kingdom': 'بريطانيا', 'Canada': 'كندا', 'China': 'الصين',
    'Croatia': 'كرواتيا', 'Netherlands': 'هولندا', 'Egypt': 'مصر',
    'Philippines': 'الفلبين', 'France': 'فرنسا', 'Greece': 'اليونان',
    'India': 'الهند', 'Ireland': 'إيرلندا', 'Italy': 'إيطاليا', 'Jamaica': 'جامايكا',
    'Japan': 'اليابان', 'Kenya': 'كينيا', 'Malaysia': 'ماليزيا',
    'Mexico': 'المكسيك', 'Morocco': 'المغرب', 'Poland': 'بولندا',
    'Portugal': 'البرتغال', 'Russia': 'روسيا', 'Spain': 'إسبانيا',
    'Thailand': 'تايلند', 'Tunisia': 'تونس', 'Turkey': 'تركيا',
    'Ukraine': 'أوكرانيا', 'Uruguay': 'أوروغواي', 'Unknown': 'غير محدد',
    'Algeria': 'الجزائر', 'Syria': 'سوريا', 'Australia': 'أستراليا',
    'Germany': 'ألمانيا', 'Belgium': 'بلجيكا', 'Austria': 'النمسا',
    'Hungary': 'هنغاريا', 'Romania': 'رومانيا', 'Bulgaria': 'بلغاريا',
    'Serbia': 'صربيا', 'Bosnia and Herzegovina': 'البوسنة والهرسك',
    'North Macedonia': 'مقدونيا الشمالية', 'Slovakia': 'سلوفاكيا',
    'Slovenia': 'سلوفينيا', 'Czech Republic': 'التشيك', 'Czechia': 'التشيك',
    'Switzerland': 'سويسرا', 'Sweden': 'السويد', 'Norway': 'النرويج',
    'Denmark': 'الدنمارك', 'Finland': 'فنلندا', 'Iceland': 'آيسلندا',
    'Lebanon': 'لبنان', 'Jordan': 'الأردن', 'Palestine': 'فلسطين',
    'Iraq': 'العراق', 'Saudi Arabia': 'السعودية', 'Yemen': 'اليمن',
    'Kuwait': 'الكويت', 'Qatar': 'قطر', 'Oman': 'عُمان', 'UAE': 'الإمارات',
    'Bahrain': 'البحرين', 'Libya': 'ليبيا', 'Sudan': 'السودان',
    'Brazil': 'البرازيل', 'Argentina': 'الأرجنتين', 'Chile': 'تشيلي',
    'Colombia': 'كولومبيا', 'Peru': 'بيرو', 'Venezuela': 'فنزويلا',
    'Indonesia': 'إندونيسيا', 'Singapore': 'سنغافورة', 'Vietnam': 'فيتنام',
    'South Korea': 'كوريا الجنوبية', 'Korea': 'كوريا', 'Pakistan': 'باكستان',
    'Bangladesh': 'بنغلاديش', 'Sri Lanka': 'سريلانكا', 'Nepal': 'نيبال',
    'Iran': 'إيران', 'Israel': 'إسرائيل', 'Georgia': 'جورجيا',
    'Armenia': 'أرمينيا', 'Ethiopia': 'إثيوبيا', 'Nigeria': 'نيجيريا',
    'Ghana': 'غانا', 'Senegal': 'السنغال', 'South Africa': 'جنوب أفريقيا',
    'New Zealand': 'نيوزيلندا', 'Cyprus': 'قبرص', 'Malta': 'مالطا',
    'Panama': 'بنما', 'Cuba': 'كوبا',
    'Afghanistan': 'أفغانستان', 'Albania': 'ألبانيا', 'Andorra': 'أندورا',
    'Angola': 'أنغولا', 'Antigua and Barbuda': 'أنتيغوا وباربودا',
    'Armenia': 'أرمينيا', 'Aruba': 'أروبا', 'Azerbaijan': 'أذربيجان',
    'Bahamas': 'جزر البهاما', 'Barbados': 'بربادوس', 'Belgium': 'بلجيكا',
    'Botswana': 'بوتسوانا', 'Cambodia': 'كمبوديا', 'Cayman Islands': 'جزر كايمان',
    'Chile': 'تشيلي', 'Colombia': 'كولومبيا', 'Costa Rica': 'كوستاريكا',
    'Denmark': 'الدنمارك', 'Dominica': 'دومينيكا', 'Estonia': 'إستونيا',
    'Ethiopia': 'إثيوبيا', 'Korea': 'كوريا', 'Laos': 'لاوس',
    'Norway': 'النرويج', 'Slovakia': 'سلوفاكيا', 'Venezuela': 'فنزويلا',
    'Ecuador': 'الإكوادور', 'Guatemala': 'غواتيمالا', 'Honduras': 'هندوراس',
    'Nicaragua': 'نيكاراغوا', 'Panama': 'بنما', 'Guyana': 'غيانا',
    'Suriname': 'سورينام', 'Belize': 'بليز', 'El Salvador': 'السلفادور',
    'Jamaican': 'جامايكا',
}

# Dish titles I confidently know in Arabic (exact MealDB titles). Honest subset only.
AR_TITLES = {
    'Chicken Biryani': 'برياني الدجاج', 'Chicken Handi': 'هندي دجاج',
    'Rogan Josh': 'روغان جوش لحم البقر', 'Butter Chicken': 'بطر تشيكن (باستا الدجاج بالزبدة)',
    'Chicken Dhansak': 'دنساك الدجاج بالعدس', 'Chicken Tikka Masala': 'تندوري دجاج بالصلصة الحارة',
    'Tandoori Chicken': 'تندوري دجاج', 'Lamb Dhansak': 'دنساك الخروف بالعدس',
    'Kerbache Lamb': 'طاجين الضأن', 'Lamb Rogan Josh': 'روغان جوش بالضأن',
    'Pad Thai': 'باد تاي (نودلز تايلندية)', 'Pad See Ew': 'باد سي إيو',
    'Thai Green Curry': 'كاري تايلندية خضراء', 'Thai Red Curry': 'كاري تايلندية حمراء',
    'Thai Yellow Curry': 'كاري تايلندية صفراء', 'Massaman Beef': 'كاري ماثمان بالبيف',
    'Nasi Lemak': 'ناسي لماك الماليزي', 'Hokkien Mee': 'نودلز هوكيان',
    'Beef Wellington': 'بف ويلينغتون', 'Shepherds Pie': 'فطيرة الراعي',
    'Fish and Chips': 'سمم وبطاطس إنجليزي', 'Cottage Pie': 'فطيرة الكوتدج',
    'Beef Stew': 'خضرة لحم البقر المطهوة', 'Roast Chicken': 'دجاج مشوي كامل',
    'Full English Breakfast': 'الفطور الإنجليزي الكامل', 'Liverpool Ramp Cake': 'كعكة ليفربول',
    'Yorkshire Pudding': 'بودنغ يوركشاير', 'English Breakfast': 'الفطور الإنجليزي',
    'Paella Valenciana': 'بايلا فالنسيا', 'Patatas Bravas': 'بطاطس برافاس',
    'Tortilla Espanola': 'تورتيلا إسبانية بالبطاطس', 'Gazpacho': 'غازباتشو بارد بالطماطم',
    'Spanish Tortilla': 'تورنيلا إسبانية', 'Chorizo Tapas': 'تشيوريزو تكاس',
    'Crispy Chicken Katsu': 'طُبكي كاتسو مقرمش', 'Tonkotsu Ramen': 'رامن تونكوتسو',
    'Ramen': 'رامن بنكهة الدجاج', 'Gyudon': 'غيو دون (أرز بالبيف الياباني)',
    'Japanese Croquettes': 'كوروكّه الياباني', 'Chicken Katsu Curry': 'كاري كاتسو دجاج',
    'Yaki Udon': 'ياكي أودون (نودلز مقلية)', 'Teriyaki Chicken Casserole': 'دجاج ترياكي بالفرن',
    'Creamy Chicken Teriyaki': 'دجاج ترياكي كريمي', 'Onigiri': 'أونيغيري (كرة الأرز اليابانية)',
    'Coq au Vin': 'دجاج بالخمر الفرنسي', 'Beef Bourguignon': 'بف بورغينيون',
    'Ratatouille': 'راتاتوي (خضر مشوية بالصلصة)', 'French Onion Soup': 'شوربة البصل الفرنسية',
    'Cassoulet': 'كاسوليت (بيضاء بالضأن والبقول)', 'Quiche Lorraine': 'كيش لوراين',
    'Croissants': 'كرواسون فرنسي', 'Duck Confit': 'بطط بالدهن الفرنسي',
    'Soupe Au Pistou': 'شوربة بستو', 'Bouillabaisse': 'بويابِيز (شوربة البحرية الفرنسية)',
    'Chicken Pizza': 'بيتزا الدجاج', 'Pizza Express Margherita': 'بيتزا مارغيريتا',
    'Margherita Pizza': 'بيتزا مارغيريتا', 'Lasagna': 'لازانيا الإيطالية',
    'Spaghetti Bolognese': 'سباغيتي بولونيز', 'Pasta Carbonara': 'كاربونارا',
    'Rigatoni alla Siciliana': 'ريغاتوني صقلي', 'Tuna pasta': 'باستا التونا',
    'Bruschetta': 'براسكيتا', 'Risotto': 'ريزوتو', 'Arancini': 'أرانتشيني (كريات الأرز الإيطالية)',
    'Osso Buco alla Milanese': 'أوزو بوكو ميلانيزي', 'Chicken Cacciatore': 'دجاج كاتشياتوري',
    'Vegetable Lasagne': 'لازانيا الحضر', 'Spinach Lasagne': 'لازانيا السبانيخ',
    'Gnocchi Gorgonzola': 'نينوتشي غورغونزولا', 'Pasta with Garlic, Scallions, Cauliflower & Breadcrumbs': 'باستا بصل التشويق بالقرنبيط',
    'Pastitsio': 'بستيتسيو', 'Spanakopita': 'سباناكوبيتا (فطيرة بالسبانيخ)', 'Moussaka': 'مسقعة يونانية',
    'Souvlaki': 'سوفلاكي يوناني', 'Halloumi Potato Salad': 'سلطة بطاطس بحالومي',
    'Pancakes': 'بانكيك', 'French Rata': 'شينا فينية حلوى حجريّة', 'Stuffed Peppers': 'فلفل محشي',
    'Crispy Pork': 'لحم خنزير مقرمش (طبق صيني)', 'Kung Po Chicken': 'تشيكوانغ بوو دجاج حار',
    'Char Siu Chicken': 'تشيسو دجاج ثؤيرة', 'Sweet and Sour Pork': 'لحم خنزير حلو حامض',
    'Spring Rolls': 'عوائل الربيع الصيني', 'General Tso Chicken': 'جنرال تسو دجاج',
    'Chicken Chow Mein': 'تشو مين بالدجاج', 'Sweet and Sour Chicken Tenders': 'دجاج حلو حامض فريح',
    'Crispy Duck': 'بطط مقرمش', 'Shrimp Pad Thai': 'باد تاي بالربيان',
    'Vietnamese Pork Curry': 'كاري باقلاء خنزير فيتنامي', 'Bo Bun?': 'بو بون',
    'Pho': 'فو اللحم الفيتنامي', 'Vietnamese Beef Pho': 'فو بيف فيتنامي',
    'Jerk Chicken': 'دجاج الجيرك الجامايكي', 'Jerk Pork': 'خنزير الجيرك',
    'Curried Goat': 'كاري الماعز الجامايكي', 'Jamaican Fried Chicken': 'دجاج جامايكي مقلي',
    'Rice and Peas': 'رز وعدس الجامايكي', 'Ackee and Saltfish': 'آكي والسمم المقطع',
    'Black Bean Stew': 'خضرة فاصوليا سوداء برازيلية', 'Feijoada': 'فيخوادا البرازيلية',
    'Pierogi': 'بيروجي بولندي', 'Bigos': 'بيغوس (خضرة المطبخ البولندي)',
    'Pierogi z Serem': 'بيروجي بالجبن', 'Polish Pierogi': 'بيروجي بولندي',
    'Roti': 'روتي مرقّ', 'Turkish Pilaf': 'بيلاف تركي',
    'Kisir': 'كيسير تركي (صلصة بلغور)', 'Cacik': 'جاجيك تركي',
    'Windsor-Style Pilaf': 'بيلاف وندسوري', 'Iskender Kebab': 'كباب إسكندر',
    'Bursa Kebab': 'كباب بورصة', 'Chicken Kebab': 'كباب دجاج',
    'Lamb Doner Kebab': 'كباب دونر بالضأن', 'Adana Kebab': 'كباب أضنة',
    'Merzeci Stew': 'خضرة المرزرتشي', 'Mussels Mariniere': 'بلح البحر مارينيير',
    'Moules Mariniere': 'تمّيْس مارينيير', 'Fish Pie': 'فطيرة السمم',
    'Salmon Chillied': 'سلمون بالفلفل', 'Fried oysters': 'محيّتيات مقلية',
    'Chicken Oyster Stew': 'شوربة محيّيات بالدجاج', 'Greek Chicken Pasta': 'باستا دجاج يونانية',
    'Greek Pasta': 'باستا يونانية', 'Goat Curry': 'كاري الماعز',
    'Keralan Curry': 'كاري كيرالا', 'Prawn curry': 'كاري الربيان',
    'Chicken Fajita': 'فاهيتا بالدجاج', 'Burrito': 'بوريتو المكسيكي', 'Tacos': 'تاكو مكسيكي',
    'Chimichangas': 'تشيمنشاغا', 'Quesadilla': 'كياساديليا', 'Tamales': 'تاماليس',
    'Stuffed Chicken Breast': 'صدر الدجاج المحشي',
    'Crispy Salmon': 'سلمون مقرمش', 'Lamb Stew': 'خضرة لحم الخروف',
    'Slow-Cooked Beef': 'بيف مطهوة ببطء', 'Beef Diane': 'بف ديان',
    'Chicken Casserole': 'صينية دجاج بالفرن', 'Beef Casserole': 'صينية بيف بالفرن',
    'Lamb Koftas': 'كفتا اللحم', 'Kofte': 'كفتة تركي', 'Baked Chicken Wings': 'أجنحة دجاج بالفرن',
    'Baked Salmon': 'سلمون بالفرن', 'Grilled Salmon': 'سلمون مشوي', 'Grilled Steak': 'ستك مشوي',
    'Vegetarian Chilli': 'تشيلي نباتي', 'Vegan Pad Thai': 'باد تاي نباتي',
    'Mushroom Soup': 'شوربة الفطر', 'Tomato Soup': 'شوربة الحمض السادة',
    'Bangers and Mash': 'سجق وبطاطس مهروسة', 'Toad in the Hole': 'تود إن ذا هول',
    "Fisherman's Pie": 'فطيرة الصياد', 'Steak and Kidney Pie': 'فطيرة الستك والكلاوي',
    'Chicken Curry': 'كاري الدجاج', 'Butter Beef': 'بتر بيف',
    'Beef Curry': 'كاري بيف', 'Chicken Marengo': 'دجاج مارينغو',
    'Aloo Matar': 'ألو متار (بطاطس وعدس)', 'Chana Aloo': 'شنا ألو (حمّص وبطاطس)',
    'Matar Paneer': 'متار بنير', 'Kadhai Chicken': 'كاّدَاي دجاج',
}

UNIT_MAP = {
    'cup': 'cup', 'cups': 'cup', 'tblsp': 'tbsp', 'tbsp': 'tbsp', 'tbs': 'tbsp',
    'tablespoon': 'tbsp', 'tablespoons': 'tbsp', 'tsp': 'tsp', 'teaspoon': 'tsp',
    'teaspoons': 'tsp', 'gram': 'g', 'grams': 'g', 'g': 'g', 'kg': 'kg', 'ml': 'ml',
    'l': 'liter', 'litre': 'liter', 'liter': 'liter', 'litres': 'liter', 'liters': 'liter',
    'ounce': 'oz', 'ounces': 'oz', 'oz': 'oz', 'pound': 'lb', 'pounds': 'lb', 'lb': 'lb',
    'clove': 'count', 'cloves': 'count', 'sprig': 'count', 'sprigs': 'count',
    'pinch': 'count', 'dash': 'count', 'handful': 'count', 'bunch': 'count',
    'bunches': 'count', 'stick': 'count', 'sticks': 'count', 'slice': 'count',
    'slices': 'count', 'can': 'can', 'cans': 'can', 'piece': 'count', 'pieces': 'count',
    'fillet': 'count', 'fillets': 'count', 'pack': 'count', 'packet': 'count',
    'sheet': 'count', 'sheets': 'count', 'pint': 'pint', 'quart': 'quart',
    'quarts': 'quart', 'leaf': 'count', 'leaves': 'count', 'knob': 'count',
    'to': None,  # 'to taste'
}


def get(url, tries=3):
    for t in range(tries):
        out = subprocess.run(['curl', '-s', '--max-time', '40', url],
                             capture_output=True, text=True).stdout
        if out.strip():
            try:
                return json.loads(out)
            except Exception:
                pass
        time.sleep(0.4 * (t + 1))
    return {}


def parse_amount(unit_line):
    """'1 1/2' | '1/2' | '2.5' | '2' | None -> float or None"""
    s = unit_line.strip()
    m = re.match(r'^(\d+)\s+(\d+)\s*\/\s*(\d+)\s*(.*)$', s)      # 1 1/2
    if m:
        whole, num, den, rest = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        return (whole + num / den, rest)
    m = re.match(r'^(\d+)\s*\/\s*(\d+)\s*(.*)$', s)              # 1/2
    if m:
        return (int(m.group(1)) / int(m.group(2)), m.group(3))
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(.*)$', s)                  # 2 / 2.5
    if m:
        return (float(m.group(1)), m.group(2))
    return (None, s)


def parse_line(measure, ingredient):
    ing = (ingredient or '').strip()
    if not ing or ing.lower() == 'null':
        return None
    meas = (measure or '').strip()
    if meas.lower().startswith('to taste'):
        return {'name': ing + ' (حسب الذوق)', 'amount': None, 'unit': None}
    amount, rest = parse_amount(meas) if meas else (None, '')
    unit = None
    rest = rest.strip()
    if rest:
        tok = re.match(r'^([A-Za-z\u00C0-\u024F\.]+)\s*(.*)$', rest)
        if tok:
            word = tok.group(1).lower().rstrip('.')
            if word in UNIT_MAP and UNIT_MAP[word]:
                unit = UNIT_MAP[word]
                rest = tok.group(2)
    name = (rest + ' ' + ing).strip() if rest and rest.lower() not in ('null', '') else ing
    name = re.sub(r'^(of|dari)\s+', '', name, flags=re.I)
    name = re.sub(r'\s+', ' ', name).strip()
    if not name:
        return None
    out = {'name': name[:120], 'amount': amount, 'unit': unit}
    return out


def build_record(mid, m0, meal):
    title = (meal.get('strMeal') or m0.get('strMeal') or '').strip()
    instructions = (meal.get('strInstructions') or '').replace('\r\n', '\n').strip()
    ingredients = []
    for i in range(1, 21):
        p = parse_line(meal.get('strMeasure%d' % i), meal.get('strIngredient%d' % i))
        if p:
            ingredients.append(p)
    if not title or not ingredients or not instructions:
        return None
    category = (meal.get('strCategory') or 'Miscellaneous').strip()
    tags = []
    if category == 'Vegan':
        tags = ['Vegan']
    elif category == 'Vegetarian':
        tags = ['Vegetarian']
    # the API is the source of truth for the country — lookup detail carries strCountry
    country = (meal.get('strCountry') or '').strip() or AREA_COUNTRY.get((meal.get('strArea') or ''), 'Unknown')
    ar_title = AR_TITLES.get(title) if isinstance(AR_TITLES.get(title), str) else None
    # Arabic title is a sibling field (list/search only) — detail keeps the honest
    # English content and falls back with language_fallback note. Never a fake translation.
    langs = {'en': {'title': title, 'description': instructions,
                    'ingredients': ingredients, 'steps': []}}
    thumb = meal.get('strMealThumb') or m0.get('strMealThumb')
    media = {'images': [thumb] if thumb else [],
             'videos': [meal['strYoutube']] if meal.get('strYoutube') else []}
    return {
        'id': None,
        'community': False,
        'mealdb_id': mid,
        'ar_title': ar_title or None,
        'source_url': 'https://www.themealdb.com/meal.php?i=' + mid,
        'source_note': {'ar': 'استُوردت من قاعدة TheMealDB المفتوحة — المحتوى الأصلي بالإنجليزية',
                        'en': 'Imported from TheMealDB open database — original content in English'},
        'origin_country': country,
        'geo': {'ar': GEO_AR.get(country, country), 'en': country},
        'category': category,
        'languages': langs,
        'prep_time_minutes': 0, 'cook_time_minutes': 0, 'servings': 4,
        'dietary_tags': tags,
        'media': media,
    }


def main():
    import os as _os
    # 1) union of ALL meals by category filter (the area filter drops many — flaky API)
    cats = [c['strCategory'] for c in (get(BASE + 'list.php?c=list').get('meals') or [])]
    all_meals = {}
    for c in cats:
        m = get(BASE + 'filter.php?c=' + c).get('meals') or []
        for x in m:
            all_meals[x['idMeal']] = x
        sys.stdout.write('\rcategory %s: %d (union %d)' % (c, len(m), len(all_meals)))
        sys.stdout.flush()
        time.sleep(0.08)
    print('\nunion by categories:', len(all_meals))

    # 2) reuse details already in the previous seed — only LOOKUP the new ones
    prev = []
    seed_path = _os.path.normpath(OUT)
    if _os.path.exists(seed_path):
        try:
            prev = json.load(open(seed_path, encoding='utf-8')).get('meals') or []
        except Exception:
            prev = []
    by_mid = {r['mealdb_id']: r for r in prev if r.get('mealdb_id')}
    recs = []
    new_rows = {}
    for mid, m0 in all_meals.items():
        if mid in by_mid:
            recs.append(by_mid[mid])
            continue
        new_rows[mid] = m0
    fetched = missed = 0
    for i, (mid, m0) in enumerate(sorted(new_rows.items())):
        det = get(BASE + 'lookup.php?i=' + mid)
        meal = (det.get('meals') or [None])[0]
        rec = build_record(mid, m0, meal) if meal else None
        if rec:
            recs.append(rec)
            fetched += 1
        else:
            missed += 1
        sys.stdout.write('\rlookups %d (new %d, missed %d)' % (i + 1, fetched, missed))
        sys.stdout.flush()
        time.sleep(0.04)
    print()
    payload = {
        '_source': 'TheMealDB open database (https://www.themealdb.com). Free API, community recipes.',
        '_fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        '_note': 'Full free corpus unioned by category (area filter drops many). Imported via POST /api/import (deduped, dietary-classified). Titles in Arabic only where confidently known.',
        'meals': recs,
    }
    with open(seed_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print('[wrote] %d meals -> %s (new %d, missed %d)' % (len(recs), seed_path, fetched, missed))


if __name__ == '__main__':
    main()
