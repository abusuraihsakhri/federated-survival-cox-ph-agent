/* Local-only rule-based audit demonstration; no Cox regression is performed. */
(function (root) {
  'use strict';
  const suspicious = [
    /\bMRN[:#\s-]*\d{4,10}\b/i,
    /\b\d{3}-\d{2}-\d{4}\b/,
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/,
    /\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/
  ];
  function evaluate(data) {
    for (const field of ['task_id', 'target_identifier', 'status_descriptor']) {
      if (typeof data[field] !== 'string' || !data[field].trim()) {
        throw new Error(field + ' is required');
      }
      if (data[field].length > 200) throw new Error(field + ' exceeds 200 characters');
      if (suspicious.some(pattern => pattern.test(data[field]))) {
        throw new Error('Possible personal identifier detected. Use synthetic labels only.');
      }
    }
    if (typeof data.primary_metric !== 'number' || !Number.isFinite(data.primary_metric) ||
        typeof data.secondary_metric !== 'number' || !Number.isFinite(data.secondary_metric)) {
      throw new Error('Both metrics must be finite numbers');
    }
    if (typeof data.is_critical_flag !== 'boolean') {
      throw new Error('Critical flag must be true or false');
    }
    const alerts = [];
    if (data.primary_metric > 25) {
      alerts.push({ worker: 'InvariantQCWorker', urgency: 'ELEVATED_RISK',
        summary: 'Primary metric exceeds configured threshold (25)' });
    }
    if (data.is_critical_flag || data.secondary_metric > 12) {
      alerts.push({ worker: 'SafetyEscalationWorker',
        urgency: data.is_critical_flag ? 'CRITICAL_STAT_PANIC' : 'ELEVATED_RISK',
        summary: 'Critical flag or secondary threshold (12) triggered' });
    }
    if (['DISCORDANT', 'ANOMALY', 'MUTANT', 'VIOLATION', 'FAIL', 'REJECT']
        .some(word => data.status_descriptor.toUpperCase().includes(word))) {
      alerts.push({ worker: 'ProtocolConformanceWorker', urgency: 'ELEVATED_RISK',
        summary: 'Status descriptor contains a configured anomaly keyword' });
    }
    const critical = alerts.filter(a => a.urgency === 'CRITICAL_STAT_PANIC').length;
    const overall = critical ? 'CRITICAL_STAT_PANIC' : alerts.length ? 'ELEVATED_RISK' : 'ROUTINE';
    return {
      task_id: data.task_id,
      target_identifier: data.target_identifier,
      overall_urgency: overall,
      integrity_status: critical ? 'RECALIBRATION_REQUIRED' : alerts.length ? 'DISCORDANT_ANOMALY' : 'VALIDATED_OPTIMAL',
      total_alerts: alerts.length,
      critical_alerts_count: critical,
      alerts,
      implementation: 'Browser-only deterministic threshold rules, not a Cox PH model',
      cryptographic_audit: false
    };
  }
  const api = { evaluate };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document === 'undefined') return;

  const form = document.getElementById('audit-form');
  const output = document.getElementById('output');
  const status = document.getElementById('status');
  const count = document.getElementById('count');
  const download = document.getElementById('download');
  let lastResult = null;
  let processed = 0;

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    try {
      const primary = form.elements.primary_metric.value.trim();
      const secondary = form.elements.secondary_metric.value.trim();
      if (primary === '' || secondary === '') throw new Error('Both metrics are required');
      const result = evaluate({
        task_id: form.elements.task_id.value,
        target_identifier: form.elements.target_identifier.value,
        primary_metric: Number(primary),
        secondary_metric: Number(secondary),
        status_descriptor: form.elements.status_descriptor.value,
        is_critical_flag: form.elements.is_critical_flag.checked
      });
      lastResult = result;
      processed++;
      status.textContent = result.overall_urgency;
      count.textContent = String(processed);
      output.textContent = JSON.stringify(result, null, 2);
      download.disabled = false;
    } catch (err) {
      lastResult = null;
      status.textContent = 'INPUT ERROR';
      output.textContent = err.message;
      download.disabled = true;
    }
  });

  download.addEventListener('click', function () {
    if (!lastResult) return;
    const blob = new Blob([JSON.stringify(lastResult, null, 2) + '\n'], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'audit-result.json';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}(typeof globalThis !== 'undefined' ? globalThis : this));
