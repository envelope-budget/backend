async function get_transactions(budgetId, page = 1, pageSize = 20, accountId = null) {
  const offset = (page - 1) * pageSize;
  let url = `/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}&in_inbox=true`;
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

async function get_transactions_with_search(budgetId, page = 1, pageSize = 20, accountId = null, searchQuery = null) {
  const offset = (page - 1) * pageSize;
  let url = `/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}`;

  // If we're not searching, show inbox transactions by default
  if (!searchQuery) {
    url += '&in_inbox=true';
  }

  const csrfToken = getCookie('csrftoken');

  if (accountId) {
    url += `&account_id=${accountId}`;
  }

  // Add search query if provided
  if (searchQuery) {
    url += `&search=${encodeURIComponent(searchQuery)}`;
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

async function bulkArchiveTransactions(transaction_ids) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/archive`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ transaction_ids }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error archiving transactions:', error);
    showToast('Error archiving transactions');
    throw error;
  }
}

async function mergeTransactions(transaction_ids) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/merge`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ transaction_ids }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error merging transactions:', error);
    showToast(error.message || 'Error merging transactions');
    throw error;
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
    showToast('Error deleting transaction');
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
    showToast('Error updating account balances');
    console.error('Error updating account balances:', error);
    throw error; // Rethrow the error to be handled by the caller.
  }
}

function transactionData() {
  return {
    activeIndex: 0,
    transactions: [],
    totalTransactions: null,
    currentPage: 1,
    transactionsPerPage: 20,
    showEditForm: false,
    editableTransaction: { cleared: false },
    searchQuery: '',
    showSearchHelp: false,
    isSearching: false,
    isSaving: false,
    showTransferForm: false,
    transferData: {
      fromAccount: '',
      toAccount: '',
      amount: '',
      date: '',
      memo: '',
    },
    // New search suggestion properties
    showSearchSuggestions: false,
    searchSuggestions: [],
    selectedSuggestionIndex: -1,
    envelopes: [],
    accounts: [],

    async loadSearchData() {
      try {
        // Use the shared envelope data manager if available
        if (window.envelopeDataManager) {
          const data = await window.envelopeDataManager.loadData();
          this.envelopes = data.envelopes;
          this.accounts = data.accounts;
        } else {
          // Fallback to direct loading if manager not available
          await this.loadSearchDataFallback();
        }
      } catch (error) {
        console.error('Error loading search data:', error);
        // Try fallback method
        await this.loadSearchDataFallback();
      }
    },

    async loadSearchDataFallback() {
      try {
        // Load envelopes data directly
        const envelopeResponse = await fetch('/envelopes/categorized_envelopes.json');
        const envelopeData = await envelopeResponse.json();
        this.envelopes = envelopeData.categorized_envelopes.flatMap(category =>
          category.envelopes.map(envelope => ({
            id: envelope.id,
            name: envelope.name,
            categoryName: category.category.name,
          }))
        );

        // Load accounts data from the existing dropdown options
        const accountSelect = document.getElementById('id_account');
        if (accountSelect) {
          this.accounts = Array.from(accountSelect.options)
            .filter(option => option.value && option.value !== '')
            .map(option => ({
              id: option.value,
              name: option.textContent,
            }));
        }
      } catch (error) {
        console.error('Error in fallback search data loading:', error);
      }
    },

    handleSearchInput() {
      if (this.searchQuery.length === 0) {
        this.showSearchSuggestions = false;
        this.searchSuggestions = [];
        return;
      }

      this.generateSearchSuggestions();
      this.selectedSuggestionIndex = -1;
      this.showSearchSuggestions = true;
    },

    handleSearchKeydown(event) {
      if (!this.showSearchSuggestions || this.searchSuggestions.length === 0) {
        return;
      }

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          this.selectedSuggestionIndex = Math.min(this.selectedSuggestionIndex + 1, this.searchSuggestions.length - 1);
          this.scrollToSelectedSuggestion();
          break;

        case 'ArrowUp':
          event.preventDefault();
          this.selectedSuggestionIndex = Math.max(this.selectedSuggestionIndex - 1, -1);
          this.scrollToSelectedSuggestion();
          break;

        case 'Enter':
          if (this.selectedSuggestionIndex >= 0) {
            event.preventDefault();
            this.selectSuggestion(this.searchSuggestions[this.selectedSuggestionIndex]);
          }
          break;

        case 'Escape':
          this.showSearchSuggestions = false;
          this.selectedSuggestionIndex = -1;
          break;

        case 'Tab':
          // Allow tab to select current suggestion if one is highlighted
          if (this.selectedSuggestionIndex >= 0) {
            event.preventDefault();
            this.selectSuggestion(this.searchSuggestions[this.selectedSuggestionIndex]);
          }
          break;
      }
    },

    scrollToSelectedSuggestion() {
      // Use Alpine's nextTick to ensure DOM is updated
      this.$nextTick(() => {
        const dropdown = document.querySelector('.absolute.z-20.w-full.mt-1.bg-white');
        if (!dropdown) return;

        const selectedElement = dropdown.children[this.selectedSuggestionIndex];
        if (!selectedElement) return;

        // Calculate if the element is visible in the dropdown
        const dropdownRect = dropdown.getBoundingClientRect();
        const elementRect = selectedElement.getBoundingClientRect();

        // Check if element is above the visible area
        if (elementRect.top < dropdownRect.top) {
          selectedElement.scrollIntoView({ block: 'start', behavior: 'smooth' });
        }
        // Check if element is below the visible area
        else if (elementRect.bottom > dropdownRect.bottom) {
          selectedElement.scrollIntoView({ block: 'end', behavior: 'smooth' });
        }
      });
    },

    generateSearchSuggestions() {
      const suggestions = [];
      const currentTerm = this.getCurrentSearchTerm();

      if (!currentTerm) {
        this.searchSuggestions = [];
        return;
      }

      const lowerTerm = currentTerm.toLowerCase();

      // Number-based suggestions (amount, inflow, outflow)
      const numberMatch = currentTerm.match(/^-?\d+\.?\d{0,2}$/);
      if (numberMatch) {
        const value = numberMatch[0];
        // Add outflow suggestions first (most common)
        suggestions.push(
          {
            display: `outflow:${value}`,
            description: 'Exact outflow amount',
            type: 'amount',
            value: `outflow:${value}`,
            priority: 1,
          },
          {
            display: `outflow:>${value}`,
            description: 'Outflow greater than',
            type: 'amount',
            value: `outflow:>${value}`,
            priority: 2,
          },
          {
            display: `outflow:>=${value}`,
            description: 'Outflow greater than or equal',
            type: 'amount',
            value: `outflow:>=${value}`,
            priority: 3,
          },
          {
            display: `outflow:<${value}`,
            description: 'Outflow less than',
            type: 'amount',
            value: `outflow:<${value}`,
            priority: 4,
          },
          {
            display: `outflow:<=${value}`,
            description: 'Outflow less than or equal',
            type: 'amount',
            value: `outflow:<=${value}`,
            priority: 5,
          },
          {
            display: `inflow:${value}`,
            description: 'Exact inflow amount',
            type: 'amount',
            value: `inflow:${value}`,
            priority: 6,
          },
          {
            display: `inflow:>${value}`,
            description: 'Inflow greater than',
            type: 'amount',
            value: `inflow:>${value}`,
            priority: 7,
          },
          {
            display: `inflow:>=${value}`,
            description: 'Inflow greater than or equal',
            type: 'amount',
            value: `inflow:>=${value}`,
            priority: 8,
          }
        );
      } else {
        // Status and location filters
        const statusFilters = [
          { key: 'is:cleared', description: 'Cleared transactions' },
          { key: 'is:uncleared', description: 'Uncleared transactions' },
          { key: 'is:pending', description: 'Pending transactions' },
          { key: 'is:unassigned', description: 'Unassigned transactions' },
          { key: 'in:inbox', description: 'Transactions in inbox' },
          { key: 'in:trash', description: 'Transactions in trash' },
        ];

        for (const filter of statusFilters) {
          if (filter.key.toLowerCase().includes(lowerTerm)) {
            suggestions.push({
              display: filter.key,
              description: filter.description,
              type: 'filter',
              value: filter.key,
              priority: 100,
            });
          }
        }

        // Envelope suggestions
        for (const envelope of this.envelopes) {
          if (envelope.name.toLowerCase().includes(lowerTerm)) {
            suggestions.push({
              display: `envelope:${envelope.name}`,
              description: `Filter by ${envelope.categoryName} envelope`,
              type: 'envelope',
              value: `envelope:${envelope.name}`,
              priority: 200,
            });
          }
        }

        // Account suggestions
        for (const account of this.accounts) {
          if (account.name.toLowerCase().includes(lowerTerm)) {
            suggestions.push({
              display: `account:${account.name}`,
              description: 'Filter by account',
              type: 'account',
              value: `account:${account.name}`,
              priority: 300,
            });
          }
        }

        // Sort non-number suggestions by relevance (exact matches first, then partial matches)
        suggestions.sort((a, b) => {
          const aExact = a.display.toLowerCase().startsWith(lowerTerm);
          const bExact = b.display.toLowerCase().startsWith(lowerTerm);

          if (aExact && !bExact) return -1;
          if (!aExact && bExact) return 1;

          // Then by priority, then alphabetically
          if (a.priority !== b.priority) return a.priority - b.priority;
          return a.display.localeCompare(b.display);
        });
      }

      this.searchSuggestions = suggestions.slice(0, 8); // Limit to 8 suggestions for better UX
    },
    getCurrentSearchTerm() {
      const terms = this.searchQuery.split(',');
      const currentTerm = terms[terms.length - 1].trim();
      return currentTerm;
    },

    selectSuggestion(suggestion) {
      const terms = this.searchQuery.split(',');
      // Replace the last term with the selected suggestion
      terms[terms.length - 1] = ` ${suggestion.value}`;
      this.searchQuery = terms.join(',').trim();

      // Add a space and comma if this isn't the first term, to prepare for next input
      if (terms.length === 1) {
        this.searchQuery += ', ';
      } else {
        this.searchQuery += ', ';
      }

      this.showSearchSuggestions = false;
      this.selectedSuggestionIndex = -1;

      // Focus back on the input
      setTimeout(() => {
        const searchInput = document.getElementById('transaction-search');
        if (searchInput) {
          searchInput.focus();
          // Move cursor to end
          searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        }
      }, 10);

      // Trigger search
      this.performSearch();
    },

    hideSearchSuggestions() {
      // Add a small delay to allow for suggestion clicks
      setTimeout(() => {
        this.showSearchSuggestions = false;
        this.selectedSuggestionIndex = -1;
      }, 150);
    },

    async performSearch() {
      this.currentPage = 1;
      this.isSearching = !!this.searchQuery.trim();
      await this.fetchTransactions();
    },

    async fetchTransactions() {
      const budgetId = getCookie('budget_id');
      const accountId = getCookie('account_id');

      try {
        // Use the search-enabled function
        const data = await get_transactions_with_search(
          budgetId,
          this.currentPage,
          this.transactionsPerPage,
          accountId,
          this.searchQuery
        );

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

    pullSimpleFINTransactions(sfin_id) {
      const budgetId = getCookie('budget_id');

      // Base endpoint
      let endpoint = `/api/accounts/${budgetId}/simplefin/transactions`;

      // If we're on an account view, add the account_id parameter
      if (sfin_id) {
        endpoint += `?account_id=${sfin_id}`;
      }

      // Get button element
      const button = document.getElementById('pull-simplefin-button');

      // Disable button and show spinner
      if (button) {
        button.disabled = true;
        const buttonText = button.querySelector('span');
        const originalText = buttonText.textContent;

        // Replace text with spinner and loading text
        buttonText.innerHTML = `
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Pulling...
        `;
      }

      fetch(endpoint)
        .then(response => response.json())
        .then(data => {
          if (data.errors && data.errors.length > 0) {
            // Display errors if any
            showToast(`Error pulling transactions: ${data.errors.join(', ')}`);

            // Reset button
            if (button) {
              button.disabled = false;
              button.querySelector('span').textContent = 'Pull';
            }
          } else {
            // Success - reload the page to show new transactions
            window.location.reload();
          }
        })
        .catch(error => {
          console.error('Error pulling SimpleFIN transactions:', error);
          showToast(`Failed to pull transactions: ${error.message}`);

          // Reset button
          if (button) {
            button.disabled = false;
            button.querySelector('span').textContent = 'Pull';
          }
        });
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

    clearSearch() {
      this.searchQuery = '';
      this.isSearching = false;
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

        // If marking as cleared, remove pending status
        if (transaction.cleared && transaction.pending) {
          transaction.pending = false;
        }

        if (transaction.id) {
          patchTransaction(transaction.id, {
            cleared: transaction.cleared,
          });
        }
      }
    },

    async archive(transaction) {
      let idsToArchive = [];
      if (transaction) {
        idsToArchive = [transaction.id];
      } else {
        // Gather IDs of checked transactions that have envelopes and are cleared
        idsToArchive = this.transactions
          .filter(transaction => transaction.checked && transaction.envelope && transaction.cleared)
          .map(transaction => transaction.id);

        if (this.transactions.filter(transaction => transaction.checked).length === 0) {
          const activeTransaction = this.transactions[this.activeIndex];
          if (activeTransaction?.envelope && activeTransaction.cleared) {
            idsToArchive = [activeTransaction.id];
          } else {
            showToast('Please select transactions with envelopes and are cleared');
            return;
          }
        }
      }

      const skippedTransactions = this.transactions.filter(
        transaction => transaction.checked && (!transaction.envelope || !transaction.cleared)
      ).length;

      if (idsToArchive.length > 0) {
        await bulkArchiveTransactions(idsToArchive);
        this.fetchTransactions(); // Refresh the transaction list
        if (skippedTransactions > 0) {
          showToast(`${skippedTransactions} transaction(s) skipped - must have envelope assigned and be cleared`);
        }
      } else {
        if (skippedTransactions > 0) {
          showToast('Selected transactions must have envelope assigned and be cleared');
        } else {
          showToast('No transactions selected to archive');
        }
      }
    },

    async mergeSelectedTransactions() {
      // Get IDs of checked transactions
      const checkedTransactions = this.transactions.filter(transaction => transaction.checked);

      if (checkedTransactions.length !== 2) {
        showToast('Please select exactly 2 transactions to merge');
        return;
      }

      const idsToMerge = checkedTransactions.map(transaction => transaction.id);

      try {
        await mergeTransactions(idsToMerge);
        showToast('Transactions merged successfully');
        this.fetchTransactions(); // Refresh the transaction list
        updateAccountBalances();
      } catch (error) {
        // Error is already handled in mergeTransactions function
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
      } else {
        showToast('No transactions selected to delete');
      }
      updateAccountBalances();
    },

    editTransactionAtIndex(transaction, index, highlightField = 'account') {
      this.editableTransaction = { ...transaction };
      this.editableTransaction.inflow = this.formatAmount(transaction.amount, 'inflow');
      this.editableTransaction.outflow = this.formatAmount(transaction.amount, 'outflow');
      // Keep the payee as an object instead of converting to string
      // this.editableTransaction.payee = this.editableTransaction.payee.name; // Remove this line
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
          if (highlightField === 'payee') {
            // Handle payee field specially since it's a custom element
            setTimeout(() => {
              const payeeSelect = document.getElementById('id_payee');
              if (payeeSelect?.input) {
                payeeSelect.input.focus();
                payeeSelect.input.select();
              }
            }, 100);
          } else {
            document.getElementById(`id_${highlightField}`).select();
          }
        } else if (highlightField === 'envelope') {
          setTimeout(() => {
            document.getElementById('id_envelope').querySelector('input').focus();
          }, 100);
        } else {
          document.getElementById(`id_${highlightField}`).focus();
        }
      });
    },

    toBudget(transaction) {
      const unallocatedId = document.getElementById('unallocated_funds_envelope_id').value;
      const budgetId = getCookie('budget_id');

      let transactionIds = [];
      if (transaction) {
        transactionIds = [transaction.id];
      } else {
        // Get checked transaction IDs or active transaction ID
        transactionIds = this.transactions
          .filter(transaction => transaction.checked)
          .map(transaction => transaction.id);

        console.log('Checked transactions:', transactionIds);

        // If no transactions are checked, get the active transaction ID
        if (transactionIds.length === 0 && this.activeIndex !== -1) {
          console.log('Active transaction:', this.activeIndex);
          const activeTransaction = this.transactions[this.activeIndex];
          if (activeTransaction) {
            transactionIds = [activeTransaction.id];
          }
        }
      }

      console.log('Transaction IDs:', transactionIds);

      // Filter out transactions with negative amounts and show toast if any were ignored
      const validTransactions = this.transactions.filter(t => transactionIds.includes(t.id)).filter(t => t.amount >= 0);

      const ignoredCount = transactionIds.length - validTransactions.length;
      if (ignoredCount > 0) {
        showToast(`${ignoredCount} outflow transaction${ignoredCount === 1 ? ' was' : 's were'} ignored`);
      }

      transactionIds = validTransactions.map(t => t.id);

      // Update transactions with unallocated envelope ID
      if (transactionIds.length > 0) {
        const updatePromises = transactionIds.map(id =>
          fetch(`/api/transactions/${budgetId}/${id}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
              envelope_id: unallocatedId,
              in_inbox: false,
            }),
          })
        );

        Promise.all(updatePromises)
          .then(() => {
            this.fetchTransactions();
            updateAccountBalances();
          })
          .catch(error => {
            console.error('Error updating transactions:', error);
            showToast('Error updating transactions');
          });
      }
    },

    startNewTransaction() {
      if (!this.showEditForm) {
        // Get today's date in YYYY-MM-DD format
        const today = new Date();
        const todayString = today.toISOString().split('T')[0];

        this.editableTransaction = {
          account: '',
          amount: 0,
          budget_id: getCookie('budget_id'),
          date: todayString, // Prepopulate with today's date
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
          const $account = document.getElementById('id_account');
          const active_account_id = document.querySelector('[x-account-id]')?.getAttribute('x-account-id') || '';
          if (active_account_id) {
            this.editableTransaction.account = active_account_id;
            $account.value = active_account_id;
          }

          // Move the form to the top of the table
          const formFieldsRow = this.$refs.editForm;
          const formButtonsRow = this.$refs.editFormButtons;
          const allRows = document.querySelectorAll('.transaction-row');
          allRows[0].before(formFieldsRow);
          formFieldsRow.after(formButtonsRow);

          // Focus on payee field if account is pre-populated, otherwise focus on account field
          if (active_account_id) {
            setTimeout(() => {
              const payeeSelect = document.getElementById('id_payee');
              if (payeeSelect?.input) {
                payeeSelect.input.focus();
              }
            }, 100);
          } else {
            $account.focus();
          }
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
      this.editableTransaction.amount = Number.parseInt(
        this.editableTransaction[type] * 1000 * (type === 'outflow' ? -1 : 1)
      );
    },

    async saveTransaction() {
      // Add a guard to prevent double submission
      if (this.isSaving) return;
      this.isSaving = true;

      try {
        // Calculate amount from inflow/outflow before saving
        if (this.editableTransaction.inflow) {
          this.calculateAmount('inflow');
        } else if (this.editableTransaction.outflow) {
          this.calculateAmount('outflow');
        }

        let url = `/api/transactions/${this.editableTransaction.budget_id}`;
        const csrfToken = getCookie('csrftoken');
        const date = new Date(document.querySelector('.editable-transaction-date').value);
        const formattedDate = date.toISOString().slice(0, 10);

        // Handle payee - extract the name from the payee object
        let payeeName = '';
        if (this.editableTransaction.payee) {
          if (typeof this.editableTransaction.payee === 'string') {
            payeeName = this.editableTransaction.payee;
          } else if (this.editableTransaction.payee.name) {
            payeeName = this.editableTransaction.payee.name;
          }
        }

        const postData = {
          account_id: this.editableTransaction.account,
          amount: this.editableTransaction.amount,
          cleared: this.editableTransaction.cleared,
          date: formattedDate,
          memo: this.editableTransaction.memo,
          payee: payeeName,
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
                'Content-Type': 'application/json',
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
            console.error('Error updating transaction:', error);
            showToast(`Error updating transaction: ${error}`, 'error');
          }
        } else {
          try {
            const response = await fetch(url, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json', // Add this header
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
            showToast(`Error creating transaction: ${error}`, 'error');
          }
        }
        updateAccountBalances();
      } finally {
        // Reset the saving flag
        this.isSaving = false;
      }
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

    async init() {
      await this.loadSearchData();
      this.fetchTransactions();
      initKeyboardShortcuts(this);

      // Add event listener for URL params
      const urlParams = new URLSearchParams(window.location.search);
      const searchParam = urlParams.get('search');
      if (searchParam) {
        this.searchQuery = searchParam;
        this.performSearch();
      }
    },

    startNewTransfer() {
      this.transferData = {
        fromAccount: '',
        toAccount: '',
        amount: '',
        date: new Date().toISOString().slice(0, 10),
        memo: '',
      };
      this.showTransferForm = true;

      Alpine.nextTick(() => {
        document.getElementById('transfer_from_account').focus();
      });
    },

    async saveTransfer() {
      if (!this.transferData.fromAccount || !this.transferData.toAccount || !this.transferData.amount) {
        showToast('Please fill in all required fields');
        return;
      }

      if (this.transferData.fromAccount === this.transferData.toAccount) {
        showToast('From and To accounts must be different');
        return;
      }

      try {
        const amount = Number.parseFloat(this.transferData.amount) * 1000; // Convert to milliunits
        await createTransfer(
          this.transferData.fromAccount,
          this.transferData.toAccount,
          amount,
          this.transferData.date,
          this.transferData.memo
        );

        this.showTransferForm = false;
        this.fetchTransactions();
        updateAccountBalances();
        showToast('Transfer created successfully');
      } catch (error) {
        console.error('Error saving transfer:', error);
      }
    },

    cancelTransfer() {
      this.showTransferForm = false;
    },

    async markTransactionAsTransfer(transaction) {
      // Show account selection modal or prompt
      const transferAccountId = prompt('Enter the account ID to transfer to/from:');
      if (!transferAccountId) return;

      try {
        await markAsTransfer(transaction.id, transferAccountId, true);
        this.fetchTransactions();
        updateAccountBalances();
        showToast('Transaction marked as transfer');
      } catch (error) {
        console.error('Error marking as transfer:', error);
      }
    },
  };
}

async function createTransfer(fromAccountId, toAccountId, amount, date, memo = '') {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/transfer`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        from_account_id: fromAccountId,
        to_account_id: toAccountId,
        amount: amount,
        date: date,
        memo: memo,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error creating transfer:', error);
    showToast('Error creating transfer');
    throw error;
  }
}

async function markAsTransfer(transactionId, transferAccountId, createCounterpart = true) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/${transactionId}/mark-transfer`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        transfer_account_id: transferAccountId,
        create_counterpart: createCounterpart,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error marking as transfer:', error);
    showToast('Error marking as transfer');
    throw error;
  }
}
