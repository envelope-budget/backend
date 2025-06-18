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

    // Merge functionality (simplified - no merge mode)
    selectedPayees: [],
    mergePreview: null,
    showMergeModal: false,
    suggestedMergeName: '',
    customMergeName: '',
    isMergeLoading: false,

    async init() {
      await this.loadPayees();
    },

    async loadPayees() {
      this.isLoading = true;
      try {
        const response = await fetch(`/api/payees/${this.budgetId}`, {
          headers: {
            Accept: 'application/json',
            Authorization: `Bearer ${this.csrfToken}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to load payees');
        }

        const payeesData = await response.json();
        this.payees = payeesData;

        // Reapply the current search filter after loading
        this.applySearchFilter();
      } catch (error) {
        console.error('Error loading payees:', error);
        this.showResult('Error loading payees', 'error');
      } finally {
        this.isLoading = false;
      }
    },

    // Extract the search logic into a separate method
    applySearchFilter() {
      const term = this.searchTerm.toLowerCase().trim();

      if (term === '') {
        this.filteredPayees = [...this.payees];
        return;
      }

      this.filteredPayees = this.payees.filter(payee => payee.name.toLowerCase().includes(term));
    },

    // Update the search method to use the extracted logic
    search() {
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }

      this.searchTimeout = setTimeout(() => {
        this.applySearchFilter();
      }, 300);
    },

    isPayeeVisible(payee) {
      return this.filteredPayees.includes(payee);
    },

    async cleanUnusedPayees() {
      if (this.isLoading) return;

      if (!confirm('This will delete all unused payees. Continue?')) {
        return;
      }

      this.isLoading = true;
      const url = `/api/payees/${this.budgetId}/delete-unused`;

      try {
        const response = await fetch(url, {
          method: 'DELETE',
          headers: {
            Accept: 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to delete unused payees');
        }

        const data = await response.json();
        this.showResult(`Successfully deleted ${data.count} unused payees`, 'success');
        await this.loadPayees(); // Reload payees instead of page refresh
      } catch (error) {
        console.error('Error deleting unused payees:', error);
        this.showResult('Error deleting unused payees', 'error');
      } finally {
        this.isLoading = false;
      }
    },

    showResult(message, type) {
      this.resultMessage = message;
      this.showResultMessage = true;

      // Auto-hide success messages after 3 seconds, keep error messages longer
      const timeout = type === 'error' ? 5000 : 3000;
      setTimeout(() => {
        this.showResultMessage = false;
      }, timeout);
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

    async openEditPayeeModal(payee) {
      this.isEditing = true;
      this.currentPayee = payee;
      this.newPayeeName = payee.name;

      this.isLoading = true;
      try {
        const response = await fetch(`/api/payees/${this.budgetId}/${payee.id}`, {
          headers: {
            Accept: 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch payee details');
        }

        const data = await response.json();
        this.selectedCategory = data.category || '';
        this.renameRules = data.rename_rules || [];

        if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
          FlowbiteInstances.getInstance('Modal', 'payee-modal').show();
        }
      } catch (error) {
        console.error('Error fetching payee details:', error);
        this.showResult('Error fetching payee details', 'error');
      } finally {
        this.isLoading = false;
      }
    },

    async savePayee() {
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

      try {
        const response = await fetch(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
          body: JSON.stringify(payeeData),
        });

        if (!response.ok) {
          throw new Error(`Failed to ${this.isEditing ? 'update' : 'create'} payee`);
        }

        const data = await response.json();
        this.showResult(`Successfully ${this.isEditing ? 'updated' : 'created'} payee: ${data.name}`, 'success');

        if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
          FlowbiteInstances.getInstance('Modal', 'payee-modal').hide();
        }

        await this.loadPayees(); // Reload payees instead of page refresh
      } catch (error) {
        console.error(`Error ${this.isEditing ? 'updating' : 'creating'} payee:`, error);
        this.showResult(`Error ${this.isEditing ? 'updating' : 'creating'} payee`, 'error');
      } finally {
        this.isLoading = false;
      }
    },

    async deletePayee() {
      if (!this.isEditing || !this.currentPayee) {
        return;
      }

      if (!confirm(`Are you sure you want to delete payee "${this.currentPayee.name}"?`)) {
        return;
      }

      this.isLoading = true;

      try {
        const response = await fetch(`/api/payees/${this.budgetId}/${this.currentPayee.id}`, {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': this.csrfToken,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to delete payee');
        }

        const data = await response.json();
        this.showResult(`Successfully deleted payee: ${this.currentPayee.name}`, 'success');

        if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'payee-modal')) {
          FlowbiteInstances.getInstance('Modal', 'payee-modal').hide();
        }

        await this.loadPayees(); // Reload payees instead of page refresh
      } catch (error) {
        console.error('Error deleting payee:', error);
        this.showResult('Error deleting payee', 'error');
      } finally {
        this.isLoading = false;
      }
    },

    async cleanPayeeNames() {
      if (this.isLoading) return;

      if (!confirm('This will use AI to clean up all payee names. Continue?')) {
        return;
      }

      this.isLoading = true;
      const url = `/api/payees/${this.budgetId}/clean-names`;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to clean payee names');
        }

        const data = await response.json();
        this.showResult(`Successfully cleaned ${data.count} payee names`, 'success');
        await this.loadPayees(); // Reload payees instead of page refresh
      } catch (error) {
        console.error('Error cleaning payee names:', error);
        this.showResult('Error cleaning payee names', 'error');
      } finally {
        this.isLoading = false;
      }
    },

    clearSearch() {
      this.searchTerm = '';
      this.applySearchFilter();

      // Optional: Focus back on the search input for better UX
      document.getElementById('simple-search').focus();
    },

    togglePayeeSelection(payee) {
      const index = this.selectedPayees.findIndex(p => p.id === payee.id);
      if (index > -1) {
        this.selectedPayees.splice(index, 1);
      } else {
        this.selectedPayees.push(payee);
      }
    },

    isPayeeSelected(payee) {
      return this.selectedPayees.some(p => p.id === payee.id);
    },

    clearSelection() {
      this.selectedPayees = [];
    },

    async previewMerge() {
      if (this.selectedPayees.length < 2) {
        this.showResult('Please select at least 2 payees to merge', 'error');
        return;
      }

      this.isMergeLoading = true;

      try {
        const response = await fetch(`/api/payees/${this.budgetId}/merge/preview`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
          body: JSON.stringify({
            payee_ids: this.selectedPayees.map(p => p.id),
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Failed to preview merge');
        }

        this.mergePreview = await response.json();
        this.suggestedMergeName = this.mergePreview.suggested_name;
        this.customMergeName = this.suggestedMergeName;
        this.showMergeModal = true;

        // Initialize modal if using Flowbite
        if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'merge-preview-modal')) {
          FlowbiteInstances.getInstance('Modal', 'merge-preview-modal').show();
        }
      } catch (error) {
        console.error('Error previewing merge:', error);
        this.showResult(`Error previewing merge: ${error.message}`, 'error');
      } finally {
        this.isMergeLoading = false;
      }
    },

    async confirmMerge() {
      if (!this.customMergeName.trim()) {
        this.showResult('Please enter a name for the merged payee', 'error');
        return;
      }

      this.isMergeLoading = true;

      try {
        const response = await fetch(`/api/payees/${this.budgetId}/merge/confirm`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
          body: JSON.stringify({
            payee_ids: this.selectedPayees.map(p => p.id),
            new_payee_name: this.customMergeName.trim(),
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Failed to merge payees');
        }

        const result = await response.json();

        this.showResult(
          `Successfully merged ${this.selectedPayees.length} payees into "${result.merged_payee.name}". Updated ${result.updated_transaction_count} transactions.`,
          'success'
        );

        // Close modal and clear selection
        this.showMergeModal = false;
        if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'merge-preview-modal')) {
          FlowbiteInstances.getInstance('Modal', 'merge-preview-modal').hide();
        }

        // Clear selection and reload payees
        this.selectedPayees = [];
        await this.loadPayees();
      } catch (error) {
        console.error('Error merging payees:', error);
        this.showResult(`Error merging payees: ${error.message}`, 'error');
      } finally {
        this.isMergeLoading = false;
      }
    },

    cancelMerge() {
      this.showMergeModal = false;
      this.mergePreview = null;
      this.customMergeName = '';
      this.suggestedMergeName = '';

      if (typeof FlowbiteInstances !== 'undefined' && FlowbiteInstances.getInstance('Modal', 'merge-preview-modal')) {
        FlowbiteInstances.getInstance('Modal', 'merge-preview-modal').hide();
      }
    },

    // Helper method to format currency for display
    formatCurrency(amount) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(amount / 1000); // Assuming amounts are stored in cents/thousandths
    },

    // Helper method to format date for display
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString();
    },
  };
}
