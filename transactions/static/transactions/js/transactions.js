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
  const url = `/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}`;
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
  const url = `/api/transactions/${budgetId}/${id}`;
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

async function deleteTransaction(transaction_id) {
  const budgetId = getCookie("budget_id");
  const url = `/api/transactions/${budgetId}/${transaction_id}`;
  const csrfToken = getCookie("csrftoken");

  try {
    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        "X-CSRFToken": csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json(); // or handle the response as needed
  } catch (error) {
    console.error("Error deleting transaction:", error);
    // Handle the error appropriately in your application
  }
}

function transactionData() {
  return {
    activeIndex: 0,
    transactions: [],
    totalTransactions: 0,
    currentPage: 1,
    transactionsPerPage: 20,
    showNewTransactionForm: false,
    editableTransaction: { cleared: false },

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

    async importTransactions() {
      const budgetId = getCookie("budget_id");
      const accountId = document.getElementById("import_account_id").value;
      if (!accountId) {
        return;
      }
      const url = `/api/transactions/${budgetId}/${accountId}/import/ofx/file`;
      const csrfToken = getCookie("csrftoken");

      const formData = new FormData();
      const fileInput = document.getElementById("ofx_file");
      if (fileInput.files.length > 0) {
        formData.append("ofx_file", fileInput.files[0]);
      } else {
        return;
      }
      // turn button into spinner
      const importButton = document.getElementById("import-transactions-button");
      importButton.disabled = true;
      importButton.innerHTML = "Importing...";

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        resp = await response.json();
        const message = `Import complete. ${resp.created_ids.length} transactions imported. ${resp.duplicate_ids.length} transactions skipped.`;
        console.log(message);
        this.fetchTransactions(); // Reload transactions
      } catch (error) {
        console.error("Error posting file:", error);
      } finally {
        // turn button back into text
        importButton.disabled = false;
        importButton.innerHTML = "Upload & Import";
        // Close dropdown
        const importDropdownButton = document.getElementById("importDropdownButton");
        importDropdownButton.click();
        // Reset file input
        document.getElementById("ofx_file").value = "";
      }
    },

    get totalPages() {
      return Math.ceil(this.totalTransactions / this.transactionsPerPage);
    },

    getActiveTransaction() {
      if (this.activeIndex > -1 && this.activeIndex < this.transactions.length) {
        return this.transactions[this.activeIndex];
      }
      return null;
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
      if (transaction) {
        transaction.cleared = !transaction.cleared;
        if (transaction.id) {
          patchTransaction(transaction.id, {
            cleared: transaction.cleared,
          });
        }
      }
    },

    async deleteCheckedRows() {
      // Gather IDs of checked transactions
      const idsToDelete = this.transactions
        .filter((transaction) => transaction.checked)
        .map((transaction) => transaction.id);

      this.transactions = this.transactions.filter((transaction) => !transaction.checked);

      // Call the bulkDeleteTransactions function if there are IDs to delete
      if (idsToDelete.length > 0) {
        for (const id of idsToDelete) {
          await deleteTransaction(id);
        }
        this.fetchTransactions(); // Refresh the transaction list
      }
    },

    editTransaction(transaction) {
      console.log("Editing transaction:", transaction);
      this.editableTransaction = transaction;
    },

    startNewTransaction() {
      if (!this.showNewTransactionForm) {
        this.editableTransaction = {
          account: null,
          amount: 0,
          approved: false,
          budget_id: getCookie("budget_id"),
          date: null,
          envelope: null,
          payee: null,
          memo: "",
          inflow: null,
          outflow: null,
          cleared: false,
        };
        this.showNewTransactionForm = true;
        this.activeIndex = -1;
      }
    },

    cancelNewTransaction() {
      if (this.showNewTransactionForm) {
        this.showNewTransactionForm = false;
        this.activeIndex = 0;
      }
    },

    setupKeyboardShortcuts() {
      document.addEventListener("keydown", (event) => {
        if ((event.key === "j" || event.key === "k") && !this.showNewTransactionForm) {
          let newIndex = this.activeIndex + (event.key === "j" ? 1 : -1);
          if (newIndex >= 0 && newIndex < this.transactions.length) {
            this.setActiveTransaction(newIndex);
          }
        } else if (event.key === "a") {
          this.startNewTransaction();
        } else if (event.key === "c") {
          this.toggleCleared(this.getActiveTransaction());
        } else if (event.key === "e") {
          this.editTransaction(this.getActiveTransaction());
        } else if (event.key === "x") {
          this.toggleCheckboxInActiveRow();
        } else if (event.key === "#") {
          this.deleteCheckedRows();
        } else if (event.key === "Escape") {
          this.cancelNewTransaction();
        }
      });
    },

    init() {
      this.fetchTransactions();
      this.setupKeyboardShortcuts();
    },
  };
}
