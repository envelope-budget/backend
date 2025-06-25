async function get_transactions(budgetId, page = 1, pageSize = 20, accountId = null) {
  const offset = (page - 1) * pageSize;
  let url = `/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}&in_inbox=true`;
  const csrfToken = getCookie('csrftoken');

  if (accountId) {
    url += `&account_id=${accountId}`;
  }

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

async function get_transactions_with_search(budgetId, page = 1, pageSize = 20, accountId = null, searchQuery = null) {
  const offset = (page - 1) * pageSize;
  let url = `/api/transactions/${budgetId}?offset=${offset}&limit=${pageSize}`;

  // If we're not searching, show inbox transactions by default
  if (!searchQuery) {
    url += '&in_inbox=true';
  }

  const csrfToken = getCookie('csrftoken');

  if (accountId) {
    url += `&account_id=${accountId}`;
  }

  // Add search query if provided
  if (searchQuery) {
    url += `&search=${encodeURIComponent(searchQuery)}`;
  }

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

async function patchTransaction(id, data) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/${id}`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    return responseData; // Return the parsed JSON data.
  } catch (error) {
    console.error('Error updating transaction:', error);
    throw error; // Rethrow the error to be handled by the caller.
  }
}

async function bulkArchiveTransactions(transaction_ids) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/archive`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ transaction_ids }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error archiving transactions:', error);
    showToast('Error archiving transactions');
    throw error;
  }
}

async function mergeTransactions(transaction_ids) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/merge`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ transaction_ids }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error merging transactions:', error);
    showToast(error.message || 'Error merging transactions');
    throw error;
  }
}

async function deleteTransaction(transaction_id) {
  const budgetId = getCookie('budget_id');
  const url = `/api/transactions/${budgetId}/${transaction_id}`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': csrfToken,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json(); // or handle the response as needed
  } catch (error) {
    showToast('Error deleting transaction');
    console.error('Error deleting transaction:', error);
    // Handle the error appropriately in your application
  }
}

async function updateAccountBalances() {
  const budgetId = getCookie('budget_id');
  const url = `/api/accounts/${budgetId}`;
  const csrfToken = getCookie('csrftoken');

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    for (const account of data) {
      const accountBalanceElement = document.getElementById(`id_account_balance_${account.id}`);
      if (accountBalanceElement) {
        accountBalanceElement.innerText = moneyFormat(account.balance);
      }
    }
  } catch (error) {
    showToast('Error updating account balances');
    console.error('Error updating account balances:', error);
    throw error; // Rethrow the error to be handled by the caller.
  }
}
