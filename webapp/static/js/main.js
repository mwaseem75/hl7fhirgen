(function () {
  /* ---- Theme toggle: system -> light -> dark -> system ---- */
  const THEME_KEY = 'hl7fhirgen-theme';
  const toggleBtn = document.getElementById('theme-toggle');
  const root = document.documentElement;

  function applyTheme(mode) {
    if (mode === 'system') {
      root.removeAttribute('data-theme');
    } else {
      root.setAttribute('data-theme', mode);
    }
    toggleBtn.setAttribute('data-mode', mode);
  }

  let currentMode = localStorage.getItem(THEME_KEY) || 'system';
  applyTheme(currentMode);

  toggleBtn.addEventListener('click', () => {
    const order = ['system', 'light', 'dark'];
    currentMode = order[(order.indexOf(currentMode) + 1) % order.length];
    localStorage.setItem(THEME_KEY, currentMode);
    applyTheme(currentMode);
  });

  /* ---- Tiny markdown renderer (just enough for explainer.py's output) ---- */
  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function inlineMarkdown(text) {
    let out = escapeHtml(text);
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return out;
  }

  function renderMarkdown(md) {
    const lines = md.split('\n');
    const html = [];
    let inList = false;
    let inQuote = false;

    function closeList() { if (inList) { html.push('</ul>'); inList = false; } }
    function closeQuote() { if (inQuote) { html.push('</blockquote>'); inQuote = false; } }

    for (const line of lines) {
      if (line.startsWith('# ')) {
        closeList(); closeQuote();
        html.push(`<h1>${inlineMarkdown(line.slice(2))}</h1>`);
      } else if (line.startsWith('## ')) {
        closeList(); closeQuote();
        html.push(`<h2>${inlineMarkdown(line.slice(3))}</h2>`);
      } else if (line.startsWith('> ')) {
        closeList();
        if (!inQuote) { html.push('<blockquote>'); inQuote = true; }
        html.push(`<p>${inlineMarkdown(line.slice(2))}</p>`);
      } else if (line.startsWith('- ')) {
        closeQuote();
        if (!inList) { html.push('<ul>'); inList = true; }
        html.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
      } else if (line.trim() === '') {
        closeList(); closeQuote();
      } else {
        closeList(); closeQuote();
        html.push(`<p>${inlineMarkdown(line)}</p>`);
      }
    }
    closeList(); closeQuote();
    return html.join('\n');
  }

  /* ---- Shared elements ---- */
  const exampleSelect = document.getElementById('example-select');
  const fullCheckbox = document.getElementById('full');
  const profileBox = document.getElementById('profile-box');
  const profileStatus = document.getElementById('profile-status');
  const resourceBox = document.getElementById('resource-box');
  const resourceStatus = document.getElementById('resource-status');
  const issueList = document.getElementById('issue-list');
  const explainSection = document.getElementById('explain-section');
  const explainOutput = document.getElementById('explain-output');
  const rejectionResults = document.getElementById('rejection-results');
  const rejectionLookupResult = document.getElementById('rejection-lookup-result');
  const rejectionCodeInput = document.getElementById('rejection-code-input');
  const rejectionCodesList = document.getElementById('rejection-codes');
  const nphiesDisclaimer = document.getElementById('nphies-disclaimer');

  function setStatus(el, text, kind) {
    el.textContent = text;
    el.className = 'status' + (kind ? ' ' + kind : '');
  }

  function renderIssues(issues) {
    issueList.innerHTML = '';
    issues.forEach((issue) => {
      const li = document.createElement('li');
      li.className = 'issue issue-' + issue.severity;
      li.innerHTML = `<span class="issue-severity">${issue.severity}</span>` +
        `<span class="issue-path">${escapeHtml(issue.path)}</span>` +
        `<span class="issue-message">${escapeHtml(issue.message)}</span>`;
      issueList.appendChild(li);
    });
  }

  function renderRejectionCard(exp, container) {
    const div = document.createElement('div');
    div.className = 'rejection-card';
    const causes = exp.likely_causes.map((c) => `<li>${escapeHtml(c)}</li>`).join('');
    div.innerHTML = `<h3>${escapeHtml(exp.code)}</h3><p>${escapeHtml(exp.title)}</p>` +
      `<ul>${causes}</ul><p class="fix"><strong>Suggested fix:</strong> ${escapeHtml(exp.suggested_fix)}</p>`;
    container.appendChild(div);
  }

  /* ---- Load bundled examples + known rejection codes on startup ---- */
  let examples = { profiles: {}, resources: {} };

  Promise.all([
    fetch('/api/examples').then((r) => r.json()),
    fetch('/api/nphies/rejection-codes').then((r) => r.json()),
  ])
    .then(([ex, codes]) => {
      examples = ex;
      codes.codes.forEach((code) => {
        const opt = document.createElement('option');
        opt.value = code;
        rejectionCodesList.appendChild(opt);
      });
    })
    .catch(() => setStatus(profileStatus, 'Could not load examples.', 'err'));

  exampleSelect.addEventListener('change', () => {
    const key = exampleSelect.value;
    if (!key) return;
    profileBox.value = examples.profiles[key] || '';
    if (examples.resources[key]) {
      resourceBox.value = examples.resources[key];
    }
    setStatus(profileStatus, 'Loaded example.', 'ok');
  });

  /* ---- Generate ---- */
  document.getElementById('generate-btn').addEventListener('click', () => {
    setStatus(profileStatus, 'Generating…');
    fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_json: profileBox.value, include_optional: fullCheckbox.checked }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Generation failed.');
        return data;
      })
      .then((resource) => {
        resourceBox.value = JSON.stringify(resource, null, 2);
        setStatus(profileStatus, 'Generated.', 'ok');
        issueList.innerHTML = '';
      })
      .catch((err) => setStatus(profileStatus, err.message, 'err'));
  });

  /* ---- Explain ---- */
  document.getElementById('explain-btn').addEventListener('click', () => {
    setStatus(profileStatus, 'Explaining…');
    fetch('/api/explain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_json: profileBox.value }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Could not explain profile.');
        return data;
      })
      .then((data) => {
        explainOutput.innerHTML = renderMarkdown(data.markdown);
        explainSection.classList.remove('hidden');
        setStatus(profileStatus, 'Explained.', 'ok');
      })
      .catch((err) => setStatus(profileStatus, err.message, 'err'));
  });

  /* ---- Validate ---- */
  document.getElementById('validate-btn').addEventListener('click', () => {
    setStatus(resourceStatus, 'Validating…');
    fetch('/api/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_json: resourceBox.value, profile_json: profileBox.value }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Validation failed.');
        return data;
      })
      .then((data) => {
        renderIssues(data.issues);
        setStatus(resourceStatus, data.valid ? 'Valid.' : `${data.issues.length} issue(s) found.`, data.valid ? 'ok' : 'err');
      })
      .catch((err) => setStatus(resourceStatus, err.message, 'err'));
  });

  /* ---- NPHIES: check claim ---- */
  document.getElementById('check-claim-btn').addEventListener('click', () => {
    rejectionResults.innerHTML = '';
    setStatus(resourceStatus, 'Checking claim…');
    fetch('/api/nphies/check-claim', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_json: resourceBox.value, profile_json: profileBox.value }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Check failed.');
        return data;
      })
      .then((data) => {
        renderIssues(data.issues);
        setStatus(resourceStatus, data.valid ? 'Valid.' : `${data.issues.length} issue(s) found.`, data.valid ? 'ok' : 'err');
        if (data.rejection_explanations.length) {
          const heading = document.createElement('p');
          heading.textContent = `Recognized rejection pattern(s): ${data.rejection_explanations.length}`;
          rejectionResults.appendChild(heading);
          data.rejection_explanations.forEach((exp) => renderRejectionCard(exp, rejectionResults));
        }
        nphiesDisclaimer.textContent = data.disclaimer;
      })
      .catch((err) => setStatus(resourceStatus, err.message, 'err'));
  });

  /* ---- NPHIES: explain a rejection code directly ---- */
  document.getElementById('explain-rejection-btn').addEventListener('click', () => {
    rejectionLookupResult.innerHTML = '';
    const code = rejectionCodeInput.value.trim();
    if (!code) return;
    fetch('/api/nphies/explain-rejection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    })
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Not found.');
        return data;
      })
      .then((exp) => {
        renderRejectionCard({ code, ...exp }, rejectionLookupResult);
        nphiesDisclaimer.textContent = exp.disclaimer;
      })
      .catch((err) => {
        rejectionLookupResult.innerHTML = `<p class="status err">${err.message}</p>`;
      });
  });
})();
