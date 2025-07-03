const DuplicateDetection = {
  async checkForDuplicates(transactionIds = null) {
    const budgetId = getCookie('budget_id');
    let url = `/api/transactions/${budgetId}/duplicates`;

    if (transactionIds && transactionIds.length > 0) {
      url += `?transaction_ids=${transactionIds.join(',')}`;
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking for duplicates:', error);
      showToast('Error checking for duplicates');
      throw error;
    }
  },

  async mergeDuplicateTransactions(groupId, transactionIds) {
    const budgetId = getCookie('budget_id');
    const url = `/api/transactions/${budgetId}/duplicates/merge`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
          group_id: groupId,
          transaction_ids: transactionIds,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to merge transactions');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error merging duplicate transactions:', error);
      showToast(`Error merging transactions: ${error.message}`);
      throw error;
    }
  },

  formatAmount(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount / 1000);
  },

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  },

  showDuplicatesModal(duplicateGroups, callback = null) {
    if (duplicateGroups.length === 0) {
      showToast('No duplicate transactions found');
      if (callback) callback();
      return;
    }

    const modal = this.createDuplicatesModal(duplicateGroups);
    document.body.appendChild(modal);

    // Show the modal with animation
    setTimeout(() => {
      modal.classList.add('opacity-100');
      modal.querySelector('.modal-content').classList.add('scale-100');
      modal.setAttribute('aria-hidden', 'false');
    }, 10);

    // Store callback for when modal is completely closed
    modal._closeCallback = callback;

    // Clean up when clicking outside
    modal.addEventListener('click', e => {
      if (e.target === modal || e.target.classList.contains('modal-backdrop')) {
        this.hideModal(modal);
      }
    });
  },

  hideModal(modal) {
    modal.classList.remove('opacity-100');
    modal.querySelector('.modal-content').classList.remove('scale-100');
    modal.setAttribute('aria-hidden', 'true');
    setTimeout(() => {
      if (modal.parentNode) {
        document.body.removeChild(modal);
      }
      // Call the callback if one was provided (e.g., to reload the page)
      if (modal._closeCallback) {
        modal._closeCallback();
      }
    }, 300);
  },

  createDuplicatesModal(duplicateGroups) {
    const modal = document.createElement('div');
    modal.className =
      'fixed inset-0 z-50 flex items-center justify-center p-4 opacity-0 transition-opacity duration-300';
    modal.setAttribute('aria-labelledby', 'duplicates-modal-title');
    modal.setAttribute('aria-hidden', 'true');
    modal.id = 'duplicates-modal';

    const duplicateGroupsHtml = duplicateGroups
      .map((group, groupIndex) => {
        const transactionsHtml = group.transactions
          .map(
            (transaction, transIndex) => `
        <tr class="border-b dark:border-gray-700">
          <td class="px-4 py-3">
            <input type="checkbox"
                   class="duplicate-transaction-checkbox w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                   data-group-id="${group.id}"
                   data-transaction-id="${transaction.id}"
                   checked>
          </td>
          <td class="px-4 py-3">${transaction.account.name}</td>
          <td class="px-4 py-3">${this.formatDate(transaction.date)}</td>
          <td class="px-4 py-3">${transaction.payee ? transaction.payee.name : ''}</td>
          <td class="px-4 py-3">${transaction.envelope ? transaction.envelope.name : ''}</td>
          <td class="px-4 py-3 text-right">${this.formatAmount(transaction.amount)}</td>
          <td class="px-4 py-3">
            ${transaction.import_id ? '<span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Imported</span>' : ''}
            ${transaction.sfin_id ? '<span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">SimpleFIN</span>' : ''}
          </td>
        </tr>
      `
          )
          .join('');

        return `
        <div class="mb-8 bg-white dark:bg-gray-800 rounded-lg shadow">
          <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700 rounded-t-lg border-b dark:border-gray-600">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Duplicate Group ${groupIndex + 1}
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              ${group.transactions.length} transactions • ${this.formatAmount(group.transactions[0].amount)}
            </p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
              <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                <tr>
                  <th scope="col" class="px-4 py-3">
                    <input type="checkbox"
                           class="group-select-all w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                           data-group-id="${group.id}"
                           title="Select All"
                           checked>
                  </th>
                  <th scope="col" class="px-4 py-3">Account</th>
                  <th scope="col" class="px-4 py-3">Date</th>
                  <th scope="col" class="px-4 py-3">Payee</th>
                  <th scope="col" class="px-4 py-3">Envelope</th>
                  <th scope="col" class="px-4 py-3">Amount</th>
                  <th scope="col" class="px-4 py-3">Source</th>
                </tr>
              </thead>
              <tbody>
                ${transactionsHtml}
              </tbody>
            </table>
          </div>
          <div class="px-6 py-4 bg-gray-50 dark:bg-gray-700 rounded-b-lg flex justify-between items-center">
            <button type="button"
                    class="ignore-group-btn text-gray-900 bg-white border border-gray-300 hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:text-white dark:focus:ring-gray-700"
                    data-group-id="${group.id}">
              Not Duplicates
            </button>
            <div>
              <span class="text-sm text-gray-600 dark:text-gray-400 mr-3 selected-count" data-group-id="${group.id}">${group.transactions.length} selected</span>
              <button type="button"
                      class="merge-group-btn text-white bg-primary-700 hover:bg-primary-800 focus:ring-4 focus:ring-primary-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-primary-600 dark:hover:bg-primary-700 focus:outline-none dark:focus:ring-primary-800"
                      data-group-id="${group.id}">
                Merge Selected
              </button>
            </div>
          </div>
        </div>
      `;
      })
      .join('');

    modal.innerHTML = `
      <!-- Modal backdrop -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity modal-backdrop" aria-hidden="true"></div>

      <!-- Modal content -->
      <div class="modal-content bg-white dark:bg-gray-800 rounded-lg shadow-xl transform transition-all duration-300 scale-95 w-full max-w-6xl max-h-[90vh] overflow-hidden">
        <div class="bg-white dark:bg-gray-800 px-6 pt-6 pb-4">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white" id="duplicates-modal-title">
              Potential Duplicate Transactions
            </h3>
            <button type="button" class="close-modal-btn text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" data-dismiss="modal">
              <span class="sr-only">Close</span>
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="max-h-[60vh] overflow-y-auto">
            ${duplicateGroupsHtml}
          </div>
        </div>
        <div class="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex justify-end">
          <button type="button" class="close-modal-btn px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700">
            Close
          </button>
        </div>
      </div>
    `;

    // Add event listeners
    this.addModalEventListeners(modal);

    // Initialize selected counts for each group
    duplicateGroups.forEach((group, index) => {
      const groupId = `group_${index}`;
      this.updateSelectedCount(modal, groupId);
    });

    return modal;
  },

  addModalEventListeners(modal) {
    // Close modal buttons
    for (const btn of modal.querySelectorAll('.close-modal-btn')) {
      btn.addEventListener('click', () => {
        this.hideModal(modal);
      });
    }

    // Select all checkbox behavior
    for (const selectAllCheckbox of modal.querySelectorAll('.group-select-all')) {
      selectAllCheckbox.addEventListener('change', e => {
        const groupId = e.target.dataset.groupId;
        const isChecked = e.target.checked;

        // Check/uncheck all checkboxes in this group
        for (const checkbox of modal.querySelectorAll(
          `input.duplicate-transaction-checkbox[data-group-id="${groupId}"]`
        )) {
          checkbox.checked = isChecked;
        }

        this.updateSelectedCount(modal, groupId);
      });
    }

    // Individual checkbox behavior
    for (const checkbox of modal.querySelectorAll('.duplicate-transaction-checkbox')) {
      checkbox.addEventListener('change', e => {
        const groupId = e.target.dataset.groupId;
        this.updateSelectedCount(modal, groupId);

        // Update select all checkbox state
        const selectAllCheckbox = modal.querySelector(`.group-select-all[data-group-id="${groupId}"]`);
        const allCheckboxes = modal.querySelectorAll(
          `input.duplicate-transaction-checkbox[data-group-id="${groupId}"]`
        );
        const checkedCheckboxes = modal.querySelectorAll(
          `input.duplicate-transaction-checkbox[data-group-id="${groupId}"]:checked`
        );

        if (checkedCheckboxes.length === allCheckboxes.length) {
          selectAllCheckbox.checked = true;
          selectAllCheckbox.indeterminate = false;
        } else if (checkedCheckboxes.length === 0) {
          selectAllCheckbox.checked = false;
          selectAllCheckbox.indeterminate = false;
        } else {
          selectAllCheckbox.checked = false;
          selectAllCheckbox.indeterminate = true;
        }
      });
    }

    // Ignore group buttons
    for (const btn of modal.querySelectorAll('.ignore-group-btn')) {
      btn.addEventListener('click', e => {
        const groupId = e.target.dataset.groupId;

        // Remove this group from the modal
        const groupElement = e.target.closest('.mb-8');
        groupElement.remove();

        // Check if there are any groups left
        const remainingGroups = modal.querySelectorAll('.mb-8');
        if (remainingGroups.length === 0) {
          showToast('All duplicate groups have been processed');
          this.hideModal(modal);
        } else {
          showToast('Duplicate group ignored');
        }
      });
    }

    // Merge group buttons
    for (const btn of modal.querySelectorAll('.merge-group-btn')) {
      btn.addEventListener('click', async e => {
        const groupId = e.target.dataset.groupId;
        const checkedBoxes = modal.querySelectorAll(
          `input.duplicate-transaction-checkbox[data-group-id="${groupId}"]:checked`
        );

        if (checkedBoxes.length < 2) {
          showToast('Please select at least 2 transactions to merge');
          return;
        }

        const transactionIds = Array.from(checkedBoxes).map(cb => cb.dataset.transactionId);

        try {
          btn.disabled = true;
          btn.innerHTML = 'Merging...';

          await this.mergeDuplicateTransactions(groupId, transactionIds);
          showToast('Transactions merged successfully');

          // Remove this group from the modal
          const groupElement = e.target.closest('.mb-8');
          groupElement.remove();

          // Always refresh the transaction list after a merge
          if (typeof fetchTransactions === 'function') {
            fetchTransactions();
          }

          // Check if there are any groups left
          const remainingGroups = modal.querySelectorAll('.mb-8');
          if (remainingGroups.length === 0) {
            this.hideModal(modal);
          }
        } catch (error) {
          btn.disabled = false;
          btn.innerHTML = 'Merge Selected';
        }
      });
    }
  },

  updateSelectedCount(modal, groupId) {
    const checkedBoxes = modal.querySelectorAll(
      `input.duplicate-transaction-checkbox[data-group-id="${groupId}"]:checked`
    );
    const countElement = modal.querySelector(`.selected-count[data-group-id="${groupId}"]`);

    if (countElement) {
      const count = checkedBoxes.length;
      countElement.textContent = `${count} selected`;

      // Update merge button state
      const mergeButton = modal.querySelector(`.merge-group-btn[data-group-id="${groupId}"]`);
      if (mergeButton) {
        if (count < 2) {
          mergeButton.disabled = true;
          mergeButton.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
          mergeButton.disabled = false;
          mergeButton.classList.remove('opacity-50', 'cursor-not-allowed');
        }
      }
    }
  },
};
