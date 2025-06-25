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

    // Split transaction properties
    isSplitMode: false,
    splitRows: [],
    splitTotal: 0,
    splitInflowTotal: 0,
    splitAmountsMatch: false,

    async loadSearchData() {
      try {
        const data = await SearchFunctions.loadSearchData();
        this.envelopes = data.envelopes;
        this.accounts = data.accounts;
      } catch (error) {
        console.error('Error loading search data:', error);
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
          if (this.selectedSuggestionIndex >= 0) {
            event.preventDefault();
            this.selectSuggestion(this.searchSuggestions[this.selectedSuggestionIndex]);
          }
          break;
      }
    },

    handleSearchEnter(event) {
      if (this.showSearchSuggestions && this.searchSuggestions.length > 0 && this.selectedSuggestionIndex >= 0) {
        event.preventDefault();
        event.stopPropagation();

        const selectedSuggestion = this.searchSuggestions[this.selectedSuggestionIndex];
        this.selectSuggestion(selectedSuggestion);
        return;
      }

      this.performSearch();
    },

    scrollToSelectedSuggestion() {
      this.$nextTick(() => {
        const dropdown = document.querySelector('.absolute.z-20.w-full.mt-1.bg-white');
        if (!dropdown) return;

        const selectedElement = dropdown.children[this.selectedSuggestionIndex];
        if (!selectedElement) return;

        const dropdownRect = dropdown.getBoundingClientRect();
        const elementRect = selectedElement.getBoundingClientRect();

        if (elementRect.top < dropdownRect.top) {
          selectedElement.scrollIntoView({ block: 'start', behavior: 'smooth' });
        }
        else if (elementRect.bottom > dropdownRect.bottom) {
          selectedElement.scrollIntoView({ block: 'end', behavior: 'smooth' });
        }
      });
    },

    generateSearchSuggestions() {
      this.searchSuggestions = SearchFunctions.generateSearchSuggestions(
        this.searchQuery, 
        this.envelopes, 
        this.accounts
      );
    },

    selectSuggestion(suggestion) {
      this.searchQuery = SearchFunctions.selectSuggestion(this.searchQuery, suggestion);
      this.showSearchSuggestions = false;
      this.selectedSuggestionIndex = -1;

      setTimeout(() => {
        const searchInput = document.getElementById('transaction-search');
        if (searchInput) {
          searchInput.focus();
          searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        }
      }, 10);

      this.performSearch();
    },

    hideSearchSuggestions() {
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
      TransactionOperations.pullSimpleFINTransactions(sfin_id);
    },

    async importTransactions() {
      await TransactionOperations.importTransactions(this.fetchTransactions.bind(this));
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
      return formatAmount(amount, type);
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
      const success = await TransactionOperations.archive(this.transactions, this.activeIndex, transaction);
      if (success) {
        this.fetchTransactions();
      }
    },

    async mergeSelectedTransactions() {
      const success = await TransactionOperations.mergeSelectedTransactions(this.transactions);
      if (success) {
        this.fetchTransactions();
      }
    },

    async deleteCheckedRows() {
      const success = await TransactionOperations.deleteCheckedRows(this.transactions);
      if (success) {
        this.fetchTransactions();
      }
    },

    editTransactionAtIndex(transaction, index, highlightField = 'account') {
      this.editableTransaction = { ...transaction };
      this.editableTransaction.inflow = this.formatAmount(transaction.amount, 'inflow');
      this.editableTransaction.outflow = this.formatAmount(transaction.amount, 'outflow');
      this.editableTransaction.account = transaction.account.id;
      if (transaction.envelope) {
        this.editableTransaction.envelope = transaction.envelope.id;
      }

      // Check if this is a split transaction
      if (transaction.subtransactions && transaction.subtransactions.length > 0) {
        this.isSplitMode = true;
        this.splitRows = transaction.subtransactions.map(sub => ({
          envelope: sub.envelope_id,
          memo: sub.memo || '',
          inflow: sub.amount > 0 ? (sub.amount / 1000).toFixed(2) : '',
          outflow: sub.amount < 0 ? (Math.abs(sub.amount) / 1000).toFixed(2) : '',
        }));
        this.validateSplitAmounts();
      } else {
        this.isSplitMode = false;
        this.splitRows = [];
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

          if (this.isSplitMode) {
            this.positionSplitRows();
          }
        }

        const selectFields = ['date', 'payee', 'memo', 'inflow', 'outflow'];
        if (selectFields.includes(highlightField)) {
          if (highlightField === 'payee') {
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

    async toBudget(transaction) {
      const success = await TransactionOperations.toBudget(this.transactions, this.activeIndex, transaction);
      if (success) {
        this.fetchTransactions();
      }
    },

    startNewTransaction() {
      if (!this.showEditForm) {
        const today = new Date();
        const todayString = today.toISOString().split('T')[0];

        this.editableTransaction = {
          account: '',
          amount: 0,
          budget_id: getCookie('budget_id'),
          date: todayString,
          envelope: '',
          cleared: false,
          pending: false,
          inflow: '',
          outflow: '',
          memo: '',
          payee: '',
        };
        this.activeIndex = -1;
        this.showEditForm = true;
        this.isSplitMode = false;
        this.splitRows = [];

        Alpine.nextTick(() => {
          const formFieldsRow = this.$refs.editForm;
          const formButtonsRow = this.$refs.editFormButtons;
          const firstTransactionRow = document.querySelector('.transaction-row');

          if (formFieldsRow && formButtonsRow && firstTransactionRow) {
            firstTransactionRow.before(formFieldsRow);
            formFieldsRow.after(formButtonsRow);
            document.getElementById('id_account').focus();
          }
        });
      } else {
        this.cancelTransaction();
      }
    },

    calculateAmount(type) {
      TransactionOperations.calculateAmount(this.editableTransaction, type);
    },

    // Split transaction methods
    toggleSplitMode() {
      this.isSplitMode = !this.isSplitMode;
      if (this.isSplitMode) {
        if (this.splitRows.length === 0) {
          this.addSplitRow();
        }
        Alpine.nextTick(() => {
          this.positionSplitRows();
        });
      }
      this.validateSplitAmounts();
    },

    addSplitRow() {
      this.splitRows.push(SplitTransactions.addSplitRow());
      Alpine.nextTick(() => {
        const newIndex = this.splitRows.length - 1;
        const envelopeSelect = document.getElementById(`id_split_envelope_${newIndex}`);
        if (envelopeSelect) {
          setTimeout(() => {
            const input = envelopeSelect.querySelector('input');
            if (input) input.focus();
          }, 100);
        }
        this.positionSplitRows();
      });
    },

    removeSplitRow(index) {
      this.splitRows.splice(index, 1);
      this.validateSplitAmounts();
      Alpine.nextTick(() => {
        this.positionSplitRows();
      });
    },

    validateSplitAmounts() {
      const result = SplitTransactions.validateSplitAmounts(this.splitRows, this.editableTransaction);
      this.splitTotal = result.splitOutflowTotal;
      this.splitInflowTotal = result.splitInflowTotal;
      this.splitAmountsMatch = result.amountsMatch;
    },

    positionSplitRows() {
      const formButtonsRow = this.$refs.editFormButtons;
      SplitTransactions.positionSplitRows(this.activeIndex, formButtonsRow);

      setTimeout(() => {
        this.initializeSplitEnvelopeSelectors();
      }, 100);
    },

    initializeSplitEnvelopeSelectors() {
      SplitTransactions.initializeSplitEnvelopeSelectors(this.splitRows);
    },

    async saveTransaction() {
      if (this.isSaving) return;
      this.isSaving = true;

      try {
        if (this.isSplitMode) {
          if (!this.splitAmountsMatch) {
            showToast('Split amounts must match the main transaction amount', 'error');
            return;
          }

          if (this.editableTransaction.id) {
            await this.updateSplitTransaction();
          } else {
            await this.saveSplitTransaction();
          }
          return;
        }

        if (this.editableTransaction.id && this.editableTransaction.subtransactions?.length > 0) {
          await this.convertSplitToRegular();
          return;
        }

        if (this.editableTransaction.inflow) {
          this.calculateAmount('inflow');
        } else if (this.editableTransaction.outflow) {
          this.calculateAmount('outflow');
        }

        let url = `/api/transactions/${this.editableTransaction.budget_id}`;
        const csrfToken = getCookie('csrftoken');
        const date = new Date(document.querySelector('.editable-transaction-date').value);
        const formattedDate = date.toISOString().slice(0, 10);

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
                'Content-Type': 'application/json',
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
        this.isSaving = false;
      }
    },

    async saveSplitTransaction() {
      try {
        if (this.editableTransaction.inflow) {
          this.calculateAmount('inflow');
        } else if (this.editableTransaction.outflow) {
          this.calculateAmount('outflow');
        }

        await SplitTransactions.saveSplitTransaction(this.editableTransaction, this.splitRows);

        this.showEditForm = false;
        this.isSplitMode = false;
        this.splitRows = [];
        this.activeIndex = 0;
        this.showAllTransactions();

        await this.fetchTransactions();
        showToast('Split transaction created successfully', 'success');
        updateAccountBalances();
      } catch (error) {
        console.error('Error creating split transaction:', error);
        showToast(`Error creating split transaction: ${error}`, 'error');
      }
    },

    async updateSplitTransaction() {
      try {
        if (this.editableTransaction.inflow) {
          this.calculateAmount('inflow');
        } else if (this.editableTransaction.outflow) {
          this.calculateAmount('outflow');
        }

        await SplitTransactions.updateSplitTransaction(this.editableTransaction, this.splitRows);

        this.showEditForm = false;
        this.isSplitMode = false;
        this.splitRows = [];
        this.showAllTransactions();

        await this.fetchTransactions();
        showToast('Split transaction updated successfully', 'success');
        updateAccountBalances();
      } catch (error) {
        console.error('Error updating split transaction:', error);
        showToast(`Error updating split transaction: ${error}`, 'error');
      }
    },

    async convertSplitToRegular() {
      try {
        if (this.editableTransaction.inflow) {
          this.calculateAmount('inflow');
        } else if (this.editableTransaction.outflow) {
          this.calculateAmount('outflow');
        }

        await SplitTransactions.convertSplitToRegular(this.editableTransaction);

        this.showEditForm = false;
        this.isSplitMode = false;
        this.splitRows = [];

        await this.fetchTransactions();
        showToast('Split transaction converted to regular transaction', 'success');
        updateAccountBalances();
      } catch (error) {
        console.error('Error converting split transaction:', error);
        showToast(`Error converting split transaction: ${error}`, 'error');
      }
    },

    showAllTransactions() {
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
        this.isSplitMode = false;
        this.splitRows = [];
        this.splitTotal = 0;
        this.splitInflowTotal = 0;
        this.splitAmountsMatch = false;
        this.showAllTransactions();
      }
    },

    async init() {
      await this.loadSearchData();
      this.fetchTransactions();
      if (typeof initKeyboardShortcuts === 'function') {
        initKeyboardShortcuts(this);
      }

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
        const amount = Number.parseFloat(this.transferData.amount) * 1000;
        await TransactionOperations.createTransfer(
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
      const transferAccountId = prompt('Enter the account ID to transfer to/from:');
      if (!transferAccountId) return;

      try {
        await TransactionOperations.markAsTransfer(transaction.id, transferAccountId, true);
        this.fetchTransactions();
        updateAccountBalances();
        showToast('Transaction marked as transfer');
      } catch (error) {
        console.error('Error marking as transfer:', error);
      }
    },
  };
}
