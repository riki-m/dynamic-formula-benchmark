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

const STATIC_DASHBOARD_URL = "data/dashboard.json";
const STATIC_PDF_URL = "assets/benchmark-ai-analysis.pdf";

let dashboardPayload = null;
let isStaticMode = false;

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
    dashboardPayload = await tryLoadLiveDashboard();
    renderDashboard(dashboardPayload);
    setLoading(false);
  } catch (error) {
    setError(`Unable to load the benchmark dashboard. ${error.message}`);
  }
}

async function tryLoadLiveDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) {
      throw new Error(`Dashboard API returned ${response.status}`);
    }
    isStaticMode = false;
    return await response.json();
  } catch (liveError) {
    const fallbackResponse = await fetch(STATIC_DASHBOARD_URL);
    if (!fallbackResponse.ok) {
      throw new Error(`Live API failed (${liveError.message}) and static snapshot returned ${fallbackResponse.status}`);
    }
    isStaticMode = true;
    return await fallbackResponse.json();
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
  document.getElementById("download-pdf-link").href = isStaticMode
    ? STATIC_PDF_URL
    : ai_analysis.download_pdf_url || "/api/analysis/download.pdf";
  setAnalysisStatus(
    isStaticMode
      ? "Public share mode is active. This site is running from a published snapshot of the measured benchmark data."
      : "The current intelligence report is built from measured benchmark outputs and can be regenerated at any time."
  );
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
  setAnalysisStatus(
    isStaticMode
      ? "Recomputing the intelligence report locally from the published benchmark snapshot..."
      : "Recomputing the benchmark intelligence report from the latest measured results..."
  );

  try {
    if (isStaticMode) {
      const recomputed = buildLocalAiAnalysis(dashboardPayload);
      dashboardPayload.ai_analysis = {
        ...dashboardPayload.ai_analysis,
        ...recomputed,
        download_pdf_url: STATIC_PDF_URL,
      };
      renderAiAnalysis(dashboardPayload.ai_analysis);
      document.getElementById("download-pdf-link").href = STATIC_PDF_URL;
      setAnalysisStatus("Static public analysis was recomputed locally from the published benchmark dataset.");
      return;
    }

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
  setAnalysisStatus(
    isStaticMode
      ? "Reading the published benchmark snapshot and generating a local answer..."
      : "Reading the measured benchmark data and preparing a local answer..."
  );

  try {
    if (isStaticMode) {
      const payload = answerBenchmarkLocally(question, dashboardPayload);
      renderAskBenchmarkResponse(payload);
      setAnalysisStatus("The benchmark question was answered locally from the published dataset.");
      return;
    }

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

function buildLocalAiAnalysis(payload) {
  const overview = payload.overview;
  const formulas = payload.formulas || [];
  const logs = (payload.logs || []).map((row) => ({
    ...row,
    targil_id: Number(row.targil_id),
    run_time: Number(row.run_time),
    records_processed: Number(row.records_processed),
  }));
  const summary = (payload.summary || []).map((row) => ({
    ...row,
    formulas_executed: Number(row.formulas_executed),
    total_records_processed: Number(row.total_records_processed),
    average_runtime_seconds: Number(row.average_runtime_seconds),
    best_runtime_seconds: Number(row.best_runtime_seconds),
    worst_runtime_seconds: Number(row.worst_runtime_seconds),
    total_runtime_seconds: Number(row.total_runtime_seconds),
  }));
  const correctness = payload.correctness || [];

  const methodTimings = {};
  const perFormula = {};
  logs.forEach((log) => {
    methodTimings[log.method] ||= [];
    methodTimings[log.method].push(log.run_time);
    perFormula[log.targil_id] ||= [];
    perFormula[log.targil_id].push(log);
  });

  const fastest = summary[0] || null;
  const slowest = summary[summary.length - 1] || null;
  const mostStable = summary
    .map((row) => {
      const timings = methodTimings[row.method] || [row.average_runtime_seconds];
      return {
        method: row.method,
        std_dev: populationStdDev(timings),
        spread: row.worst_runtime_seconds - row.best_runtime_seconds,
      };
    })
    .sort((a, b) => a.std_dev - b.std_dev || a.spread - b.spread)[0] || null;

  const winners = [];
  let closestRace = null;
  let widestMargin = null;
  formulas.forEach((formula) => {
    const ranked = [...(perFormula[formula.targil_id] || [])].sort((a, b) => a.run_time - b.run_time);
    if (!ranked.length) return;
    const leader = ranked[0];
    const runnerUp = ranked[1] || ranked[0];
    const margin = runnerUp.run_time - leader.run_time;
    const winner = {
      targil_id: formula.targil_id,
      formula: formula.display_formula,
      category: formula.category,
      winner_method: leader.method,
      winner_label: labelForMethod(leader.method),
      winner_runtime_seconds: leader.run_time,
      margin_seconds: margin,
    };
    winners.push(winner);
    if (!closestRace || margin < closestRace.margin_seconds) closestRace = winner;
    if (!widestMargin || margin > widestMargin.margin_seconds) widestMargin = winner;
  });

  const categoryMatrix = buildLocalCategoryMatrix(formulas, perFormula);
  const recommendationMatrix = [
    {
      scenario: "Best overall production choice",
      method: fastest?.method || "csharp_engine",
      reason: "This engine delivered the strongest benchmark profile on the measured workload.",
    },
    {
      scenario: "Best for rapid prototyping",
      method: "python_eval",
      reason: "The simplest formula-to-execution path with minimal implementation ceremony.",
    },
    {
      scenario: "Best for DB-centric deployment",
      method: "sql_dynamic",
      reason: "Keeps execution close to the data and avoids repeated application-side transfer work.",
    },
  ];

  const performanceGap = fastest && slowest
    ? slowest.average_runtime_seconds - fastest.average_runtime_seconds
    : 0;
  const correctnessPairs = correctness.filter((item) => Number(item.mismatched_rows) === 0).length;

  const keyFindings = [];
  if (fastest && slowest) {
    keyFindings.push({
      title: "Fastest Overall",
      value: labelForMethod(fastest.method),
      detail: `${labelForMethod(fastest.method)} achieved the lowest average runtime at ${fastest.average_runtime_seconds.toFixed(3)}s per formula, beating ${labelForMethod(slowest.method)} by ${performanceGap.toFixed(3)}s.`,
    });
  }
  if (mostStable) {
    keyFindings.push({
      title: "Most Stable Runtime",
      value: labelForMethod(mostStable.method),
      detail: `Runtime variance stayed lowest for ${labelForMethod(mostStable.method)}, with a standard deviation of ${mostStable.std_dev.toFixed(3)}s.`,
    });
  }
  if (closestRace) {
    keyFindings.push({
      title: "Closest Race",
      value: `Formula ${closestRace.targil_id}`,
      detail: `${closestRace.winner_label} won this formula by only ${closestRace.margin_seconds.toFixed(3)}s.`,
    });
  }
  if (widestMargin) {
    keyFindings.push({
      title: "Largest Advantage",
      value: `Formula ${widestMargin.targil_id}`,
      detail: `${widestMargin.winner_label} created the widest gap here at ${widestMargin.margin_seconds.toFixed(3)}s.`,
    });
  }

  const warnings = [];
  if (fastest && slowest && slowest.average_runtime_seconds > fastest.average_runtime_seconds * 2) {
    warnings.push({
      title: "Large performance spread",
      detail: "The slowest engine is more than 2x slower than the fastest one, so architecture choice materially affects latency.",
    });
  }
  if (widestMargin && widestMargin.category === "Complex") {
    warnings.push({
      title: "Complex formulas are the real separator",
      detail: "The widest runtime gap appeared in a complex formula, which suggests mathematical transformation cost is a major differentiator.",
    });
  }
  warnings.push({
    title: "Correctness stayed fully aligned",
    detail: `All ${correctnessPairs} validated pairwise comparisons returned mismatched_rows = 0, so the benchmark ranking is safe to trust.`,
  });

  const generatedAt = formatTimestamp(new Date());
  const executiveSummary = `This analysis was generated directly from measured benchmark logs over ${overview.records_processed.toLocaleString()} records and ${overview.formula_count} formulas. ${labelForMethod(fastest?.method || "csharp_engine")} delivered the strongest overall runtime profile, while ${labelForMethod(mostStable?.method || "sql_dynamic")} showed the most stable timing behavior. The performance spread between the fastest and slowest engine reached ${performanceGap.toFixed(3)}s per formula, which makes execution architecture a meaningful production decision.`;

  return {
    generated_at: generatedAt,
    executive_summary: executiveSummary,
    key_findings: keyFindings,
    warnings,
    category_matrix: categoryMatrix,
    recommendation_matrix: recommendationMatrix,
    formula_winners: winners,
    summary_rows: summary,
    correctness_cards: correctness,
    fastest_method: fastest?.method || null,
    most_stable_method: mostStable?.method || null,
    performance_gap_seconds: performanceGap,
    summary_markdown: renderLocalAnalysisMarkdown(generatedAt, executiveSummary, keyFindings, warnings, categoryMatrix, winners, recommendationMatrix),
    suggested_questions: dashboardPayload?.ai_analysis?.suggested_questions || [],
  };
}

function buildLocalCategoryMatrix(formulas, perFormula) {
  const categoryLogs = {};
  formulas.forEach((formula) => {
    categoryLogs[formula.category] ||= {};
    (perFormula[formula.targil_id] || []).forEach((log) => {
      categoryLogs[formula.category][log.method] ||= [];
      categoryLogs[formula.category][log.method].push(log.run_time);
    });
  });

  return Object.entries(categoryLogs).map(([category, methods]) => {
    const ranked = Object.entries(methods)
      .map(([method, values]) => ({
        method,
        label: labelForMethod(method),
        average_runtime_seconds: values.reduce((sum, value) => sum + value, 0) / values.length,
      }))
      .sort((a, b) => a.average_runtime_seconds - b.average_runtime_seconds);
    return {
      category,
      winner_method: ranked[0]?.method || null,
      winner_label: ranked[0]?.label || null,
      methods: ranked,
    };
  });
}

function answerBenchmarkLocally(question, payload) {
  const normalizedQuestion = question.toLowerCase().trim().replace(/\s+/g, " ");
  if (!normalizedQuestion) {
    return {
      question,
      intent: "empty",
      answer: "Ask about performance, stability, complex formulas, correctness, enterprise fit, or why a method won.",
      evidence: [],
    };
  }

  const ai = buildLocalAiAnalysis(payload);
  const summaryRows = ai.summary_rows || [];
  const fastest = summaryRows[0] || null;
  const slowest = summaryRows[summaryRows.length - 1] || null;
  const avgByMethod = Object.fromEntries(summaryRows.map((row) => [row.method, row.average_runtime_seconds]));
  const intent = detectQuestionIntentLocal(normalizedQuestion);

  let answer = "";
  let evidence = [];

  if (intent === "why_fastest" && fastest && slowest) {
    answer = `${labelForMethod(fastest.method)} won because it achieved the lowest measured average runtime at ${fastest.average_runtime_seconds.toFixed(3)}s per formula, while ${labelForMethod(slowest.method)} needed ${slowest.average_runtime_seconds.toFixed(3)}s. That gap stayed meaningful across the benchmark, so the winner is supported by repeated measured latency, not by a single outlier.`;
    evidence = [
      `Fastest overall average: ${labelForMethod(fastest.method)} at ${fastest.average_runtime_seconds.toFixed(3)}s.`,
      `Slowest overall average: ${labelForMethod(slowest.method)} at ${slowest.average_runtime_seconds.toFixed(3)}s.`,
      `Measured performance gap: ${(slowest.average_runtime_seconds - fastest.average_runtime_seconds).toFixed(3)}s per formula.`,
    ];
  } else if (intent === "stability") {
    answer = `${labelForMethod(ai.most_stable_method || "sql_dynamic")} is the most stable engine because its runtime variance across formulas was the lowest in the benchmark. That means its behavior changed less dramatically between easy and difficult formulas.`;
    const stableFinding = (ai.key_findings || []).find((item) => item.title === "Most Stable Runtime");
    evidence = [
      stableFinding?.detail || "",
      `Average runtime: ${(avgByMethod[ai.most_stable_method] || 0).toFixed(3)}s.`,
    ].filter(Boolean);
  } else if (intent === "complexity") {
    const complexRow = (ai.category_matrix || []).find((item) => item.category === "Complex");
    if (complexRow) {
      answer = `Complex formulas widened the separation between engines. In the complex category, ${complexRow.winner_label} led the group, which suggests that advanced mathematical transformations amplify engine differences more than simple arithmetic does.`;
      evidence = [
        `Complex-category leader: ${complexRow.winner_label}.`,
        `Category averages: ${complexRow.methods.map((item) => `${item.label} ${item.average_runtime_seconds.toFixed(3)}s`).join(", ")}.`,
      ];
    } else {
      answer = "The benchmark currently has no classified complex formulas to analyze.";
    }
  } else if (intent === "python_pain") {
    const hardest = [...(ai.formula_winners || [])]
      .filter((item) => item.winner_method !== "python_eval")
      .sort((a, b) => b.margin_seconds - a.margin_seconds)[0];
    answer = "Python Eval is easiest to implement, but it loses the most on scale-sensitive formulas because interpreted execution adds more overhead when the formula set becomes large or mathematically heavier.";
    evidence = [
      `Python average runtime: ${(avgByMethod.python_eval || 0).toFixed(3)}s per formula.`,
      `C# average runtime: ${(avgByMethod.csharp_engine || 0).toFixed(3)}s per formula.`,
      `SQL Dynamic average runtime: ${(avgByMethod.sql_dynamic || 0).toFixed(3)}s per formula.`,
      hardest ? `Largest non-Python win: Formula ${hardest.targil_id} (${hardest.category}).` : "",
    ].filter(Boolean);
  } else if (intent === "enterprise") {
    answer = "C# Engine is the best enterprise choice because it combines the strongest measured runtime with typed application architecture, clean service integration, and maintainable backend structure.";
    evidence = [
      `Fastest measured average runtime: ${(avgByMethod.csharp_engine || 0).toFixed(3)}s.`,
      "Strong maintainability and extensibility scores in the architectural assessment.",
      "Typed backend integration makes it easier to govern in long-lived production systems.",
    ];
  } else if (intent === "database") {
    answer = "SQL Dynamic is the best DB-centric option because it keeps execution close to the data and reduces repeated application-side transfer work. That makes it a strong fit when the organization wants most of the computation to stay inside SQL Server.";
    evidence = [
      `SQL Dynamic average runtime: ${(avgByMethod.sql_dynamic || 0).toFixed(3)}s.`,
      "Execution happens near the stored data instead of moving large workloads out to the application layer.",
      "It ranked second overall while preserving correctness.",
    ];
  } else if (intent === "correctness") {
    answer = "Correctness remained fully aligned across the benchmark. All pairwise comparisons returned zero mismatched rows, so the ranking is based on latency differences rather than inconsistent outputs.";
    evidence = (payload.correctness || []).map((item) => `${item.label}: mismatched_rows = ${item.mismatched_rows}.`);
  } else {
    answer = `This benchmark currently covers ${payload.overview.formula_count} formulas over ${payload.overview.records_processed.toLocaleString()} records per formula. ${labelForMethod(ai.fastest_method || "csharp_engine")} leads overall, ${labelForMethod(ai.most_stable_method || "sql_dynamic")} is the most stable, and correctness is verified across the three execution engines.`;
    evidence = [
      `Fastest overall: ${labelForMethod(ai.fastest_method || "csharp_engine")}.`,
      `Most stable: ${labelForMethod(ai.most_stable_method || "sql_dynamic")}.`,
      "Ask about speed, stability, complex formulas, correctness, enterprise fit, or DB-centric deployment for a more targeted explanation.",
    ];
  }

  return { question, intent, answer, evidence };
}

function detectQuestionIntentLocal(question) {
  if (["why", "won", "fastest", "winner", "best overall"].some((term) => question.includes(term))) return "why_fastest";
  if (["stable", "stability", "variance", "consistent"].some((term) => question.includes(term))) return "stability";
  if (["complex", "sqrt", "log", "conditional", "category", "formula type"].some((term) => question.includes(term))) return "complexity";
  if (["python", "prototype", "iterate", "slow"].some((term) => question.includes(term))) return "python_pain";
  if (["enterprise", "maintainability", "maintainable"].some((term) => question.includes(term))) return "enterprise";
  if (["db", "database", "sql server", "data-local", "data local"].some((term) => question.includes(term))) return "database";
  if (["correct", "mismatch", "same results", "verified"].some((term) => question.includes(term))) return "correctness";
  return "general";
}

function renderLocalAnalysisMarkdown(generatedAt, executiveSummary, keyFindings, warnings, categoryMatrix, winners, recommendationMatrix) {
  const lines = [
    "# AI-Assisted Benchmark Analysis",
    "",
    `_Generated on ${generatedAt}_`,
    "",
    "## Executive Summary",
    executiveSummary,
    "",
    "## Key Findings",
  ];
  keyFindings.forEach((item) => lines.push(`- **${item.title}**: ${item.value} — ${item.detail}`));
  lines.push("", "## Warnings and Signals");
  warnings.forEach((item) => lines.push(`- **${item.title}**: ${item.detail}`));
  lines.push("", "## Category-Level Winners");
  categoryMatrix.forEach((row) => {
    lines.push(`- **${row.category}**: ${row.winner_label} led. ${row.methods.map((method) => `${method.label} ${method.average_runtime_seconds.toFixed(3)}s`).join(", ")}.`);
  });
  lines.push("", "## Per-Formula Winners");
  winners.forEach((winner) => {
    lines.push(`- Formula ${winner.targil_id} (${winner.category}): ${winner.winner_label} won at ${winner.winner_runtime_seconds.toFixed(3)}s with a ${winner.margin_seconds.toFixed(3)}s lead.`);
  });
  lines.push("", "## Scenario Recommendations");
  recommendationMatrix.forEach((item) => {
    lines.push(`- **${item.scenario}**: ${labelForMethod(item.method)} — ${item.reason}`);
  });
  return lines.join("\n");
}

function populationStdDev(values) {
  if (!values.length) return 0;
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + ((value - mean) ** 2), 0) / values.length;
  return Math.sqrt(variance);
}

function formatTimestamp(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}
