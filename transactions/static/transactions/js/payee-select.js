class PayeeSelect extends HTMLElement {
  constructor() {
    super();
    this.payees = [];
    this.filteredPayees = [];
    this.selectedIndex = -1;
    this.isOpen = false;
    this.selectedPayeeId = null;
    this.selectedPayeeName = '';
    this.isCommitted = false;
  }

  connectedCallback() {
    this.innerHTML = `
      <div class="relative">
        <input
          type="text"
          class="payee-input block w-full p-1 text-gray-900 border border-gray-300 rounded bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
          placeholder="Enter payee..."
          autocomplete="off"
        />
        <div class="payee-dropdown absolute z-50 w-full bg-white border border-gray-300 rounded-b-lg shadow-lg max-h-48 overflow-y-auto hidden dark:bg-gray-700 dark:border-gray-600">
        </div>
      </div>
    `;

    this.input = this.querySelector('.payee-input');
    this.dropdown = this.querySelector('.payee-dropdown');

    this.setupEventListeners();

    this.loadPayees().then(() => {
      const selectedId = this.getAttribute('data-selected-id');
      const selectedName = this.getAttribute('data-selected-name');

      if (selectedId) {
        this.setPayeeById(selectedId);
      } else if (selectedName) {
        this.setPayeeByName(selectedName);
      }
    });
  }

  setupEventListeners() {
    this.input.addEventListener('input', e => {
      this.handleInput(e.target.value);
    });

    this.input.addEventListener('keydown', e => {
      this.handleKeydown(e);
    });

    this.input.addEventListener('focus', () => {
      if (this.input.value.trim()) {
        this.showDropdown();
      }
    });

    this.input.addEventListener('blur', e => {
      const currentValue = this.input.value.trim();
      if (currentValue) {
        if (!this.selectedPayeeId || this.selectedPayeeName !== currentValue) {
          this.selectedPayeeId = null;
          this.selectedPayeeName = currentValue;
          this.dispatchChangeEvent();
        }
      }

      setTimeout(() => {
        this.hideDropdown();
      }, 150);
    });

    document.addEventListener('click', e => {
      if (!this.contains(e.target)) {
        this.hideDropdown();
      }
    });
  }

  async loadPayees() {
    try {
      const response = await fetch('/transactions/payees.json');
      if (response.ok) {
        const data = await response.json();
        this.payees = data.payees;

        if (this._pendingValue) {
          this.setValue(this._pendingValue);
          this._pendingValue = null;
        }

        this.dispatchEvent(new CustomEvent('payees-ready', { bubbles: true }));
      }
    } catch (error) {
      console.error('Error loading payees:', error);
    }
  }

  handleInput(value) {
    this.selectedPayeeId = null;
    this.selectedPayeeName = value;
    this.isCommitted = false;

    if (value.trim()) {
      this.filterPayees(value);
      this.showDropdown();
    } else {
      this.hideDropdown();
    }

    this.dispatchChangeEvent();
  }

  filterPayees(query) {
    const lowerQuery = query.toLowerCase();
    this.filteredPayees = this.payees.filter(payee => payee.name.toLowerCase().includes(lowerQuery));
    this.selectedIndex = -1;
    this.renderDropdown();
  }

  renderDropdown() {
    if (this.filteredPayees.length === 0) {
      this.dropdown.innerHTML = `
        <div class="px-3 py-2 text-gray-500 dark:text-gray-400">
          No payees found. Press Enter to create "${this.input.value}"
        </div>
      `;
    } else {
      this.dropdown.innerHTML = this.filteredPayees
        .map(
          (payee, index) => `
        <div class="payee-option px-3 py-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 ${
          index === this.selectedIndex ? 'bg-blue-100 dark:bg-blue-600' : ''
        }" data-payee-id="${payee.id}" data-payee-name="${payee.name}">
          ${this.escapeHtml(payee.name)}
        </div>
      `
        )
        .join('');

      this.dropdown.querySelectorAll('.payee-option').forEach((option, index) => {
        option.addEventListener('click', () => {
          this.selectPayee(index);
        });
      });
    }
  }

  handleKeydown(e) {
    if (!this.isOpen) {
      if (e.key === 'ArrowDown' && this.input.value.trim()) {
        e.preventDefault();
        this.showDropdown();
        return;
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        const hadChange = this.selectCurrentValue();
        if (hadChange) {
          e.stopPropagation();
        }
        return;
      }
      if (e.key === 'Tab') {
        this.selectCurrentValue();
        return;
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredPayees.length - 1);
        this.updateSelection();
        break;
      case 'ArrowUp':
        e.preventDefault();
        this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
        this.updateSelection();
        break;
      case 'Enter': {
        e.preventDefault();
        let hadChange = false;
        if (this.selectedIndex >= 0) {
          hadChange = this.selectPayee(this.selectedIndex);
        } else {
          hadChange = this.selectCurrentValue();
        }
        if (hadChange) {
          e.stopPropagation();
        }
        break;
      }
      case 'Tab':
        if (this.selectedIndex >= 0) {
          this.selectPayee(this.selectedIndex);
        } else {
          this.selectCurrentValue();
        }
        break;
      case 'Escape':
        e.preventDefault();
        this.hideDropdown();
        this.input.blur();
        break;
    }
  }

  updateSelection() {
    this.dropdown.querySelectorAll('.payee-option').forEach((option, index) => {
      if (index === this.selectedIndex) {
        option.classList.add('bg-blue-100', 'dark:bg-blue-600');
        option.scrollIntoView({ block: 'nearest' });
      } else {
        option.classList.remove('bg-blue-100', 'dark:bg-blue-600');
      }
    });
  }

  selectPayee(index) {
    const payee = this.filteredPayees[index];
    const hadChange = this.selectedPayeeId !== payee.id || this.selectedPayeeName !== payee.name || !this.isCommitted;

    this.selectedPayeeId = payee.id;
    this.selectedPayeeName = payee.name;
    this.input.value = payee.name;
    this.isCommitted = true;
    this.hideDropdown();

    if (hadChange) {
      this.dispatchChangeEvent();
    }

    return hadChange;
  }

  selectCurrentValue() {
    const currentValue = this.input.value.trim();
    const hadChange = !this.isCommitted;

    this.selectedPayeeId = null;
    this.selectedPayeeName = currentValue;
    this.isCommitted = true;
    this.hideDropdown();

    if (hadChange) {
      this.dispatchChangeEvent();
    }

    return hadChange;
  }

  showDropdown() {
    this.isOpen = true;
    this.dropdown.classList.remove('hidden');
  }

  hideDropdown() {
    this.isOpen = false;
    this.dropdown.classList.add('hidden');
    this.selectedIndex = -1;
  }

  setPayeeById(payeeId) {
    const payee = this.payees.find(p => String(p.id) === String(payeeId));
    if (payee) {
      this.selectedPayeeId = payee.id;
      this.selectedPayeeName = payee.name;
      this.input.value = payee.name;
      this.dispatchChangeEvent();
    }
  }

  setPayeeByName(payeeName) {
    const payee = this.payees.find(p => p.name === payeeName);
    if (payee) {
      this.selectedPayeeId = payee.id;
      this.selectedPayeeName = payee.name;
    } else {
      this.selectedPayeeId = null;
      this.selectedPayeeName = payeeName;
    }
    this.input.value = payeeName;
    this.dispatchChangeEvent();
  }

  getValue() {
    return {
      id: this.selectedPayeeId,
      name: this.selectedPayeeName,
    };
  }

  setValue(payeeData) {
    if (this.payees.length === 0) {
      this._pendingValue = payeeData;
      return;
    }

    if (typeof payeeData === 'string') {
      this.setPayeeByName(payeeData);
    } else if (payeeData?.id) {
      this.setPayeeById(payeeData.id);
    } else if (payeeData?.name) {
      this.setPayeeByName(payeeData.name);
    }
  }

  clear() {
    this.selectedPayeeId = null;
    this.selectedPayeeName = '';
    this.input.value = '';
    this.hideDropdown();
    this.dispatchChangeEvent();
  }

  focus() {
    this.input.focus();
  }

  dispatchChangeEvent() {
    this.dispatchEvent(
      new CustomEvent('change', {
        detail: {
          id: this.selectedPayeeId,
          name: this.selectedPayeeName,
        },
        bubbles: true,
      })
    );
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

customElements.define('payee-select', PayeeSelect);
