/* Floor Record: search, filters, tabs, topic picker, bill lists and the Compare table. No dependencies. */
(function () {
  var root = document.body.getAttribute('data-root') || '';
  var chamber = document.body.getAttribute('data-c') || '';  // '' on House pages, 'senate/' on Senate pages
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function getJSON(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }); }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var WORDS = { yea: 'Yea', nay: 'Nay', present: 'Present', nv: 'Did not vote' };
  function word(pos) { return WORDS[pos] || String(pos).replace('other:', ''); }
  var cache = {};
  function once(url) { return cache[url] || (cache[url] = getJSON(url)); }

  // ---- "my representative": found by ZIP code, kept only in this browser
  function store(key, val) { try { if (val === undefined) return localStorage.getItem(key) || ''; if (val === null) localStorage.removeItem(key); else localStorage.setItem(key, val); } catch (e) {} return ''; }
  function myRep() { try { return JSON.parse(store('fr-rep') || 'null'); } catch (e) { return null; } }
  function setMyRep(id, name) { store('fr-rep', id ? JSON.stringify({ id: id, name: name }) : null); showMyRep(); }
  function contactRows() { return once(root + 'contacts.json'); }
  // -> { rows: members for that ZIP, where: ['KY3', ...] } or null when the ZIP is not known
  function byZip(zip) {
    return Promise.all([once(root + 'zip/' + zip.charAt(0) + '.json'), contactRows()]).then(function (res) {
      var where = res[0][zip]; if (!where) return null;
      where = where.split(',');
      return { where: where, rows: res[1].filter(function (r) { return where.indexOf(r[2] + r[8]) !== -1; }) };
    });
  }
  function showMyRep() {
    var rep = myRep(), nav = document.querySelector('.nav'), old = document.querySelector('.myrep');
    if (old) old.parentNode.removeChild(old);
    if (rep && nav) { var a = document.createElement('a'); a.className = 'myrep'; a.href = root + 'members/' + rep.id + '/'; a.textContent = 'Your Rep: ' + rep.name; nav.insertBefore(a, nav.firstChild); }
    each(document.querySelectorAll('[data-myrep]'), function (b) { var on = rep && rep.id === b.getAttribute('data-myrep'); b.textContent = on ? 'This is your representative. Undo' : 'This is my representative'; b.classList.toggle('on', !!on); });
  }
  showMyRep();
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-myrep]'); if (!b) return;
    var rep = myRep(), id = b.getAttribute('data-myrep');
    setMyRep(rep && rep.id === id ? null : id, b.getAttribute('data-name'));
    yourVote();
  });
  // on a vote page, say up front how your own representative voted
  function yourVote() {
    var score = document.querySelector('.split3'), old = document.getElementById('your-vote'), rep = myRep();
    if (old) old.parentNode.removeChild(old);
    if (!score || !rep) return;
    var said = { 'voted-yea': 'voted Yea', 'voted-nay': 'voted Nay', 'voted-nv': 'did not vote', 'voted-present': 'voted Present' }, found = '';
    each(document.querySelectorAll('details[id^="voted-"]'), function (d) { if (d.querySelector('a[href$="members/' + rep.id + '/"]')) found = said[d.id] || 'is listed below'; });
    if (!found) return;
    var p = document.createElement('p'); p.id = 'your-vote'; p.className = 'yourvote';
    p.innerHTML = '<span class="label purple">Your representative</span><span><a href="' + root + 'members/' + esc(rep.id) + '/">' + esc(rep.name) + '</a> <strong>' + found + '</strong> on this.</span>';
    var card = score.closest('.card') || score; card.parentNode.insertBefore(p, card);
  }
  yourVote();

  // ---- search boxes (the one in the header and the big one on the home page share an index)
  var index = null, loading = null;
  function loadIndex() { return loading || (loading = getJSON(root + 'search.json').then(function (d) { index = d; return d; })); }
  each(document.querySelectorAll('[data-search]'), function (wrap) {
    var box = wrap.querySelector('input'), out = wrap.querySelector('.results');
    if (!box || !out) return;
    var run = function () {
      var q = box.value.trim().toLowerCase();
      if (/^\d{1,5}$/.test(q)) {  // a ZIP code: show who represents it
        out.classList.add('open');
        if (q.length < 5) { out.innerHTML = '<div class="none">Keep typing: a ZIP code has 5 digits.</div>'; return; }
        byZip(q).then(function (hit) {
          if (box.value.trim() !== q) return;
          if (!hit || !hit.rows.length) { out.innerHTML = '<div class="none">We could not match ' + esc(q) + '. Try a nearby ZIP code, or pick your state on the Members page.</div>'; return; }
          var one = hit.rows.length === 1;
          if (one) setMyRep(hit.rows[0][0], hit.rows[0][1]);
          out.innerHTML = '<div class="none">' + (one ? 'Your representative:' : 'ZIP code ' + esc(q) + ' is shared by ' + hit.rows.length + ' districts. One of these is yours:') + '</div>' + hit.rows.map(function (r) {
            return '<a role="option" href="' + root + 'members/' + esc(r[0]) + '/"><span>' + esc(r[1]) + ' (' + esc(r[4]) + ')</span><span class="small muted">' + esc(r[2]) + ' · ' + esc(r[3]) + '</span></a>';
          }).join('') + (one ? '' : '<a role="option" rel="noopener" href="https://www.house.gov/representatives/find-your-representative"><span class="small">Settle it with your street address on house.gov</span></a>');
        }).catch(function () { out.innerHTML = '<div class="none">Could not load. Try again.</div>'; });
        return;
      }
      if (!q || !index) { out.classList.remove('open'); return; }
      var terms = q.split(/\s+/);
      var hits = index.filter(function (it) { return terms.every(function (t) { return it.k.indexOf(t) !== -1; }); }).slice(0, 8);
      out.innerHTML = hits.length ? hits.map(function (it) {
        return '<a role="option" href="' + root + esc(it.u) + '"><span>' + esc(it.t) + '</span><span class="small muted">' + esc(it.s) + '</span></a>';
      }).join('') : '<div class="none">Nothing matches. Try your ZIP code, a last name, a state or a bill name.</div>';
      out.classList.add('open');
    };
    box.addEventListener('focus', function () { loadIndex().then(run).catch(function () {}); });
    box.addEventListener('input', function () { if (index) run(); else loadIndex().then(run).catch(function () {}); });
    box.addEventListener('keydown', function (e) { if (e.key === 'Escape') { out.classList.remove('open'); } if (e.key === 'Enter') { var a = out.querySelector('a'); if (a) location.href = a.href; } });
    document.addEventListener('click', function (e) { if (!wrap.contains(e.target) && !e.target.closest('[data-example]')) out.classList.remove('open'); });
    each(document.querySelectorAll('[data-example]'), function (btn) {
      if (!wrap.classList.contains('big')) return;
      btn.addEventListener('click', function () { box.value = btn.getAttribute('data-example'); box.focus(); loadIndex().then(run).catch(function () {}); });
    });
  });

  // ---- simple list filters
  each(document.querySelectorAll('input[data-filter]'), function (input) {
    var items = document.querySelectorAll(input.getAttribute('data-filter'));
    var groups = input.getAttribute('data-groups') ? document.querySelectorAll(input.getAttribute('data-groups')) : [];
    input.addEventListener('input', function () {
      var terms = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      each(items, function (el) {
        var text = (el.getAttribute('data-text') || el.textContent).toLowerCase();
        el.classList.toggle('hide', !terms.every(function (t) { return text.indexOf(t) !== -1; }));
      });
      each(groups, function (g) { g.classList.toggle('hide', !g.querySelector('[data-text]:not(.hide)')); });
    });
  });

  // ---- show or hide routine procedural votes
  each(document.querySelectorAll('[data-routine-toggle]'), function (boxEl) {
    boxEl.addEventListener('change', function () {
      var scope = boxEl.closest('[data-routine-scope]');
      if (scope) scope.classList.toggle('hide-routine', !boxEl.checked);
    });
  });

  // ---- jump to a state
  each(document.querySelectorAll('select[data-jump]'), function (sel) {
    sel.addEventListener('change', function () {
      var target = sel.value && document.getElementById(sel.value);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // ---- vote page: press a number to see who voted that way
  var rollNote = document.getElementById('roll-note'), rollAll = document.getElementById('roll-all');
  function rollFilter(only, label) {
    each(document.querySelectorAll('details[id^="voted-"]'), function (d) {
      var shown = 0;
      each(d.querySelectorAll('[data-p]'), function (el) { var ok = !only || el.getAttribute('data-p') === only; el.classList.toggle('hide', !ok); if (ok) shown++; });
      var c = d.querySelector('[data-count]'); if (c) c.textContent = shown;
    });
    if (rollNote) { rollNote.classList.toggle('hide', !only); rollNote.querySelector('span').textContent = only ? 'Showing ' + label + ' only.' : ''; }
  }
  each(document.querySelectorAll('[data-open]'), function (link) {
    link.addEventListener('click', function (e) {
      var target = document.getElementById(link.getAttribute('data-open'));
      if (!target) return;
      e.preventDefault();
      rollFilter(link.getAttribute('data-only') || '', link.getAttribute('data-only-name') || '');
      each(document.querySelectorAll('details[id^="voted-"]'), function (d) { d.open = d === target; });
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (history.replaceState) history.replaceState(null, '', '#' + target.id);
    });
  });
  if (rollAll) rollAll.addEventListener('click', function () { rollFilter('', ''); });
  if (location.hash.indexOf('#voted-') === 0) { var opened = document.getElementById(location.hash.slice(1)); if (opened) opened.open = true; }

  // ---- tabs
  each(document.querySelectorAll('[data-tab]'), function (btn) {
    btn.addEventListener('click', function () {
      var scope = btn.closest('[data-tabs]') || btn.closest('.card');
      each(scope.querySelectorAll('[data-tab]'), function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      each(scope.querySelectorAll('[data-pane]'), function (p) { p.classList.toggle('hide', p.getAttribute('data-pane') !== btn.getAttribute('data-tab')); });
    });
  });

  // ---- long bill lists
  each(document.querySelectorAll('[data-show-extra]'), function (btn) {
    btn.addEventListener('click', function () {
      each(btn.parentNode.querySelectorAll('[data-extra]'), function (el) { el.classList.remove('hide'); });
      btn.classList.add('hide');
    });
  });
  var coBtn = document.getElementById('co-all'), coRows = document.getElementById('co-rows');
  if (coBtn && coRows) {
    coBtn.addEventListener('click', function () {
      coBtn.disabled = true; coBtn.textContent = 'Loading…';
      getJSON(coBtn.getAttribute('data-src')).then(function (bills) {
        coRows.innerHTML = bills.map(function (b) {
          return '<a class="vrow" href="' + esc(b[4]) + '"><span class="main"><span class="name">' + esc(b[0]) + '</span><span class="fine">' + esc(b[1]) +
            (b[6] ? ' · Introduced ' + esc(b[6]) : '') + (b[5] ? ' · ' + esc(b[5]) : '') + '</span></span><span class="tag status' + (b[3] ? ' moved' : '') + '">' + esc(b[2]) + '</span></a>';
        }).join('');
      }).catch(function () { coBtn.disabled = false; coBtn.textContent = 'Could not load. Try again'; });
    });
  }

  // ---- a member's votes: the full log and the topic picker
  // votes-index.json rows: [id, date, roll, name, outcome, yeas, nays, routine, topicKeys, finePrint, yeaMeans, nayMeans]
  function memberData(src) { return Promise.all([once(root + chamber + 'votes-index.json'), once(src)]); }
  function phrase(v, pos) {
    if (pos === 'yea') return 'Voted to ' + v[10] + '.';
    if (pos === 'nay') return 'Voted to ' + v[11] + '.';
    if (pos === 'present') return 'Voted present.';
    if (pos === 'nv') return 'Did not vote.';
    return 'Voted for ' + word(pos) + '.';
  }
  function voteRow(v, m) {
    return '<a class="vrow" href="' + root + chamber + 'votes/' + esc(v[0]) + '/"><span class="when">' + esc(v[1]) + '</span><span class="main"><span class="tags"><span class="name">' + esc(v[3]) + '</span>' +
      '</span><span class="plain">' + esc(phrase(v, m[1])) + '</span><span class="fine">' + esc(v[9]) + '</span></span>' +
      '<span class="end"><span class="pos">' + esc(word(m[1])) + '</span><span style="font-size:14px;color:var(--muted)">' + esc(v[4]) + ', ' + v[5] + ' to ' + v[6] + '</span></span></a>';
  }

  var logBar = document.querySelector('[data-log]'), log = document.getElementById('vote-log');
  if (logBar && log) {
    var firstLog = log.innerHTML;
    each(logBar.querySelectorAll('[data-log-show]'), function (btn) {
      btn.addEventListener('click', function () {
        var mode = btn.getAttribute('data-log-show');
        each(logBar.querySelectorAll('[data-log-show]'), function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
        if (mode === 'recent') { log.innerHTML = firstLog; return; }
        log.innerHTML = '<tr><td colspan="4" class="muted">Loading…</td></tr>';
        memberData(logBar.getAttribute('data-src')).then(function (res) {
          var votes = res[0], mine = res[1];
          log.innerHTML = mine.slice().reverse().filter(function (m) { return mode === 'all' || m[2] === 0; }).map(function (m) {
            var v = votes[m[0]];
            return '<tr><td class="small muted" style="white-space:nowrap">' + esc(v[1]) + '</td><td><a href="' + root + chamber + 'votes/' + esc(v[0]) + '/">' + esc(v[3]) + '</a>' +
              (v[7] ? ' <span class="tag proc">Procedural step</span>' : '') +
              '</td><td class="strong">' + esc(word(m[1])) + '</td><td class="small">' + esc(v[4]) + ', ' + v[5] + '–' + v[6] + '</td></tr>';
          }).join('') || '<tr><td colspan="4" class="muted">Nothing to show.</td></tr>';
        }).catch(function () { log.innerHTML = '<tr><td colspan="4" class="muted">Could not load. Try again.</td></tr>'; });
      });
    });
  }

  var topicBar = document.querySelector('[data-topics]'), topicRows = document.getElementById('topic-rows');
  if (topicBar && topicRows) {
    var first = topicRows.innerHTML, summary = document.getElementById('topic-summary'), hidden = document.getElementById('topic-hidden');
    var firstSummary = summary.textContent, firstHidden = hidden.textContent, more = document.getElementById('more-topics');
    var pick = function (key, label) {
      each(topicBar.querySelectorAll('[data-topic]'), function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-topic') === key ? 'true' : 'false'); });
      if (more && !topicBar.querySelector('[data-topic="' + key + '"]')) more.value = key; else if (more) more.value = '';
      if (!key) { topicRows.innerHTML = first; summary.textContent = firstSummary; hidden.textContent = firstHidden; return; }
      summary.textContent = 'Loading…';
      memberData(topicBar.getAttribute('data-src')).then(function (res) {
        var votes = res[0], mine = res[1], shown = [], routine = 0;
        for (var i = mine.length - 1; i >= 0; i--) {
          var v = votes[mine[i][0]];
          if (v[8].indexOf(key) === -1) continue;
          if (v[7]) { routine++; continue; }
          shown.push(voteRow(v, mine[i]));
        }
        topicRows.innerHTML = shown.join('') || '<p class="muted" style="padding:24px 28px;margin:0">No votes on this topic yet.</p>';
        summary.textContent = shown.length + (shown.length === 1 ? ' vote on ' : ' votes on ') + label.toLowerCase();
        hidden.textContent = routine ? routine + (routine === 1 ? ' procedural vote hidden' : ' procedural votes hidden') : '';
      }).catch(function () { summary.textContent = 'Could not load. Try again.'; });
    };
    each(topicBar.querySelectorAll('[data-topic]'), function (b) { b.addEventListener('click', function () { pick(b.getAttribute('data-topic'), b.textContent); }); });
    if (more) more.addEventListener('change', function () { if (more.value) pick(more.value, more.options[more.selectedIndex].text); });
    // arriving from a topic page: #topic=health opens that topic straight away
    var fromHash = /topic=([\w-]+)/.exec(location.hash);
    if (fromHash) {
      var hb = topicBar.querySelector('[data-topic="' + fromHash[1] + '"]'), ho = more && more.querySelector('option[value="' + fromHash[1] + '"]');
      if (hb) pick(fromHash[1], hb.textContent); else if (ho) pick(fromHash[1], ho.text);
      var anchor = document.getElementById('topics'); if (anchor && (hb || ho)) anchor.scrollIntoView();
    }
  }

  // ---- "tell your representative": ZIP code or state -> who represents you, with ways to reach them
  each(document.querySelectorAll('[data-reach]'), function (box) {
    var sel = box.querySelector('[data-reach-state]'), zip = box.querySelector('[data-reach-zip]'), list = box.querySelector('[data-reach-list]'), msg = box.querySelector('[data-reach-msg]');
    var key = box.getAttribute('data-topic'), label = box.getAttribute('data-topic-name');
    var show = function (rows, text) {
      var rep = myRep();
      msg.innerHTML = text || '';
      list.innerHTML = rows.map(function (r) {
        var page = root + 'members/' + r[0] + '/' + (key ? '#topic=' + key : ''), acts = '', mine = rep && rep.id === r[0];
        if (r[6]) acts += '<a class="btn go" href="tel:+1' + esc(r[6].replace(/\D/g, '')) + '">Call ' + esc(r[6]) + '</a>';
        if (r[7] || r[5]) acts += '<a class="btn" rel="noopener" href="' + esc(r[7] || r[5]) + '">' + (r[7] ? 'Send a message' : 'Write on their website') + '</a>';
        return '<div class="reach-row' + (mine ? ' mine' : '') + '"><div class="who"><span class="dist">' + esc(r[3]) + (mine ? ' · your representative' : '') + '</span><span class="nm"><a href="' + page + '">' + esc(r[1]) + '</a><span class="party sm ' + esc(r[4]) + '">' + esc(r[4]) + '</span></span>' +
          '<a class="small" href="' + page + '">' + (key ? 'See how they voted on ' + esc(label) : 'See how they vote') + '</a>' +
          (rows.length > 1 ? '<button type="button" class="linkish small" data-myrep="' + esc(r[0]) + '" data-name="' + esc(r[1]) + '">This is my representative</button>' : '') +
          '</div><div class="reach-acts">' + acts + '</div></div>';
      }).join('');
      showMyRep();
    };
    var fail = function () { show([], 'Could not load. Try again.'); };
    var fromState = function () {
      var st = sel.value; if (!st) { show([]); return; }
      store('fr-state', st); zip.value = '';
      contactRows().then(function (rows) {
        var mine = rows.filter(function (r) { return r[2] === st; });
        show(mine, mine.length > 1 ? 'Everyone who represents ' + esc(sel.options[sel.selectedIndex].text) + '. Yours depends on where in the state you live. Enter your ZIP code to narrow it down.' : '');
      }).catch(fail);
    };
    var fromZip = function () {
      var z = zip.value.replace(/\D/g, ''); if (z.length < 5) { if (!sel.value) show([]); return; }
      byZip(z).then(function (hit) {
        if (!hit || !hit.rows.length) { show([], 'We could not match ' + esc(z) + '. Try a nearby ZIP code or choose your state.'); return; }
        store('fr-zip', z); sel.value = '';
        if (hit.rows.length === 1) { setMyRep(hit.rows[0][0], hit.rows[0][1]); yourVote(); show(hit.rows, '<strong>This is your representative.</strong>'); }
        else show(hit.rows, 'ZIP code ' + esc(z) + ' is shared by ' + hit.rows.length + ' districts. <strong>One of these is yours.</strong> To settle it, <a rel="noopener" href="https://www.house.gov/representatives/find-your-representative">enter your street address on house.gov</a>, then mark yours here.');
      }).catch(fail);
    };
    sel.addEventListener('change', fromState);
    zip.addEventListener('input', fromZip);
    list.addEventListener('click', function (e) { if (e.target.closest('[data-myrep]')) setTimeout(function () { if (zip.value) fromZip(); else fromState(); }, 0); });
    var z0 = store('fr-zip'), s0 = store('fr-state');
    if (z0) { zip.value = z0; fromZip(); } else if (s0 && sel.querySelector('option[value="' + s0 + '"]')) { sel.value = s0; fromState(); }
  });

  // ---- committees: search by committee or member, filter by kind, expand all, open from a link
  var clist = document.getElementById('committee-list');
  if (clist) {
    var cards = clist.querySelectorAll('.cmte'), cbox = document.querySelector('[data-cfilter]'), cnone = document.querySelector('[data-cnone]'), ckind = '', call = document.querySelector('[data-call]');
    var cdraw = function () {
      var q = cbox.value.trim().toLowerCase(), shown = 0;
      each(cards, function (c) {
        var ok = (!ckind || c.getAttribute('data-kind') === ckind) && (!q || c.getAttribute('data-text').indexOf(q) !== -1);
        c.hidden = !ok; if (ok) shown++;
        var hits = 0;
        each(c.querySelectorAll('.roster li'), function (li) { var hit = q.length > 2 && li.getAttribute('data-name').indexOf(q) !== -1; li.classList.toggle('hit', hit); if (hit) hits++; });
        if (ok && q.length > 2) c.open = hits > 0;
      });
      cnone.hidden = shown > 0;
    };
    cbox.addEventListener('input', cdraw);
    each(document.querySelectorAll('[data-ckind]'), function (b) { b.addEventListener('click', function () {
      ckind = b.getAttribute('data-ckind'); each(document.querySelectorAll('[data-ckind]'), function (x) { x.classList.toggle('on', x === b); }); cdraw(); }); });
    call.addEventListener('click', function () { var open = call.textContent === 'Expand all'; each(cards, function (c) { c.open = open; }); call.textContent = open ? 'Collapse all' : 'Expand all'; });
    var copen = function () { var t = location.hash && document.getElementById(location.hash.slice(1)); if (t && t.classList.contains('cmte')) { t.open = true; t.scrollIntoView(); } };
    window.addEventListener('hashchange', copen); copen();
  }

  // ---- Compare table
  var table = document.getElementById('lb'), dataEl = document.getElementById('lb-data');
  if (table && dataEl) {
    var rows = JSON.parse(dataEl.textContent), key = 'sort', dir = 1, party = 'all';
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
      var num = function (v) { return v == null ? '<span class="muted">n/a</span>' : v; };
      body.innerHTML = list.map(function (r, i) {
        return '<tr><td class="small muted">' + (i + 1) + '</td><td><span class="who"><span class="party ' + esc(r.p) + '">' + esc(r.p) + '</span><span><a class="strong" href="' + root + 'members/' + esc(r.id) + '/">' + esc(r.n) + '</a><span class="small muted">' + esc(r.seat) + '</span></span></span></td>' +
          '<td class="strong">' + pct(r.at) + '</td><td>' + num(r.bi) + '</td><td>' + num(r.ph) + '</td><td>' + num(r.bl) + '</td><td>' + pct(r.wp) + '</td></tr>';
      }).join('');
      count.textContent = 'Showing ' + list.length + ' of ' + rows.length + ' members.';
      each(table.querySelectorAll('th button'), function (b) {
        var base = b.getAttribute('data-label') || b.textContent; b.setAttribute('data-label', base);
        b.textContent = base + (b.getAttribute('data-sort') === key ? (dir < 0 ? ' ↓' : ' ↑') : '');
      });
    };
    each(table.querySelectorAll('th button'), function (b) {
      b.addEventListener('click', function () { var k = b.getAttribute('data-sort'); if (k === key) dir = -dir; else { key = k; dir = k === 'sort' ? 1 : -1; } draw(); });
    });
    each(document.querySelectorAll('[data-party]'), function (b) {
      b.addEventListener('click', function () { party = b.getAttribute('data-party'); each(document.querySelectorAll('[data-party]'), function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); }); draw(); });
    });
    stateSel.addEventListener('change', draw); nameBox.addEventListener('input', draw);
    draw();
  }
})();
