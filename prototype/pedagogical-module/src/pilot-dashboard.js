(() => {
  'use strict';

  const manifest = window.RAIATEA_PILOT;
  if (!manifest || !Array.isArray(manifest.modules)) return;

  const STATES = Object.freeze({
    NOT_STARTED: 'not-started',
    IN_PROGRESS: 'in-progress',
    COMPLETED: 'locally-completed'
  });
  const STEP_FIELDS = Object.freeze([
    'attempts',
    'correct',
    'usedRemediation',
    'activityCompleted'
  ]);

  function isPlainObject(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
  }

  function hasExactFields(value, fields) {
    return isPlainObject(value)
      && Object.keys(value).length === fields.length
      && fields.every(field => Object.hasOwn(value, field));
  }

  function validStep(value) {
    return hasExactFields(value, STEP_FIELDS)
      && Number.isInteger(value.attempts)
      && value.attempts >= 0
      && typeof value.correct === 'boolean'
      && typeof value.usedRemediation === 'boolean'
      && typeof value.activityCompleted === 'boolean';
  }

  function parseProgress(module) {
    const raw = localStorage.getItem(`raiatea-progress:${module.id}`);
    if (raw === null) return null;
    try {
      const value = JSON.parse(raw);
      if (!hasExactFields(value, ['currentStep', 'steps'])) return null;
      if (!Number.isInteger(value.currentStep)
          || value.currentStep < 0
          || value.currentStep >= module.stepCount
          || !Array.isArray(value.steps)
          || value.steps.length !== module.stepCount
          || !value.steps.every(validStep)) return null;
      return value;
    } catch (_) {
      return null;
    }
  }

  function derive(module) {
    const progress = parseProgress(module);
    if (!progress) return {status: STATES.NOT_STARTED, completed: 0};
    const completed = progress.steps.filter(
      step => step.correct === true || step.activityCompleted === true
    ).length;
    const active = progress.currentStep > 0 || progress.steps.some(step =>
      step.attempts > 0
      || step.correct === true
      || step.usedRemediation === true
      || step.activityCompleted === true
    );
    if (completed === module.stepCount) {
      return {status: STATES.COMPLETED, completed};
    }
    return {
      status: active ? STATES.IN_PROGRESS : STATES.NOT_STARTED,
      completed
    };
  }

  function label(status) {
    if (status === STATES.COMPLETED) return 'Completato localmente';
    if (status === STATES.IN_PROGRESS) return 'In corso';
    return 'Non iniziato';
  }

  function render() {
    const results = manifest.modules.map(module => ({module, ...derive(module)}));
    results.forEach(({module, status, completed}) => {
      const card = document.querySelector(`[data-pilot-module="${CSS.escape(module.id)}"]`);
      if (!card) return;
      const statusNode = card.querySelector('[data-pilot-status]');
      const countNode = card.querySelector('[data-pilot-count]');
      if (statusNode) {
        statusNode.textContent = label(status);
        statusNode.dataset.state = status;
      }
      if (countNode) countNode.textContent = `${completed}/${module.stepCount} attività verificate`;
    });

    const recommendation = document.querySelector('[data-pilot-recommendation]');
    if (!recommendation) return;
    const next = results.find(result => result.status !== STATES.COMPLETED);
    if (next) {
      recommendation.textContent = `Prossimo passo consigliato: ${next.module.title}.`;
    } else {
      recommendation.textContent = 'Percorso completato localmente: puoi rivedere liberamente i moduli.';
    }
  }

  const routeKeys = new Set(manifest.modules.map(module => `raiatea-progress:${module.id}`));
  window.addEventListener('pageshow', render);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') render();
  });
  window.addEventListener('storage', event => {
    if (event.storageArea === localStorage && routeKeys.has(event.key)) render();
  });
  render();
})();
