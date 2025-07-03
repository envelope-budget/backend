const TransactionOperations = {
  calculateAmount(editableTransaction, type) {
    const value = editableTransaction[type];
    if (value !== '') {
      const amount = Number.parseFloat(value) * 1000;
      editableTransaction.amount = type === 'outflow' ? -amount : amount;
      editableTransaction[type === 'outflow' ? 'inflow' : 'outflow'] = '';
    }
  },

  pullSimpleFINTransactions(sfin_id, fetchTransactions) {
    const budgetId = getCookie('budget_id');

    let endpoint = `/api/accounts/${budgetId}/simplefin/transactions`;

    if (sfin_id) {
      endpoint += `?account_id=${sfin_id}`;
    }

    const button = document.getElementById('pull-simplefin-button');
    const buttonText = button.querySelector('span');

    if (button) {
      button.disabled = true;

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
      .then(async data => {
        if (data.errors && data.errors.length > 0) {
          showToast(`Error pulling transactions: ${data.errors.join(', ')}`);

          if (button) {
            button.disabled = false;
            buttonText.innerHTML = 'Pull';
          }
        } else {
          // Check for duplicates if new transactions were created
          if (data.created_ids && data.created_ids.length > 0) {
            try {
              const duplicateData = await DuplicateDetection.checkForDuplicates(data.created_ids);
              if (duplicateData.duplicate_groups.length > 0) {
                showToast(`Found ${duplicateData.total_groups} potential duplicate groups`);
                // Show modal with callback to refresh transactions when modal is closed
                DuplicateDetection.showDuplicatesModal(duplicateData.duplicate_groups, () => {
                  if (typeof fetchTransactions === 'function') {
                    fetchTransactions();
                  }
                });
                button.disabled = false;
                buttonText.innerHTML = 'Pull';
                return;
              }
            } catch (error) {
              console.error('Error checking for duplicates after pull:', error);
            }
          }
          // Only refresh transactions if no duplicates were found or if duplicate check failed
          if (typeof fetchTransactions === 'function') {
            fetchTransactions();
          }

          button.disabled = false;
          buttonText.innerHTML = 'Pull';
        }
      })
      .catch(error => {
        console.error('Error pulling SimpleFIN transactions:', error);
        showToast(`Failed to pull transactions: ${error.message}`);

        if (button) {
          button.disabled = false;
          buttonText.innerHTML = 'Pull';
        }
      });
  },

  async importTransactions(fetchTransactions) {
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

      const resp = await response.json();
      const message = `Import complete. ${resp.created_ids.length} transactions imported. ${resp.duplicate_ids.length} transactions skipped.`;
      console.log(message);
      fetchTransactions();

      // Check for duplicates among newly imported transactions
      if (resp.created_ids.length > 0) {
        setTimeout(async () => {
          try {
            const duplicateData = await DuplicateDetection.checkForDuplicates(resp.created_ids);
            if (duplicateData.duplicate_groups.length > 0) {
              showToast(`Found ${duplicateData.total_groups} potential duplicate groups`);
              DuplicateDetection.showDuplicatesModal(duplicateData.duplicate_groups);
            }
          } catch (error) {
            console.error('Error checking for duplicates after import:', error);
          }
        }, 1000);
      }
    } catch (error) {
      console.error('Error posting file:', error);
    } finally {
      importButton.disabled = false;
      importButton.innerHTML = 'Upload & Import';
      const importDropdownButton = document.getElementById('importDropdownButton');
      importDropdownButton.click();
      document.getElementById('ofx_file').value = '';
    }
    updateAccountBalances();
  },

  async archive(transactions, activeIndex, transaction = null) {
    let idsToArchive = [];
    if (transaction) {
      idsToArchive = [transaction.id];
    } else {
      idsToArchive = transactions
        .filter(transaction => {
          if (!transaction.checked || !transaction.cleared) return false;

          // For split transactions, check that all subtransactions have envelopes
          if (transaction.subtransactions?.length > 0) {
            return transaction.subtransactions.every(sub => sub.envelope_id);
          }

          // For regular transactions, check that envelope is assigned
          return transaction.envelope;
        })
        .map(transaction => transaction.id);

      if (transactions.filter(transaction => transaction.checked).length === 0) {
        const activeTransaction = transactions?.[activeIndex];
        if (activeTransaction?.cleared) {
          // Check if it's a split transaction or regular transaction
          const hasValidEnvelopes =
            activeTransaction.subtransactions?.length > 0
              ? activeTransaction.subtransactions.every(sub => sub.envelope_id)
              : activeTransaction.envelope;

          if (hasValidEnvelopes) {
            idsToArchive = [activeTransaction.id];
          } else {
            showToast('Please select transactions with envelopes and are cleared');
            return;
          }
        } else {
          showToast('Please select transactions with envelopes and are cleared');
          return;
        }
      }
    }

    const skippedTransactions = transactions.filter(transaction => {
      if (!transaction.checked) return false;
      if (!transaction.cleared) return true;

      // For split transactions, check that all subtransactions have envelopes
      if (transaction.subtransactions?.length > 0) {
        return !transaction.subtransactions.every(sub => sub.envelope_id);
      }

      // For regular transactions, check that envelope is assigned
      return !transaction.envelope;
    }).length;

    if (idsToArchive.length > 0) {
      await bulkArchiveTransactions(idsToArchive);
      if (skippedTransactions > 0) {
        showToast(`${skippedTransactions} transaction(s) skipped - must have envelope assigned and be cleared`);
      }
      return true;
    }
    if (skippedTransactions > 0) {
      showToast('Selected transactions must have envelope assigned and be cleared');
    } else {
      showToast('No transactions selected to archive');
    }
    return false;
  },

  async mergeSelectedTransactions(transactions) {
    const checkedTransactions = transactions.filter(transaction => transaction.checked);

    if (checkedTransactions.length !== 2) {
      showToast('Please select exactly 2 transactions to merge');
      return false;
    }

    const idsToMerge = checkedTransactions.map(transaction => transaction.id);

    try {
      await mergeTransactions(idsToMerge);
      showToast('Transactions merged successfully');
      updateAccountBalances();
      return true;
    } catch (error) {
      return false;
    }
  },

  async deleteCheckedRows(transactions) {
    const idsToDelete = transactions.filter(transaction => transaction.checked).map(transaction => transaction.id);

    if (idsToDelete.length > 0) {
      const deletePromises = idsToDelete.map(id => deleteTransaction(id));
      await Promise.all(deletePromises);
      updateAccountBalances();
      return true;
    }
    showToast('No transactions selected to delete');
    return false;
  },

  async toBudget(transactions, activeIndex, transaction = null) {
    const unallocatedId = document.getElementById('unallocated_funds_envelope_id').value;
    const budgetId = getCookie('budget_id');

    let transactionIds = [];
    if (transaction) {
      transactionIds = [transaction.id];
    } else {
      transactionIds = transactions.filter(transaction => transaction.checked).map(transaction => transaction.id);

      if (transactionIds.length === 0 && activeIndex !== -1) {
        const activeTransaction = transactions[activeIndex];
        if (activeTransaction) {
          transactionIds = [activeTransaction.id];
        }
      }
    }

    const validTransactions = transactions.filter(t => transactionIds.includes(t.id)).filter(t => t.amount >= 0);
    const ignoredCount = transactionIds.length - validTransactions.length;
    if (ignoredCount > 0) {
      showToast(`${ignoredCount} outflow transaction${ignoredCount === 1 ? ' was' : 's were'} ignored`);
    }

    transactionIds = validTransactions.map(t => t.id);

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

      try {
        await Promise.all(updatePromises);
        updateAccountBalances();
        return true;
      } catch (error) {
        console.error('Error updating transactions:', error);
        showToast('Error updating transactions');
        return false;
      }
    }
    return false;
  },

  async createTransfer(fromAccountId, toAccountId, amount, date, memo = '') {
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
  },

  async markAsTransfer(transactionId, transferAccountId, createCounterpart = true) {
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
  },
};
