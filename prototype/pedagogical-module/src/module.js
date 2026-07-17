(() => {
  const data = window.RAIATEA_MODULE;
  const $ = (s) => document.querySelector(s);
  const storageKey = `raiatea-progress:${data.id}`;
  let step = 0;
  let timer = null;

  const emptyState = () => ({
    currentStep: 0,
    steps: data.steps.map(() => ({attempts: 0, correct: false, usedRemediation: false, activityCompleted: false}))
  });

  function loadProgress() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
      if (!saved || !Array.isArray(saved.steps) || saved.steps.length !== data.steps.length) return emptyState();
      return saved;
    } catch (_) {
      return emptyState();
    }
  }

  let progressState = loadProgress();
  step = Math.min(Math.max(Number(progressState.currentStep) || 0, 0), data.steps.length - 1);

  function saveProgress() {
    progressState.currentStep = step;
    localStorage.setItem(storageKey, JSON.stringify(progressState));
    renderEvidence();
  }

  function escapeHtml(value) {
    return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  }

  function remediationMarkup(remediation) {
    if (!remediation) return '';
    const conceptLink = remediation.conceptRef
      ? `<a class="remediation-action" href="#concept-${escapeHtml(remediation.conceptRef)}">${escapeHtml(remediation.actionLabel || 'Ripassa il concetto')}</a>`
      : '';
    const activity = remediation.activity;
    const activityMarkup = activity ? `<div class="remediation-activity" data-remediation-activity><b>${escapeHtml(activity.prompt)}</b><div class="remediation-answers">${activity.answers.map((answer, index) => `<button type="button" data-activity-answer="${index}">${escapeHtml(answer)}</button>`).join('')}</div><div class="remediation-activity-feedback" aria-live="polite"></div></div>` : '';
    return `<div class="remediation" role="region" aria-label="Recupero mirato"><h4>${escapeHtml(remediation.title)}</h4><p>${escapeHtml(remediation.explanation)}</p><div class="remediation-actions">${conceptLink}</div>${activityMarkup}<div class="remediation-actions"><button type="button" data-retry ${activity ? 'disabled' : ''}>${escapeHtml(remediation.retryLabel || 'Riprova')}</button></div></div>`;
  }

  function wireRemediation(remediation) {
    const feedback = $('#quizFeedback');
    const retry = feedback.querySelector('[data-retry]');
    const activity = remediation?.activity;
    feedback.querySelectorAll('[data-activity-answer]').forEach((button) => {
      button.addEventListener('click', () => {
        const index = Number(button.dataset.activityAnswer);
        const correct = index === activity.correctIndex;
        const message = feedback.querySelector('.remediation-activity-feedback');
        feedback.querySelectorAll('[data-activity-answer]').forEach((candidate) => { candidate.disabled = true; });
        message.textContent = correct ? activity.correctFeedback : activity.incorrectFeedback;
        if (correct) {
          progressState.steps[step].activityCompleted = true;
          retry.disabled = false;
          saveProgress();
        } else {
          setTimeout(() => feedback.querySelectorAll('[data-activity-answer]').forEach((candidate) => { candidate.disabled = false; }), 700);
        }
      });
    });
    retry?.addEventListener('click', () => {
      feedback.className = 'feedback';
      feedback.innerHTML = '';
      $('#quizAnswers').querySelectorAll('button').forEach((candidate) => { candidate.disabled = false; });
      $('#quizAnswers button')?.focus();
    });
  }

  function renderEvidence() {
    const completed = progressState.steps.filter((item) => item.correct).length;
    const recovered = progressState.steps.filter((item) => item.correct && item.usedRemediation).length;
    const attempts = progressState.steps.reduce((sum, item) => sum + item.attempts, 0);
    $('#evidenceSummary').textContent = `${completed}/${data.steps.length} verifiche completate · ${attempts} tentativi · ${recovered} risposte corrette dopo recupero.`;
    $('#evidenceGrid').innerHTML = data.steps.map((item, index) => {
      const evidence = progressState.steps[index];
      const stateClass = evidence.correct ? (evidence.usedRemediation ? 'evidence-recovered' : 'evidence-ok') : 'evidence-pending';
      const status = evidence.correct ? (evidence.usedRemediation ? 'Corretta dopo recupero' : 'Corretta al primo percorso') : (evidence.attempts ? 'Da consolidare' : 'Non ancora verificata');
      return `<div class="evidence-item ${stateClass}"><strong>${escapeHtml(item.title)}</strong><span>${status}</span><span>${evidence.attempts} tentativi</span></div>`;
    }).join('');
    const recommendation = progressState.steps.findIndex((item) => item.attempts > 0 && !item.correct);
    const recoveredIndex = progressState.steps.findIndex((item) => item.usedRemediation);
    if (recommendation >= 0) $('#evidenceRecommendation').textContent = `Prossimo passo consigliato: riprendi “${data.steps[recommendation].title}”.`;
    else if (recoveredIndex >= 0) $('#evidenceRecommendation').textContent = `Consolida il concetto collegato a “${data.steps[recoveredIndex].title}” con un nuovo esempio.`;
    else if (completed === data.steps.length) $('#evidenceRecommendation').textContent = 'Percorso completato: puoi passare alla prossima unità.';
    else $('#evidenceRecommendation').textContent = 'Completa almeno una verifica per ricevere una raccomandazione.';
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
    document.querySelectorAll('#stepsNav button').forEach((button) => button.classList.toggle('current', Number(button.dataset.step) === step));
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
        const evidence = progressState.steps[step];
        evidence.attempts += 1;
        $('#quizAnswers').querySelectorAll('button').forEach((candidate) => { candidate.disabled = true; });
        $('#quizFeedback').className = `feedback ${correct ? 'ok' : 'no'}`;
        if (correct) {
          evidence.correct = true;
          $('#quizFeedback').textContent = item.quiz.correctFeedback;
          saveProgress();
          return;
        }
        evidence.usedRemediation = Boolean(item.quiz.remediation);
        $('#quizFeedback').innerHTML = `<p>${escapeHtml(item.quiz.incorrectFeedback)}</p>${remediationMarkup(item.quiz.remediation)}<small>Tentativo ${evidence.attempts}</small>`;
        wireRemediation(item.quiz.remediation);
        saveProgress();
      });
      $('#quizAnswers').appendChild(button);
    });
    saveProgress();
  }

  function stop() { if (timer) clearInterval(timer); timer = null; $('#playBtn').textContent = '▶ Riproduci'; }
  function next() { if (step < data.steps.length - 1) { step += 1; renderStep(); } else stop(); }
  $('#nextBtn').addEventListener('click', () => { stop(); next(); });
  $('#prevBtn').addEventListener('click', () => { stop(); if (step > 0) { step -= 1; renderStep(); } });
  $('#resetBtn').addEventListener('click', () => { stop(); step = 0; renderStep(); });
  $('#resetProgressBtn').addEventListener('click', () => { localStorage.removeItem(storageKey); progressState = emptyState(); step = 0; renderStep(); });
  $('#playBtn').addEventListener('click', () => { if (timer) { stop(); return; } $('#playBtn').textContent = '⏸ Pausa'; timer = setInterval(next, 5500); });
  document.querySelectorAll('#stepsNav button').forEach((button) => button.addEventListener('click', () => { stop(); step = Number(button.dataset.step); renderStep(); }));
  document.addEventListener('keydown', (event) => { if (event.key === 'ArrowRight') { stop(); next(); } if (event.key === 'ArrowLeft' && step > 0) { stop(); step -= 1; renderStep(); } });

  const root = document.documentElement;
  const controls = {theme: $('#themeBtn'), size: $('#fontSizeSelect'), density: $('#densitySelect'), width: $('#widthSelect'), align: $('#alignSelect'), motion: $('#motionSelect')};
  const defaults = {theme:'light',size:'17',density:'normal',width:'68',align:'left',motion:'normal'};
  function current() { return {theme:root.dataset.theme,size:controls.size.value,density:controls.density.value,width:controls.width.value,align:controls.align.value,motion:controls.motion.value}; }
  function apply(settings) { const s={...defaults,...settings}; root.dataset.theme=s.theme;root.dataset.density=s.density;root.dataset.align=s.align;root.dataset.motion=s.motion;root.style.setProperty('--reading-size',`${s.size}px`);root.style.setProperty('--reading-width',`${s.width}ch`);controls.size.value=s.size;controls.density.value=s.density;controls.width.value=s.width;controls.align.value=s.align;controls.motion.value=s.motion;controls.theme.textContent=s.theme==='dark'?'☀ Giorno':'☾ Notte';$('#focusStatus').textContent=`${s.size}px · ${controls.density.options[controls.density.selectedIndex].text.toLowerCase()} · ${controls.width.options[controls.width.selectedIndex].text.toLowerCase()}`; }
  function saveReading() { localStorage.setItem('raiatea-reading-settings', JSON.stringify(current())); }
  let saved={};try{saved=JSON.parse(localStorage.getItem('raiatea-reading-settings')||'{}');}catch(_){}apply(saved);
  controls.theme.addEventListener('click',()=>{apply({...current(),theme:root.dataset.theme==='dark'?'light':'dark'});saveReading();});
  [controls.size,controls.density,controls.width,controls.align,controls.motion].forEach((control)=>control.addEventListener('change',()=>{apply(current());saveReading();}));
  $('#resetReadingBtn').addEventListener('click',()=>{localStorage.removeItem('raiatea-reading-settings');apply(defaults);});
  document.addEventListener('click',(event)=>{const link=event.target.closest('a[href^="#"]');if(!link)return;const target=document.getElementById(link.getAttribute('href').slice(1));if(!target)return;event.preventDefault();target.scrollIntoView({behavior:root.dataset.motion==='reduced'?'auto':'smooth',block:'center'});setTimeout(()=>{target.classList.remove('target-flash');void target.offsetWidth;target.classList.add('target-flash');target.focus({preventScroll:true});},root.dataset.motion==='reduced'?50:450);});
  const toast=$('#pauseToast');let pauseTimer=setTimeout(()=>toast.classList.add('show'),20*60*1000);$('#dismissPause').addEventListener('click',()=>{toast.classList.remove('show');clearTimeout(pauseTimer);pauseTimer=setTimeout(()=>toast.classList.add('show'),20*60*1000);});
  renderStep();
})();