const pickerOptions = { onEmojiSelect: addEmojiToName };
const picker = new EmojiMart.Picker(pickerOptions);

document.getElementById('emoji-picker').appendChild(picker);

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
});

// Save the order of categories
function saveCategoriesOrder() {
  const categoryItems = document.querySelectorAll('.category-item');
  const orderData = Array.from(categoryItems).map((item, index) => {
    return {
      id: item.getAttribute('data-id'),
      order: index,
    };
  });

  const endpoint = `/api/categories/${window.getCookie('budget_id')}/order`;
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

  const endpoint = `/api/envelopes/${window.getCookie('budget_id')}/order`;
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
  const endpoint = `/api/envelopes/${window.getCookie('budget_id')}/${envelopeId}`;
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
    envelope: {
      id: '',
      name: 'Test',
      balance: 0,
      category_id: '',
      note: 'Test Note',
    },

    category: {
      name: '',
    },

    selectedItem: {
      id: null,
      type: null,
      name: '',
      balance: '',
      categoryName: '',
    },

    categoryForm: {
      id: null,
      name: '',
      isEdit: false,
    },

    searchQuery: '',

    getBalanceColorClass(balance) {
      // Remove currency symbol and commas, then convert to number
      const numericBalance = Number.parseFloat(balance.replace(/[$,]/g, ''));

      if (numericBalance > 0) {
        return 'text-green-600 dark:text-green-400';
      }
      if (numericBalance < 0) {
        return 'text-red-600 dark:text-red-400';
      }
      return 'text-gray-900 dark:text-white';
    },

    // Perform search as user types
    performSearch() {
      const query = this.searchQuery.toLowerCase().trim();

      // If search is empty, show all categories and envelopes
      if (!query) {
        for (const item of document.querySelectorAll('.category-item, .envelope-item')) {
          item.style.display = '';
        }
        return;
      }

      // Hide all categories initially
      for (const category of document.querySelectorAll('.category-item')) {
        category.style.display = 'none';
      }

      // Show envelopes that match the search and their parent categories
      for (const envelope of document.querySelectorAll('.envelope-item')) {
        const envelopeName = envelope.querySelector('.font-medium').textContent.toLowerCase();
        const matches = envelopeName.includes(query);

        envelope.style.display = matches ? '' : 'none';

        // If envelope matches, show its parent category
        if (matches) {
          const categoryItem = envelope.closest('.category-item');
          if (categoryItem) {
            categoryItem.style.display = '';
          }
        }
      }

      // Also check category names
      for (const category of document.querySelectorAll('.category-item')) {
        const categoryHeader = category.querySelector('.category-item > div');
        if (categoryHeader) {
          const categoryName = categoryHeader.querySelector('.font-medium').textContent.toLowerCase();
          if (categoryName.includes(query)) {
            category.style.display = '';
            // Show all envelopes in this category
            for (const envelope of category.querySelectorAll('.envelope-item')) {
              envelope.style.display = '';
            }
          }
        }
      }
    },
    startNewEnvelope(category_id) {
      this.envelope.id = '';
      this.envelope.name = '';
      this.envelope.balance = 0;
      this.envelope.category_id = category_id;
      this.envelope.note = '';
    },

    createEnvelope() {
      const endpoint = `/api/envelopes/${window.getCookie('budget_id')}`;
      const csrfToken = window.getCookie('csrftoken');

      // Prepare the headers
      const headers = new Headers({
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      });

      // Prepare the request options
      const requestOptions = {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          name: this.envelope.name,
          balance: this.envelope.balance,
          category_id: this.envelope.category_id,
          note: this.envelope.note,
        }),
        credentials: 'include', // necessary for cookies to be sent with the request
      };

      // Post to endpoint
      fetch(endpoint, requestOptions)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Envelope created successfully:', data);
          // Refresh the envelope data
          window.location.reload();
        })
        .catch(error => {
          console.error('Error creating envelope:', error);
          // Handle the error case here
        });
    },

    selectCategory(categoryId) {
      // Get the current name from the DOM
      const categoryElement = document.querySelector(`.category-item[data-id="${categoryId}"] .font-medium`);
      const categoryName = categoryElement ? categoryElement.textContent.trim() : '';

      // Get the current balance from the DOM
      const balanceElement = document.querySelector(`.category-item[data-id="${categoryId}"] .text-right.font-medium`);
      const balance = balanceElement ? balanceElement.textContent.trim() : '$0.00';

      this.selectedItem = {
        id: categoryId,
        type: 'category',
        name: categoryName,
        balance: balance,
      };
    },

    selectEnvelope(id, name, balance, categoryName) {
      this.selectedItem = {
        id: id,
        type: 'envelope',
        name: name,
        balance: balance,
        categoryName: categoryName,
      };

      // Add selected class to the clicked envelope
      for (const el of document.querySelectorAll('.category-item, .envelope-item')) {
        el.classList.remove('selected-item');
      }
      document.querySelector(`.envelope-item[data-id="${id}"]`).classList.add('selected-item');
    },

    editCategory(categoryId) {
      this.categoryForm.isEdit = true;
      this.categoryForm.id = categoryId;
      this.categoryForm.name = this.selectedItem.name;

      // The modal will be shown by the data-modal-toggle attribute
    },

    saveCategory() {
      const budgetId = getCookie('budget_id');
      console.log(`Saving category in budget id: ${budgetId}`);
      const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      };

      if (this.categoryForm.isEdit) {
        // Update existing category
        const url = `/api/categories/${budgetId}/${this.categoryForm.id}`;

        fetch(url, {
          method: 'PATCH',
          headers,
          body: JSON.stringify({
            name: this.categoryForm.name,
          }),
          credentials: 'include',
        })
          .then(response => {
            if (!response.ok) {
              throw new Error('Failed to update category');
            }
            return response.json();
          })
          .then(data => {
            // Update the category name in the UI
            const categoryElement = document.querySelector(
              `.category-item[data-id="${this.categoryForm.id}"] .font-medium`
            );
            if (categoryElement) {
              categoryElement.textContent = this.categoryForm.name;
            }

            // Update the selected item if it's the current category
            if (this.selectedItem.id === this.categoryForm.id && this.selectedItem.type === 'category') {
              this.selectedItem.name = this.categoryForm.name;
            }

            // Close the modal
            FlowbiteInstances.getInstance('Modal', 'category-modal').hide();

            // Reset the form
            this.resetCategoryForm();
          })
          .catch(error => {
            console.error('Error updating category:', error);
            // Show error message to user
            alert('Failed to update category. Please try again.');
          });
      } else {
        const endpoint = `/api/categories/${budgetId}`;

        // Prepare the request options
        const requestOptions = {
          method: 'POST',
          headers,
          body: JSON.stringify({
            name: this.categoryForm.name,
          }),
          credentials: 'include', // necessary for cookies to be sent with the request
        };

        // Post to endpoint
        fetch(endpoint, requestOptions)
          .then(response => {
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            console.log('Category created successfully:', data);
            // Refresh the page to show the new category
            window.location.reload();
          })
          .catch(error => {
            console.error('Error creating category:', error);
            // Handle the error case here
          });
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
        balance: '',
        type: null,
        categoryName: '',
        categoryId: null,
      };
      // Remove highlight from all items
      for (const item of document.querySelectorAll('.category-item, .envelope-item')) {
        item.classList.remove('selected-item');
      }
    },
    editEnvelope(id) {
      // Implement envelope editing logic
      console.log('Edit envelope:', id);
    },
  };
}
