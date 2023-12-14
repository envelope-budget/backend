function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function get_transactions(budgetId, page = 1, pageSize = 20) {
  const offset = (page - 1) * pageSize;
  const url = `http://localhost:8007/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}`;
  const csrfToken = getCookie("csrftoken");

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "X-CSRFToken": csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

function transactionData() {
  return {
    transactions: [],
    totalTransactions: 0,
    currentPage: 1,
    transactionsPerPage: 25,

    async fetchTransactions() {
      const budgetId = getCookie("budget_id");
      try {
        const data = await get_transactions(budgetId, this.currentPage, this.transactionsPerPage);
        if (data && data.items) {
          this.transactions = data.items;
          this.totalTransactions = data.count;
        }
      } catch (error) {
        console.error("Error fetching transactions:", error);
      }
    },

    get totalPages() {
      return Math.ceil(this.totalTransactions / this.transactionsPerPage);
    },

    changePage(page) {
      this.currentPage = page;
      this.fetchTransactions();
    },

    formatAmount(amount, type) {
      if ((type === "outflow" && amount < 0) || (type === "inflow" && amount >= 0)) {
        return (Math.abs(amount) / 1000).toFixed(2);
      }
      return "";
    },

    init() {
      this.fetchTransactions();
    },
  };
}
