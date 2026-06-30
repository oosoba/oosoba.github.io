/* Tabs + hash routing. Progressive enhancement: with JS off, all panels
   remain visible (CSS only hides inactive panels once body.js is set). */
(function () {
  document.body.classList.add('js');

  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.panel'));
  var valid = panels.map(function (p) { return p.id; });

  function show(id, push) {
    if (valid.indexOf(id) === -1) { id = valid[0]; }
    tabs.forEach(function (t) {
      t.classList.toggle('active', t.dataset.tab === id);
      t.setAttribute('aria-selected', t.dataset.tab === id ? 'true' : 'false');
    });
    panels.forEach(function (p) { p.classList.toggle('active', p.id === id); });
    if (push && location.hash !== '#' + id) {
      history.replaceState(null, '', '#' + id);
    }
    window.scrollTo({ top: 0, behavior: 'auto' });
  }

  tabs.forEach(function (t) {
    t.addEventListener('click', function () { show(t.dataset.tab, true); });
  });

  window.addEventListener('hashchange', function () {
    show(location.hash.replace('#', ''), false);
  });

  show(location.hash.replace('#', '') || valid[0], false);
})();

/* Temporary font switcher (footer) — preview Atkinson / Lexend / Inter. */
(function () {
  var stacks = {
    atkinson: '"Atkinson Hyperlegible", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    lexend:   '"Lexend", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    inter:    '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  };
  var btns = Array.prototype.slice.call(document.querySelectorAll('.fontswitch button'));
  if (!btns.length) return;
  function apply(f) {
    if (!stacks[f]) f = 'atkinson';
    document.documentElement.style.setProperty('--font', stacks[f]);
    try { localStorage.setItem('font', f); } catch (e) {}
    btns.forEach(function (b) { b.classList.toggle('active', b.dataset.font === f); });
  }
  btns.forEach(function (b) { b.addEventListener('click', function () { apply(b.dataset.font); }); });
  var saved = 'atkinson';
  try { saved = localStorage.getItem('font') || 'atkinson'; } catch (e) {}
  apply(saved);
})();
