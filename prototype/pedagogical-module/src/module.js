(() => {
  const data = window.RAIATEA_MODULE;
  const $ = (s) => document.querySelector(s);
  const storageKey = `raiatea-progress:${data.id}`;
  const EVIDENCE_EXPORT_FORMAT = 'raiatea-learner-evidence';
  const EVIDENCE_EXPORT_VERSION = 1;
  const MAX_EVIDENCE_IMPORT_BYTES = 1_000_000;
  let step = 0;
  let timer = null;
  let pendingEvidenceImport = null;
  let evidenceImportSelection = 0;

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
    if (pendingEvidenceImport) {
      clearPendingEvidenceImport('Avanzamento locale cambiato. Importazione annullata: seleziona di nuovo il file prima di ripristinare.');
    }
    renderEvidence();
  }

  function exportSourceContext() {
    const source = data.source;
    if (!source || typeof source !== 'object') return undefined;
    const context = {};
    ['title', 'chapter', 'section', 'figure'].forEach((field) => {
      if (typeof source[field] === 'string' && source[field].trim()) context[field] = source[field];
    });
    if (Array.isArray(source.pages)) {
      const pages = source.pages.filter((page) => Number.isInteger(page) && page > 0);
      if (pages.length) context.pages = pages;
    }
    return Object.keys(context).length ? context : undefined;
  }

  function buildEvidenceExport() {
    const moduleContext = {
      id: data.id,
      title: data.title,
      language: data.language,
      stepCount: data.steps.length
    };
    const source = exportSourceContext();
    if (source) moduleContext.source = source;
    return {
      format: EVIDENCE_EXPORT_FORMAT,
      version: EVIDENCE_EXPORT_VERSION,
      module: moduleContext,
      progress: {
        currentStep: step,
        steps: data.steps.map((item, index) => {
          const evidence = progressState.steps[index] || {};
          return {
            index,
            title: item.title,
            attempts: Number.isInteger(evidence.attempts) && evidence.attempts >= 0 ? evidence.attempts : 0,
            correct: evidence.correct === true,
            usedRemediation: evidence.usedRemediation === true,
            activityCompleted: evidence.activityCompleted === true
          };
        })
      }
    };
  }

  function evidenceFilename() {
    const safeModuleId = String(data.id || 'raiatea-module')
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'raiatea-module';
    return `${safeModuleId}-evidence-v${EVIDENCE_EXPORT_VERSION}.json`;
  }

  function exportEvidence() {
    const payload = `${JSON.stringify(buildEvidenceExport(), null, 2)}\n`;
    const blob = new Blob([payload], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = evidenceFilename();
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
    const status = $('#evidenceExportStatus');
    if (status) status.textContent = 'Evidenze esportate in un file JSON locale.';
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
  }

  function validateObjectFields(value, required, allowed, path, issues) {
    if (!isPlainObject(value)) {
      issues.push(`${path}: deve essere un oggetto`);
      return false;
    }
    required.forEach((field) => {
      if (!Object.hasOwn(value, field)) issues.push(`${path}.${field}: campo obbligatorio mancante`);
    });
    Object.keys(value).forEach((field) => {
      if (!allowed.includes(field)) issues.push(`${path}.${field}: campo non supportato`);
    });
    return true;
  }

  function validateNonEmptyString(value, path, issues) {
    if (typeof value !== 'string' || !value.trim()) {
      issues.push(`${path}: deve essere una stringa non vuota`);
      return false;
    }
    return true;
  }

  function validateNonNegativeInteger(value, path, issues) {
    if (!Number.isInteger(value) || value < 0) {
      issues.push(`${path}: deve essere un intero non negativo`);
      return false;
    }
    return true;
  }

  function validateEvidenceImport(candidate) {
    const issues = [];
    const topFields = ['format', 'version', 'module', 'progress'];
    if (!validateObjectFields(candidate, topFields, topFields, '$', issues)) return issues;

    if (candidate.format !== EVIDENCE_EXPORT_FORMAT) issues.push('$.format: formato non supportato');
    if (!Number.isInteger(candidate.version) || candidate.version !== EVIDENCE_EXPORT_VERSION) {
      issues.push('$.version: versione non supportata');
    }

    const moduleFields = ['id', 'title', 'language', 'stepCount', 'source'];
    const moduleRequired = ['id', 'title', 'language', 'stepCount'];
    const moduleValid = validateObjectFields(candidate.module, moduleRequired, moduleFields, '$.module', issues);
    let exportedStepCount = null;
    if (moduleValid) {
      if (validateNonEmptyString(candidate.module.id, '$.module.id', issues) && !/^[a-z0-9-]+$/.test(candidate.module.id)) {
        issues.push('$.module.id: deve contenere solo lettere minuscole, cifre e trattini');
      }
      validateNonEmptyString(candidate.module.title, '$.module.title', issues);
      validateNonEmptyString(candidate.module.language, '$.module.language', issues);
      if (validateNonNegativeInteger(candidate.module.stepCount, '$.module.stepCount', issues)) {
        if (candidate.module.stepCount < 1) issues.push('$.module.stepCount: deve essere almeno 1');
        else exportedStepCount = candidate.module.stepCount;
      }
      if (Object.hasOwn(candidate.module, 'source')) {
        const sourceFields = ['title', 'chapter', 'section', 'figure', 'pages'];
        if (validateObjectFields(candidate.module.source, [], sourceFields, '$.module.source', issues)) {
          ['title', 'chapter', 'section', 'figure'].forEach((field) => {
            if (Object.hasOwn(candidate.module.source, field)) validateNonEmptyString(candidate.module.source[field], `$.module.source.${field}`, issues);
          });
          if (Object.hasOwn(candidate.module.source, 'pages')) {
            const pages = candidate.module.source.pages;
            if (!Array.isArray(pages) || !pages.length) issues.push('$.module.source.pages: deve contenere almeno una pagina');
            else pages.forEach((page, index) => {
              if (!Number.isInteger(page) || page < 1) issues.push(`$.module.source.pages[${index}]: deve essere un intero positivo`);
            });
          }
        }
      }
    }

    const progressFields = ['currentStep', 'steps'];
    const progressValid = validateObjectFields(candidate.progress, progressFields, progressFields, '$.progress', issues);
    let exportedSteps = null;
    if (progressValid) {
      if (validateNonNegativeInteger(candidate.progress.currentStep, '$.progress.currentStep', issues) && exportedStepCount !== null && candidate.progress.currentStep >= exportedStepCount) {
        issues.push('$.progress.currentStep: deve riferirsi a un passo esistente');
      }
      if (!Array.isArray(candidate.progress.steps) || !candidate.progress.steps.length) {
        issues.push('$.progress.steps: deve contenere almeno un passo');
      } else {
        exportedSteps = candidate.progress.steps;
        if (exportedStepCount !== null && exportedSteps.length !== exportedStepCount) {
          issues.push('$.progress.steps: la lunghezza deve corrispondere a $.module.stepCount');
        }
        const stepFields = ['index', 'title', 'attempts', 'correct', 'usedRemediation', 'activityCompleted'];
        exportedSteps.forEach((item, index) => {
          const path = `$.progress.steps[${index}]`;
          if (!validateObjectFields(item, stepFields, stepFields, path, issues)) return;
          if (validateNonNegativeInteger(item.index, `${path}.index`, issues) && item.index !== index) issues.push(`${path}.index: deve coincidere con la posizione nell'array`);
          validateNonEmptyString(item.title, `${path}.title`, issues);
          validateNonNegativeInteger(item.attempts, `${path}.attempts`, issues);
          ['correct', 'usedRemediation', 'activityCompleted'].forEach((field) => {
            if (typeof item[field] !== 'boolean') issues.push(`${path}.${field}: deve essere booleano`);
          });
        });
      }
    }

    if (moduleValid && candidate.module.id !== data.id) {
      issues.push(`$.module.id: il file appartiene al modulo “${candidate.module.id}”, non a “${data.id}”`);
    }
    if (exportedStepCount !== null && exportedStepCount !== data.steps.length) {
      issues.push(`$.module.stepCount: ${exportedStepCount} passi esportati, ${data.steps.length} nel modulo corrente`);
    }
    if (exportedSteps) {
      if (exportedSteps.length !== data.steps.length) issues.push('$.progress.steps: sequenza incompatibile con il modulo corrente');
      exportedSteps.slice(0, data.steps.length).forEach((item, index) => {
        if (isPlainObject(item) && typeof item.title === 'string' && item.title !== data.steps[index].title) {
          issues.push(`$.progress.steps[${index}].title: titolo incompatibile con il modulo corrente`);
        }
      });
    }

    return issues;
  }

  function sanitizeImportedProgress(candidate) {
    return {
      currentStep: candidate.progress.currentStep,
      steps: candidate.progress.steps.map((item) => ({
        attempts: item.attempts,
        correct: item.correct,
        usedRemediation: item.usedRemediation,
        activityCompleted: item.activityCompleted
      }))
    };
  }

  function evidenceStats(state) {
    return {
      completed: state.steps.filter((item) => item.correct).length,
      attempts: state.steps.reduce((sum, item) => sum + item.attempts, 0)
    };
  }

  function clearPendingEvidenceImport(message = '') {
    evidenceImportSelection += 1;
    pendingEvidenceImport = null;
    const input = $('#importEvidenceInput');
    const panel = $('#evidenceImportPanel');
    const confirm = $('#confirmEvidenceImportBtn');
    const preview = $('#evidenceImportPreview');
    if (input) input.value = '';
    if (panel) panel.hidden = true;
    if (confirm) confirm.disabled = true;
    if (preview) preview.textContent = '';
    const status = $('#evidenceImportStatus');
    if (status) status.textContent = message;
  }

  async function handleEvidenceImportSelection() {
    stop();
    const selection = ++evidenceImportSelection;
    const input = $('#importEvidenceInput');
    const file = input?.files?.[0];
    pendingEvidenceImport = null;
    $('#evidenceImportPanel').hidden = true;
    $('#confirmEvidenceImportBtn').disabled = true;
    $('#evidenceImportPreview').textContent = '';
    if (!file) return;
    if (file.size > MAX_EVIDENCE_IMPORT_BYTES) {
      clearPendingEvidenceImport('File non importabile: supera il limite di 1 MB.');
      return;
    }

    let candidate;
    try {
      const serialized = await file.text();
      if (selection !== evidenceImportSelection) return;
      candidate = JSON.parse(serialized);
    } catch (_) {
      if (selection !== evidenceImportSelection) return;
      clearPendingEvidenceImport('File non importabile: JSON non valido. Nessuna modifica applicata.');
      return;
    }

    const issues = validateEvidenceImport(candidate);
    if (issues.length) {
      clearPendingEvidenceImport(`File non importabile: ${issues.slice(0, 3).join(' · ')}. Nessuna modifica applicata.`);
      return;
    }

    pendingEvidenceImport = sanitizeImportedProgress(candidate);
    const current = evidenceStats(progressState);
    const imported = evidenceStats(pendingEvidenceImport);
    $('#evidenceImportPreview').textContent = `Avanzamento attuale: ${current.completed}/${data.steps.length} verifiche, ${current.attempts} tentativi. File selezionato: ${imported.completed}/${data.steps.length} verifiche, ${imported.attempts} tentativi. Il ripristino sostituirà solo l'avanzamento di questo modulo.`;
    $('#evidenceImportPanel').hidden = false;
    $('#confirmEvidenceImportBtn').disabled = false;
    $('#evidenceImportStatus').textContent = 'File compatibile. Controlla l’anteprima e conferma esplicitamente il ripristino.';
  }

  function confirmEvidenceImport() {
    if (!pendingEvidenceImport) return;
    stop();
    progressState = {
      currentStep: pendingEvidenceImport.currentStep,
      steps: pendingEvidenceImport.steps.map((item) => ({...item}))
    };
    step = progressState.currentStep;
    pendingEvidenceImport = null;
    $('#importEvidenceInput').value = '';
    $('#evidenceImportPanel').hidden = true;
    $('#confirmEvidenceImportBtn').disabled = true;
    $('#evidenceImportPreview').textContent = '';
    renderStep();
    $('#evidenceImportStatus').textContent = 'Avanzamento ripristinato dal file JSON locale.';
  }

  function escapeHtml(value) {
    return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  }

  function renderStepProvenance(item) {
    const box = $('#stepProvenance');
    const body = $('#stepProvenanceBody');
    const provenance = item.provenance;
    if (!provenance) {
      box.hidden = true;
      body.innerHTML = '';
      return;
    }
    const sourcePages = (provenance.sourcePages || []).join(', ');
    const transformations = (provenance.transformations || []).map((value) => `<span class="chip">${escapeHtml(value)}</span>`).join('');
    body.innerHTML = [
      provenance.sourceSection ? `<p><b>Sezione:</b> ${escapeHtml(provenance.sourceSection)}</p>` : '',
      sourcePages ? `<p><b>Pagine:</b> ${escapeHtml(sourcePages)}</p>` : '',
      provenance.sourceFigure ? `<p><b>Figura:</b> ${escapeHtml(provenance.sourceFigure)}</p>` : '',
      transformations ? `<div class="step-transformations">${transformations}</div>` : '',
      `<p><b>Natura:</b> ${escapeHtml(provenance.kind)}</p>`,
      provenance.derivedValues ? '<p><b>Valori derivati:</b> sì, ottenuti durante la rielaborazione.</p>' : '',
      provenance.note ? `<p>${escapeHtml(provenance.note)}</p>` : ''
    ].join('');
    box.hidden = false;
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
    renderStepProvenance(item);
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
  $('#resetProgressBtn').addEventListener('click', () => { localStorage.removeItem(storageKey); progressState = emptyState(); step = 0; clearPendingEvidenceImport(); renderStep(); });
  $('#exportEvidenceBtn')?.addEventListener('click', exportEvidence);
  $('#selectEvidenceBtn')?.addEventListener('click', () => $('#importEvidenceInput')?.click());
  $('#importEvidenceInput')?.addEventListener('change', handleEvidenceImportSelection);
  $('#confirmEvidenceImportBtn')?.addEventListener('click', confirmEvidenceImport);
  $('#cancelEvidenceImportBtn')?.addEventListener('click', () => clearPendingEvidenceImport('Importazione annullata. Nessuna modifica applicata.'));
  $('#playBtn').addEventListener('click', () => { if (timer) { stop(); return; } $('#playBtn').textContent = '⏸ Pausa'; timer = setInterval(next, 5500); });
  document.querySelectorAll('#stepsNav button').forEach((button) => button.addEventListener('click', () => { stop(); step = Number(button.dataset.step); renderStep(); }));
  document.addEventListener('keydown', (event) => {
    const target = event.target;
    const focusedControl = target instanceof Element && target.closest('a, button, input, select, textarea, [contenteditable="true"]');
    if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || focusedControl) return;
    if (event.key === 'ArrowRight') { stop(); next(); }
    if (event.key === 'ArrowLeft' && step > 0) { stop(); step -= 1; renderStep(); }
  });

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
