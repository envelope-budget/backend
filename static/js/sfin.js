// Add styles for active button
const styleElement = document.createElement('style');
styleElement.textContent = `
    .active-type {
      background-color: #1d4ed8 !important;
      color: white !important;
    }
  `;
document.head.appendChild(styleElement);

let sfinData = {};

// Function to fetch SimpleFIN accounts
function fetchSimpleFINAccounts() {
  budgetId = getCookie('budget_id');
  sfinAccountsEndpoint = `/api/accounts/${budgetId}/simplefin/accounts`;
  fetch(sfinAccountsEndpoint)
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch SimpleFIN accounts');
      }
      return response.json();
    })
    .then(data => {
      console.log('SimpleFIN accounts response:', data);
      if (data.errors && data.errors.length > 0) {
        throw new Error(data.errors.join(', '));
      }
      sfinData = data;
      displayAccounts(data.accounts || []);
    })
    .catch(error => {
      console.error('Error fetching SimpleFIN accounts:', error);
      document.querySelector('.text-center').innerHTML = `
          <div class="text-red-500 mt-4">
            <p>Error loading accounts: ${error.message}</p>
            <button class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" onclick="fetchSimpleFINAccounts()">
              Try Again
            </button>
          </div>
        `;
    });
}

// Function to display accounts with checkboxes
function displayAccounts(accounts) {
  const container = document.querySelector('.simplefin-modal-container');

  if (!accounts || accounts.length === 0) {
    container.innerHTML = `
        <div class="mt-4">
          <p class="text-gray-700">No SimpleFIN accounts found.</p>
        </div>
      `;
    return;
  }

  // Group accounts by organization
  const accountsByOrg = {};
  for (const account of accounts) {
    const orgName = account.org.name;
    if (!accountsByOrg[orgName]) {
      accountsByOrg[orgName] = [];
    }
    accountsByOrg[orgName].push(account);
  }

  let html = `
      <div class="mt-4">
        <h3 class="text-lg font-medium mb-3">Select accounts to add:</h3>
        <form id="add-accounts-form" class="space-y-4">
    `;

  // Create sections for each organization
  for (const orgName of Object.keys(accountsByOrg)) {
    html += `
        <div class="border rounded p-3">
          <h4 class="font-bold text-lg mb-2">${orgName}</h4>
          <div class="grid gap-2">
      `;
    for (const account of accountsByOrg[orgName]) {
      // Format balance for display
      const balance = Number.parseFloat(account.balance);
      const formattedBalance = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: account.currency || 'USD',
      }).format(balance);

      html += `
          <div class="p-3 border rounded shadow hover:bg-gray-50 text-left">
            <div class="flex items-center mb-2">
              <input type="checkbox"
                     id="account-${account.id}"
                     name="selected_accounts"
                     value="${account.id}"
                     data-name="${account.name.replace(/"/g, '"')}"
                     data-org="${account.org.name.replace(/"/g, '"')}"
                     class="mr-3 h-5 w-5 text-blue-600 rounded">
              <label for="account-${account.id}" class="flex-grow flex justify-between items-center cursor-pointer">
                <span class="font-medium">${account.name}</span>
                <span class="${balance < 0 ? 'text-red-600' : 'text-green-600'} font-medium">${formattedBalance}</span>
              </label>
            </div>

            <div class="ml-8 mt-2">
              <p class="text-sm text-gray-500 mb-1">Account Type:</p>
              <div class="inline-flex rounded-md shadow-sm" role="group">
                <button type="button" data-account-id="${account.id}" data-type="checking" class="account-type-btn px-2 py-1 text-xs font-medium text-gray-900 bg-white border border-gray-200 rounded-l-lg hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 active-type">
                  Checking
                </button>
                <button type="button" data-account-id="${account.id}" data-type="savings" class="account-type-btn px-2 py-1 text-xs font-medium text-gray-900 bg-white border-t border-b border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700">
                  Savings
                </button>
                <button type="button" data-account-id="${account.id}" data-type="credit_card" class="account-type-btn px-2 py-1 text-xs font-medium text-gray-900 bg-white border-t border-b border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700">
                  Credit Card
                </button>
                <button type="button" data-account-id="${account.id}" data-type="loan" class="account-type-btn px-2 py-1 text-xs font-medium text-gray-900 bg-white border border-gray-200 rounded-r-md hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700">
                  Loan
                </button>
              </div>
              <input type="hidden" name="account_type_${account.id}" data-account-id="${account.id}" value="checking">
            </div>          </div>
        `;
    }

    html += `
          </div>
        </div>
      `;
  }

  html += `
        <div class="flex justify-end mt-4">
          <button type="button" id="add-selected-accounts" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed" disabled>
            Add Selected Accounts
          </button>
        </div>
        </form>
      </div>
    `;

  container.innerHTML = html;

  // Add event listeners for checkboxes and submit button
  const checkboxes = document.querySelectorAll('input[name="selected_accounts"]');
  const submitButton = document.getElementById('add-selected-accounts');
  for (const checkbox of checkboxes) {
    checkbox.addEventListener('change', () => {
      // Enable the submit button if at least one checkbox is checked
      submitButton.disabled = !Array.from(checkboxes).some(cb => cb.checked);
    });
  }

  submitButton.addEventListener('click', addSelectedAccounts);

  // Add event listeners for account type buttons
  const accountTypeButtons = document.querySelectorAll('.account-type-btn');
  for (const button of accountTypeButtons) {
    button.addEventListener('click', function () {
      const accountId = this.getAttribute('data-account-id');
      const accountType = this.getAttribute('data-type');

      // Update hidden input with selected type using querySelector with data attribute
      const hiddenInput = document.querySelector(`input[data-account-id="${accountId}"]`);
      if (hiddenInput) {
        hiddenInput.value = accountType;
      }

      // Update button styles in this group
      const buttons = document.querySelectorAll(`.account-type-btn[data-account-id="${accountId}"]`);
      for (const btn of buttons) {
        btn.classList.remove('active-type', 'bg-blue-700', 'text-white');
        btn.classList.add('bg-white', 'text-gray-900');
      }

      // Add active style to clicked button
      this.classList.remove('bg-white', 'text-gray-900');
      this.classList.add('active-type', 'bg-blue-700', 'text-white');
    });
  }
}
// Function to handle adding multiple selected accounts
function addSelectedAccounts() {
  const selectedCheckboxes = document.querySelectorAll('input[name="selected_accounts"]:checked');

  if (selectedCheckboxes.length === 0) {
    return;
  }

  // Disable the button to prevent multiple submissions
  document.getElementById('add-selected-accounts').disabled = true;

  // Get all selected account IDs with their types
  console.log(
    'Selected account IDs:',
    Array.from(selectedCheckboxes).map(cb => cb.value)
  );
  const accountData = Array.from(selectedCheckboxes).map(cb => {
    const accountId = cb.value;
    const accountTypeElement = document.querySelector(`input[data-account-id="${accountId}"]`);
    console.log(`Looking for input with data-account-id="${accountId}":`, accountTypeElement);
    const accountType = accountTypeElement ? accountTypeElement.value : 'checking';

    return {
      id: accountId,
      type: accountType,
    };
  });

  console.log('Account data:', accountData);

  // Show loading state
  document.querySelector('.simplefin-modal-container').innerHTML = `
    <div class="text-center">
      <div role="status">
        <svg aria-hidden="true" class="inline w-8 h-8 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor" />
          <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill" />
        </svg>
        <span class="sr-only">Loading...</span>
      </div>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">Adding ${selectedCheckboxes.length} account(s)...</p>
    </div>
  `;

  // Send the selected accounts to the server
  fetch(`/api/accounts/${budgetId}/simplefin/add-accounts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ accounts: accountData, sfinData }),
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to add accounts');
      }
      return response.json();
    })
    .then(data => {
      console.log('Accounts added successfully:', data);
      // Show success message and redirect
      document.querySelector('.simplefin-modal-container').innerHTML = `
        <div class="text-center">
          <div class="text-green-500 mt-4">
            <p class="text-lg font-medium">Accounts added successfully!</p>
            <p class="mt-2">Redirecting to accounts page...</p>
          </div>
        </div>
      `;
      setTimeout(() => {
        window.location.href = '/accounts/';
      }, 2000);
    })
    .catch(error => {
      console.error('Error adding accounts:', error);
      document.querySelector('.simplefin-modal-container').innerHTML = `
        <div class="text-center">
          <div class="text-red-500 mt-4">
            <p>Error adding accounts: ${error.message}</p>
            <button class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" onclick="fetchSimpleFINAccounts()">
              Try Again
            </button>
          </div>
        </div>
      `;
    });
}
