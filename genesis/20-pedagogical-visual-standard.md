# Raiatea Pedagogical Visual Standard

**Status:** Draft standard  
**Version:** 0.1.0  
**Project phase:** Project Genesis — Leaving the Shore  
**Purpose:** Turn dense, static source figures into calm, navigable, pedagogically superior learning experiences without hiding the original source.

---

## 1. Principle

A Raiatea figure is not merely translated or decorated.

It must help a learner understand more accurately, with less avoidable cognitive effort, than by viewing the static source alone.

> A source figure shows a compressed result. A Raiatea figure reconstructs the path required to understand it.

The original figure remains available for verification. The Raiatea version is an independently authored pedagogical reconstruction.

---

## 2. When a figure should be transformed

Transform a source figure when it:

- represents a process, state transition, algorithm, data flow, or causal sequence;
- compresses several conceptual or mathematical steps;
- contains dense English labels that obstruct the target learner;
- introduces a difficult concept essential to later chapters;
- benefits from progressive disclosure, highlighting, simulation, or interaction;
- can support a diagnostic question or practical experiment.

Do not transform a figure merely because it exists. Decorative images, simple tables, and already-clear diagrams should remain lightweight references.

---

## 3. Required pedagogical sequence

Every substantial visual module should contain three phases.

### 3.1 Before the figure — orientation

The learner must see:

- where the module sits in the expedition;
- a brief summary of what was covered previously;
- required, useful, and optional prerequisites;
- links to short prerequisite recovery modules;
- estimated time;
- conceptual, mathematical, and coding difficulty;
- the learning objective;
- a warning not to proceed when a critical prerequisite is missing.

The module must answer:

> Where am I, why am I here, and what must I already know?

### 3.2 During the figure — guided reconstruction

The figure should be decomposed into controllable steps.

Each step should provide:

- one conceptual change at a time;
- visual highlighting of the relevant elements;
- an Italian explanation;
- the reason the step exists;
- the input, operation, output, and meaning;
- a typical misconception or interpretation limit;
- an optional equation or code fragment;
- one small diagnostic question;
- forward, backward, direct-step, pause, replay, and keyboard navigation.

Autoplay may exist, but the learner controls the pace.

### 3.3 After the figure — consolidation and route continuation

The learner must see:

- what should now be explainable;
- what should now be calculable or implementable;
- remaining simplifications and limitations;
- signs that the concept is still fragile;
- the minimum next step;
- optional mathematical, practical, or historical branches;
- links to the next modules and relevant concepts.

The module must answer:

> What changed in my understanding, and where do I go next?

---

## 4. Concepts, tooltips, and internal navigation

Technical terms should be represented as addressable knowledge nodes.

### 4.1 Tooltip

A tooltip provides a definition short enough not to interrupt reading.

It should:

- fit in approximately two lines;
- avoid introducing new unexplained terminology;
- remain available by hover, keyboard focus, and touch-compatible interaction;
- never contain the only complete explanation of a concept.

### 4.2 Concept card

A click may navigate to a concept card containing:

- concise definition;
- why it matters;
- example;
- prerequisites;
- concepts often confused with it;
- where it first appeared;
- where it will be used next.

When navigation lands on a concept card, the card should be brought near the center of the viewport and receive a slow, brief, non-flashing border/background highlight. The effect must respect reduced-motion preferences.

### 4.3 Knowledge graph evolution

The same identifiers should later address nodes in the wider Raiatea knowledge graph. An HTML anchor is therefore not only presentation markup; it is the first lightweight representation of a durable concept identity.

---

## 5. Visual and typographic standard — Raiatea Focus UI

The default visual language should be calm, familiar, and suitable for prolonged technical reading.

### 5.1 Design direction

Use a restrained interface inspired by GitHub Primer:

- neutral page background;
- white or dark neutral reading surfaces;
- one principal accent color;
- limited shadows;
- modest corner radii;
- no decorative gradients behind the reading area;
- no unnecessary motion;
- content and figures remain visually dominant.

### 5.2 Typography

Default body stack:

```css
-apple-system,
BlinkMacSystemFont,
"Segoe UI",
"Noto Sans",
Helvetica,
Arial,
sans-serif
```

Default code stack:

```css
ui-monospace,
SFMono-Regular,
"SF Mono",
Menlo,
Consolas,
"Liberation Mono",
monospace
```

Default reading settings:

- body size: 17 px;
- line height: approximately 1.65;
- measure: approximately 68 characters;
- left alignment;
- moderate paragraph spacing;
- headings lighter than conventional bold web headings;
- restrained emphasis weights.

Titles must establish hierarchy without becoming visually aggressive.

### 5.3 Reading controls

The user should be able to change and persist:

- system/day/night theme;
- text size;
- line spacing;
- reading-column width;
- left or justified alignment;
- normal or reduced animation;
- eventually font family and higher-contrast mode.

Controls must visibly affect all reading components, not only selected paragraphs.

### 5.4 Accessibility and comfort

The interface should:

- preserve strong text contrast;
- support zoom and responsive reflow;
- avoid conveying meaning by color alone;
- support keyboard navigation;
- respect `prefers-reduced-motion`;
- avoid flashes and abrupt movement;
- optionally suggest a discreet visual pause after prolonged continuous reading.

Raiatea cannot eliminate screen fatigue, but it should avoid adding preventable strain.

---

## 6. Interaction levels

A visual module may have progressively richer levels.

### Level A — translated guided figure

- reconstructed or annotated figure;
- Italian labels;
- sequential steps;
- before/during/after explanations;
- concept links;
- diagnostic questions.

### Level B — computed simulation

- values recomputed locally;
- editable inputs or presets;
- responsive tables, bars, matrices, and outputs;
- mathematical consistency checks;
- guided experiments.

Use lightweight JavaScript when the interaction is small, deterministic, and pedagogically local.

### Level C — executable laboratory

- real project files;
- notebook, editor, terminal, tests, and outputs;
- reproducible environment definition;
- support for multiple languages and dependencies;
- persistent learner work separate from the disposable runtime.

Level C should use isolated execution infrastructure rather than forcing every language into the browser.

---

## 7. Execution-lab direction

The provisional architectural decision is:

> JavaScript for lightweight pedagogical interaction; isolated on-demand runtimes for real code execution.

The browser should act as the learning workspace and connect to an execution service through stable contracts.

Possible executors include:

- local Docker or Podman;
- remote containers;
- Kubernetes jobs;
- micro-VMs for stronger isolation;
- CPU or GPU runners;
- approved federated compute nodes.

A laboratory definition should specify:

- language and version;
- base image/environment;
- dependencies;
- CPU, memory, GPU, process, and timeout limits;
- network policy;
- mounted exercise workspace;
- test command;
- persistence/export policy.

The runtime is disposable. The learner's code, attempts, test evidence, feedback, environment version, and mastery evidence are durable knowledge objects.

---

## 8. Pedagogical quality gate

Before accepting a transformed figure, answer:

1. What can the learner understand after this module that was difficult to infer from the original figure alone?
2. Did the module add explanation, or merely spread the original content across more screens?
3. Is every animation tied to a pedagogical purpose?
4. Can the learner control the pace and revisit a step?
5. Are prerequisites and next steps explicit?
6. Are formulas, labels, and code technically correct?
7. Are simplifications and analogy limits visible?
8. Can a learner with reduced motion, keyboard navigation, or a smaller screen still use it?
9. Does the module remain readable for an extended session?
10. Is the original source still traceable and available privately?

A module that fails these questions should be revised or remain a static source figure.

---

## 9. Evidence and evaluation

The standard should eventually be validated against the original source using controlled comparisons.

Measure:

- time to explain the figure correctly;
- conceptual errors;
- ability to reproduce the process;
- transfer to a new example;
- delayed recall;
- number and type of prerequisite recoveries;
- navigation effort;
- learner-reported visual fatigue;
- usefulness of animation versus static presentation.

Visual richness is not success. Improved understanding with acceptable time and effort is success.

---

## 10. Reference pilot

The first reference implementation covers simplified self-attention:

```text
input embeddings
→ select query
→ compute attention scores
→ normalize with softmax
→ form attention weights
→ weighted sum
→ context vector
→ transition to learned Q, K, V
```

The pilot established the following decisions:

- use one navigable HTML learning environment;
- keep internal Markdown and assets as implementation artefacts;
- use self-contained figures to avoid broken asset paths;
- translate labels but independently reconstruct the pedagogy;
- connect concepts to durable internal identities;
- show prerequisites and route continuation;
- provide diagnostic questions per step;
- use Focus UI for prolonged reading;
- reserve full executable laboratories for isolated runtimes.

---

## 11. Provisional rule

> Raiatea should transform only those figures for which guided reconstruction produces clear pedagogical value. Every transformed figure must orient, reveal, verify, and reconnect the learner to the wider route.
