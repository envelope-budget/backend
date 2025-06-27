const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
const themeToggleAutoIcon = document.getElementById('theme-toggle-auto-icon');

// Function to apply theme based on current setting
const applyTheme = (theme) => {
  // Hide all icons first
  themeToggleDarkIcon.classList.add('hidden');
  themeToggleLightIcon.classList.add('hidden');
  themeToggleAutoIcon.classList.add('hidden');

  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
    themeToggleDarkIcon.classList.remove('hidden'); // Show dark icon when in dark mode
  } else if (theme === 'light') {
    document.documentElement.classList.remove('dark');
    themeToggleLightIcon.classList.remove('hidden'); // Show light icon when in light mode
  } else { // auto mode
    // Follow system preference
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    themeToggleAutoIcon.classList.remove('hidden'); // Show auto icon when in auto mode
  }
};

// Initialize theme based on stored preference or system default
const currentTheme = localStorage.getItem('color-theme') || 'auto';
applyTheme(currentTheme);

// Listen for system theme changes when in auto mode
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
mediaQuery.addEventListener('change', () => {
  if (!localStorage.getItem('color-theme') || localStorage.getItem('color-theme') === 'auto') {
    applyTheme('auto');
  }
});

const themeToggleBtn = document.getElementById('theme-toggle');

themeToggleBtn.addEventListener('click', () => {
  const currentTheme = localStorage.getItem('color-theme') || 'auto';
  let nextTheme;

  // Cycle through: light → auto → dark → light
  if (currentTheme === 'light') {
    nextTheme = 'auto';
  } else if (currentTheme === 'auto') {
    nextTheme = 'dark';
  } else { // dark
    nextTheme = 'light';
  }

  localStorage.setItem('color-theme', nextTheme);
  applyTheme(nextTheme);
});

// Add Account Modal
const originalModalContent = document.getElementById('add-account-modal-body').innerHTML;
const loadOriginalModalContent = () => {
  const modalBody = document.getElementById('add-account-modal-body');
  modalBody.innerHTML = originalModalContent;
  htmx.process(modalBody);
};
document.getElementById('btn-add-account').addEventListener('click', () => {
  loadOriginalModalContent();
});

window.getCookie = name => {
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
};

window.setCookie = (name, value, days) => {
  let expires = '';
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = `; expires=${date.toUTCString()}`;
  }
  document.cookie = `${name}=${value || ''}${expires}; path=/`;
};

// SimpleFIN connection handling
window.getSimpleFINConnection = async budgetId => {
  // Check if we already have a stored access URL for this budget
  const storedBudgetId = getCookie('simplefin-budget-id');
  const storedAccessUrl = getCookie('simplefin-access-url');

  // If we have a stored access URL for the current budget, return it
  if (storedBudgetId === budgetId && storedAccessUrl) {
    return storedAccessUrl;
  }

  try {
    // Get the CSRF token for the request
    const csrftoken = getCookie('csrftoken');

    // Fetch the SimpleFIN connection info
    const response = await fetch(`/api/accounts/${budgetId}/simplefin`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      credentials: 'same-origin',
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch SimpleFIN connection: ${response.status}`);
    }

    const data = await response.json();

    if (data) {
      // Store the budget ID and access URL in cookies (30 days expiration)
      setCookie('simplefin-budget-id', budgetId, 30);
      setCookie('simplefin-access-url', data.access_url, 30);
      console.log('SimpleFIN connection info updated');
      return data.access_url;
    }
    // Clear cookies if no connection exists
    setCookie('simplefin-budget-id', '', -1);
    setCookie('simplefin-access-url', '', -1);
    console.log('No SimpleFIN connection found for this budget');
    return null;
  } catch (error) {
    console.error('Error fetching SimpleFIN connection:', error);
    return null;
  }
};

// side menu drop-down toggles
document.addEventListener('DOMContentLoaded', event => {
  const dropdowns = ['loans', 'credit-cards', 'accounts', 'archived'];

  // Restore the state from cookies
  for (const dropdown of dropdowns) {
    const button = document.querySelector(`[data-collapse-toggle="dropdown-${dropdown}"]`);
    const content = document.querySelector(`#dropdown-${dropdown}`);
    if (button) {
      const icon = button.querySelector('svg:last-child');

      // Save the state in cookies on toggle
      button.addEventListener('click', () => {
        icon.classList.toggle('rotate-90');
        content.classList.toggle('hidden');
        const isCurrentlyOpen = !icon.classList.contains('rotate-90');
        setCookie(`show-${dropdown}`, isCurrentlyOpen, 30); // Cookie expires in 30 days
      });
    }
  }

  // Look for a budget ID in the cookie
  const budgetId = getCookie('budget_id');
  if (budgetId) {
    getSimpleFINConnection(budgetId)
      .then(accessUrl => {
        if (accessUrl) {
        }
      })
      .catch(error => {
        console.error('Failed to load SimpleFIN connection:', error);
      });
  }
});
