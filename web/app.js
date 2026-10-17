/**
 * app.js - Evolutionary Game Theory Tax Simulation Core & Interactive Visualizer
 */

// --- Global Simulation State ---
const State = {
  // Parameters
  W: 100.0,
  t: 0.30,
  f: 1.5,
  ca: 8.0,
  nAgents: 500,
  temperature: 8.0,
  mutationRate: 0.005,
  policyName: "pid",

  // Runtime
  step: 0,
  maxSteps: 150,
  isRunning: false,
  timer: null,
  speedMs: 80,

  // Population arrays
  strategies: [],      // 1 = Comply, 0 = Evade
  isFlagged: [],       // Risk-targeted flags
  flagTimer: [],
  payoffs: [],

  // Tracking history
  history: {
    steps: [],
    compliance: [],
    evasion: [],
    alpha: [],
    grossRev: [],
    cost: [],
    netRev: []
  },

  // Policy Internal States
  proportionalAlpha: 0.35,
  pid: {
    integral: 0,
    prevError: 0
  },
  prevGrossRevenue: 15000
};

// --- Mathematical Helpers & Game Theory Engine ---
function getAlphaStar() {
  return 1.0 / (1.0 + State.f);
}

function getXStar() {
  const caughtLiability = (1.0 + State.f) * State.t * State.W;
  const xStar = 1.0 - (State.ca / caughtLiability);
  return Math.max(0, Math.min(1, xStar));
}

function initializePopulation() {
  State.step = 0;
  State.strategies = new Int8Array(State.nAgents);
  State.isFlagged = new Uint8Array(State.nAgents);
  State.flagTimer = new Int16Array(State.nAgents);
  State.payoffs = new Float32Array(State.nAgents);

  // 50% initial compliance
  const half = Math.floor(State.nAgents / 2);
  for (let i = 0; i < State.nAgents; i++) {
    State.strategies[i] = i < half ? 1 : 0;
  }
  // Shuffle
  for (let i = State.nAgents - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const temp = State.strategies[i];
    State.strategies[i] = State.strategies[j];
    State.strategies[j] = temp;
  }

  // Reset policies
  State.proportionalAlpha = 0.35;
  State.pid.integral = 0;
  State.pid.prevError = 0;
  State.prevGrossRevenue = State.nAgents * State.t * State.W * 0.5;

  // Clear history
  State.history = {
    steps: [],
    compliance: [],
    evasion: [],
    alpha: [],
    grossRev: [],
    cost: [],
    netRev: []
  };

  updateThresholdDisplay();
}

function getAuditIntensity(observedEvasion) {
  const alphaMin = 0.02;
  const alphaMax = 0.95;

  switch (State.policyName) {
    case "static":
      return Math.min(alphaMax, Math.max(alphaMin, 0.35));

    case "proportional": {
      const targetEvasion = 0.05;
      const kp = 0.35;
      const error = observedEvasion - targetEvasion;
      State.proportionalAlpha = Math.min(alphaMax, Math.max(alphaMin, State.proportionalAlpha + kp * error));
      return State.proportionalAlpha;
    }

    case "pid": {
      const targetEvasion = 0.02;
      const kp = 0.45;
      const ki = 0.08;
      const kd = 0.20;
      const error = observedEvasion - targetEvasion;

      State.pid.integral += error;
      State.pid.integral = Math.max(-5, Math.min(5, State.pid.integral)); // Anti-windup
      const derivative = error - State.pid.prevError;
      State.pid.prevError = error;

      const alpha = 0.35 + (kp * error) + (ki * State.pid.integral) + (kd * derivative);
      return Math.min(alphaMax, Math.max(alphaMin, alpha));
    }

    case "targeted": {
      // Aggregate rate
      let flaggedCount = 0;
      for (let i = 0; i < State.nAgents; i++) {
        if (State.isFlagged[i]) flaggedCount++;
      }
      const frac = flaggedCount / State.nAgents;
      return frac * 0.85 + (1 - frac) * 0.12;
    }

    case "budget": {
      const budget = Math.max(50, State.prevGrossRevenue * 0.25);
      const maxAffordableAudits = budget / State.ca;
      const maxAffordableAlpha = maxAffordableAudits / State.nAgents;
      const desiredAlpha = alphaMin + (0.60 - alphaMin) * observedEvasion;
      return Math.min(alphaMax, Math.max(alphaMin, Math.min(desiredAlpha, maxAffordableAlpha)));
    }

    default:
      return 0.35;
  }
}

function simulationStep() {
  if (State.step >= State.maxSteps) {
    pauseSimulation();
    return;
  }

  // Current compliance & evasion
  let complyCount = 0;
  for (let i = 0; i < State.nAgents; i++) {
    if (State.strategies[i] === 1) complyCount++;
  }
  const complianceRate = complyCount / State.nAgents;
  const evasionRate = 1.0 - complianceRate;

  // Determine audits
  const baseAlpha = getAuditIntensity(evasionRate);
  let auditsConducted = 0;
  let grossRev = 0;
  const owedTax = State.t * State.W;
  const penalty = (1.0 + State.f) * owedTax;

  for (let i = 0; i < State.nAgents; i++) {
    let pAudit = baseAlpha;
    if (State.policyName === "targeted") {
      pAudit = State.isFlagged[i] ? 0.85 : 0.12;
    }

    const isAudited = Math.random() < pAudit;
    if (isAudited) auditsConducted++;

    if (State.strategies[i] === 1) {
      // Comply
      State.payoffs[i] = State.W - owedTax;
      grossRev += owedTax;
      if (isAudited && State.isFlagged[i]) {
        State.flagTimer[i]--;
        if (State.flagTimer[i] <= 0) State.isFlagged[i] = 0;
      }
    } else {
      // Evade
      if (isAudited) {
        // Caught
        State.payoffs[i] = State.W - penalty;
        grossRev += penalty;
        State.isFlagged[i] = 1;
        State.flagTimer[i] = 5;
      } else {
        // Uncaught
        State.payoffs[i] = State.W;
      }
    }
  }

  const enforcementCost = auditsConducted * State.ca;
  const netRev = grossRev - enforcementCost;
  State.prevGrossRevenue = grossRev;
  const actualAlpha = auditsConducted / State.nAgents;

  // Fermi Pairwise Learning
  for (let i = 0; i < State.nAgents; i++) {
    const peer = Math.floor(Math.random() * State.nAgents);
    const deltaPi = State.payoffs[peer] - State.payoffs[i];
    const exponent = Math.max(-50, Math.min(50, -deltaPi / State.temperature));
    const pSwitch = 1.0 / (1.0 + Math.exp(exponent));

    if (Math.random() < pSwitch) {
      State.strategies[i] = State.strategies[peer];
    }
    // Spontaneous mutation
    if (Math.random() < State.mutationRate) {
      State.strategies[i] = 1 - State.strategies[i];
    }
  }

  // Record history
  State.history.steps.push(State.step);
  State.history.compliance.push(complianceRate);
  State.history.evasion.push(evasionRate);
  State.history.alpha.push(actualAlpha);
  State.history.grossRev.push(grossRev);
  State.history.cost.push(enforcementCost);
  State.history.netRev.push(netRev);

  // Update UI & Charts
  updateKPIs(complianceRate, evasionRate, actualAlpha, netRev, enforcementCost);
  updateCharts();

  State.step++;
}

// --- UI Updates ---
function updateKPIs(comp, evas, alpha, netRev, cost) {
  document.getElementById("kpi-compliance").textContent = (comp * 100).toFixed(1) + "%";
  document.getElementById("kpi-evasion").textContent = (evas * 100).toFixed(1) + "%";
  document.getElementById("kpi-alpha").textContent = (alpha * 100).toFixed(1) + "%";
  document.getElementById("kpi-net-rev").textContent = "$" + Math.round(netRev).toLocaleString();
  document.getElementById("kpi-cost").textContent = "$" + Math.round(cost).toLocaleString();

  const roi = cost > 0 ? (netRev / cost).toFixed(2) + "x" : "N/A";
  document.getElementById("kpi-roi").textContent = roi;
}

function updateThresholdDisplay() {
  const alphaStar = getAlphaStar();
  const xStar = getXStar();
  document.getElementById("val-alpha-star").textContent = (alphaStar * 100).toFixed(1) + "%";
  document.getElementById("val-x-star").textContent = (xStar * 100).toFixed(1) + "%";
}

// --- Chart.js Instances ---
let trajectoryChart = null;
let phaseChart = null;
let financeChart = null;

function initCharts() {
  const textMuted = "#9ca3af";
  const gridColor = "rgba(255, 255, 255, 0.06)";

  // 1. Trajectory Chart
  const ctxTraj = document.getElementById("chart-trajectories").getContext("2d");
  trajectoryChart = new Chart(ctxTraj, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Compliance (x)",
          data: [],
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.2,
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: "Evasion (1-x)",
          data: [],
          borderColor: "#f43f5e",
          tension: 0.2,
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: "Audit Rate (α)",
          data: [],
          borderColor: "#06b6d4",
          borderDash: [4, 4],
          tension: 0.2,
          borderWidth: 2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: textMuted } },
        y: { min: 0, max: 1.05, grid: { color: gridColor }, ticks: { color: textMuted } }
      },
      plugins: {
        legend: { labels: { color: "#e5e7eb", boxWidth: 12 } }
      }
    }
  });

  // 2. Phase Portrait Chart (Compliance vs Alpha)
  const ctxPhase = document.getElementById("chart-phase").getContext("2d");
  phaseChart = new Chart(ctxPhase, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Trajectory Path (x, α)",
          data: [],
          borderColor: "#8b5cf6",
          showLine: true,
          tension: 0.1,
          borderWidth: 2,
          pointRadius: 2,
          pointBackgroundColor: "#a855f7"
        },
        {
          label: "Equilibrium (x*, α*)",
          data: [{ x: getXStar(), y: getAlphaStar() }],
          pointRadius: 8,
          pointBackgroundColor: "#f59e0b",
          borderColor: "#fbbf24",
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { min: 0, max: 1, title: { display: true, text: "Compliance (x)", color: textMuted }, grid: { color: gridColor }, ticks: { color: textMuted } },
        y: { min: 0, max: 1, title: { display: true, text: "Audit Rate (α)", color: textMuted }, grid: { color: gridColor }, ticks: { color: textMuted } }
      },
      plugins: {
        legend: { labels: { color: "#e5e7eb", boxWidth: 12 } }
      }
    }
  });

  // 3. Financial Metrics Chart
  const ctxFinance = document.getElementById("chart-finance").getContext("2d");
  financeChart = new Chart(ctxFinance, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Net Revenue",
          data: [],
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.15)",
          fill: true,
          tension: 0.2,
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: "Enforcement Cost",
          data: [],
          borderColor: "#f59e0b",
          tension: 0.2,
          borderWidth: 2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: gridColor }, ticks: { color: textMuted } },
        y: { grid: { color: gridColor }, ticks: { color: textMuted } }
      },
      plugins: {
        legend: { labels: { color: "#e5e7eb", boxWidth: 12 } }
      }
    }
  });
}

function updateCharts() {
  const steps = State.history.steps;
  const comp = State.history.compliance;
  const evas = State.history.evasion;
  const alpha = State.history.alpha;
  const netRev = State.history.netRev;
  const cost = State.history.cost;

  // Trajectory update
  trajectoryChart.data.labels = steps;
  trajectoryChart.data.datasets[0].data = comp;
  trajectoryChart.data.datasets[1].data = evas;
  trajectoryChart.data.datasets[2].data = alpha;
  trajectoryChart.update('none');

  // Phase update
  const phasePoints = steps.map((s, i) => ({ x: comp[i], y: alpha[i] }));
  phaseChart.data.datasets[0].data = phasePoints;
  phaseChart.data.datasets[1].data = [{ x: getXStar(), y: getAlphaStar() }];
  phaseChart.update('none');

  // Finance update
  financeChart.data.labels = steps;
  financeChart.data.datasets[0].data = netRev;
  financeChart.data.datasets[1].data = cost;
  financeChart.update('none');
}

// --- Simulation Controls ---
function playSimulation() {
  if (State.isRunning) return;
  State.isRunning = true;
  document.getElementById("btn-play").innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
  State.timer = setInterval(() => {
    simulationStep();
  }, State.speedMs);
}

function pauseSimulation() {
  State.isRunning = false;
  document.getElementById("btn-play").innerHTML = '<i class="fa-solid fa-play"></i> Run';
  if (State.timer) {
    clearInterval(State.timer);
    State.timer = null;
  }
}

function resetSimulation() {
  pauseSimulation();
  initializePopulation();
  updateKPIs(0.5, 0.5, 0.35, 0, 0);
  updateCharts();
}

// --- Event Listeners & Setup ---
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  initializePopulation();

  // Inputs
  const taxInput = document.getElementById("slider-tax");
  const fineInput = document.getElementById("slider-fine");
  const costInput = document.getElementById("slider-cost");
  const policySelect = document.getElementById("select-policy");
  const presetSelect = document.getElementById("select-preset");

  taxInput.addEventListener("input", (e) => {
    State.t = parseFloat(e.target.value);
    document.getElementById("val-tax").textContent = Math.round(State.t * 100) + "%";
    updateThresholdDisplay();
  });

  fineInput.addEventListener("input", (e) => {
    State.f = parseFloat(e.target.value);
    document.getElementById("val-fine").textContent = State.f.toFixed(1) + "x";
    updateThresholdDisplay();
  });

  costInput.addEventListener("input", (e) => {
    State.ca = parseFloat(e.target.value);
    document.getElementById("val-cost").textContent = "$" + State.ca.toFixed(1);
    updateThresholdDisplay();
  });

  policySelect.addEventListener("change", (e) => {
    State.policyName = e.target.value;
    resetSimulation();
  });

  presetSelect.addEventListener("change", (e) => {
    const preset = e.target.value;
    if (preset === "baseline") {
      taxInput.value = 0.30;
      fineInput.value = 1.5;
      costInput.value = 8.0;
      policySelect.value = "static";
    } else if (preset === "deterrence") {
      taxInput.value = 0.30;
      fineInput.value = 3.0;
      costInput.value = 6.0;
      policySelect.value = "proportional";
    } else if (preset === "costly") {
      taxInput.value = 0.35;
      fineInput.value = 1.0;
      costInput.value = 16.0;
      policySelect.value = "budget";
    } else if (preset === "optimal_pid") {
      taxInput.value = 0.30;
      fineInput.value = 1.5;
      costInput.value = 8.0;
      policySelect.value = "pid";
    }
    // Trigger updates
    taxInput.dispatchEvent(new Event("input"));
    fineInput.dispatchEvent(new Event("input"));
    costInput.dispatchEvent(new Event("input"));
    policySelect.dispatchEvent(new Event("change"));
  });

  document.getElementById("btn-play").addEventListener("click", () => {
    if (State.isRunning) {
      pauseSimulation();
    } else {
      playSimulation();
    }
  });

  document.getElementById("btn-step").addEventListener("click", () => {
    pauseSimulation();
    simulationStep();
  });

  document.getElementById("btn-reset").addEventListener("click", resetSimulation);

  // Auto-run first 50 steps for initial preview
  for (let i = 0; i < 60; i++) {
    simulationStep();
  }
});
