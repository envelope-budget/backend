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

  const endpoint = `/api/categories/${window.budgetId}/order`;
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
        console.log(`Budget ID: ${window.budgetId}`);
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
        this.showToast('Failed to load envelopes. Please refresh the page.');
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
      const dollars = amount / 100;
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
          // Reload data to show updated balances
          await this.loadEnvelopes();
          this.showToast('Funds allocated successfully!');
        } else {
          throw new Error(data.message || 'Failed to allocate funds');
        }
      } catch (error) {
        console.error('Error allocating funds:', error);
        this.showToast('Failed to allocate funds. Please check if you have enough unallocated funds.');
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
          // Reload data to show updated balances
          await this.loadEnvelopes();
          this.showToast('Funds swept to unallocated successfully!');
        } else {
          throw new Error(data.message || 'Failed to sweep funds');
        }
      } catch (error) {
        console.error('Error sweeping funds:', error);
        this.showToast('Failed to sweep funds. Please try again.');
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
            balance: this.envelope.balance,
            category_id: this.envelope.category_id,
            note: this.envelope.note,
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

        this.showToast('Envelope created successfully!');
      } catch (error) {
        console.error('Error creating envelope:', error);
        this.showToast('Failed to create envelope. Please try again.');
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

          this.showToast('Category updated successfully!');
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
          this.showToast('Category created successfully!');
        }

        // Close the modal
        const modal = FlowbiteInstances.getInstance('Modal', 'category-modal');
        if (modal) modal.hide();

        // Reset the form
        this.resetCategoryForm();
      } catch (error) {
        console.error('Error saving category:', error);
        this.showToast('Failed to save category. Please try again.');
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
          balance: envelope.balance,
          category_id: envelope.category_id,
          note: envelope.note || '',
        };
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

    showToast(message) {
      // Simple toast implementation - you can replace with your preferred toast library
      console.log('Toast:', message);
      // You could implement a proper toast notification here
      alert(message); // Temporary - replace with proper toast
    },
  };
}
