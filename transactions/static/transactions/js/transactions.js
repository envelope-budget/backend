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

async function patchTransaction(id, data) {
  const budgetId = getCookie("budget_id");
  const url = `http://localhost:8007/api/transactions/${budgetId}/${id}`;
  const csrfToken = getCookie("csrftoken");

  try {
    const response = await fetch(url, {
      method: "PATCH",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    return responseData; // Return the parsed JSON data.
  } catch (error) {
    console.error("Error updating transaction:", error);
    throw error; // Rethrow the error to be handled by the caller.
  }
}

function transactionData() {
  return {
    activeIndex: 0,
    transactions: [],
    totalTransactions: 0,
    currentPage: 1,
    transactionsPerPage: 20,

    async fetchTransactions() {
      const budgetId = getCookie("budget_id");
      try {
        const data = await get_transactions(budgetId, this.currentPage, this.transactionsPerPage);
        if (data && data.items) {
          this.transactions = data.items.map((transaction) => ({
            ...transaction,
            checked: false,
          }));
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

    setActiveTransaction(index) {
      this.activeIndex = index;
    },

    toggleCheckboxInActiveRow() {
      if (this.activeIndex > -1 && this.activeIndex < this.transactions.length) {
        this.transactions[this.activeIndex].checked = !this.transactions[this.activeIndex].checked;
      }
    },

    toggleCleared(transaction) {
      transaction.cleared = !transaction.cleared;
      patchTransaction(transaction.id, {
        cleared: transaction.cleared,
      });
    },

    deleteCheckedRows() {
      this.transactions = this.transactions.filter((transaction) => !transaction.checked);
      this.fetchTransactions();
    },

    setupKeyboardShortcuts() {
      document.addEventListener("keydown", (event) => {
        if (event.key === "j" || event.key === "k") {
          let newIndex = this.activeIndex + (event.key === "j" ? 1 : -1);
          if (newIndex >= 0 && newIndex < this.transactions.length) {
            this.setActiveTransaction(newIndex);
          }
        } else if (event.key === "c") {
          if (this.activeIndex > -1 && this.activeIndex < this.transactions.length) {
            this.toggleCleared(this.transactions[this.activeIndex]);
          }
        } else if (event.key === "x") {
          this.toggleCheckboxInActiveRow();
        } else if (event.key === "#") {
          this.deleteCheckedRows();
        }
      });
    },

    init() {
      this.fetchTransactions();
      this.setupKeyboardShortcuts();
    },
  };
}
