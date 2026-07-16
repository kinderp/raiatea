(() => {
  const data = window.RAIATEA_MODULE;
  const $ = (s) => document.querySelector(s);
  let step = 0;
  let timer = null;
  const attempts = Array(data.steps.length).fill(0);

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function remediationMarkup(remediation) {
    if (!remediation) return '';
    const conceptLink = remediation.conceptRef
      ? `<a class="remediation-action" href="#concept-${escapeHtml(remediation.conceptRef)}">${escapeHtml(remediation.actionLabel || 'Ripassa il concetto')}</a>`
      : '';
    return `
      <div class="remediation" role="region" aria-label="Recupero mirato">
        <h4>${escapeHtml(remediation.title)}</h4>
        <p>${escapeHtml(remediation.explanation)}</p>
        <div class="remediation-actions">
          ${conceptLink}
          <button type="button" data-retry>${escapeHtml(remediation.retryLabel || 'Riprova')}</button>
        </div>
      </div>`;
  }

  function renderStep() {
    const item = data.steps[step];
    $('#phaseEyebrow').textContent = item.eyebrow || `Passo ${step + 1}`;
    $('#phaseTitle').textContent = item.title;
    $('#phaseText').innerHTML = item.explanation;
    $('#goalBox').innerHTML = item.goal;
    $('#observeBox').innerHTML = item.observe;
    $('#equationBox').textContent = item.equation || '';
    $('#stepLabel').innerHTML = `<b>Passo ${step + 1} di ${data.steps.length}</b>`;
    $('#progressBar').style.width = `${((step + 1) / data.steps.length) * 100}%`;
    $('#prevBtn').disabled = step === 0;
    $('#nextBtn').disabled = step === data.steps.length - 1;
    document.querySelectorAll('#stepsNav button').forEach((button) => {
      button.classList.toggle('current', Number(button.dataset.step) === step);
    });

    document.querySelectorAll('[data-node]').forEach((node) => node.classList.add('dim'));
    (item.activeNodes || []).forEach((id) => document.getElementById(id)?.classList.remove('dim'));
    document.querySelectorAll('[data-flow]').forEach((flow) => flow.classList.remove('animate'));
    (item.animatedFlows || []).forEach((id) => document.getElementById(id)?.classList.add('animate'));

    $('#quizQuestion').textContent = item.quiz.question;
    $('#quizAnswers').innerHTML = '';
    $('#quizFeedback').className = 'feedback';
    $('#quizFeedback').innerHTML = '';
    item.quiz.answers.forEach((answer, index) => {
      const button = document.createElement('button');
      button.textContent = answer;
      button.addEventListener('click', () => {
        const correct = index === item.quiz.correctIndex;
        attempts[step] += 1;
        $('#quizAnswers').querySelectorAll('button').forEach((candidate) => {
          candidate.disabled = true;
        });
        $('#quizFeedback').className = `feedback ${correct ? 'ok' : 'no'}`;
        if (correct) {
          $('#quizFeedback').textContent = item.quiz.correctFeedback;
          return;
        }
        $('#quizFeedback').innerHTML = `
          <p>${escapeHtml(item.quiz.incorrectFeedback)}</p>
          ${remediationMarkup(item.quiz.remediation)}
          <small>Tentativo ${attempts[step]}</small>`;
        $('#quizFeedback').querySelector('[data-retry]')?.addEventListener('click', () => {
          $('#quizFeedback').className = 'feedback';
          $('#quizFeedback').innerHTML = '';
          $('#quizAnswers').querySelectorAll('button').forEach((candidate) => {
            candidate.disabled = false;
          });
          $('#quizAnswers button')?.focus();
        });
      });
      $('#quizAnswers').appendChild(button);
    });
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    $('#playBtn').textContent = '▶ Riproduci';
  }
  function next() {
    if (step < data.steps.length - 1) { step += 1; renderStep(); }
    else stop();
  }

  $('#nextBtn').addEventListener('click', () => { stop(); next(); });
  $('#prevBtn').addEventListener('click', () => { stop(); if (step > 0) { step -= 1; renderStep(); } });
  $('#resetBtn').addEventListener('click', () => { stop(); step = 0; renderStep(); });
  $('#playBtn').addEventListener('click', () => {
    if (timer) { stop(); return; }
    $('#playBtn').textContent = '⏸ Pausa';
    timer = setInterval(next, 5500);
  });
  document.querySelectorAll('#stepsNav button').forEach((button) => {
    button.addEventListener('click', () => { stop(); step = Number(button.dataset.step); renderStep(); });
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight') { stop(); next(); }
    if (event.key === 'ArrowLeft' && step > 0) { stop(); step -= 1; renderStep(); }
  });

  const root = document.documentElement;
  const controls = {
    theme: $('#themeBtn'), size: $('#fontSizeSelect'), density: $('#densitySelect'),
    width: $('#widthSelect'), align: $('#alignSelect'), motion: $('#motionSelect')
  };
  const defaults = {theme:'light', size:'17', density:'normal', width:'68', align:'left', motion:'normal'};
  function current() { return {theme:root.dataset.theme, size:controls.size.value, density:controls.density.value, width:controls.width.value, align:controls.align.value, motion:controls.motion.value}; }
  function apply(settings) {
    const s = {...defaults, ...settings};
    root.dataset.theme = s.theme;
    root.dataset.density = s.density;
    root.dataset.align = s.align;
    root.dataset.motion = s.motion;
    root.style.setProperty('--reading-size', `${s.size}px`);
    root.style.setProperty('--reading-width', `${s.width}ch`);
    controls.size.value = s.size;
    controls.density.value = s.density;
    controls.width.value = s.width;
    controls.align.value = s.align;
    controls.motion.value = s.motion;
    controls.theme.textContent = s.theme === 'dark' ? '☀ Giorno' : '☾ Notte';
    $('#focusStatus').textContent = `${s.size}px · ${controls.density.options[controls.density.selectedIndex].text.toLowerCase()} · ${controls.width.options[controls.width.selectedIndex].text.toLowerCase()}`;
  }
  function save() { localStorage.setItem('raiatea-reading-settings', JSON.stringify(current())); }
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem('raiatea-reading-settings') || '{}'); } catch (_) {}
  apply(saved);
  controls.theme.addEventListener('click', () => { apply({...current(), theme:root.dataset.theme === 'dark' ? 'light' : 'dark'}); save(); });
  [controls.size, controls.density, controls.width, controls.align, controls.motion].forEach((control) => control.addEventListener('change', () => { apply(current()); save(); }));
  $('#resetReadingBtn').addEventListener('click', () => { localStorage.removeItem('raiatea-reading-settings'); apply(defaults); });

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;
    const target = document.getElementById(link.getAttribute('href').slice(1));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({behavior:root.dataset.motion === 'reduced' ? 'auto' : 'smooth', block:'center'});
    setTimeout(() => {
      target.classList.remove('target-flash');
      void target.offsetWidth;
      target.classList.add('target-flash');
      target.focus({preventScroll:true});
    }, root.dataset.motion === 'reduced' ? 50 : 450);
  });

  const toast = $('#pauseToast');
  let pauseTimer = setTimeout(() => toast.classList.add('show'), 20 * 60 * 1000);
  $('#dismissPause').addEventListener('click', () => {
    toast.classList.remove('show');
    clearTimeout(pauseTimer);
    pauseTimer = setTimeout(() => toast.classList.add('show'), 20 * 60 * 1000);
  });

  renderStep();
})();
