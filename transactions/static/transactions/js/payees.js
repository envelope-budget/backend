function payeeData() {
  return {
    renameRules: [],
    searchTerm: '',
    payees: [],
    filteredPayees: [],
    searchTimeout: null,

    init() {
      // Initialize with all payees
      this.payees = Array.from(document.querySelectorAll('tbody tr')).map(row => {
        return {
          element: row,
          name: row.querySelector('th').textContent.trim(),
        };
      });
      this.filteredPayees = [...this.payees];
    },

    search(event) {
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
          this.updateDisplay();
          return;
        }

        // Filter payees based on search term
        this.filteredPayees = this.payees.filter(payee => payee.name.toLowerCase().includes(term));

        this.updateDisplay();
      }, 300); // 300ms debounce delay
    },

    updateDisplay() {
      // Hide all payees first
      for (const payee of this.payees) {
        payee.element.classList.add('hidden');
      }

      // Show only filtered payees
      for (const payee of this.filteredPayees) {
        payee.element.classList.remove('hidden');
      }
    },

    addRule() {
      this.renameRules.push({ type: 'matches', text: '' });
    },

    removeRule(index) {
      this.renameRules.splice(index, 1);
    },
  };
}
