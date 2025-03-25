document.addEventListener('alpine:init', () => {
  Alpine.data('payeeData', () => ({
    renameRules: [],
    searchTerm: '',
    payees: [],
    filteredPayees: [],
    searchTimeout: null,
    isLoading: false,
    resultMessage: '',
    showResultMessage: false,
    csrfToken: getCookie('csrftoken'),
    budgetId: getCookie('budget_id'),

    init() {
      // Initialize with all payees
      this.payees = Array.from(this.$el.querySelectorAll('tbody tr')).map(row => {
        return {
          element: row,
          name: row.querySelector('th').textContent.trim(),
        };
      });
      this.filteredPayees = [...this.payees];
    },

    updateDisplay() {
      // Get all the payee rows
      const rows = document.querySelectorAll('tbody tr');

      // Create a set of visible payee names for quick lookup
      const visiblePayeeNames = new Set(this.filteredPayees.map(p => p.name));

      // Show or hide rows based on filter
      for (const row of rows) {
        const payeeName = row.querySelector('th').textContent.trim();
        if (visiblePayeeNames.has(payeeName)) {
          row.style.display = ''; // Show the row
        } else {
          row.style.display = 'none'; // Hide the row
        }
      }
    },

    search() {
      // Clear any existing timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }

      // Set a new timeout (300ms debounce)
      this.searchTimeout = setTimeout(() => {
        const term = this.searchTerm.toLowerCase().trim();

        if (term === '') {
          // Show all payees if search is empty
          this.filteredPayees = [...this.payees];
          this.updateDisplay(); // Add this call
          return;
        }

        // Filter payees based on search term
        this.filteredPayees = this.payees.filter(payee => payee.name.toLowerCase().includes(term));
        this.updateDisplay(); // Add this call
      }, 300); // 300ms debounce delay
    },

    isPayeeVisible(payee) {
      return this.filteredPayees.includes(payee);
    },

    cleanUnusedPayees() {
      if (this.isLoading) return;

      this.isLoading = true;
      const url = `/api/payees/${this.budgetId}/delete-unused`;

      fetch(url, {
        method: 'DELETE',
        headers: {
          Accept: 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to delete unused payees');
          }
          return response.json();
        })
        .then(data => {
          this.showResult(`Successfully deleted ${data.count} unused payees`, 'success');
          this.window.location.reload();
        })
        .catch(error => {
          console.error('Error deleting unused payees:', error);
          this.showResult('Error deleting unused payees', 'error');
        })
        .finally(() => {
          this.isLoading = false;
        });
    },

    showResult(message, type) {
      this.resultMessage = message;
      this.showResultMessage = true;

      setTimeout(() => {
        this.showResultMessage = false;
      }, 3000);
    },

    addRule() {
      this.renameRules.push({ type: 'matches', text: '' });
    },

    removeRule(index) {
      this.renameRules.splice(index, 1);
    },
  }));
});
