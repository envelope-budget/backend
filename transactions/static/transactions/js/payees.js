function payeeData() {
  return {
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
    currentPayee: null,
    isEditing: false,
    newPayeeName: '',
    selectedCategory: '',

    init() {
      // Initialize with all payees
      this.payees = Array.from(document.querySelectorAll('tbody tr')).map(row => {
        return {
          element: row,
          name: row.querySelector('th').textContent.trim(),
          id: row.getAttribute('data-payee-id'),
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
          window.location.reload();
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

    // New methods for adding/editing payees
    openAddPayeeModal() {
      this.isEditing = false;
      this.currentPayee = null;
      this.newPayeeName = '';
      this.selectedCategory = '';
      this.renameRules = [];

      // Open the modal
      if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
        FlowbiteInstances.getInstance('Modal', 'payee-modal').show();
      }
    },

    openEditPayeeModal(payee) {
      this.isEditing = true;
      this.currentPayee = payee;
      this.newPayeeName = payee.name;

      // Fetch payee details including rename rules
      this.isLoading = true;
      fetch(`/api/payees/${this.budgetId}/${payee.id}`, {
        headers: {
          Accept: 'application/json',
        },
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to fetch payee details');
          }
          return response.json();
        })
        .then(data => {
          this.selectedCategory = data.category || '';
          this.renameRules = data.rename_rules || [];

          // Open the modal
          if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
            FlowbiteInstances.getInstance('Modal', 'payee-modal').show();
          }
        })
        .catch(error => {
          console.error('Error fetching payee details:', error);
          this.showResult('Error fetching payee details', 'error');
        })
        .finally(() => {
          this.isLoading = false;
        });
    },

    savePayee() {
      if (!this.newPayeeName.trim()) {
        this.showResult('Payee name cannot be empty', 'error');
        return;
      }

      this.isLoading = true;

      const payeeData = {
        name: this.newPayeeName.trim(),
        category: this.selectedCategory || null,
        rename_rules: this.renameRules,
      };

      const url = this.isEditing
        ? `/api/payees/${this.budgetId}/${this.currentPayee.id}`
        : `/api/payees/${this.budgetId}`;

      const method = this.isEditing ? 'PUT' : 'POST';

      fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
        body: JSON.stringify(payeeData),
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Failed to ${this.isEditing ? 'update' : 'create'} payee`);
          }
          return response.json();
        })
        .then(data => {
          this.showResult(`Successfully ${this.isEditing ? 'updated' : 'created'} payee: ${data.name}`, 'success');

          // Close the modal
          if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
            FlowbiteInstances.getInstance('Modal', 'payee-modal').hide();
          }

          // Refresh the page to show updated data
          window.location.reload();
        })
        .catch(error => {
          console.error(`Error ${this.isEditing ? 'updating' : 'creating'} payee:`, error);
          this.showResult(`Error ${this.isEditing ? 'updating' : 'creating'} payee`, 'error');
        })
        .finally(() => {
          this.isLoading = false;
        });
    },

    deletePayee() {
      if (!this.isEditing || !this.currentPayee) {
        return;
      }

      if (!confirm(`Are you sure you want to delete payee "${this.currentPayee.name}"?`)) {
        return;
      }

      this.isLoading = true;

      fetch(`/api/payees/${this.budgetId}/${this.currentPayee.id}`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': this.csrfToken,
        },
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to delete payee');
          }
          return response.json();
        })
        .then(data => {
          this.showResult(`Successfully deleted payee: ${this.currentPayee.name}`, 'success');

          // Close the modal
          if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
            FlowbiteInstances.getInstance('Modal', 'payee-modal').hide();
          }

          // Refresh the page to show updated data
          window.location.reload();
        })
        .catch(error => {
          console.error('Error deleting payee:', error);
          this.showResult('Error deleting payee', 'error');
        })
        .finally(() => {
          this.isLoading = false;
        });
    },

    cleanPayeeNames() {
      if (this.isLoading) return;

      if (!confirm('This will use AI to clean up all payee names. Continue?')) {
        return;
      }

      this.isLoading = true;
      const url = `/api/payees/${this.budgetId}/clean-names`;

      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to clean payee names');
          }
          return response.json();
        })
        .then(data => {
          this.showResult(`Successfully cleaned ${data.count} payee names`, 'success');
          window.location.reload();
        })
        .catch(error => {
          console.error('Error cleaning payee names:', error);
          this.showResult('Error cleaning payee names', 'error');
        })
        .finally(() => {
          this.isLoading = false;
        });
    },
  };
}
