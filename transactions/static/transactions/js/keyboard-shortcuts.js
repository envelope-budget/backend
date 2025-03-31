/**
 * Sets up keyboard shortcuts for the transactions interface
 * @param {Object} context - The Alpine.js component context (transactionData)
 */
function initKeyboardShortcuts(context) {
  document.addEventListener('keydown', event => {
    // Check if the active element is the search input or any other input/textarea
    const activeElement = document.activeElement;
    const isInputActive =
      activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'SELECT';

    if (event.key === 'Escape') {
      context.cancelTransaction();

      // Remove focus from the active element
      if (activeElement) {
        activeElement.blur();
      }
    }

    // Save transaction on Enter key if form is active (except when in a textarea)
    if (event.key === 'Enter' && context.showEditForm && !(activeElement.tagName === 'TEXTAREA')) {
      // Prevent form submission if the enter was pressed in an input field
      if (isInputActive) {
        event.preventDefault();
      }
      if (!activeElement.classList.contains('search-envelopes')) {
        context.saveTransaction();
      } else {
        activeElement.blur();
      }
      return;
    }

    // If user is typing in an input field, don't trigger other keyboard shortcuts
    if (isInputActive) {
      return;
    }

    if ((event.key === 'j' || event.key === 'k') && !context.showEditForm) {
      const newIndex = context.activeIndex + (event.key === 'j' ? 1 : -1);
      if (newIndex >= 0 && newIndex < context.transactions.length) {
        context.setActiveTransaction(newIndex);
      }
    } else if (event.key === 'a' && !context.showEditForm) {
      context.startNewTransaction();
    } else if (event.key === 'b') {
      context.toBudget();
    } else if (event.key === 'c') {
      context.toggleCleared(context.getActiveTransaction());
    } else if ((event.key === 'e' || event.key === 'Enter') && !context.showEditForm) {
      context.editTransactionAtIndex(context.getActiveTransaction(), context.activeIndex, 'envelope');
    } else if (event.key === 'm') {
      context.mergeSelectedTransactions();
    } else if (event.key === 'x') {
      context.toggleCheckboxInActiveRow();
    } else if (event.key === 'y') {
      context.archive();
    } else if (event.key === '#') {
      context.deleteCheckedRows();
    } else if (event.key === 'g') {
      const keyListener = e => {
        if (e.key === 'i') {
          window.location.href = '/transactions';
        }
        document.removeEventListener('keydown', keyListener);
      };
      document.addEventListener('keydown', keyListener);
    } else if (event.key === '?') {
      // Open the keyboard shortcuts modal
      FlowbiteInstances.getInstance('Modal', 'keyboardShortcutsModal').show();
    }
  });
}
