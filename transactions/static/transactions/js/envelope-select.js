class EnvelopeDataManager {
  constructor() {
    this.envelopes = [];
    this.accounts = [];
    this.dataLoaded = false;
    this.loadPromise = null;
  }

  loadData() {
    if (this.loadPromise) {
      return this.loadPromise;
    }

    this.loadPromise = this._fetchData();
    return this.loadPromise;
  }

  async _fetchData() {
    if (this.dataLoaded) {
      return { envelopes: this.envelopes, accounts: this.accounts };
    }

    try {
      // Fetch envelopes
      const response = await fetch('/envelopes/categorized_envelopes.json');
      const data = await response.json();

      this.envelopes = data.categorized_envelopes.flatMap(category =>
        category.envelopes.map(envelope => ({
          id: envelope.id,
          name: envelope.name,
          balance: envelope.balance,
          categoryName: category.category.name,
          linked_account_name: envelope.linked_account_name,
        }))
      );

      // Get accounts from the existing dropdown if available
      const accountSelect = document.getElementById('id_account');
      if (accountSelect) {
        this.accounts = Array.from(accountSelect.options)
          .filter(option => option.value && option.value !== '')
          .map(option => ({
            id: option.value,
            name: option.textContent,
          }));
      }

      this.dataLoaded = true;
      return { envelopes: this.envelopes, accounts: this.accounts };
    } catch (error) {
      console.error('Error loading envelope/account data:', error);
      throw error;
    }
  }

  getEnvelopes() {
    return this.envelopes;
  }

  getAccounts() {
    return this.accounts;
  }
}

// Create a singleton instance
const envelopeDataManager = new EnvelopeDataManager();

// Export for use in other components
window.envelopeDataManager = envelopeDataManager;

class SearchableSelect extends HTMLElement {
  constructor() {
    super();
    this.envelopes = [];
    this.filteredEnvelopes = [];
    this.selectedIndex = -1;
    this.value = null;
    this.isOpen = false;
    this.isClickingDropdown = false;
    this.showSplitOption = true;
  }

  async connectedCallback() {
    try {
      // Use the shared data manager
      const data = await envelopeDataManager.loadData();
      this.envelopes = data.envelopes;

      this.filteredEnvelopes = [...this.envelopes];

      // Check if this is a split row selector (hide split option for split rows)
      if (this.id?.includes('split_envelope')) {
        this.showSplitOption = false;
      }

      this.render();
      this.setupEventListeners();

      // Check if there's a value set by Alpine.js
      // This will handle the case when editing an existing transaction
      if (this.hasAttribute('data-selected-id')) {
        const selectedId = this.getAttribute('data-selected-id');
        if (selectedId) {
          this.setValue(selectedId);
        }
      }
    } catch (error) {
      console.error('Error loading envelope data:', error);
    }
  }

  render() {
    this.innerHTML = `
      <div class="relative">
        <input type="text"
               class="search-envelopes bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"
               placeholder="Search envelopes...">
      </div>
    `;

    // Create dropdown as a separate element appended to body
    this.dropdown = document.createElement('div');
    this.dropdown.className =
      'envelope-dropdown absolute z-50 bg-white rounded-lg border border-gray-200 shadow-md dark:bg-gray-800 dark:border-gray-700 max-h-60 overflow-y-auto hidden';
    this.dropdown.style.minWidth = '200px';
    this.dropdown.innerHTML = this.renderOptions();
    document.body.appendChild(this.dropdown);
  }

  renderOptions() {
    let content = '';

    // Add split option if it should be shown
    if (this.showSplitOption !== false) {
      // Split option is highlighted when selectedIndex is -1 (if split is shown) or 0 (if split is first item)
      const isSplitHighlighted = this.selectedIndex === -1;
      const splitHighlightClass = isSplitHighlighted
        ? 'bg-blue-100 dark:bg-blue-900'
        : 'hover:bg-gray-100 dark:hover:bg-gray-700';

      content += `
        <div class="envelope-option p-2 ${splitHighlightClass} cursor-pointer border-b border-gray-200 dark:border-gray-600"
             data-envelope-id="split"
             data-index="-1">
            <div class="flex justify-between items-center">
                <div>
                    <span class="font-medium text-blue-600 dark:text-blue-400">Split...</span>
                    <div class="text-xs text-gray-500">Split between multiple envelopes</div>
                </div>
                <span class="text-sm text-gray-400">⚡</span>
            </div>
        </div>
      `;
    }

    if (this.filteredEnvelopes.length === 0) {
      if (this.showSplitOption !== false) {
        return content;
      }
      return '<div class="p-2 text-gray-500 dark:text-gray-400">No envelopes found</div>';
    }

    const envelopeOptions = this.filteredEnvelopes
      .map((envelope, index) => {
        // When split option is shown, envelope indices start from 0 (selectedIndex 0, 1, 2...)
        // When split option is not shown, envelope indices also start from 0
        const isHighlighted =
          this.showSplitOption !== false
            ? this.selectedIndex === index // Split takes selectedIndex -1, envelopes start at 0
            : this.selectedIndex === index;

        const highlightClass = isHighlighted
          ? 'bg-blue-100 dark:bg-blue-900'
          : 'hover:bg-gray-100 dark:hover:bg-gray-700';

        return `
            <div class="envelope-option p-2 ${highlightClass} cursor-pointer"
                 data-envelope-id="${envelope.id}"
                 data-index="${index}">
                <div class="flex justify-between items-center">
                    <div>
                        <span class="font-medium">${envelope.name}</span>
                        <div class="text-xs text-gray-500">${envelope.categoryName}</div>
                        ${envelope.linked_account_name ? `<span class="text-xs text-blue-600 dark:text-blue-400">🔗 ${envelope.linked_account_name}</span>` : ''}
                    </div>
                    <span class="text-sm ${envelope.balance >= 0 ? 'text-green-600' : 'text-red-600'}">
                        ${(envelope.balance / 1000).toFixed(2)}
                    </span>
                </div>
            </div>
        `;
      })
      .join('');

    return content + envelopeOptions;
  }

  updateDropdown() {
    this.dropdown.innerHTML = this.renderOptions();

    // Don't re-setup listeners, just use event delegation
    // The click listener on the dropdown container will handle clicks on new options

    // Ensure the highlighted option is visible in the dropdown
    if (this.selectedIndex >= -1) {
      let highlighted;

      if (this.selectedIndex === -1 && this.showSplitOption !== false) {
        // Split option is selected
        highlighted = this.dropdown.querySelector('[data-envelope-id="split"]');
      } else {
        // Regular envelope option is selected
        const envelopeIndex = this.showSplitOption !== false ? this.selectedIndex - 1 : this.selectedIndex;
        highlighted = this.dropdown.querySelector(`[data-index="${envelopeIndex}"]`);
      }

      if (highlighted) {
        highlighted.scrollIntoView({ block: 'nearest' });
      }
    }
  }

  setupEventListeners() {
    const input = this.querySelector('input');

    // Input focus events
    input.addEventListener('focus', () => {
      this.isOpen = true;

      // Initialize selectedIndex if not set
      if (this.selectedIndex === -1) {
        const totalItems = this.getTotalSelectableItems();
        if (totalItems > 0) {
          this.selectedIndex = this.showSplitOption !== false ? -1 : 0;
        }
      }

      // Position the dropdown relative to the input
      const inputRect = input.getBoundingClientRect();
      this.dropdown.style.left = `${inputRect.left}px`;
      this.dropdown.style.top = `${inputRect.bottom + window.scrollY}px`;
      this.dropdown.style.width = `${inputRect.width}px`;

      this.dropdown.classList.remove('hidden');
    });

    // Input blur events - increase delay significantly
    input.addEventListener('blur', event => {
      setTimeout(() => {
        if (this.isOpen) {
          this.closeDropdown();
        }
      }, 300); // Increased delay
    });

    // Input text change event
    input.addEventListener('input', event => {
      const searchText = event.target.value.toLowerCase();
      this.filteredEnvelopes = this.envelopes.filter(envelope => envelope.name.toLowerCase().includes(searchText));

      // Check if "Split..." should be included in filtered results
      this.showSplitOption = searchText === '' || 'split'.includes(searchText);

      // Reset to first item (split if available, otherwise first envelope)
      const totalItems = this.getTotalSelectableItems();
      this.selectedIndex = totalItems > 0 ? (this.showSplitOption !== false ? -1 : 0) : -1;

      this.updateDropdown();
    });

    // Keyboard navigation
    input.addEventListener('keydown', event => {
      const totalItems = this.getTotalSelectableItems();

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          if (totalItems > 0) {
            if (this.showSplitOption !== false) {
              // With split: -1 (split) -> 0, 1, 2... (envelopes) -> -1
              if (this.selectedIndex === -1) {
                this.selectedIndex = this.filteredEnvelopes.length > 0 ? 0 : -1;
              } else {
                this.selectedIndex = (this.selectedIndex + 1) % this.filteredEnvelopes.length;
                if (this.selectedIndex === 0 && this.filteredEnvelopes.length > 1) {
                  // Continue to next envelope
                } else if (this.selectedIndex === 0) {
                  // Wrap back to split
                  this.selectedIndex = -1;
                }
              }
            } else {
              // Without split: normal 0-based indexing
              this.selectedIndex = (this.selectedIndex + 1) % this.filteredEnvelopes.length;
            }
            this.updateDropdown();
          }
          break;

        case 'ArrowUp':
          event.preventDefault();
          if (totalItems > 0) {
            if (this.showSplitOption !== false) {
              // With split: navigate between -1 and envelope indices
              if (this.selectedIndex === -1) {
                this.selectedIndex = this.filteredEnvelopes.length > 0 ? this.filteredEnvelopes.length - 1 : -1;
              } else if (this.selectedIndex === 0) {
                this.selectedIndex = -1;
              } else {
                this.selectedIndex = this.selectedIndex - 1;
              }
            } else {
              // Without split: normal 0-based indexing
              this.selectedIndex =
                (this.selectedIndex - 1 + this.filteredEnvelopes.length) % this.filteredEnvelopes.length;
            }
            this.updateDropdown();
          }
          break;

        case 'Enter':
          if (this.isOpen) {
            event.preventDefault();
            event.stopPropagation();

            if (this.selectedIndex === -1 && this.showSplitOption !== false) {
              this.selectSplitOption();
            } else if (this.selectedIndex >= 0 && this.selectedIndex < this.filteredEnvelopes.length) {
              this.selectOption(this.selectedIndex);
            }
          }
          break;

        case 'Escape':
          event.preventDefault();
          this.closeDropdown();
          break;
      }
    });

    // Set up initial dropdown listeners
    this.setupDropdownListeners();
  }

  setupDropdownListeners() {
    // Use this.dropdown instead of querySelector since it's appended to document.body
    if (!this.dropdown) {
      return;
    }

    // Use event delegation - listen on the dropdown container
    this.dropdown.addEventListener('click', event => {
      // Find the option element
      const option = event.target.closest('.envelope-option');

      if (option) {
        // Prevent the blur event from firing
        event.preventDefault();
        event.stopPropagation();

        const envelopeId = option.getAttribute('data-envelope-id');
        const index = option.getAttribute('data-index');

        // Handle split option
        if (envelopeId === 'split') {
          setTimeout(() => {
            this.selectSplitOption();
          }, 10);
          return;
        }

        if (index !== null) {
          const parsedIndex = Number.parseInt(index, 10);

          // Add a small delay to ensure the click is processed before blur
          setTimeout(() => {
            this.selectOption(parsedIndex);
          }, 10);
        }
      }
    });
  }

  closeDropdown() {
    this.isOpen = false;
    if (this.dropdown) {
      this.dropdown.classList.add('hidden');
    }
  }

  selectOption(index) {
    if (index >= 0 && index < this.filteredEnvelopes.length) {
      const selectedEnvelope = this.filteredEnvelopes[index];
      this.value = selectedEnvelope.id;

      // Update input to show the selected value
      const input = this.querySelector('input');
      input.value = selectedEnvelope.name;

      // Close dropdown - use this.dropdown instead of querySelector
      this.isOpen = false;
      this.dropdown.classList.add('hidden');

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

  selectSplitOption() {
    this.value = 'split';

    // Update input to show the selected value
    const input = this.querySelector('input');
    input.value = '⚡️ Split...';

    // Close dropdown
    this.isOpen = false;
    this.dropdown.classList.add('hidden');

    // Dispatch change event with split indicator
    this.dispatchEvent(
      new CustomEvent('change', {
        detail: {
          value: 'split',
          envelope: null,
          isSplit: true,
        },
        bubbles: true,
      })
    );
  }

  // Public methods
  getValue() {
    return this.value;
  }

  setValue(id) {
    if (!id) {
      this.reset();
      return;
    }

    const envelope = this.envelopes.find(env => env.id === id);
    if (envelope) {
      this.value = id;
      const input = this.querySelector('input');
      if (input) {
        input.value = envelope.name;
      }

      // Dispatch change event to ensure Alpine.js knows the value changed
      this.dispatchEvent(
        new CustomEvent('change', {
          detail: {
            value: this.value,
            envelope: envelope,
          },
          bubbles: true,
        })
      );
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

  getTotalSelectableItems() {
    const splitCount = this.showSplitOption !== false ? 1 : 0;
    return splitCount + this.filteredEnvelopes.length;
  }

  getSelectedItem() {
    if (this.selectedIndex === -1 && this.showSplitOption !== false) {
      return { type: 'split' };
    }
    if (this.selectedIndex >= 0) {
      const envelopeIndex = this.showSplitOption !== false ? this.selectedIndex - 1 : this.selectedIndex;
      if (envelopeIndex >= 0 && envelopeIndex < this.filteredEnvelopes.length) {
        return { type: 'envelope', envelope: this.filteredEnvelopes[envelopeIndex], index: envelopeIndex };
      }
    }
    return null;
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
