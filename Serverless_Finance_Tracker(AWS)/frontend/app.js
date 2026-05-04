// Replace this value with the ApiBaseUrl output from `sam deploy`.
const API_BASE_URL = "https://xumta3bqu4.execute-api.ap-south-1.amazonaws.com/Prod";

const form = document.getElementById("expenseForm");
const amountInput = document.getElementById("amount");
const categoryInput = document.getElementById("category");
const noteInput = document.getElementById("note");
const dateInput = document.getElementById("date");
const message = document.getElementById("message");
const loadingIndicator = document.getElementById("loadingIndicator");
const expenseList = document.getElementById("expenseList");
const totalAmount = document.getElementById("totalAmount");
const categoryFilter = document.getElementById("categoryFilter");

let summaryChart;
let expenses = [];

dateInput.value = new Date().toISOString().slice(0, 10);

function apiUrl(path) {
  return `${API_BASE_URL.replace(/\/$/, "")}${path}`;
}

function setLoading(isLoading) {
  loadingIndicator.hidden = !isLoading;
  form.querySelector("button").disabled = isLoading;
}

function setMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`.trim();
}

function formatCurrency(value) {
  return Number(value || 0).toLocaleString(undefined, {
    style: "currency",
    currency: "INR",
  });
}

function validateExpense(payload) {
  if (!payload.amount || Number(payload.amount) <= 0) {
    return "Enter an amount greater than zero.";
  }

  if (!payload.category.trim()) {
    return "Enter a category.";
  }

  if (!payload.date) {
    return "Choose a date.";
  }

  return "";
}

async function request(path, options = {}) {
  if (API_BASE_URL.includes("REPLACE_WITH")) {
    throw new Error("Set API_BASE_URL in frontend/app.js after deploying the SAM stack.");
  }

  const response = await fetch(apiUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "Request failed.");
  }

  return data;
}

async function loadExpenses() {
  const selectedCategory = categoryFilter.value;
  const query = selectedCategory ? `?category=${encodeURIComponent(selectedCategory)}` : "";
  const data = await request(`/expenses${query}`);
  expenses = data.expenses || [];
  renderExpenses();
  updateTotal();

  if (!selectedCategory) {
    updateCategoryFilter(expenses);
  }
}

async function loadSummary() {
  const data = await request("/summary");
  renderChart(data.summary || []);
}

function renderExpenses() {
  expenseList.innerHTML = "";

  if (!expenses.length) {
    expenseList.innerHTML = '<div class="empty-state">No expenses found.</div>';
    return;
  }

  const fragment = document.createDocumentFragment();
  expenses.forEach((expense) => {
    const row = document.createElement("article");
    row.className = "expense-row";
    row.innerHTML = `
      <div class="expense-main">
        <strong>${escapeHtml(expense.category)}</strong>
        <span>${escapeHtml(expense.date || "")}</span>
      </div>
      <div class="expense-amount">${formatCurrency(expense.amount)}</div>
      <div class="expense-note">${escapeHtml(expense.note || "No note")}</div>
      <button class="delete-button" type="button" data-id="${escapeHtml(expense.expenseId)}">Delete</button>
    `;
    fragment.appendChild(row);
  });

  expenseList.appendChild(fragment);
}

function updateTotal() {
  const total = expenses.reduce((sum, expense) => sum + Number(expense.amount || 0), 0);
  totalAmount.textContent = formatCurrency(total);
}

function updateCategoryFilter(allExpenses) {
  const currentValue = categoryFilter.value;
  const categories = [...new Set(allExpenses.map((item) => item.category).filter(Boolean))].sort();

  categoryFilter.innerHTML = '<option value="">All</option>';
  categories.forEach((category) => {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    categoryFilter.appendChild(option);
  });

  categoryFilter.value = categories.includes(currentValue) ? currentValue : "";
}

function renderChart(summary) {
  const labels = summary.map((item) => item.month);
  const totals = summary.map((item) => Number(item.total || 0));
  const context = document.getElementById("summaryChart");

  if (summaryChart) {
    summaryChart.destroy();
  }

  summaryChart = new Chart(context, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Monthly Spend",
          data: totals,
          backgroundColor: "#176b87",
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => formatCurrency(value),
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function refreshData({ clearMessage = true } = {}) {
  setLoading(true);
  if (clearMessage) {
    setMessage("");
  }

  try {
    await Promise.all([loadExpenses(), loadSummary()]);
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    amount: amountInput.value,
    category: categoryInput.value.trim(),
    note: noteInput.value.trim(),
    date: dateInput.value,
  };

  const validationError = validateExpense(payload);
  if (validationError) {
    setMessage(validationError, "error");
    return;
  }

  setLoading(true);
  setMessage("");

  try {
    await request("/expense", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    form.reset();
    dateInput.value = new Date().toISOString().slice(0, 10);
    await refreshData({ clearMessage: false });
    setMessage("Expense added.", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setLoading(false);
  }
});

expenseList.addEventListener("click", async (event) => {
  const button = event.target.closest(".delete-button");
  if (!button) {
    return;
  }

  setLoading(true);
  setMessage("");

  try {
    await request(`/expense/${encodeURIComponent(button.dataset.id)}`, {
      method: "DELETE",
    });
    await refreshData({ clearMessage: false });
    setMessage("Expense deleted.", "success");
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    setLoading(false);
  }
});

categoryFilter.addEventListener("change", refreshData);

refreshData();
