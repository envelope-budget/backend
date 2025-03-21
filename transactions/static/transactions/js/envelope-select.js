class SearchableSelect extends HTMLElement {
  constructor() {
    super();
    this.envelopes = [];
    this.filteredEnvelopes = [];
    this.selectedIndex = -1;
    this.value = null;
    this.isOpen = false;
  }

  async connectedCallback() {
    try {
      // Fetch the data
      const response = await fetch('/envelopes/categorized_envelopes.json');
      const data = await response.json();

      // Extract all envelopes from categories
      this.envelopes = data.categorized_envelopes.flatMap(category =>
        category.envelopes.map(envelope => ({
          id: envelope.id,
          name: envelope.name,
          balance: envelope.balance,
          categoryName: category.category.name,
        }))
      );

      this.filteredEnvelopes = [...this.envelopes];
      this.render();
      this.setupEventListeners();
    } catch (error) {
      console.error('Error loading envelope data:', error);
    }
  }

  render() {
    this.innerHTML = `
      <div class="relative">
        <input type="text"
               class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"
               placeholder="Search envelopes...">
        <div class="envelope-dropdown absolute z-10 w-full mt-1 bg-white rounded-lg border border-gray-200 shadow-md dark:bg-gray-800 dark:border-gray-700 max-h-60 overflow-y-auto hidden">
          ${this.renderOptions()}
        </div>
      </div>
    `;
  }

  renderOptions() {
    if (this.filteredEnvelopes.length === 0) {
      return '<div class="p-2 text-sm text-gray-500 dark:text-gray-400 italic">No matching envelopes found</div>';
    }

    return this.filteredEnvelopes
      .map(
        (envelope, index) => `
      <div class="envelope-option p-2 cursor-pointer text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 ${index === this.selectedIndex ? 'bg-gray-100 dark:bg-gray-700' : ''}"
           data-index="${index}"
           data-id="${envelope.id}">
        ${envelope.name}
        <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">${envelope.categoryName}</span>
      </div>
    `
      )
      .join('');
  }

  updateDropdown() {
    const dropdown = this.querySelector('.envelope-dropdown');
    dropdown.innerHTML = this.renderOptions();

    // Ensure the highlighted option is visible in the dropdown
    if (this.selectedIndex >= 0) {
      const highlighted = dropdown.querySelector(`[data-index="${this.selectedIndex}"]`);
      if (highlighted) {
        highlighted.scrollIntoView({ block: 'nearest' });
      }
    }
  }

  setupEventListeners() {
    const input = this.querySelector('input');
    const dropdown = this.querySelector('.envelope-dropdown');

    // Input focus events
    input.addEventListener('focus', () => {
      this.isOpen = true;
      dropdown.classList.remove('hidden');
    });

    // Input blur events - delayed to allow click events on options
    input.addEventListener('blur', event => {
      // Small delay to allow click events on dropdown options
      setTimeout(() => {
        this.isOpen = false;
        dropdown.classList.add('hidden');
      }, 150);
    });

    // Input text change event
    input.addEventListener('input', event => {
      const searchText = event.target.value.toLowerCase();
      this.filteredEnvelopes = this.envelopes.filter(envelope => envelope.name.toLowerCase().includes(searchText));
      this.selectedIndex = this.filteredEnvelopes.length > 0 ? 0 : -1;
      this.updateDropdown();
    });

    // Keyboard navigation
    input.addEventListener('keydown', event => {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          if (this.filteredEnvelopes.length > 0) {
            this.selectedIndex = (this.selectedIndex + 1) % this.filteredEnvelopes.length;
            this.updateDropdown();
          }
          break;

        case 'ArrowUp':
          event.preventDefault();
          if (this.filteredEnvelopes.length > 0) {
            this.selectedIndex =
              (this.selectedIndex - 1 + this.filteredEnvelopes.length) % this.filteredEnvelopes.length;
            this.updateDropdown();
          }
          break;

        case 'Enter':
          event.preventDefault();
          // If only one option after search, select it
          if (this.filteredEnvelopes.length === 1) {
            this.selectOption(0);
          }
          // Otherwise select the highlighted option
          else if (this.selectedIndex >= 0) {
            this.selectOption(this.selectedIndex);
          }
          break;

        case 'Escape':
          event.preventDefault();
          this.isOpen = false;
          dropdown.classList.add('hidden');
          break;
      }
    });

    // Click event for options
    this.addEventListener('click', event => {
      const option = event.target.closest('.envelope-option');
      if (option) {
        const index = Number.parseInt(option.dataset.index, 10);
        this.selectOption(index);
      }
    });

    // Mouse events for options
    this.addEventListener('mouseover', event => {
      const option = event.target.closest('.envelope-option');
      if (option) {
        const index = Number.parseInt(option.dataset.index, 10);
        this.selectedIndex = index;
        this.updateDropdown();
      }
    });
  }

  selectOption(index) {
    if (index >= 0 && index < this.filteredEnvelopes.length) {
      const selectedEnvelope = this.filteredEnvelopes[index];
      this.value = selectedEnvelope.id;

      // Update input to show the selected value
      const input = this.querySelector('input');
      input.value = selectedEnvelope.name;

      // Close dropdown
      this.isOpen = false;
      this.querySelector('.envelope-dropdown').classList.add('hidden');

      // Dispatch change event
      this.dispatchEvent(
        new CustomEvent('change', {
          detail: {
            value: this.value,
            envelope: selectedEnvelope,
          },
          bubbles: true,
        })
      );
    }
  }

  // Public methods
  getValue() {
    return this.value;
  }

  setValue(id) {
    const envelope = this.envelopes.find(env => env.id === id);
    if (envelope) {
      this.value = id;
      const input = this.querySelector('input');
      if (input) {
        input.value = envelope.name;
      }
    }
  }

  reset() {
    this.value = null;
    const input = this.querySelector('input');
    if (input) {
      input.value = '';
    }
    this.filteredEnvelopes = [...this.envelopes];
    this.selectedIndex = -1;
    this.updateDropdown();
  }
}

// Register the custom element
customElements.define('searchable-select', SearchableSelect);

// Usage example:
// <searchable-select id="envelope-select"></searchable-select>
//
// const select = document.getElementById('envelope-select');
// select.addEventListener('change', (event) => {
//   console.log('Selected envelope:', event.detail.value);
// });
