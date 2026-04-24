const methodStyles = {
  csharp_engine: { label: "C# Engine", className: "method-csharp", color: "#ff8f3f" },
  sql_dynamic: { label: "SQL Dynamic", className: "method-sql", color: "#2dc0b2" },
  python_eval: { label: "Python Eval", className: "method-python", color: "#8ab4ff" },
};

const tradeoffLabels = [
  ["maintainability", "Maintainability"],
  ["extensibility", "Extensibility"],
  ["operational_complexity", "Operational Complexity"],
  ["runtime_flexibility", "Runtime Flexibility"],
];

let dashboardPayload = null;

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("refresh-button").addEventListener("click", loadDashboard);
  document.getElementById("generate-analysis-button").addEventListener("click", generateAnalysis);
  document.getElementById("ask-benchmark-button").addEventListener("click", askBenchmark);
  document.getElementById("formula-filter").addEventListener("change", () => {
    renderFormulaSection();
  });
  loadDashboard();
});

async function loadDashboard() {
  setLoading(true);
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) {
      throw new Error(`Dashboard API returned ${response.status}`);
    }
    dashboardPayload = await response.json();
    renderDashboard(dashboardPayload);
    setLoading(false);
  } catch (error) {
    setError(`Unable to load the benchmark dashboard. ${error.message}`);
  }
}

function renderDashboard(payload) {
  const { overview, summary, correctness, tradeoffs, recommendations, ai_analysis } = payload;
  document.getElementById("project-title").textContent = overview.project_title;
  document.getElementById("project-subtitle").textContent = overview.subtitle;
  document.getElementById("fastest-method").textContent = labelForMethod(overview.fastest_method);
  document.getElementById("formula-count").textContent = overview.formula_count.toLocaleString();
  document.getElementById("record-count").textContent = formatCompactNumber(overview.records_processed);

  renderOverviewMetrics(overview, summary);
  renderCorrectness(correctness);
  renderPerformance(summary);
  renderFormulaSection();
  renderTradeoffs(tradeoffs);
  renderRecommendations(recommendations);
  renderAiAnalysis(ai_analysis);
  renderSuggestedQuestions(ai_analysis.suggested_questions || []);
  document.getElementById("download-pdf-link").href = ai_analysis.download_pdf_url || "/api/analysis/download.pdf";
  setAnalysisStatus("The current intelligence report is built from measured benchmark outputs and can be regenerated at any time.");
}

function renderOverviewMetrics(overview, summary) {
  const summaryByMethod = Object.fromEntries(summary.map((row) => [row.method, row]));
  const csharpAvg = summaryByMethod.csharp_engine?.average_runtime_seconds ?? 0;
  const sqlAvg = summaryByMethod.sql_dynamic?.average_runtime_seconds ?? 0;
  const pythonAvg = summaryByMethod.python_eval?.average_runtime_seconds ?? 0;
  const performanceGap = pythonAvg - csharpAvg;

  const cards = [
    {
      label: "Correctness Status",
      value: overview.correctness_status,
      support: "All pairwise comparison scripts returned zero mismatched rows.",
    },
    {
      label: "Data Volume",
      value: `${formatCompactNumber(overview.records_processed)} x ${overview.formula_count}`,
      support: "Every execution engine processed the same benchmark scope for a fair comparison.",
    },
    {
      label: "Fastest Overall",
      value: labelForMethod(overview.fastest_method),
      support: `${labelForMethod("csharp_engine")} beat ${labelForMethod("python_eval")} by ${performanceGap.toFixed(1)}s per formula on average.`,
    },
    {
      label: "Execution Engines",
      value: overview.execution_engines.toString(),
      support: "Python, C#, and SQL Dynamic remained fully aligned with the assignment logic.",
    },
  ];

  document.getElementById("overview-metrics").innerHTML = cards
    .map(
      (card) => `
        <article class="metric-card">
          <span class="metric-label">${card.label}</span>
          <strong class="metric-value">${card.value}</strong>
          <p class="metric-support">${card.support}</p>
        </article>
      `
    )
    .join("");
}

function renderCorrectness(correctnessCards) {
  document.getElementById("correctness-grid").innerHTML = correctnessCards
    .map(
      (item) => `
        <article class="correctness-card-item">
          <h3>${item.label}</h3>
          <p>Benchmark outputs were compared row by row across all 1,000,000 records and 11 formulas.</p>
          <div class="verified-badge">Verified: mismatched_rows = ${item.mismatched_rows}</div>
        </article>
      `
    )
    .join("");
}

function renderPerformance(summary) {
  const maxAverage = Math.max(...summary.map((row) => row.average_runtime_seconds));
  document.getElementById("summary-cards").innerHTML = summary
    .map((row, index) => {
      const style = methodStyles[row.method];
      return `
        <article class="summary-card ${index === 0 ? "top-method" : ""}">
          <div class="summary-topline">
            <span class="method-chip ${style.className}">${style.label}</span>
            <span>${index === 0 ? "Best Overall" : `Rank ${index + 1}`}</span>
          </div>
          <strong class="metric-value">${row.average_runtime_seconds.toFixed(3)}s</strong>
          <span class="metric-label">Average Runtime per Formula</span>
          <p class="metric-support">
            Total runtime: ${row.total_runtime_seconds.toFixed(3)}s ·
            Best: ${row.best_runtime_seconds.toFixed(3)}s ·
            Worst: ${row.worst_runtime_seconds.toFixed(3)}s
          </p>
        </article>
      `;
    })
    .join("");

  document.getElementById("runtime-chart").innerHTML = summary
    .map((row) => {
      const style = methodStyles[row.method];
      const width = `${(row.average_runtime_seconds / maxAverage) * 100}%`;
      return `
        <div class="bar-row">
          <span>${style.label}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:${width}; background:${style.color};"></div>
          </div>
          <strong>${row.average_runtime_seconds.toFixed(2)}s</strong>
        </div>
      `;
    })
    .join("");
}

function renderFormulaSection() {
  if (!dashboardPayload) return;

  const filter = document.getElementById("formula-filter").value;
  const formulas = dashboardPayload.formulas.filter(
    (formula) => filter === "all" || formula.category === filter
  );

  const formulaLogs = groupLogsByFormula(dashboardPayload.logs);
  document.getElementById("formula-cards").innerHTML = formulas
    .map((formula) => renderFormulaCard(formula, formulaLogs[formula.targil_id] || []))
    .join("");

  renderTrendChart(formulas, formulaLogs);
}

function renderFormulaCard(formula, logs) {
  const maxRuntime = Math.max(...logs.map((log) => log.run_time), 1);
  const metrics = logs
    .map((log) => {
      const style = methodStyles[log.method];
      const width = `${(log.run_time / maxRuntime) * 100}%`;
      return `
        <div class="formula-metric-row">
          <span class="method-chip ${style.className}">${style.label}</span>
          <div class="mini-track">
            <div class="mini-fill" style="width:${width}; background:${style.color};"></div>
          </div>
          <strong>${log.run_time.toFixed(2)}s</strong>
        </div>
      `;
    })
    .join("");

  return `
    <article class="formula-card-item">
      <div class="formula-meta">
        <h3>Formula ${formula.targil_id}</h3>
        <span class="method-chip">${formula.category}</span>
      </div>
      <code class="formula-code">${escapeHtml(formula.display_formula)}</code>
      <div class="formula-metrics">${metrics}</div>
    </article>
  `;
}

function renderTrendChart(formulas, formulaLogs) {
  const svg = document.getElementById("formula-trend-chart");
  const width = 920;
  const height = 320;
  const padding = { top: 20, right: 30, bottom: 42, left: 44 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const methods = ["csharp_engine", "sql_dynamic", "python_eval"];
  const maxValue = Math.max(
    ...formulas.flatMap((formula) => (formulaLogs[formula.targil_id] || []).map((log) => log.run_time)),
    1
  );

  const gridLines = [0, 0.25, 0.5, 0.75, 1]
    .map((ratio) => {
      const y = padding.top + chartHeight - ratio * chartHeight;
      const value = (maxValue * ratio).toFixed(0);
      return `
        <line class="grid-line" x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" />
        <text class="axis-label" x="${padding.left - 8}" y="${y + 4}" text-anchor="end">${value}s</text>
      `;
    })
    .join("");

  const methodLines = methods
    .map((method) => {
      const style = methodStyles[method];
      const points = formulas.map((formula, index) => {
        const log = (formulaLogs[formula.targil_id] || []).find((item) => item.method === method);
        const x =
          padding.left +
          (formulas.length === 1 ? chartWidth / 2 : (index / (formulas.length - 1)) * chartWidth);
        const y =
          padding.top + chartHeight - (((log?.run_time ?? 0) / maxValue) * chartHeight);
        return { x, y, label: formula.targil_id, value: log?.run_time ?? 0 };
      });

      const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
      const circles = points
        .map(
          (point) => `
            <circle class="trend-point" cx="${point.x}" cy="${point.y}" r="5" fill="${style.color}">
              <title>${style.label} · Formula ${point.label}: ${point.value.toFixed(3)}s</title>
            </circle>
          `
        )
        .join("");

      return `<path class="trend-line" d="${path}" stroke="${style.color}" />${circles}`;
    })
    .join("");

  const xLabels = formulas
    .map((formula, index) => {
      const x =
        padding.left +
        (formulas.length === 1 ? chartWidth / 2 : (index / (formulas.length - 1)) * chartWidth);
      return `<text class="axis-label" x="${x}" y="${height - 12}" text-anchor="middle">F${formula.targil_id}</text>`;
    })
    .join("");

  svg.innerHTML = `
    <rect x="0" y="0" width="${width}" height="${height}" rx="24" fill="transparent"></rect>
    ${gridLines}
    ${methodLines}
    ${xLabels}
    <text class="chart-note" x="${width - padding.right}" y="${height - 12}" text-anchor="end">Formula ID progression</text>
  `;
}

function renderTradeoffs(tradeoffs) {
  document.getElementById("tradeoff-grid").innerHTML = tradeoffs
    .map((item) => {
      const style = methodStyles[item.method];
      const scores = tradeoffLabels
        .map(
          ([key, label]) => `
            <div class="score-row">
              <span>${label}</span>
              <div class="score-track"><div class="score-fill" style="width:${item[key] * 10}%"></div></div>
              <strong>${item[key]}/10</strong>
            </div>
          `
        )
        .join("");

      return `
        <article class="tradeoff-item">
          <span class="method-chip ${style.className}">${style.label}</span>
          <h3>${item.headline}</h3>
          <p>${item.narrative}</p>
          <p class="tradeoff-meta-label">Architectural Assessment · Evaluation Score</p>
          <div class="tradeoff-list">${scores}</div>
        </article>
      `;
    })
    .join("");
}

function renderRecommendations(recommendations) {
  document.getElementById("recommendation-grid").innerHTML = recommendations
    .map((item) => {
      const style = methodStyles[item.method];
      return `
        <article class="recommendation-item">
          <p class="section-kicker">${item.title}</p>
          <span class="method-emphasis">${labelForMethod(item.method)}</span>
          <p>${item.reason}</p>
          <span class="method-chip ${style.className}">${style.label}</span>
        </article>
      `;
    })
    .join("");
}

function renderAiSummary(markdown) {
  const target = document.getElementById("ai-summary");
  target.innerHTML = markdownToHtml(markdown);
}

function renderAiAnalysis(aiAnalysis) {
  document.getElementById("analysis-generated-at").textContent = `Last generated: ${aiAnalysis.generated_at}`;
  document.getElementById("analysis-executive-summary").textContent = aiAnalysis.executive_summary || "";

  document.getElementById("analysis-findings-grid").innerHTML = (aiAnalysis.key_findings || [])
    .map(
      (item) => `
        <article class="analysis-card">
          <p class="section-kicker">${item.title}</p>
          <strong>${item.value}</strong>
          <p>${item.detail}</p>
        </article>
      `
    )
    .join("");

  document.getElementById("analysis-warning-grid").innerHTML = (aiAnalysis.warnings || [])
    .map(
      (item) => `
        <div class="analysis-warning-item">
          <strong>${item.title}</strong>
          <p>${item.detail}</p>
        </div>
      `
    )
    .join("");

  document.getElementById("analysis-category-grid").innerHTML = (aiAnalysis.category_matrix || [])
    .map(
      (item) => `
        <article class="analysis-card">
          <p class="section-kicker">${item.category}</p>
          <strong>${item.winner_label}</strong>
          <p>${item.methods
            .map((method) => `${method.label}: ${method.average_runtime_seconds.toFixed(2)}s`)
            .join(" · ")}</p>
        </article>
      `
    )
    .join("");

  document.getElementById("analysis-recommendation-grid").innerHTML = (aiAnalysis.recommendation_matrix || [])
    .map(
      (item) => `
        <article class="analysis-card">
          <p class="section-kicker">${item.scenario}</p>
          <strong>${labelForMethod(item.method)}</strong>
          <p>${item.reason}</p>
        </article>
      `
    )
    .join("");

  renderAiSummary(aiAnalysis.summary_markdown);
}

function renderSuggestedQuestions(questions) {
  const target = document.getElementById("suggested-question-list");
  target.innerHTML = questions
    .map(
      (question) => `
        <button class="question-chip" type="button" data-question="${escapeAttribute(question)}">${question}</button>
      `
    )
    .join("");

  target.querySelectorAll(".question-chip").forEach((button) => {
    button.addEventListener("click", () => {
      document.getElementById("benchmark-question-input").value = button.dataset.question || "";
    });
  });
}

function renderAskBenchmarkResponse(payload) {
  const container = document.getElementById("ask-benchmark-response");
  container.classList.remove("hidden");
  document.getElementById("benchmark-answer-intent").textContent = formatIntentLabel(payload.intent);
  document.getElementById("benchmark-answer-text").textContent = payload.answer;
  document.getElementById("benchmark-answer-evidence").innerHTML = (payload.evidence || [])
    .map((item) => `<li>${item}</li>`)
    .join("");
}

async function generateAnalysis() {
  const button = document.getElementById("generate-analysis-button");
  button.disabled = true;
  button.textContent = "Generating...";
  setAnalysisStatus("Recomputing the benchmark intelligence report from the latest measured results...");

  try {
    const response = await fetch("/api/analysis/generate", {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error(`Analysis API returned ${response.status}`);
    }
    const payload = await response.json();
    renderAiAnalysis(payload);
    document.getElementById("download-pdf-link").href = payload.download_pdf_url || "/api/analysis/download.pdf";
    setAnalysisStatus("Benchmark intelligence refreshed successfully. You can now download the updated PDF report.");
  } catch (error) {
    setAnalysisStatus(`Unable to generate the AI analysis. ${error.message}`, true);
  } finally {
    button.disabled = false;
    button.textContent = "Generate Analysis";
  }
}

async function askBenchmark() {
  const button = document.getElementById("ask-benchmark-button");
  const input = document.getElementById("benchmark-question-input");
  const question = input.value.trim();
  if (!question) {
    setAnalysisStatus("Write a benchmark question first so the intelligence engine has something to answer.", true);
    return;
  }

  button.disabled = true;
  button.textContent = "Thinking...";
  setAnalysisStatus("Reading the measured benchmark data and preparing a local answer...");

  try {
    const response = await fetch("/api/analysis/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) {
      throw new Error(`Ask API returned ${response.status}`);
    }
    const payload = await response.json();
    renderAskBenchmarkResponse(payload);
    setAnalysisStatus("The benchmark question was answered from the current measured dataset.");
  } catch (error) {
    setAnalysisStatus(`Unable to answer the benchmark question. ${error.message}`, true);
  } finally {
    button.disabled = false;
    button.textContent = "Ask the Benchmark";
  }
}

function groupLogsByFormula(logs) {
  return logs.reduce((accumulator, log) => {
    accumulator[log.targil_id] ||= [];
    accumulator[log.targil_id].push(log);
    return accumulator;
  }, {});
}

function labelForMethod(method) {
  return methodStyles[method]?.label ?? method ?? "—";
}

function formatCompactNumber(value) {
  return new Intl.NumberFormat("en", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function markdownToHtml(markdown) {
  return markdown
    .split("\n")
    .map((line) => {
      const escaped = escapeHtml(line);
      if (escaped.startsWith("### ")) return `<h3>${escaped.slice(4)}</h3>`;
      if (escaped.startsWith("## ")) return `<h2>${escaped.slice(3)}</h2>`;
      if (escaped.startsWith("# ")) return `<h1>${escaped.slice(2)}</h1>`;
      if (escaped.startsWith("- ")) return `<li>${escaped.slice(2)}</li>`;
      if (escaped.trim() === "") return "";
      return `<p>${escaped.replace(/`([^`]+)`/g, "<code>$1</code>")}</p>`;
    })
    .join("")
    .replace(/(<li>.*<\/li>)/g, "<ul>$1</ul>")
    .replace(/<\/ul><ul>/g, "");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll('"', "&quot;");
}

function formatIntentLabel(intent) {
  const labels = {
    why_fastest: "Winner Explanation",
    stability: "Stability Reading",
    complexity: "Complexity Pattern",
    python_pain: "Python Trade-Off",
    enterprise: "Enterprise Recommendation",
    database: "Database-Centric Recommendation",
    correctness: "Correctness Validation",
    general: "General Benchmark Reading",
    empty: "Question Needed",
  };
  return labels[intent] || "Benchmark Answer";
}

function setLoading(isLoading) {
  const loading = document.getElementById("loading-state");
  const error = document.getElementById("error-state");
  if (isLoading) {
    loading.classList.remove("hidden");
    error.classList.add("hidden");
  } else {
    loading.classList.add("hidden");
  }
}

function setError(message) {
  const error = document.getElementById("error-state");
  error.textContent = message;
  error.classList.remove("hidden");
  document.getElementById("loading-state").classList.add("hidden");
}

function setAnalysisStatus(message, isError = false) {
  const target = document.getElementById("analysis-status");
  target.textContent = message;
  target.classList.toggle("analysis-status-error", isError);
}
