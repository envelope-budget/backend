const SplitTransactions = {
  validateSplitAmounts(splitRows, editableTransaction) {
    let splitOutflowTotal = 0;
    let splitInflowTotal = 0;

    for (const row of splitRows) {
      if (row.outflow) {
        splitOutflowTotal += Number.parseFloat(row.outflow);
      }
      if (row.inflow) {
        splitInflowTotal += Number.parseFloat(row.inflow);
      }
    }

    const mainOutflow = editableTransaction.outflow ? Number.parseFloat(editableTransaction.outflow) : 0;
    const mainInflow = editableTransaction.inflow ? Number.parseFloat(editableTransaction.inflow) : 0;

    return {
      splitOutflowTotal,
      splitInflowTotal,
      amountsMatch: (mainOutflow > 0 && Math.abs(splitOutflowTotal - mainOutflow) < 0.01) ||
                   (mainInflow > 0 && Math.abs(splitInflowTotal - mainInflow) < 0.01)
    };
  },

  addSplitRow() {
    return {
      envelope: '',
      memo: '',
      inflow: '',
      outflow: '',
    };
  },

  positionSplitRows(activeIndex, formButtonsRow) {
    const splitControlsElement = document.querySelector('.split-controls');
    if (splitControlsElement && formButtonsRow) {
      // Position split controls before the form buttons
      formButtonsRow.before(splitControlsElement);
    }

    // Position all split rows after the main edit form
    const splitRowElements = document.querySelectorAll('.split-row');
    const editForm = document.querySelector('.transaction-edit[x-ref="editForm"]');
    
    if (splitRowElements.length > 0 && editForm) {
      // Move all split rows to appear right after the edit form
      for (const splitRow of splitRowElements) {
        editForm.after(splitRow);
      }
    }
  },

  initializeSplitEnvelopeSelectors(splitRows) {
    splitRows.forEach((row, index) => {
      if (row.envelope) {
        const envelopeSelect = document.getElementById(`id_split_envelope_${index}`);
        if (envelopeSelect) {
          const initializeSelector = () => {
            if (typeof envelopeSelect.setValue === 'function') {
              envelopeSelect.setValue(row.envelope);
            } else {
              setTimeout(initializeSelector, 50);
            }
          };
          initializeSelector();
        }
      }
    });
  },

  async saveSplitTransaction(editableTransaction, splitRows) {
    const budgetId = editableTransaction.budget_id;
    const csrfToken = getCookie('csrftoken');
    const dateInput = document.querySelector('.editable-transaction-date');
    if (!dateInput) {
      throw new Error('Date input element not found');
    }
    const date = new Date(dateInput.value);
    const formattedDate = date.toISOString().slice(0, 10);

    let payeeName = '';
    if (editableTransaction.payee) {
      if (typeof editableTransaction.payee === 'string') {
        payeeName = editableTransaction.payee;
      } else if (editableTransaction.payee.name) {
        payeeName = editableTransaction.payee.name;
      }
    }

    const subtransactions = [];
    for (const row of splitRows) {
      if (row.envelope && (row.inflow || row.outflow)) {
        const outflow = row.outflow ? Number.parseFloat(row.outflow) : 0;
        const inflow = row.inflow ? Number.parseFloat(row.inflow) : 0;
        const amount = inflow > 0 ? inflow * 1000 : outflow * -1000;

        subtransactions.push({
          envelope_id: row.envelope,
          amount: amount,
          memo: row.memo,
        });
      }
    }

    if (subtransactions.length === 0) {
      showToast('Please add at least one split transaction with an envelope and amount', 'error');
      throw new Error('No valid subtransactions');
    }

    const splitTransactionData = {
      account_id: editableTransaction.account,
      amount: editableTransaction.amount,
      cleared: editableTransaction.cleared,
      date: formattedDate,
      memo: editableTransaction.memo,
      payee: payeeName,
      subtransactions: subtransactions,
    };

    const response = await fetch(`/api/transactions/${budgetId}/split`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(splitTransactionData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  },

  async updateSplitTransaction(editableTransaction, splitRows) {
    const budgetId = editableTransaction.budget_id;
    const csrfToken = getCookie('csrftoken');
    const dateInput = document.querySelector('.editable-transaction-date');
    if (!dateInput) {
      throw new Error('Date input element not found');
    }
    const date = new Date(dateInput.value);
    const formattedDate = date.toISOString().slice(0, 10);

    let payeeName = '';
    if (editableTransaction.payee) {
      if (typeof editableTransaction.payee === 'string') {
        payeeName = editableTransaction.payee;
      } else if (editableTransaction.payee.name) {
        payeeName = editableTransaction.payee.name;
      }
    }

    const subtransactions = [];
    for (const row of splitRows) {
      if (row.envelope && (row.inflow || row.outflow)) {
        const outflow = row.outflow ? Number.parseFloat(row.outflow) : 0;
        const inflow = row.inflow ? Number.parseFloat(row.inflow) : 0;
        const amount = inflow > 0 ? inflow * 1000 : outflow * -1000;

        subtransactions.push({
          envelope_id: row.envelope,
          amount: amount,
          memo: row.memo,
        });
      }
    }

    if (subtransactions.length === 0) {
      showToast('Please add at least one split transaction with an envelope and amount', 'error');
      throw new Error('No valid subtransactions');
    }

    const splitTransactionData = {
      account_id: editableTransaction.account,
      amount: editableTransaction.amount,
      cleared: editableTransaction.cleared,
      date: formattedDate,
      memo: editableTransaction.memo,
      payee: payeeName,
      subtransactions: subtransactions,
    };

    const response = await fetch(`/api/transactions/${budgetId}/split/${editableTransaction.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(splitTransactionData),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  },

  async convertSplitToRegular(editableTransaction) {
    const budgetId = editableTransaction.budget_id;
    const csrfToken = getCookie('csrftoken');
    const dateInput = document.querySelector('.editable-transaction-date');
    if (!dateInput) {
      throw new Error('Date input element not found');
    }
    const date = new Date(dateInput.value);
    const formattedDate = date.toISOString().slice(0, 10);

    let payeeName = '';
    if (editableTransaction.payee) {
      if (typeof editableTransaction.payee === 'string') {
        payeeName = editableTransaction.payee;
      } else if (editableTransaction.payee.name) {
        payeeName = editableTransaction.payee.name;
      }
    }

    const postData = {
      account_id: editableTransaction.account,
      amount: editableTransaction.amount,
      cleared: editableTransaction.cleared,
      date: formattedDate,
      memo: editableTransaction.memo,
      payee: payeeName,
    };

    if (editableTransaction.envelope) {
      postData.envelope_id = editableTransaction.envelope;
    }

    const response = await fetch(`/api/transactions/${budgetId}/split/${editableTransaction.id}/convert`, {
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

    return await response.json();
  }
};
