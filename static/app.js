/* Floor Record: search, filters, tabs, the member vote log and the leaderboard. No dependencies. */
(function () {
  var root = document.body.getAttribute('data-root') || '';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function getJSON(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  var WORDS = { yea: 'Yea', nay: 'Nay', present: 'Present', nv: 'Did not vote' };

  // ---- site search
  var box = document.getElementById('site-search'), out = document.getElementById('search-results'), index = null;
  if (box && out) {
    var run = function () {
      var q = box.value.trim().toLowerCase();
      if (!q || !index) { out.classList.remove('open'); return; }
      var terms = q.split(/\s+/);
      var hits = index.filter(function (it) { return terms.every(function (t) { return it.k.indexOf(t) !== -1; }); }).slice(0, 8);
      out.innerHTML = hits.length ? hits.map(function (it) {
        return '<a role="option" href="' + root + esc(it.u) + '"><span>' + esc(it.t) + '</span><span class="small muted">' + esc(it.s) + '</span></a>';
      }).join('') : '<div class="none">Nothing matches. Try a last name, a state or a bill number.</div>';
      out.classList.add('open');
    };
    box.addEventListener('focus', function () { if (!index) getJSON(root + 'search.json').then(function (d) { index = d; run(); }).catch(function () {}); });
    box.addEventListener('input', run);
    box.addEventListener('keydown', function (e) { if (e.key === 'Escape') { out.classList.remove('open'); } if (e.key === 'Enter') { var a = out.querySelector('a'); if (a) location.href = a.href; } });
    document.addEventListener('click', function (e) { if (!e.target.closest('.search')) out.classList.remove('open'); });
  }

  // ---- simple list filters
  Array.prototype.forEach.call(document.querySelectorAll('input[data-filter]'), function (input) {
    var items = document.querySelectorAll(input.getAttribute('data-filter'));
    var groups = input.getAttribute('data-groups') ? document.querySelectorAll(input.getAttribute('data-groups')) : [];
    input.addEventListener('input', function () {
      var terms = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      Array.prototype.forEach.call(items, function (el) {
        var text = (el.getAttribute('data-text') || el.textContent).toLowerCase();
        el.classList.toggle('hide', !terms.every(function (t) { return text.indexOf(t) !== -1; }));
      });
      Array.prototype.forEach.call(groups, function (g) { g.classList.toggle('hide', !g.querySelector('.chip:not(.hide)')); });
    });
  });

  // ---- tabs
  Array.prototype.forEach.call(document.querySelectorAll('[data-tab]'), function (btn) {
    btn.addEventListener('click', function () {
      var scope = btn.closest('.card');
      Array.prototype.forEach.call(scope.querySelectorAll('[data-tab]'), function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      Array.prototype.forEach.call(scope.querySelectorAll('[data-pane]'), function (p) { p.classList.toggle('hide', p.getAttribute('data-pane') !== btn.getAttribute('data-tab')); });
    });
  });

  // ---- a member's full vote log
  var allBtn = document.getElementById('all-votes'), log = document.getElementById('vote-log');
  if (allBtn && log) {
    allBtn.addEventListener('click', function () {
      allBtn.disabled = true; allBtn.textContent = 'Loading…';
      Promise.all([getJSON(root + 'votes-index.json'), getJSON(allBtn.getAttribute('data-src'))]).then(function (res) {
        var votes = res[0], mine = res[1];
        log.innerHTML = mine.slice().reverse().map(function (m) {
          var v = votes[m[0]], pos = WORDS[m[1]] || String(m[1]).replace('other:', '');
          return '<tr><td class="small muted" style="white-space:nowrap">' + esc(v[1]) + '</td><td class="small muted">' + esc(v[2]) + '</td><td><a href="' + root + 'votes/' + esc(v[0]) + '/">' + esc(v[3]) + '</a>' +
            (m[2] === 0 ? ' <span class="tag">Broke with party</span>' : '') + '</td><td class="strong">' + esc(pos) + '</td><td class="small">' + esc(v[4]) + ', ' + v[5] + '–' + v[6] + '</td></tr>';
        }).join('');
        allBtn.classList.add('hide');
      }).catch(function () { allBtn.disabled = false; allBtn.textContent = 'Could not load. Try again'; });
    });
  }

  // ---- leaderboard
  var table = document.getElementById('lb'), dataEl = document.getElementById('lb-data');
  if (table && dataEl) {
    var rows = JSON.parse(dataEl.textContent), key = 'ap', dir = -1, party = 'all';
    var body = table.querySelector('tbody'), stateSel = document.getElementById('lb-state'), nameBox = document.getElementById('lb-name'), count = document.getElementById('lb-count');
    var pct = function (v) { return v == null ? '<span class="muted">n/a</span>' : v.toFixed(1) + '%'; };
    var draw = function () {
      var q = (nameBox.value || '').trim().toLowerCase(), st = stateSel.value;
      var list = rows.filter(function (r) { return (party === 'all' || r.p === party) && (!st || r.st === st) && (!q || r.n.toLowerCase().indexOf(q) !== -1); });
      list.sort(function (a, b) {
        var x = a[key], y = b[key];
        if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
        return (typeof x === 'string' ? x.localeCompare(y) : x - y) * dir;
      });
      body.innerHTML = list.map(function (r, i) {
        return '<tr><td><span class="rank">' + (i + 1) + '</span></td><td><span class="who"><span class="party ' + esc(r.p) + '">' + esc(r.p) + '</span><span><a class="strong" href="' + root + 'members/' + esc(r.id) + '/">' + esc(r.n) + '</a><span class="small muted">' + esc(r.seat) + '</span></span></span></td>' +
          '<td><span class="strong">' + pct(r.wp) + '</span>' + (r.wp == null ? '' : '<span class="meter" aria-hidden="true" style="margin-top:6px;width:140px"><span style="width:' + r.wp + '%"></span></span>') + '</td>' +
          '<td class="strong">' + pct(r.ap) + '</td><td>' + (r.br == null ? '' : r.br) + '</td><td>' + r.vc.toLocaleString() + '</td><td>' + pct(r.at) + '</td></tr>';
      }).join('');
      count.textContent = 'Showing ' + list.length + ' of ' + rows.length + ' ranked members.';
      Array.prototype.forEach.call(table.querySelectorAll('th button'), function (b) {
        var base = b.getAttribute('data-label') || b.textContent; b.setAttribute('data-label', base);
        b.textContent = base + (b.getAttribute('data-sort') === key ? (dir < 0 ? ' ↓' : ' ↑') : '');
      });
    };
    Array.prototype.forEach.call(table.querySelectorAll('th button'), function (b) {
      b.addEventListener('click', function () { var k = b.getAttribute('data-sort'); if (k === key) dir = -dir; else { key = k; dir = k === 'sort' ? 1 : -1; } draw(); });
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-party]'), function (b) {
      b.addEventListener('click', function () { party = b.getAttribute('data-party'); Array.prototype.forEach.call(document.querySelectorAll('[data-party]'), function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); }); draw(); });
    });
    stateSel.addEventListener('change', draw); nameBox.addEventListener('input', draw);
    draw();
  }
})();
