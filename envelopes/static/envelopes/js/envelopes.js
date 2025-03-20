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

    createCategory() {
      const budgetId = window.getCookie('budget_id');
      const endpoint = `/api/categories/${budgetId}`;
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
          name: this.category.name,
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
  };
}
