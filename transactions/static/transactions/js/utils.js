function moneyFormat(value) {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  });
  return formatter.format(value / 1000);
}

function formatAmount(amount, type) {
  if ((type === 'outflow' && amount < 0) || (type === 'inflow' && amount >= 0)) {
    return (Math.abs(amount) / 1000).toFixed(2);
  }
  return '';
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const trimmedCookie = cookie.trim();
      if (trimmedCookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(trimmedCookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Global function to enable split mode from envelope select
function enableSplitMode() {
  // Find the Alpine.js component and call toggleSplitMode
  const transactionElement = document.querySelector('[x-data*="transactionData"]');
  if (transactionElement && transactionElement._x_dataStack) {
    const componentData = transactionElement._x_dataStack[0];
    if (componentData && typeof componentData.toggleSplitMode === 'function') {
      if (!componentData.isSplitMode) {
        componentData.toggleSplitMode();
      }
    }
  }
}
