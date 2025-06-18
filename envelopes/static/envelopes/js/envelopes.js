const pickerOptions = { onEmojiSelect: addEmojiToName };
const picker = new EmojiMart.Picker(pickerOptions);

document.getElementById('emoji-picker').appendChild(picker);

// Set budgetId from cookie
window.budgetId = window.getCookie('budget_id');

function addEmojiToName(emoji) {
  console.log('Emoji selected:', emoji.native);
  const $name = document.getElementById('envelope-name');
  let name = $name.value;
  console.log('Name before removing emoji:', name);

  // If name starts with an emoji, remove the emoji first
  const emojiRegexPattern = /^(\p{Emoji_Presentation}|\p{Extended_Pictographic}|\u200d)+/u;
  name = name.replace(emojiRegexPattern, '').replace(/\s+/, '').trim();

  const newName = `${emoji.native} ${name}`;
  $name.value = newName;
  console.log('Name after removing emoji:', $name.value);

  // Set Alpine envelope.name value
  const envelopeComponent = Alpine.evaluate($name, 'envelope');
  if (envelopeComponent) {
    envelopeComponent.name = newName;
  }

  $name.focus();
}

// Initialize drag and drop functionality
document.addEventListener('DOMContentLoaded', () => {
  // Delay initialization to ensure Alpine.js has rendered the DOM
  setTimeout(() => {
    initializeSortable();
  }, 100);
});

function initializeSortable() {
  // Make categories sortable
  const categoriesList = document.getElementById('categories-list');
  if (categoriesList) {
    new Sortable(categoriesList, {
      animation: 150,
      handle: '.drag-handle',
      ghostClass: 'bg-gray-100',
      onEnd: evt => {
        saveCategoriesOrder();
      },
    });
  }

  // Make envelopes sortable within their categories
  const envelopesLists = document.querySelectorAll('.envelopes-list');
  for (const list of envelopesLists) {
    new Sortable(list, {
      animation: 150,
      handle: '.drag-handle',
      ghostClass: 'bg-gray-100',
      group: 'envelopes', // This allows dragging between categories
      onEnd: evt => {
        // If the envelope was moved to a different category
        if (evt.from !== evt.to) {
          updateEnvelopeCategory(evt.item.getAttribute('data-id'), evt.to.getAttribute('data-category-id'));
        }
        saveEnvelopesOrder(evt.to);
      },
    });
  }
}

// Save the order of categories
function saveCategoriesOrder() {
  const categoryItems = document.querySelectorAll('.category-item');
  const orderData = Array.from(categoryItems).map((item, index) => {
    return {
      id: item.getAttribute('data-id'),
      order: index,
    };
  });

  const endpoint = `/api/envelopes/categories/${window.budgetId}/order`;
  const csrfToken = window.getCookie('csrftoken');

  fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ categories: orderData }),
    credentials: 'include',
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Categories order saved:', data);
    })
    .catch(error => {
      console.error('Error saving categories order:', error);
    });
}

// Save the order of envelopes within a category
function saveEnvelopesOrder(categoryList) {
  const envelopeItems = categoryList.querySelectorAll('.envelope-item');
  const categoryId = categoryList.getAttribute('data-category-id');
  const orderData = Array.from(envelopeItems).map((item, index) => {
    return {
      id: item.getAttribute('data-id'),
      order: index,
    };
  });

  const endpoint = `/api/envelopes/${window.budgetId}/order`;
  const csrfToken = window.getCookie('csrftoken');

  fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
      category_id: categoryId,
      envelopes: orderData,
    }),
    credentials: 'include',
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Envelopes order saved:', data);
    })
    .catch(error => {
      console.error('Error saving envelopes order:', error);
    });
}

// Update an envelope's category
function updateEnvelopeCategory(envelopeId, newCategoryId) {
  const endpoint = `/api/envelopes/${window.budgetId}/${envelopeId}`;
  const csrfToken = window.getCookie('csrftoken');

  fetch(endpoint, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({
      category_id: newCategoryId,
    }),
    credentials: 'include',
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Envelope category updated:', data);
    })
    .catch(error => {
      console.error('Error updating envelope category:', error);
    });
}

function envelopeData() {
  return {
    // Data properties
    budget: null,
    categories: [],
    loading: true,

    envelope: {
      id: '',
      name: '',
      balance: 0,
      category_id: '',
      note: '',
      monthly_budget_amount: 0,
    },

    category: {
      name: '',
    },

    selectedItem: {
      id: null,
      type: null,
      name: '',
      balance: 0,
      categoryName: '',
    },

    categoryForm: {
      id: null,
      name: '',
      isEdit: false,
    },

    searchQuery: '',

    // Computed properties
    get filteredCategories() {
      if (!this.searchQuery.trim()) {
        return this.categories;
      }

      const query = this.searchQuery.toLowerCase();
      return this.categories
        .map(category => {
          // Check if category name matches
          const categoryMatches = category.name.toLowerCase().includes(query);

          // Filter envelopes that match the search
          const filteredEnvelopes = category.envelopes.filter(envelope => envelope.name.toLowerCase().includes(query));

          // Show category if it matches or has matching envelopes
          if (categoryMatches || filteredEnvelopes.length > 0) {
            return {
              ...category,
              envelopes: categoryMatches ? category.envelopes : filteredEnvelopes,
            };
          }
          return null;
        })
        .filter(Boolean);
    },

    // Methods
    async loadEnvelopes() {
      this.loading = true;
      try {
        // console.log(`Budget ID: ${window.budgetId}`);
        const response = await fetch(`/api/envelopes/${window.budgetId}`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        this.categories = data;

        // Load budget data including unallocated envelope
        await this.loadBudgetData();

        // Re-initialize sortable after data loads
        this.$nextTick(() => {
          initializeSortable();
        });
      } catch (error) {
        console.error('Error loading envelopes:', error);
        showToast('Failed to load envelopes. Please refresh the page.');
      } finally {
        this.loading = false;
      }
    },

    async loadBudgetData() {
      try {
        const response = await fetch(`/api/budgets/${window.budgetId}`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        this.budget = await response.json();
      } catch (error) {
        console.error('Error loading budget data:', error);
      }
    },

    formatMoney(amount) {
      // Convert cents to dollars and format
      const dollars = amount / 1000;
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(dollars);
    },

    getBalanceColorClass(balance) {
      if (balance > 0) {
        return 'text-green-600 dark:text-green-400';
      }
      if (balance < 0) {
        return 'text-red-600 dark:text-red-400';
      }
      return 'text-gray-900 dark:text-white';
    },

    getUnallocatedBackgroundClass() {
      if (!this.budget || !this.budget.unallocated_envelope) {
        return 'bg-gray-100 dark:bg-gray-700';
      }

      const balance = this.budget.unallocated_envelope.balance;
      if (balance > 0) {
        return 'bg-green-100 dark:bg-green-700';
      }
      if (balance < 0) {
        return 'bg-red-100 dark:bg-red-700';
      }
      return 'bg-gray-100 dark:bg-gray-700';
    },

    async quickAllocateFunds(envelopeId, currentBalance) {
      // Only proceed if the balance is negative
      if (currentBalance >= 0) {
        return;
      }

      // Calculate the amount needed to bring the balance to zero
      const amountToAllocate = Math.abs(currentBalance);

      try {
        const response = await fetch(`/api/envelopes/${window.budgetId}/transfer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken'),
          },
          body: JSON.stringify({
            from_envelope_id: 'unallocated',
            to_envelope_id: envelopeId,
            amount: amountToAllocate,
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          console.log('Funds allocated successfully:', data);

          // Update the specific envelope balance locally
          const envelope = this.findEnvelopeById(envelopeId);
          if (envelope) {
            envelope.balance = data.destination_envelope.balance;
          }

          // Update the unallocated envelope balance using the new API response
          if (this.budget?.unallocated_envelope && data.unallocated_envelope) {
            this.budget.unallocated_envelope.balance = data.unallocated_envelope.balance;
          }

          // Update selected item if it's the current envelope
          if (this.selectedItem.id === envelopeId && this.selectedItem.type === 'envelope') {
            this.selectedItem.balance = data.destination_envelope.balance;
          }

          // Update the balance of affected categories
          for (const category of data.affected_categories) {
            const categoryIndex = this.categories.findIndex(cat => cat.id === category.id);
            if (categoryIndex !== -1) {
              // Update the category's total balance
              this.categories[categoryIndex].balance = category.balance;
            }
          }

          showToast('Funds allocated successfully!');
        } else {
          throw new Error(data.message || 'Failed to allocate funds');
        }
      } catch (error) {
        console.error('Error allocating funds:', error);
        showToast('Failed to allocate funds. Please check if you have enough unallocated funds.');
      }
    },

    async sweepFunds(envelopeId, currentBalance) {
      // Only proceed if the balance is positive
      if (currentBalance <= 0) {
        return;
      }

      try {
        const response = await fetch(`/api/envelopes/${window.budgetId}/transfer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken'),
          },
          body: JSON.stringify({
            from_envelope_id: envelopeId,
            to_envelope_id: 'unallocated',
            amount: currentBalance,
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          console.log('Funds swept successfully:', data);

          // Update the specific envelope balance locally
          const envelope = this.findEnvelopeById(envelopeId);
          if (envelope) {
            envelope.balance = data.source_envelope.balance;
          }

          // Update the unallocated envelope balance using the new API response
          if (this.budget?.unallocated_envelope && data.unallocated_envelope) {
            this.budget.unallocated_envelope.balance = data.unallocated_envelope.balance;
          }

          // Update selected item if it's the current envelope
          if (this.selectedItem.id === envelopeId && this.selectedItem.type === 'envelope') {
            this.selectedItem.balance = data.source_envelope.balance;
          }

          // Update the balance of affected categories
          for (const category of data.affected_categories) {
            const categoryIndex = this.categories.findIndex(cat => cat.id === category.id);
            if (categoryIndex !== -1) {
              // Update the category's total balance
              this.categories[categoryIndex].balance = category.balance;
            }
          }

          showToast('Funds swept to unallocated successfully!');
        } else {
          throw new Error(data.message || 'Failed to sweep funds');
        }
      } catch (error) {
        console.error('Error sweeping funds:', error);
        showToast('Failed to sweep funds. Please try again.');
      }
    },
    performSearch() {
      // The search is now handled by the filteredCategories computed property
      // This method can be used for additional search logic if needed
    },

    startNewEnvelope(category_id) {
      this.envelope.id = '';
      this.envelope.name = '';
      this.envelope.balance = 0;
      this.envelope.category_id = category_id;
      this.envelope.note = '';
      this.monthly_budget_amount = 0;

      // Clear the name input field
      const nameInput = document.getElementById('envelope-name');
      if (nameInput) {
        nameInput.value = '';
      }
    },

    startNewCategory() {
      this.resetCategoryForm();
    },

    async createEnvelope() {
      try {
        const response = await fetch(`/api/envelopes/${window.budgetId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken'),
          },
          body: JSON.stringify({
            name: this.envelope.name,
            balance: Number.parseInt(this.envelope.balance * 1000), // Convert dollars to thousandths
            category_id: this.envelope.category_id,
            note: this.envelope.note,
            monthly_budget_amount: Number.parseInt(this.envelope.monthly_budget_amount * 1000),
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Envelope created successfully:', data);

        // Reload envelopes to show the new one
        await this.loadEnvelopes();

        // Close the modal
        const modal = FlowbiteInstances.getInstance('Modal', 'envelope-modal');
        if (modal) modal.hide();

        showToast('Envelope created successfully!');
      } catch (error) {
        console.error('Error creating envelope:', error);
        showToast('Failed to create envelope. Please try again.');
      }
    },

    selectCategory(categoryId) {
      const category = this.categories.find(cat => cat.id === categoryId);
      if (category) {
        this.selectedItem = {
          id: categoryId,
          type: 'category',
          name: category.name,
          balance: category.balance,
        };
      }
    },

    selectEnvelope(id, name, balance, categoryName) {
      this.selectedItem = {
        id: id,
        type: 'envelope',
        name: name,
        balance: balance,
        categoryName: categoryName,
      };
    },

    editCategory(categoryId) {
      const category = this.categories.find(cat => cat.id === categoryId);
      if (category) {
        this.categoryForm.isEdit = true;
        this.categoryForm.id = categoryId;
        this.categoryForm.name = category.name;
      }
    },

    async saveCategory() {
      const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      };

      try {
        if (this.categoryForm.isEdit) {
          // Update existing category
          const response = await fetch(`/api/categories/${window.budgetId}/${this.categoryForm.id}`, {
            method: 'PATCH',
            headers,
            body: JSON.stringify({
              name: this.categoryForm.name,
            }),
            credentials: 'include',
          });

          if (!response.ok) {
            throw new Error('Failed to update category');
          }

          // Update the category in our local data
          const categoryIndex = this.categories.findIndex(cat => cat.id === this.categoryForm.id);
          if (categoryIndex !== -1) {
            this.categories[categoryIndex].name = this.categoryForm.name;
          }

          // Update the selected item if it's the current category
          if (this.selectedItem.id === this.categoryForm.id && this.selectedItem.type === 'category') {
            this.selectedItem.name = this.categoryForm.name;
          }

          showToast('Category updated successfully!');
        } else {
          // Create new category
          const response = await fetch(`/api/categories/${window.budgetId}`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              name: this.categoryForm.name,
            }),
            credentials: 'include',
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          console.log('Category created successfully');
          // Reload envelopes to show the new category
          await this.loadEnvelopes();
          showToast('Category created successfully!');
        }

        // Close the modal
        const modal = FlowbiteInstances.getInstance('Modal', 'category-modal');
        if (modal) modal.hide();

        // Reset the form
        this.resetCategoryForm();
      } catch (error) {
        console.error('Error saving category:', error);
        showToast('Failed to save category. Please try again.');
      }
    },

    resetCategoryForm() {
      this.categoryForm = {
        id: null,
        name: '',
        isEdit: false,
      };
    },

    closeDetails() {
      this.selectedItem = {
        id: null,
        name: '',
        balance: 0,
        type: null,
        categoryName: '',
      };
    },

    editEnvelope(id) {
      const envelope = this.findEnvelopeById(id);
      if (envelope) {
        this.envelope = {
          id: envelope.id,
          name: envelope.name,
          balance: envelope.balance / 1000, // Convert from thousandths to dollars
          category_id: envelope.category_id,
          note: envelope.note || '',
          monthly_budget_amount: envelope.monthly_budget_amount / 1000 || 0,
        };

        // Update the emoji picker input field
        const nameInput = document.getElementById('envelope-name');
        if (nameInput) {
          nameInput.value = envelope.name;
        }
      }
    },

    async updateEnvelope() {
      try {
        const response = await fetch(`/api/envelopes/${window.budgetId}/${this.envelope.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken'),
          },
          body: JSON.stringify({
            name: this.envelope.name,
            balance: Number.parseInt(this.envelope.balance * 1000), // Convert dollars to thousandths
            category_id: this.envelope.category_id,
            note: this.envelope.note,
            monthly_budget_amount: Number.parseInt(this.envelope.monthly_budget_amount * 1000),
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Envelope updated successfully:', data);

        // Update the envelope in local data
        const envelope = this.findEnvelopeById(this.envelope.id);
        if (envelope) {
          envelope.name = data.name;
          envelope.balance = data.balance;
          envelope.category_id = data.category_id;
          envelope.note = data.note;
          envelope.monthly_budget_amount = data.monthly_budget_amount;
        }

        // Update selected item if it's the current envelope
        if (this.selectedItem.id === this.envelope.id && this.selectedItem.type === 'envelope') {
          this.selectedItem.name = data.name;
          this.selectedItem.balance = data.balance;
        }

        // If category changed, reload envelopes to reflect the change
        if (envelope && envelope.category_id !== data.category_id) {
          await this.loadEnvelopes();
        }

        // Close the modal
        const modal = FlowbiteInstances.getInstance('Modal', 'envelope-modal');
        if (modal) modal.hide();

        showToast('Envelope updated successfully!');
      } catch (error) {
        console.error('Error updating envelope:', error);
        showToast('Failed to update envelope. Please try again.');
      }
    },

    async confirmDeleteEnvelope() {
      // This method is called when the user confirms deletion in the modal
      if (!this.selectedItem.id || this.selectedItem.type !== 'envelope') {
        return;
      }

      try {
        const response = await fetch(`/api/envelopes/${window.budgetId}/${this.selectedItem.id}`, {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': window.getCookie('csrftoken'),
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          // Show appropriate message based on action taken
          if (data.has_transactions) {
            showToast(`Envelope archived (had transactions): ${data.message}`);
          } else {
            showToast(`Envelope deleted: ${data.message}`);
          }

          // Close details panel since the envelope was deleted/archived
          this.closeDetails();

          // Reload envelopes to reflect changes
          await this.loadEnvelopes();
        } else {
          throw new Error(data.message || 'Failed to delete envelope');
        }
      } catch (error) {
        console.error('Error deleting envelope:', error);
        showToast('Failed to delete envelope. Please try again.');
      }
    },

    findEnvelopeById(envelopeId) {
      for (const category of this.categories) {
        const envelope = category.envelopes.find(env => env.id === envelopeId);
        if (envelope) {
          return envelope;
        }
      }
      return null;
    },

    allocation: {
      amount: 0,
    },

    get allocationPreview() {
      if (!this.allocation.amount || !this.budget?.unallocated_envelope) {
        return {
          newUnallocatedBalance: this.budget?.unallocated_envelope?.balance || 0,
          newEnvelopeBalance: this.selectedItem.balance || 0,
          isOverdrawn: false,
        };
      }

      const dollarAmount = Number.parseFloat(this.allocation.amount) || 0;
      const amountStr = Math.abs(dollarAmount).toFixed(2);
      const [dollars, cents] = amountStr.split('.');
      const amount = Number.parseInt(dollars) * 1000 + Number.parseInt(cents) * 10;

      // For negative amounts, we're pulling money FROM the envelope TO unallocated
      // For positive amounts, we're moving money FROM unallocated TO the envelope
      let newUnallocatedBalance;
      let newEnvelopeBalance;

      if (dollarAmount < 0) {
        // Negative allocation: move money from envelope to unallocated
        newUnallocatedBalance = (this.budget.unallocated_envelope.balance || 0) + amount;
        newEnvelopeBalance = (this.selectedItem.balance || 0) - amount;
      } else {
        // Positive allocation: move money from unallocated to envelope
        newUnallocatedBalance = (this.budget.unallocated_envelope.balance || 0) - amount;
        newEnvelopeBalance = (this.selectedItem.balance || 0) + amount;
      }

      return {
        newUnallocatedBalance,
        newEnvelopeBalance,
        isOverdrawn: newUnallocatedBalance < 0,
      };
    },

    fillAllocationShortcut(type) {
      const envelope = this.findEnvelopeById(this.selectedItem.id);
      if (!envelope) return;

      switch (type) {
        case 'budget':
          this.allocation.amount = envelope.monthly_budget_amount / 1000 || 0;
          break;
        case 'overspent':
          if (envelope.balance < 0) {
            this.allocation.amount = Math.abs(envelope.balance / 1000);
          }
          break;
        case 'zero':
          if (envelope.balance > 0) {
            this.allocation.amount = -(envelope.balance / 1000);
          }
          break;
        case 'fill':
          if (envelope.monthly_budget_amount > 0 && envelope.balance < envelope.monthly_budget_amount) {
            this.allocation.amount = (envelope.monthly_budget_amount - envelope.balance) / 1000;
          }
          break;
      }
    },

    async submitAllocation() {
      if (!this.allocation.amount || this.selectedItem.type !== 'envelope') {
        return;
      }

      const dollarAmount = Number.parseFloat(this.allocation.amount) || 0;
      const amountStr = Math.abs(dollarAmount).toFixed(2);
      const [dollars, cents] = amountStr.split('.');
      const amount = Number.parseInt(dollars) * 1000 + Number.parseInt(cents) * 10;

      try {
        let fromEnvelopeId;
        let toEnvelopeId;

        if (dollarAmount < 0) {
          // Negative allocation: move money from envelope to unallocated
          fromEnvelopeId = this.selectedItem.id;
          toEnvelopeId = 'unallocated';
        } else {
          // Positive allocation: move money from unallocated to envelope
          fromEnvelopeId = 'unallocated';
          toEnvelopeId = this.selectedItem.id;
        }

        const response = await fetch(`/api/envelopes/${window.budgetId}/transfer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.getCookie('csrftoken'),
          },
          body: JSON.stringify({
            from_envelope_id: fromEnvelopeId,
            to_envelope_id: toEnvelopeId,
            amount: amount,
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
          // Update the specific envelope balance locally
          const envelope = this.findEnvelopeById(this.selectedItem.id);
          if (envelope) {
            envelope.balance = dollarAmount < 0 ? data.source_envelope.balance : data.destination_envelope.balance;
          }

          // Update the unallocated envelope balance
          if (this.budget?.unallocated_envelope && data.unallocated_envelope) {
            this.budget.unallocated_envelope.balance = data.unallocated_envelope.balance;
          }

          // Update selected item balance
          this.selectedItem.balance = envelope.balance;

          // Update affected categories
          for (const category of data.affected_categories) {
            const categoryIndex = this.categories.findIndex(cat => cat.id === category.id);
            if (categoryIndex !== -1) {
              this.categories[categoryIndex].balance = category.balance;
            }
          }

          // Reset allocation form
          this.allocation.amount = 0;

          showToast('Allocation completed successfully!');
        } else {
          throw new Error(data.message || 'Failed to allocate funds');
        }
      } catch (error) {
        console.error('Error allocating funds:', error);
        showToast('Failed to allocate funds. Please try again.');
      }
    },

    resetAllocation() {
      this.allocation.amount = 0;
    },
  };
}
