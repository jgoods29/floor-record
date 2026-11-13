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
  var onStore = function () {};  // set by the account code, so a change made anywhere is saved to the account too
  function store(key, val) { try { if (val === undefined) return localStorage.getItem(key) || ''; if (val === null) localStorage.removeItem(key); else localStorage.setItem(key, val); } catch (e) {} onStore(key); return ''; }
  function myRep() { try { return JSON.parse(store('fr-rep') || 'null'); } catch (e) { return null; } }
  function setMyRep(id, name) { store('fr-rep', id ? JSON.stringify({ id: id, name: name }) : null); showMyRep(); afterYours(); }
  function contactRows() { return once(root + 'contacts.json'); }
  // the two senators for a state: resolves to [] when the Senate pages are not there
  function senatorsFor(st) { return !st ? Promise.resolve([]) : once(root + 'senators.json').then(function (rows) { return rows.filter(function (r) { return r[2] === st; }); }).catch(function () { return []; }); }
  // "Home" is only ever set by a ZIP code lookup. Browsing a state in a drop-down does not make its senators yours.
  function myState() { return store('fr-home'); }
  // -> { rows: members for that ZIP, where: ['KY3', ...] } or null when the ZIP is not known
  function byZip(zip) {
    return Promise.all([once(root + 'zip/' + zip.charAt(0) + '.json'), contactRows()]).then(function (res) {
      var where = res[0][zip]; if (!where) return null;
      where = where.split(',');
      var wasHome = store('fr-home'); store('fr-home', where[0].slice(0, 2)); if (wasHome !== where[0].slice(0, 2)) setTimeout(function () { afterYours(); }, 0);
      return { where: where, state: where[0].slice(0, 2), rows: res[1].filter(function (r) { return where.indexOf(r[2] + r[8]) !== -1; }) };
    });
  }
  function showMyRep() {
    var rep = myRep(), st = myState(), scope = document.body.getAttribute('data-scope') || 'all';
    var head = document.querySelector('header .wrap'), old = document.querySelector('.yours');
    if (old) old.parentNode.removeChild(old);
    each(document.querySelectorAll('[data-myrep]'), function (b) { var on = rep && rep.id === b.getAttribute('data-myrep'); b.textContent = on ? 'This is your representative. Undo' : 'This is my representative'; b.classList.toggle('on', !!on); });
    if (!head || (!rep && !st)) return;
    // its own spot beside the site name, so it never crowds the tabs; House pages show your representative,
    // Senate pages your senators, and pages that cover both show both
    var box = document.createElement('div'); box.className = 'yours';
    var anchor = head.querySelector('.chamber') || head.querySelector('.nav'); head.insertBefore(box, anchor);
    var add = function (cls, href, text) { var a = document.createElement('a'); a.className = 'myrep ' + cls; a.href = href; a.textContent = text; box.insertBefore(a, box.querySelector('.yours-x')); };
    var x = document.createElement('button'); x.type = 'button'; x.className = 'yours-x'; x.setAttribute('aria-label', 'Forget my representative and senators'); x.textContent = 'Clear';
    x.addEventListener('click', function () { store('fr-rep', null); store('fr-home', null); store('fr-zip', null); showMyRep(); yourVote(); afterYours(); });
    box.appendChild(x);
    if (rep && scope !== 'senate') add('', root + 'members/' + rep.id + '/', 'Your Rep: ' + rep.name);
    if (st && scope !== 'house') senatorsFor(st).then(function (rows) {
      if (!rows.length || !box.parentNode || box.querySelector('.sen')) return;
      add('sen', root + 'senate/members/#state-' + st, 'Your Senators: ' + rows.map(function (r) { return r[1].split(' ').pop(); }).join(', '));
    });
    if (!box.querySelector('.myrep') && !(st && scope !== 'house')) box.parentNode.removeChild(box);
  }
  var afterYours = function () {};  // set further down by the personal home page
  showMyRep();
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-myrep]'); if (!b) return;
    var rep = myRep(), id = b.getAttribute('data-myrep');
    setMyRep(rep && rep.id === id ? null : id, b.getAttribute('data-name'));
    yourVote();
  });
  // on a vote page, say up front how your own representative voted
  function yourVote() {
    var score = document.querySelector('.split3'), old = document.getElementById('your-vote');
    if (old) old.parentNode.removeChild(old);
    if (!score) return;
    var said = { 'voted-yea': 'voted Yea', 'voted-nay': 'voted Nay', 'voted-nv': 'did not vote', 'voted-present': 'voted Present' };
    var find = function (id) { var found = ''; each(document.querySelectorAll('details[id^="voted-"]'), function (d) { if (d.querySelector('a[href$="members/' + id + '/"]')) found = said[d.id] || 'is listed below'; }); return found; };
    var put = function (label, parts) {
      if (!parts.length || document.getElementById('your-vote')) return;
      var p = document.createElement('p'); p.id = 'your-vote'; p.className = 'yourvote';
      p.innerHTML = '<span class="label purple">' + label + '</span><span>' + parts.join(' ') + '</span>';
      var card = score.closest('.card') || score; card.parentNode.insertBefore(p, card);
    };
    if (chamber) {
      senatorsFor(myState()).then(function (rows) {
        put('Your senators', rows.map(function (r) { var f = find(r[0]); return f ? '<a href="' + root + 'senate/members/' + esc(r[0]) + '/">' + esc(r[1]) + '</a> <strong>' + f + '</strong>.' : ''; }).filter(Boolean));
      });
    } else {
      var rep = myRep(), f = rep && find(rep.id);
      if (f) put('Your representative', ['<a href="' + root + 'members/' + esc(rep.id) + '/">' + esc(rep.name) + '</a> <strong>' + f + '</strong> on this.']);
    }
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
          senatorsFor(hit.state).then(function (sens) {
            if (box.value.trim() !== q || !sens.length || out.innerHTML.indexOf('Your two senators') !== -1) return;
            out.innerHTML += '<div class="none">Your two senators:</div>' + sens.map(function (r) {
              return '<a role="option" href="' + root + 'senate/members/' + esc(r[0]) + '/"><span>' + esc(r[1]) + ' (' + esc(r[4]) + ')</span><span class="small muted">' + esc(r[2]) + ' · ' + esc(r[3]) + '</span></a>';
            }).join('');
            showMyRep();
          });
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
    box.addEventListener('keydown', function (e) { if (e.key === 'Escape') { out.classList.remove('open'); } if (e.key === 'Enter') {
      var zq = box.value.trim();
      // a ZIP code belongs to three people, not one: go to the page that lists the representative and both senators
      if (/^\d{5}$/.test(zq)) { e.preventDefault(); byZip(zq).then(function (hit) { if (!hit) return; store('fr-zip', zq); if (hit.rows.length === 1) setMyRep(hit.rows[0][0], hit.rows[0][1]); else { var r0 = myRep(); if (r0 && !hit.rows.some(function (r) { return r[0] === r0.id; })) setMyRep(null); } location.href = root + 'you/'; }); return; }
      var a = out.querySelector('a'); if (a) location.href = a.href; } });
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

  // Bring the top of a section to just under the pinned header, after the page has finished opening or closing lists.
  function bringToTop(el) {
    var go = function () { var head = document.querySelector('header.top'), y = el.getBoundingClientRect().top + window.pageYOffset - (head ? head.offsetHeight : 0) - 12; window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' }); };
    requestAnimationFrame(function () { requestAnimationFrame(go); });
  }

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
      if (target) bringToTop(target);
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
      bringToTop(target);
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
      var anchor = document.getElementById('topics'); if (anchor && (hb || ho)) bringToTop(anchor);
    }
  }

  // ---- "tell your representative": ZIP code or state -> who represents you, with ways to reach them
  each(document.querySelectorAll('[data-reach]'), function (box) {
    var sel = box.querySelector('[data-reach-state]'), zip = box.querySelector('[data-reach-zip]'), list = box.querySelector('[data-reach-list]'), msg = box.querySelector('[data-reach-msg]');
    var key = box.getAttribute('data-topic'), label = box.getAttribute('data-topic-name');
    var rowHtml = function (r, base, many, mineId) {
      var page = root + base + r[0] + '/' + (key ? '#topic=' + key : ''), acts = '', mine = mineId === r[0];
      if (r[6]) acts += '<a class="btn go" href="tel:+1' + esc(r[6].replace(/\D/g, '')) + '">Call ' + esc(r[6]) + '</a>';
      if (r[7] || r[5]) acts += '<a class="btn" rel="noopener" href="' + esc(r[7] || r[5]) + '">' + (r[7] ? 'Send a message' : 'Write on their website') + '</a>';
      return '<div class="reach-row' + (mine ? ' mine' : '') + '"><div class="who"><span class="dist">' + esc(r[3]) + (mine ? ' · your representative' : '') + '</span><span class="nm"><a href="' + page + '">' + esc(r[1]) + '</a><span class="party sm ' + esc(r[4]) + '">' + esc(r[4]) + '</span></span>' +
        '<a class="small" href="' + page + '">' + (key ? 'See how they voted on ' + esc(label) : 'See how they vote') + '</a>' +
        (many ? '<button type="button" class="linkish small" data-myrep="' + esc(r[0]) + '" data-name="' + esc(r[1]) + '">This is my representative</button>' : '') +
        '</div><div class="reach-acts">' + acts + '</div></div>';
    };
    var show = function (rows, text, st, byZipCode) {
      var rep = myRep(), house = rows.map(function (r) { return rowHtml(r, 'members/', rows.length > 1, rep && rep.id); }).join('');
      msg.innerHTML = text || '';
      list.innerHTML = house;
      showMyRep();
      senatorsFor(st).then(function (sens) {
        if (!sens.length) return;
        list.innerHTML = (house ? '<div class="reach-sub">In the House</div>' + house : '') + '<div class="reach-sub">' + (byZipCode ? 'Your two senators' : 'The two senators for this state') + '</div>' +
          sens.map(function (r) { return rowHtml(r, 'senate/members/', false, ''); }).join('');
        showMyRep();
      });
    };
    var fail = function () { show([], 'Could not load. Try again.'); };
    var fromState = function () {
      var st = sel.value; if (!st) { show([]); return; }
      store('fr-state', st); zip.value = '';
      contactRows().then(function (rows) {
        var mine = rows.filter(function (r) { return r[2] === st; });
        show(mine, mine.length > 1 ? 'Everyone who represents ' + esc(sel.options[sel.selectedIndex].text) + '. Yours depends on where in the state you live. Enter your ZIP code to narrow it down.' : '', st);
      }).catch(fail);
    };
    var fromZip = function () {
      var z = zip.value.replace(/\D/g, ''); if (z.length < 5) { if (!sel.value) show([]); return; }
      byZip(z).then(function (hit) {
        if (!hit || !hit.rows.length) { show([], 'We could not match ' + esc(z) + '. Try a nearby ZIP code or choose your state.'); return; }
        store('fr-zip', z); sel.value = '';
        if (hit.rows.length === 1) { setMyRep(hit.rows[0][0], hit.rows[0][1]); yourVote(); show(hit.rows, '<strong>This is your representative.</strong>', hit.state, true); }
        else show(hit.rows, 'ZIP code ' + esc(z) + ' is shared by ' + hit.rows.length + ' districts. <strong>One of these is yours.</strong> To settle it, <a rel="noopener" href="https://www.house.gov/representatives/find-your-representative">enter your street address on house.gov</a>, then mark yours here.', hit.state, true);
      }).catch(fail);
    };
    sel.addEventListener('change', fromState);
    zip.addEventListener('input', fromZip);
    list.addEventListener('click', function (e) { if (e.target.closest('[data-myrep]')) setTimeout(function () { if (zip.value) fromZip(); else fromState(); }, 0); });
    var z0 = store('fr-zip'), s0 = store('fr-state');
    if (z0) { zip.value = z0; fromZip(); } else if (s0 && sel.querySelector('option[value="' + s0 + '"]')) { sel.value = s0; fromState(); }
  });

  // ---- following topics and bills, and the personal home page. Everything is kept in this browser only.
  function saved(k) { try { return JSON.parse(store(k) || '[]'); } catch (e) { return []; } }
  function flip(k, v) { var a = saved(k), i = a.indexOf(v); if (i < 0) a.push(v); else a.splice(i, 1); store(k, a.length ? JSON.stringify(a) : null); }
  function paintFollows() {
    each(document.querySelectorAll('[data-follow]'), function (b) {
      var on = saved(b.getAttribute('data-follow')).indexOf(b.getAttribute('data-id')) !== -1, what = b.getAttribute('data-what');
      if (what) b.textContent = on ? 'Following this ' + what + ' · Undo' : 'Follow this ' + what;
      b.classList.toggle('on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-follow]'); if (!b) return;
    flip(b.getAttribute('data-follow'), b.getAttribute('data-id')); paintFollows(); afterYours();
  });
  paintFollows();

  var mine = document.getElementById('mine');
  if (mine) {
    var q1 = function (sel) { return mine.querySelector(sel); };
    var said = { yea: 'Yea', nay: 'Nay', nv: 'Did not vote', present: 'Present' };
    var chipFor = function (pos) { return '<span class="votechip ' + (pos === 'yea' || pos === 'nay' ? pos : 'none') + '">' + (said[pos] || 'Other') + '</span>'; };
    var voteRow = function (r, pre, extra) {
      return '<a class="minerow" href="' + root + pre + 'votes/' + esc(r[0]) + '/"><span class="mr-main"><span class="mr-name">' + esc(r[3]) + '</span><span class="small muted">' + esc(r[1]) + ' · ' + esc(r[4]) + ' ' + r[5] + ' to ' + r[6] + '</span></span>' + (extra || '') + '</a>';
    };
    var person = function (role, id, name, pre) {
      return Promise.all([once(root + pre + 'votes-index.json'), once(root + pre + 'members/' + id + '/votes.json')]).then(function (res) {
        var rows = res[1].filter(function (m) { var r = res[0][m[0]]; return r && !r[7] && said[m[1]]; }).slice(-3).reverse();
        return '<div class="minecol"><span class="dist">' + role + '</span><a class="mc-name" href="' + root + pre + 'members/' + esc(id) + '/">' + esc(name) + '</a>' +
          (rows.length ? rows.map(function (m) { return voteRow(res[0][m[0]], pre, chipFor(m[1])); }).join('') : '<span class="small muted">No recent votes on file.</span>') + '</div>';
      }).catch(function () { return ''; });
    };
    var drawMine = function () {
      var rep = myRep(), st = myState(), topics = saved('fr-topics'), bills = saved('fr-bills'), all = JSON.parse(mine.getAttribute('data-topics') || '[]');
      var any = rep || st || topics.length || bills.length;
      q1('[data-mine-clear]').hidden = !any;
      if (any) q1('[data-mine-lede]').textContent = st ? 'The people who represent you, and what you follow.' : 'Add your ZIP code to see the people who represent you.';
      // your three
      var jobs = [];
      if (rep) jobs.push(person('Your representative', rep.id, rep.name, ''));
      var three = q1('[data-mine-three]');
      (st ? senatorsFor(st) : Promise.resolve([])).then(function (sens) {
        sens.forEach(function (r) { jobs.push(person('Your senator', r[0], r[1], 'senate/')); });
        if (!jobs.length) { three.innerHTML = '<div class="card youempty"><strong>Nobody here yet.</strong><span class="muted">Type your ZIP code above and your representative and two senators will appear, with how they voted.</span></div>'; return; }
        Promise.all(jobs).then(function (cols) {
          three.innerHTML = '<div class="minegrid">' + cols.join('') + '</div>' + (rep ? '' : '<div data-mine-choose></div>');
          var zip = store('fr-zip'), slot = three.querySelector('[data-mine-choose]');
          if (slot && zip) byZip(zip).then(function (hit) {
            if (!hit || hit.rows.length < 2) return;
            slot.innerHTML = '<div class="card stack" style="gap:10px;margin-top:16px"><strong>Your ZIP code is shared by ' + hit.rows.length + ' House districts. Which representative is yours?</strong><div class="picks">' + hit.rows.map(function (r) { return '<button type="button" class="pick" data-mine-rep="' + esc(r[0]) + '" data-name="' + esc(r[1]) + '">' + esc(r[1]) + ' (' + esc(r[3]) + ')</button>'; }).join('') + '</div><span class="small muted">Not sure? <a rel="noopener" href="https://www.house.gov/representatives/find-your-representative">Look it up by street address at house.gov</a>.</span></div>';
          });
        });
      });
      // topics
      var name = {}; all.forEach(function (t) { name[t[0]] = t[1]; });
      var chosen = all.filter(function (t) { return topics.indexOf(t[0]) !== -1; }), rest = all.filter(function (t) { return topics.indexOf(t[0]) === -1; });
      var pick = function (t, on) { return '<button type="button" class="pick' + (on ? ' on' : '') + '" data-follow="fr-topics" data-id="' + esc(t[0]) + '" aria-pressed="' + on + '">' + esc(t[1]) + '</button>'; };
      var few = chosen.length ? 6 : 10, wide = mine.getAttribute('data-all-topics') === '1';
      q1('[data-mine-picks]').innerHTML = chosen.map(function (t) { return pick(t, true); }).join('') + rest.slice(0, wide ? rest.length : few).map(function (t) { return pick(t, false); }).join('') +
        (rest.length > few ? '<button type="button" class="linkish small" data-mine-more>' + (wide ? 'Show fewer' : 'Show all ' + all.length + ' topics') + '</button>' : '');
      var saidEl = q1('[data-mine-topicsaid]');
      if (saidEl) saidEl.textContent = chosen.length ? 'You follow ' + chosen.length + (chosen.length === 1 ? ' topic' : ' topics') + '. Saved. Tap one again to stop following it.' : 'Tap any topic to follow it. It is saved right away.';
      var tv = q1('[data-mine-topicvotes]');
      if (!topics.length) tv.innerHTML = '';
      else Promise.all([once(root + 'votes-index.json'), once(root + 'senate/votes-index.json').catch(function () { return []; })]).then(function (res) {
        var rows = [];
        res.forEach(function (idx, c) { idx.forEach(function (r) { if (!r[7] && r[8].some(function (k) { return topics.indexOf(k) !== -1; })) rows.push([Date.parse(r[1]) || 0, r, c ? 'senate/' : '']); }); });
        rows.sort(function (a, b) { return b[0] - a[0] || b[1][2] - a[1][2]; });
        tv.innerHTML = rows.slice(0, 6).map(function (x) { return voteRow(x[1], x[2], '<span class="tag chamber-' + (x[2] ? 'senate' : 'house') + '">' + (x[2] ? 'Senate' : 'House') + '</span>'); }).join('') || '<p class="muted" style="margin:0">No votes on these topics yet.</p>';
      });
      // bills
      q1('[data-mine-billbox]').hidden = !bills.length;
      if (bills.length) once(root + 'bills-index.json').then(function (idx) {
        var cls = { d: 'done', n: 'now', t: 'todo', s: 'stop' };
        q1('[data-mine-bills]').innerHTML = bills.filter(function (b) { return idx[b]; }).map(function (b) {
          var m = idx[b];
          return '<div class="minebill"><a class="mr-name" href="' + root + 'bills/' + esc(b) + '/">' + esc(m[0]) + '</a><ol class="track sm">' + m[3].map(function (l, i) { return '<li class="' + cls[m[2].charAt(i)] + '"><span>' + esc(l) + '</span></li>'; }).join('') + '</ol><span class="small muted">' + esc(m[4]) + '</span></div>';
        }).join('');
      });
      // coming up on your topics
      var cbox = q1('[data-mine-comingbox]'); cbox.hidden = true;
      if (topics.length) once(root + 'upcoming.json').then(function (items) {
        var hits = items.filter(function (i) { return topics.indexOf(i[3]) !== -1; });
        cbox.hidden = !hits.length;
        q1('[data-mine-coming]').innerHTML = hits.slice(0, 5).map(function (i) {
          return '<a class="minerow" href="' + (i[2] ? esc(i[1]) : root + esc(i[1])) + '"' + (i[2] ? ' rel="noopener"' : '') + '><span class="mr-main"><span class="mr-name">' + esc(i[0]) + '</span><span class="small muted">' + esc(i[6]) + ' · ' + esc(i[4]) + ' · ' + esc(i[5]) + '</span></span></a>';
        }).join('');
      }).catch(function () {});
      paintFollows();
    };
    q1('[data-mine-clear]').addEventListener('click', function () { ['fr-rep', 'fr-home', 'fr-zip', 'fr-topics', 'fr-bills'].forEach(function (k) { store(k, null); }); showMyRep(); drawMine(); });
    var zform = q1('[data-mine-zip]');
    if (zform) {
      var zbox = zform.querySelector('input'), znote = q1('[data-mine-zipnote]');
      zbox.value = store('fr-zip');
      zform.addEventListener('submit', function (e) {
        e.preventDefault(); var z = zbox.value.trim(); znote.hidden = false;
        if (!/^\d{5}$/.test(z)) { znote.textContent = 'A ZIP code is five numbers.'; return; }
        byZip(z).then(function (hit) {
          if (!hit) { znote.textContent = 'We do not know that ZIP code. Check the numbers and try again.'; return; }
          znote.hidden = true; store('fr-zip', z);
          setMyRep(hit.rows.length === 1 ? hit.rows[0][0] : null, hit.rows.length === 1 ? hit.rows[0][1] : null); drawMine();
        });
      });
      mine.addEventListener('click', function (e) { var b = e.target.closest('[data-mine-rep]'); if (b) { setMyRep(b.getAttribute('data-mine-rep'), b.getAttribute('data-name')); } });
    }
    mine.addEventListener('click', function (e) { if (e.target.closest('[data-mine-more]')) { mine.setAttribute('data-all-topics', mine.getAttribute('data-all-topics') === '1' ? '0' : '1'); drawMine(); } });
    afterYours = drawMine;
    drawMine();
  }

  // ---- confirmations: filter by kind of job (works together with the search box through a shared "off" mark)
  var ngroups = document.querySelectorAll('[data-ngroup]');
  if (ngroups.length) {
    var nrows = document.querySelectorAll('#nom-list .nrow'), nbox = document.getElementById('n-filter'), nnone = document.getElementById('nom-none'), ngroup = '';
    var ndraw = function () {
      var q = nbox.value.trim().toLowerCase(), shown = 0;
      each(nrows, function (r) { var ok = (!ngroup || r.getAttribute('data-group') === ngroup) && (!q || r.getAttribute('data-text').indexOf(q) !== -1); r.hidden = !ok; if (ok) shown++; });
      nnone.hidden = shown > 0;
    };
    nbox.addEventListener('input', function () { setTimeout(ndraw, 0); });
    each(ngroups, function (b) { b.addEventListener('click', function () { ngroup = b.getAttribute('data-ngroup'); each(ngroups, function (x) { x.classList.toggle('on', x === b); }); ndraw(); }); });
  }

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
    var copen = function () { var t = location.hash && document.getElementById(location.hash.slice(1)); if (t && t.classList.contains('cmte')) { t.open = true; bringToTop(t); } };
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
        return '<tr><td class="small muted">' + (i + 1) + '</td><td><span class="who"><span class="party ' + esc(r.p) + '">' + esc(r.p) + '</span><span><a class="strong" href="' + root + chamber + 'members/' + esc(r.id) + '/">' + esc(r.n) + '</a><span class="small muted">' + esc(r.seat) + '</span></span></span></td>' +
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
  // ---- accounts: one free sign-up that keeps your picks on any device and sends the Monday and Friday emails.
  // Only switched on when the page carries the account service's address. Sign-in is a link sent by email: no passwords.
  var SB = document.body.getAttribute('data-sb-url'), SBKEY = document.body.getAttribute('data-sb-key');
  if (SB && SBKEY) (function () {
    var KEYS = ['fr-rep', 'fr-home', 'fr-zip', 'fr-topics', 'fr-bills', 'fr-news'];
    var quiet = false, timer = null;
    function sess() { try { return JSON.parse(localStorage.getItem('fr-auth') || 'null'); } catch (e) { return null; } }
    function keep(s) { try { if (s) localStorage.setItem('fr-auth', JSON.stringify(s)); else localStorage.removeItem('fr-auth'); } catch (e) {} }
    function api(path, opt, token) {
      opt = opt || {};
      var h = { apikey: SBKEY, 'Content-Type': 'application/json' }, k;
      if (token) h.Authorization = 'Bearer ' + token;
      for (k in (opt.headers || {})) h[k] = opt.headers[k];
      return fetch(SB + path, { method: opt.method || 'GET', headers: h, body: opt.body ? JSON.stringify(opt.body) : undefined }).then(function (r) {
        return r.text().then(function (t) {
          var d = null; try { d = t ? JSON.parse(t) : null; } catch (e) {}
          if (!r.ok) { var err = new Error((d && (d.msg || d.message || d.error_description)) || 'Something went wrong (' + r.status + ')'); err.status = r.status; throw err; }
          return d;
        });
      });
    }
    // a fresh sign-in token, or null when nobody is signed in
    function token() {
      var s = sess(); if (!s) return Promise.resolve(null);
      if (s.expires_at - 60 > Date.now() / 1000) return Promise.resolve(s.access_token);
      return api('/auth/v1/token?grant_type=refresh_token', { method: 'POST', body: { refresh_token: s.refresh_token } }).then(function (d) {
        s.access_token = d.access_token; s.refresh_token = d.refresh_token; s.expires_at = Math.floor(Date.now() / 1000) + (d.expires_in || 3600); keep(s); return s.access_token;
      }).catch(function (e) { if (e.status) keep(null); paint(); return null; });
    }
    function list(k) { try { return JSON.parse(store(k) || '[]'); } catch (e) { return []; } }
    function localRow(id) {
      var rep = myRep();
      return { id: id, zip: store('fr-zip') || null, state: store('fr-home') || null, rep_id: rep ? rep.id : null, rep_name: rep ? rep.name : null,
               topics: list('fr-topics'), bills: list('fr-bills'), newsletter: store('fr-news') !== '0' };
    }
    function applyRow(r) {
      quiet = true;
      store('fr-zip', r.zip || null); store('fr-home', r.state || null);
      store('fr-rep', r.rep_id ? JSON.stringify({ id: r.rep_id, name: r.rep_name || '' }) : null);
      store('fr-topics', r.topics && r.topics.length ? JSON.stringify(r.topics) : null);
      store('fr-bills', r.bills && r.bills.length ? JSON.stringify(r.bills) : null);
      store('fr-news', r.newsletter ? '1' : '0');
      quiet = false;
      showMyRep(); afterYours(); paintFollows();
    }
    function push() {
      return token().then(function (t) {
        var s = sess(); if (!t || !s || !s.id) return;
        return api('/rest/v1/profiles?on_conflict=id', { method: 'POST', body: localRow(s.id), headers: { Prefer: 'resolution=merge-duplicates,return=minimal' } }, t)
          .then(function () { status('Saved to your account.'); }).catch(function (e) { status('Could not save just now: ' + e.message); });
      });
    }
    onStore = function (key) { if (quiet || KEYS.indexOf(key) === -1 || !sess()) return; clearTimeout(timer); timer = setTimeout(push, 700); };
    // right after signing in: an account that already holds picks wins; a new one is filled from this device
    function firstSync() {
      return token().then(function (t) {
        if (!t) return;
        return api('/auth/v1/user', {}, t).then(function (u) {
          var s = sess(); s.id = u.id; s.email = u.email; keep(s);
          return api('/rest/v1/profiles?select=*&id=eq.' + encodeURIComponent(u.id), {}, t).then(function (rows) {
            if (rows && rows.length) { applyRow(rows[0]); return; }
            var meta = u.user_metadata || {}, pend = {}; try { pend = JSON.parse(localStorage.getItem('fr-pending') || '{}'); } catch (e) {}
            var zip = pend.zip || meta.zip || '', news = pend.newsletter !== undefined ? pend.newsletter : meta.newsletter;
            quiet = true; if (news !== undefined) store('fr-news', news ? '1' : '0'); quiet = false;
            var ready = zip && !store('fr-zip') ? useZip(zip) : Promise.resolve();
            return ready.then(push);
          });
        }).then(function () { try { localStorage.removeItem('fr-pending'); } catch (e) {} paint(); });
      });
    }
    // a ZIP code -> home state, and the representative when the ZIP sits in one district
    function useZip(zip) {
      return byZip(zip).then(function (hit) {
        if (!hit) return null;
        quiet = true; store('fr-zip', zip); quiet = false;
        if (hit.rows.length === 1) setMyRep(hit.rows[0][0], hit.rows[0][1]);
        else { var rep = myRep(); if (rep && !hit.rows.some(function (r) { return r[0] === rep.id; })) setMyRep(null); }
        return hit;
      }).catch(function () { return null; });
    }
    function status(text) { each(document.querySelectorAll('[data-acct-status]'), function (el) { el.textContent = text; }); }

    // ---- arriving from the emailed link: the sign-in comes back in the address after the #
    var hash = location.hash.replace(/^#/, ''), back = {};
    if (/access_token=|error_description=/.test(hash)) {
      hash.split('&').forEach(function (kv) { var i = kv.indexOf('='); back[decodeURIComponent(kv.slice(0, i))] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' ')); });
      try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {}
      if (back.access_token) keep({ access_token: back.access_token, refresh_token: back.refresh_token, expires_at: Math.floor(Date.now() / 1000) + (+back.expires_in || 3600) });
    }

    window.addEventListener('hashchange', function () { if (/access_token=/.test(location.hash)) location.reload(); });  // link opened in a tab already on this page
    // ---- the sign-up box (home page and account page)
    each(document.querySelectorAll('[data-signup]'), function (form) {
      var note = form.querySelector('[data-signup-note]');
      if (store('fr-zip')) form.elements.zip.value = store('fr-zip');
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var email = form.elements.email.value.trim(), zip = form.elements.zip.value.trim(), news = form.elements.newsletter.checked;
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { note.textContent = 'Please type your email address.'; form.elements.email.focus(); return; }
        if (zip && !/^\d{5}$/.test(zip)) { note.textContent = 'A ZIP code is five numbers. You can also leave it empty and add it later.'; form.elements.zip.focus(); return; }
        try { localStorage.setItem('fr-pending', JSON.stringify({ zip: zip, newsletter: news })); } catch (err) {}
        var btn = form.querySelector('button[type=submit]'); btn.disabled = true; note.textContent = 'Sending...';
        var home = new URL(root + 'account/', location.href).href;
        api('/auth/v1/otp?redirect_to=' + encodeURIComponent(home), { method: 'POST', body: { email: email, create_user: true, data: { zip: zip, newsletter: news } } }).then(function () {
          form.innerHTML = '<div class="stack" style="gap:6px"><span class="h3">Check Your Email</span><span class="muted">We sent a sign-in link to <strong>' + esc(email) + '</strong>. Open it on this device and you are in. It can take a minute, and it sometimes lands in spam.</span></div>';
        }).catch(function (err) { btn.disabled = false; note.textContent = err.status === 429 ? 'Too many tries just now. Please wait a minute and try again.' : 'That did not go through: ' + err.message; });
      });
    });

    // ---- the account page, and the button in the header
    var page = document.querySelector('[data-account]');
    function paint() {
      var s = sess(), on = !!s;
      each(document.querySelectorAll('[data-acct-link]'), function (a) { a.querySelector('span').textContent = on ? 'Your Page' : 'Sign In'; a.href = a.getAttribute(on ? 'data-you' : 'data-in'); });
      each(document.querySelectorAll('[data-acct-settings]'), function (el) { el.hidden = !on; });
      each(document.querySelectorAll('[data-acct-out]'), function (el) { el.hidden = on; });
      each(document.querySelectorAll('[data-pop-open]'), function (el) { el.hidden = on; });
      each(document.querySelectorAll('[data-acct-in]'), function (el) { el.hidden = !on; });
      if (!page || !on) return;
      page.querySelector('[data-acct-title]').textContent = 'Your Account';
      page.querySelector('[data-acct-lede]').textContent = 'Everything here is saved to your account, so it follows you to any phone or computer you sign in on.';
      page.querySelector('[data-acct-email]').textContent = s.email || '';
      var zipBox = page.querySelector('#acct-zip'); if (document.activeElement !== zipBox) zipBox.value = store('fr-zip');
      var news = store('fr-news') !== '0'; page.querySelector('[data-acct-news]').checked = news;
      page.querySelector('[data-acct-newsnote]').textContent = news ? 'You are on the list. Emails go to ' + (s.email || 'your address') + '.' : 'You are not getting the emails. Your account still works.';
      var all = []; try { all = JSON.parse(page.getAttribute('data-topics') || '[]'); } catch (e) {}
      var mine = list('fr-topics');
      page.querySelector('[data-acct-topics]').innerHTML = all.map(function (t) { var on = mine.indexOf(t[0]) !== -1; return '<button type="button" class="pick' + (on ? ' on' : '') + '" data-follow="fr-topics" data-id="' + esc(t[0]) + '" aria-pressed="' + on + '">' + esc(t[1]) + '</button>'; }).join('');
      three();
    }
    function three(hit) {
      var box = page.querySelector('[data-acct-three]'), rep = myRep(), st = store('fr-home');
      if (!st) { box.innerHTML = '<p class="muted" style="margin:0">Add your ZIP code and your representative and two senators will show up here.</p>'; return; }
      senatorsFor(st).then(function (sens) {
        var out = '<div class="acct-three">';
        if (rep) out += '<a class="acct-who" href="' + root + 'members/' + esc(rep.id) + '/"><span class="small muted">Your representative</span><strong>' + esc(rep.name) + '</strong></a>';
        sens.forEach(function (r) { out += '<a class="acct-who" href="' + root + 'senate/members/' + esc(r[0]) + '/"><span class="small muted">Your senator</span><strong>' + esc(r[1]) + '</strong></a>'; });
        out += '</div>';
        if (!rep) {
          var pick = hit ? Promise.resolve(hit) : (store('fr-zip') ? byZip(store('fr-zip')) : Promise.resolve(null));
          pick.then(function (h) {
            if (h && h.rows.length > 1) out += '<p style="margin:10px 0 6px"><strong>Your ZIP code is shared by ' + h.rows.length + ' House districts. Which representative is yours?</strong></p><div class="picks">' + h.rows.map(function (r) { return '<button type="button" class="pick" data-acct-rep="' + esc(r[0]) + '" data-name="' + esc(r[1]) + '">' + esc(r[1]) + ' (' + esc(r[3]) + ')</button>'; }).join('') + '</div><p class="small muted" style="margin:8px 0 0">Not sure? <a rel="noopener" href="https://www.house.gov/representatives/find-your-representative">Look it up by street address at house.gov</a>.</p>';
            box.innerHTML = out;
          });
        } else box.innerHTML = out;
      });
    }
    if (page) {
      if (back.error_description) status('That sign-in link did not work: ' + back.error_description + '. Links work once and expire after a while, so ask for a new one.');
      page.querySelector('[data-acct-zipform]').addEventListener('submit', function (e) {
        e.preventDefault(); var z = page.querySelector('#acct-zip').value.trim();
        if (!/^\d{5}$/.test(z)) { status('A ZIP code is five numbers.'); return; }
        setMyRep(null);
        useZip(z).then(function (hit) { if (!hit) { status('We do not know that ZIP code. Check the numbers and try again.'); return; } clearTimeout(timer); push(); paint(); });
      });
      page.addEventListener('click', function (e) {
        var b = e.target.closest('[data-acct-rep]'); if (b) { setMyRep(b.getAttribute('data-acct-rep'), b.getAttribute('data-name')); paint(); return; }
        if (e.target.closest('[data-follow]')) setTimeout(paint, 0);
      });
      page.querySelector('[data-acct-news]').addEventListener('change', function (e) { store('fr-news', e.target.checked ? '1' : '0'); paint(); });
      page.querySelector('[data-acct-signout]').addEventListener('click', function () {
        token().then(function (t) { return t ? api('/auth/v1/logout', { method: 'POST' }, t).catch(function () {}) : null; }).then(function () { keep(null); paint(); status(''); });
      });
      var del = page.querySelector('[data-acct-delete]'), armed = false;
      del.addEventListener('click', function () {
        var note = page.querySelector('[data-acct-delnote]');
        if (!armed) { armed = true; del.textContent = 'Yes, Delete Everything'; note.textContent = 'Press again to confirm. This cannot be undone.'; setTimeout(function () { armed = false; del.textContent = 'Delete My Account'; note.textContent = ''; }, 8000); return; }
        token().then(function (t) { return api('/rest/v1/rpc/delete_me', { method: 'POST', body: {} }, t); }).then(function () {
          keep(null); quiet = true; KEYS.forEach(function (k) { store(k, null); }); quiet = false; showMyRep(); paint();
          page.querySelector('[data-acct-title]').textContent = 'Your Account Is Deleted'; page.querySelector('[data-acct-lede]').textContent = 'Your email address and everything saved with it have been erased. You are welcome back any time.';
        }).catch(function (e) { note.textContent = 'Could not delete just now: ' + e.message; });
      });
    }
    // ---- the unsubscribe link in every email
    var un = document.querySelector('[data-unsub]');
    if (un) {
      var tok = (location.search.match(/[?&]t=([0-9a-fA-F-]{36})/) || [])[1], title = un.querySelector('[data-unsub-title]'), text = un.querySelector('[data-unsub-text]');
      (tok ? api('/rest/v1/rpc/unsubscribe', { method: 'POST', body: { token: tok } }) : Promise.resolve(false)).then(function (ok) {
        if (ok) { quiet = true; store('fr-news', '0'); quiet = false; }
        title.textContent = ok ? 'You Are Unsubscribed' : 'That Link Did Not Work';
        text.textContent = ok ? 'No more Monday and Friday emails. Your account is still there if you want it, and you can turn the emails back on from it.' : 'Sign in to your account and turn the emails off there.';
      }).catch(function () { title.textContent = 'That Link Did Not Work'; text.textContent = 'Sign in to your account and turn the emails off there.'; });
    }
    // ---- the newsletter invitation: once, after 30 seconds on the site, never for someone signed in or who said no
    var pop = document.querySelector('[data-pop]'), fab = document.querySelector('[data-pop-open]');
    if (pop) {
      var esc27 = function (e) { if (e.key === 'Escape') shut(); };
      var shut = function () { pop.hidden = true; store('fr-pop', '1'); document.removeEventListener('keydown', esc27); if (fab) fab.focus(); };
      var open = function () { pop.hidden = false; document.addEventListener('keydown', esc27); var f = pop.querySelector('input[name=email]'); if (f) f.focus(); };
      pop.addEventListener('click', function (e) { if (e.target === pop || e.target.closest('[data-pop-close]')) shut(); });
      var pf = pop.querySelector('form');
      pf.addEventListener('submit', function () { store('fr-pop', '1'); var no = pop.querySelector('.pop-card > [data-pop-close].linkish'); if (no) no.textContent = 'Close'; });
      // the small Subscribe button: there on every page until the person has signed in
      if (fab) { fab.hidden = !!sess(); fab.addEventListener('click', open); }
      if (!sess() && !store('fr-pop') && !pop.hasAttribute('data-pop-quiet')) {
        var began = 0; try { began = +sessionStorage.getItem('fr-began') || 0; if (!began) { began = Date.now(); sessionStorage.setItem('fr-began', began); } } catch (e) { began = Date.now(); }
        setTimeout(function () {
          if (sess() || store('fr-pop') || !pop.hidden) return;
          var el = document.activeElement, busy = el && /INPUT|TEXTAREA|SELECT/.test(el.tagName);
          if (busy) el.addEventListener('blur', function () { if (!store('fr-pop')) { pop.hidden = false; document.addEventListener('keydown', esc27); } }, { once: true });
          else { pop.hidden = false; document.addEventListener('keydown', esc27); }
        }, Math.max(0, 30000 - (Date.now() - began)));
      }
    }
    paint();
    if (back.access_token) firstSync(); else if (sess() && page) firstSync();
  })();
})();
