async function get_transactions(budgetId, page = 1, pageSize = 20, accountId = null) {
  const offset = (page - 1) * pageSize;
  let url = `/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}`;
  const csrfToken = getCookie('csrftoken');

  if (accountId) {
    url += `&account_id=${accountId}`;
  }

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

async function patchTransaction(id, data) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/${id}`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    return responseData; // Return the parsed JSON data.
  } catch (error) {
    console.error('Error updating transaction:', error);
    throw error; // Rethrow the error to be handled by the caller.
  }
}

async function deleteTransaction(transaction_id) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/${transaction_id}`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json(); // or handle the response as needed
  } catch (error) {
    console.error('Error deleting transaction:', error);
    // Handle the error appropriately in your application
  }
}

function moneyFormat(value) {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  });
  return formatter.format(value / 1000);
}

async function updateAccountBalances() {
  const budgetId = getCookie('budget_id');
  const url = `/api/accounts/${budgetId}`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    for (const account of data) {
      const accountBalanceElement = document.getElementById(`id_account_balance_${account.id}`);
      if (accountBalanceElement) {
        accountBalanceElement.innerText = moneyFormat(account.balance);
      }
    }
  } catch (error) {
    console.error('Error updating account balances:', error);
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
    showEditForm: false,
    editableTransaction: { cleared: false },

    async fetchTransactions() {
      const budgetId = getCookie('budget_id');
      const accountId = getCookie('account_id');
      console.log('accountId:', accountId);
      try {
        const data = await get_transactions(budgetId, this.currentPage, this.transactionsPerPage, accountId);
        if (data?.items) {
          this.transactions = data.items.map(transaction => ({
            ...transaction,
            checked: false,
          }));
          this.totalTransactions = data.count;
        }
      } catch (error) {
        console.error('Error fetching transactions:', error);
      }
    },

    async importTransactions() {
      const budgetId = getCookie('budget_id');
      const accountId = document.getElementById('import_account_id').value;
      if (!accountId) {
        return;
      }
      const url = `/api/transactions/${budgetId}/${accountId}/import/ofx/file`;
      const csrfToken = getCookie('csrftoken');

      const formData = new FormData();
      const fileInput = document.getElementById('ofx_file');
      if (fileInput.files.length > 0) {
        formData.append('ofx_file', fileInput.files[0]);
      } else {
        return;
      }
      // turn button into spinner
      const importButton = document.getElementById('import-transactions-button');
      importButton.disabled = true;
      importButton.innerHTML = 'Importing...';

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
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
        console.error('Error posting file:', error);
      } finally {
        // turn button back into text
        importButton.disabled = false;
        importButton.innerHTML = 'Upload & Import';
        // Close dropdown
        const importDropdownButton = document.getElementById('importDropdownButton');
        importDropdownButton.click();
        // Reset file input
        document.getElementById('ofx_file').value = '';
      }
      updateAccountBalances();
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
      if ((type === 'outflow' && amount < 0) || (type === 'inflow' && amount >= 0)) {
        return (Math.abs(amount) / 1000).toFixed(2);
      }
      return '';
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
        .filter(transaction => transaction.checked)
        .map(transaction => transaction.id);

      this.transactions = this.transactions.filter(transaction => !transaction.checked);

      // Call the bulkDeleteTransactions function if there are IDs to delete
      if (idsToDelete.length > 0) {
        const deletePromises = idsToDelete.map(id => deleteTransaction(id));
        await Promise.all(deletePromises);
        this.fetchTransactions(); // Refresh the transaction list
      }
      updateAccountBalances();
    },

    editTransactionAtIndex(transaction, index, highlightField = 'account') {
      this.editableTransaction = { ...transaction };
      this.editableTransaction.inflow = this.formatAmount(transaction.amount, 'inflow');
      this.editableTransaction.outflow = this.formatAmount(transaction.amount, 'outflow');
      this.editableTransaction.payee = this.editableTransaction.payee.name;
      this.editableTransaction.account = transaction.account.id;
      if (transaction.envelope) {
        this.editableTransaction.envelope = transaction.envelope.id;
      }

      this.activeIndex = index;
      this.showEditForm = true;

      Alpine.nextTick(() => {
        const formFieldsRow = this.$refs.editForm;
        const formButtonsRow = this.$refs.editFormButtons;
        const allRows = document.querySelectorAll('.transaction-row');

        this.showAllTransactions();

        if (formFieldsRow && formButtonsRow && allRows.length > index) {
          allRows[index].after(formFieldsRow);
          formFieldsRow.after(formButtonsRow);
          allRows[index].classList.add('hidden');
        }

        const selectFields = ['date', 'payee', 'memo', 'inflow', 'outflow'];
        if (selectFields.includes(highlightField)) {
          document.getElementById(`id_${highlightField}`).select();
        } else {
          document.getElementById(`id_${highlightField}`).focus();
        }
      });
    },

    startNewTransaction() {
      if (!this.showEditForm) {
        this.editableTransaction = {
          account: '',
          amount: 0,
          approved: false,
          budget_id: getCookie('budget_id'),
          date: '',
          envelope: '',
          payee: '',
          memo: '',
          inflow: '',
          outflow: '',
          cleared: false,
        };
        this.showEditForm = true;
        this.activeIndex = -1;
        Alpine.nextTick(() => {
          document.getElementById('id_account').focus();

          // Move the form to the top of the table
          const formFieldsRow = this.$refs.editForm;
          const formButtonsRow = this.$refs.editFormButtons;
          const allRows = document.querySelectorAll('.transaction-row');
          allRows[0].before(formFieldsRow);
          formFieldsRow.after(formButtonsRow);
        });
      }
    },

    calculateAmount(type) {
      let input = this.editableTransaction[type];
      if (input.includes('+')) {
        const [a, b] = input.split('+');
        input = Number(a) + Number(b);
      } else if (input.includes('-')) {
        const [a, b] = input.split('-');
        input = Number(a) - Number(b);
      } else if (input.includes('*')) {
        const [a, b] = input.split('*');
        input = Number(a) * Number(b);
      } else if (input.includes('/')) {
        const [a, b] = input.split('/');
        input = Number(a) / Number(b);
      } else {
        input = Number(input);
      }
      if (Number.isNaN(input) || input === 0) {
        this.editableTransaction[type] = null;
        return;
      }
      if (type === 'outflow') {
        this.editableTransaction.inflow = null;
      } else {
        this.editableTransaction.outflow = null;
      }

      this.editableTransaction[type] = Math.abs(input).toFixed(2);
      this.editableTransaction.amount = this.editableTransaction[type] * 1000 * (type === 'outflow' ? -1 : 1);
    },

    async saveTransaction() {
      let url = `/api/transactions/${this.editableTransaction.budget_id}`;
      const csrfToken = getCookie('csrftoken');
      const date = new Date(document.querySelector('.editable-transaction-date').value);
      const formattedDate = date.toISOString().slice(0, 10);
      const postData = {
        account_id: this.editableTransaction.account,
        amount: this.editableTransaction.amount,
        approved: this.editableTransaction.approved,
        cleared: this.editableTransaction.cleared,
        date: formattedDate,
        memo: this.editableTransaction.memo,
        payee: this.editableTransaction.payee,
      };

      if (this.editableTransaction.envelope) {
        postData.envelope_id = this.editableTransaction.envelope;
      }

      if (this.editableTransaction.id) {
        url += `/${this.editableTransaction.id}`;
        try {
          const response = await fetch(url, {
            method: 'PUT',
            headers: {
              'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(postData),
          });
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const updatedTransaction = await response.json();
          this.transactions[this.activeIndex] = updatedTransaction;
          this.showEditForm = false;
          this.showAllTransactions();
        } catch (error) {
          console.error('Error posting file:', error);
        }
      } else {
        try {
          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(postData),
          });
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const newTransaction = await response.json();
          this.transactions.unshift(newTransaction);
          this.showEditForm = false;
          this.activeIndex = 0;
        } catch (error) {
          console.error('Error posting file:', error);
        }
      }
      updateAccountBalances();
    },

    showAllTransactions() {
      // remove hidden class from each row
      const allRows = document.querySelectorAll('.transaction-row');
      for (const row of allRows) {
        row.classList.remove('hidden');
      }
    },

    cancelTransaction() {
      if (this.showEditForm) {
        this.showEditForm = false;
        if (this.activeIndex < 0) {
          this.activeIndex = 0;
        }
        this.showAllTransactions();
      }
    },

    setupKeyboardShortcuts() {
      document.addEventListener('keydown', event => {
        // Check if the active element is the search input or any other input/textarea
        const activeElement = document.activeElement;
        const isInputActive =
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          activeElement.tagName === 'SELECT';

        if (event.key === 'Escape') {
          this.cancelTransaction();
        }

        // Save transaction on Enter key if form is active (except when in a textarea)
        if (event.key === 'Enter' && this.showEditForm && !(activeElement.tagName === 'TEXTAREA')) {
          // Prevent form submission if the enter was pressed in an input field
          if (isInputActive) {
            event.preventDefault();
          }
          this.saveTransaction();
          return;
        }

        // If user is typing in an input field, don't trigger other keyboard shortcuts
        if (isInputActive) {
          return;
        }

        if ((event.key === 'j' || event.key === 'k') && !this.showEditForm) {
          const newIndex = this.activeIndex + (event.key === 'j' ? 1 : -1);
          if (newIndex >= 0 && newIndex < this.transactions.length) {
            this.setActiveTransaction(newIndex);
          }
        } else if (event.key === 'a' && !this.showEditForm) {
          this.startNewTransaction();
        } else if (event.key === 'c') {
          this.toggleCleared(this.getActiveTransaction());
        } else if ((event.key === 'e' || event.key === 'Enter') && !this.showEditForm) {
          this.editTransactionAtIndex(this.getActiveTransaction(), this.activeIndex);
          // set envelope selector as active
          Alpine.nextTick(() => {
            document.getElementById('id_envelope').focus();
          });
        } else if (event.key === 'x') {
          this.toggleCheckboxInActiveRow();
        } else if (event.key === '#') {
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
