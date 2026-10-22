/* Baran Cook — UI controller (v101) */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const box = $('#search-box');
  const lang = $('#lang-sel');
  const unit = $('#unit-sel');
  const country = $('#country-sel');
  const grid = $('#results');
  const stat = $('#stat-line');
  const modal = $('#detail');
  const sheetBody = $('#sheet-body');
  const addModal = $('#add-modal');
  const addForm = $('#add-form');

  let diet = null;
  let timer = null;

  function toast(msg, ok) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.toggle('bad', ok === false);
    t.hidden = false;
    clearTimeout(t._h);
    t._h = setTimeout(() => { t.hidden = true; }, 3200);
  }

  // PWA service worker (offline shell + cached API data)
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  }

  async function j(url, opt) {
    let r;
    try { r = await fetch(url, opt || { credentials: 'same-origin' }); }
    catch { return null; }
    if (!r.ok) return null;
    try { return await r.json(); } catch { return null; }
  }

  function badge(t, cls) { return '<span class="badge ' + (cls || '') + '">' + t + '</span>'; }

  function dirSet(l) {
    const d = l === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.setAttribute('dir', d);
    document.documentElement.setAttribute('lang', l);
  }

  function countryLabel(r) {
    return langSel() === 'ar' ? (r.title_ar ? r.country : '') : r.country;
  }

  let langSel = () => lang.value;

  function card(m) {
    const title = langSel() === 'en' ? (m.title_en || m.title_ar) : (m.title_ar || m.title_en);
    const snip = langSel() === 'en' ? (m.snippet_en || m.snippet_ar) : (m.snippet_ar || m.snippet_en);
    const tags = (m.dietary_tags || []).map(t => badge(t, t === 'Vegetarian' ? 'd' : '')).join(' ');
    const showSnip = snip && snip !== title;
    return '<article class="card" data-id="' + m.id + '">' +
      '<h3>' + title + '</h3>' +
      '<div class="meta">' + badge(m.country, 'c') + tags + '</div>' +
      (showSnip ? '<p>' + snip + '</p>' : '') +
      '</article>';
  }

  async function refreshStats() {
    const s = await j('/api/stats');
    if (s && s.ok) {
      const line = langSel() === 'ar'
        ? 'موسوعة Baran Cook: ' + s.recipes + ' وصفة من ' + s.countries + ' بلدان · محرك بحث محلي (' + s.index_tokens + ' مفاتيح)'
        : 'Baran Cook Atlas: ' + s.recipes + ' recipes from ' + s.countries + ' countries · local search (' + s.index_tokens + ' tokens)';
      stat.textContent = line;
    }
    $('#honesty-count').textContent = (s && s.recipes) || '—';
  }

  async function fillCountries() {
    const c = await j('/api/countries');
    while (country.options.length > 1) country.remove(1); // reset rebuilt labels on lang change
    if (c && c.ok) {
      for (const it of c.countries) {
        const o = document.createElement('option');
        o.value = it.code;
        o.textContent = langSel() === 'ar' && it.country_ar ? it.country_ar : it.country_en || it.code;
        country.appendChild(o);
      }
    }
    if (typeof fillCountryDatalist === 'function') fillCountryDatalist();
  }

  async function load() {
    const q = box.value.trim();
    let url;
    if (q) {
      url = '/api/search?q=' + encodeURIComponent(q) + '&limit=24';
      if (country.value) url += '&country=' + encodeURIComponent(country.value);
      if (diet) url += '&diet=' + encodeURIComponent(diet);
      const data = await j(url);
      if (!data || !data.ok) { grid.innerHTML = '<p style="color:var(--warn)">تعذّر البحث — retry later</p>'; return; }
      grid.innerHTML = data.items.length ? data.items.map(card).join('') : '<p style="color:var(--dim)">لا نتائج (الموسوعة محلية — وصفاتك القادمة عبر /api/import)</p>';
      return;
    }
    const u = new URL('/api/recipes', location.origin);
    u.searchParams.set('limit', '24');
    if (country.value) u.searchParams.set('country', country.value);
    if (diet) u.searchParams.set('diet', diet);
    const data = await j(u.toString());
    if (!data || !data.ok) { grid.innerHTML = '<p style="color:var(--warn)">تعذّر جلب القائمة</p>'; return; }
    const dishes = data.items.map(m => ({
      id: m.id, title_ar: m.title_ar, title_en: m.title_en,
      country: m.country, dietary_tags: m.dietary_tags, country_key: m.country,
      snippet_ar: m.title_ar, snippet_en: m.title_en,
    }));
    // snippet fallback: use titles so cards look complete pre-detail
    grid.innerHTML = dishes.map(card).join('');
  }

  async function openDetail(id) {
    const u = '/api/recipes/' + encodeURIComponent(id) + '?lang=' + encodeURIComponent(langSel()) + '&units=' + encodeURIComponent(unit.value);
    const d = await j(u);
    if (!d || !d.ok) return;
    const r = d.recipe;
    const tags = (r.dietary_tags || []).map(t => badge(t, t === 'Vegetarian' ? 'd' : '')).join(' ');
    const ingList = (r.ingredients || []).map(i => {
      const a = i.amount != null ? (i.converted ? i.amount + ' ' + i.unit : i.original) : '';
      return '<li><b>' + i.name + '</b><span>' + a + '</span></li>';
    }).join('');
    const steps = (r.steps || []).map(s => '<li>' + s.instruction + '</li>').join('');
    sheetBody.innerHTML =
      '<h2>' + r.title + '</h2>' +
      '<div class="heads">' + badge(r.country, 'c') + badge(r.category || '', '') + tags + '</div>' +
      '<p style="color:var(--dim)">' + (r.description || '') + '</p>' +
      (surrounds(r) ) +
      '<ul class="ing">' + ingList + '</ul>' +
      '<div class="steps"><ol>' + steps + '</ol></div>' +
      '<small class="mtime">' + badge('⏱ ' + (r.prep_time_minutes || 0) + 'm prep', '') + badge('🔥 ' + (r.cook_time_minutes || 0) + 'm cook', '') + badge('🍽 ' + (r.servings || 0), '') + '</small>';
    modal.hidden = false;
  }
  function surrounds(r) { return ''; }

  function close(){ modal.hidden = true; }

  grid.addEventListener('click', (e) => {
    const c = e.target.closest('.card');
    if (c && c.dataset.id) openDetail(c.dataset.id);
  });
  $('#detail-close').addEventListener('click', close);
  modal.addEventListener('click', (e) => { if (e.target === modal) close(); });

  box.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(load, 220); });
  lang.addEventListener('change', async () => {
    dirSet(lang.value);
    await fillCountries(); // re-populate localized labels
    await refreshStats();
    await load();
  });
  unit.addEventListener('change', load);
  country.addEventListener('change', load);
  $('#diet-veg').addEventListener('click', (e) => {
    const on = e.currentTarget.classList.toggle('on');
    diet = on ? 'Vegetarian' : null;
    load();
  });
  $('#diet-hal').addEventListener('click', (e) => {
    const on = e.currentTarget.classList.toggle('on');
    diet = on ? 'Halal' : null;
    load();
  });

  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });

  /* ---------- community add-recipe form ---------- */
  function fillCountryDatalist() {
    const dl = $('#country-list');
    if (!dl) return;
    dl.innerHTML = '';
    [...country.options].slice(1).forEach(o => {
      const op = document.createElement('option');
      op.value = o.value;
      dl.appendChild(op);
    });
  }

  function openAddModal() {
    fillCountryDatalist(); // suggestions from live data + free typing allowed
    addModal.hidden = false;
    $('#f-title').focus();
  }

  function closeAdd() {
    addModal.hidden = true;
  }

  $('#add-btn').addEventListener('click', openAddModal);
  $('#add-close').addEventListener('click', closeAdd);
  addModal.addEventListener('click', (e) => { if (e.target === addModal) closeAdd(); });
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAdd(); });

  addForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const lines = (id) => String($(id).value || '').split('\n').map(x => x.trim()).filter(Boolean);
    const title = $('#f-title').value.trim();
    const payload = {
      lang: langSel(),
      title,
      country: $('#f-country').value.trim(),
      category: $('#f-category').value.trim(),
      description: $('#f-desc').value.trim(),
      prep: $('#f-prep').value.trim(),
      cook: $('#f-cook').value.trim(),
      servings: $('#f-servings').value.trim(),
      ingredients: lines('#f-ing'),
      steps: lines('#f-steps'),
    };
    if (!payload.title || !payload.country || !payload.ingredients.length || !payload.steps.length) {
      toast('اكمل الحقول الأساسية: الاسم، البلد، مكونات، خطوات', false);
      return;
    }
    const btn = $('.submit-btn');
    btn.disabled = true;
    btn.textContent = '⏳ قيد الإضافة…';
    const res = await fetch('/api/contribute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).catch(() => null);
    btn.disabled = false;
    btn.textContent = '🍳 أنشر الوصفة للأطلس';
    let j = null; try { j = await res.json(); } catch {}
    if (res && res.ok && j && j.ok) {
      if (j.duplicates && j.duplicates.length && !(j.added || []).length) {
        toast('الوصفة موجودة بالأطلس مسبقاً ✓ (منع التكرار يعمل)', false);
      } else {
        toast(j.thanks || 'أُضيفت الوصفة شكراً يا بطل! ✓');
        addForm.reset();
        closeAdd();
        await refreshStats();
        await fillCountries();
        await load();
      }
    } else if (res && res.status === 429) {
      toast('حدّ المساهمات (10/دقيقة) — حاول بعد قليل', false);
    } else {
      const d = (j && j.details) || [];
      toast('تعذر الإضافة: ' + (d.length ? d.join(' · ') : 'تأكد من الاتصال'), false);
    }
  });

  (async () => {
    dirSet(langSel());
    await refreshStats();
    await fillCountries();
    await load();
  })();
})();
