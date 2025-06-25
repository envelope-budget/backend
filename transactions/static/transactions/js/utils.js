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
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showToast(message, type = 'error') {
  // This function should exist in the main app or be implemented
  // For now, we'll use a simple alert as fallback
  if (window.showToast) {
    window.showToast(message, type);
  } else {
    console.log(`${type.toUpperCase()}: ${message}`);
  }
}
