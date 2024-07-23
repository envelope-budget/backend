const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

// Change the icons inside the button based on previous settings
if (
  localStorage.getItem('color-theme') === 'dark' ||
  (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
) {
  themeToggleLightIcon.classList.remove('hidden');
} else {
  themeToggleDarkIcon.classList.remove('hidden');
}

const themeToggleBtn = document.getElementById('theme-toggle');

themeToggleBtn.addEventListener('click', () => {
  // toggle icons inside button
  themeToggleDarkIcon.classList.toggle('hidden');
  themeToggleLightIcon.classList.toggle('hidden');

  // if set via local storage previously
  if (localStorage.getItem('color-theme')) {
    if (localStorage.getItem('color-theme') === 'light') {
      document.documentElement.classList.add('dark');
      localStorage.setItem('color-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('color-theme', 'light');
    }

    // if NOT set via local storage previously
  } else {
    if (document.documentElement.classList.contains('dark')) {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('color-theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      localStorage.setItem('color-theme', 'dark');
    }
  }
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

// Plaid Link
const handler = Plaid.create({
  token: 'GENERATED_LINK_TOKEN',
  onSuccess: (public_token, metadata) => {},
  onLoad: () => {},
  onExit: (err, metadata) => {},
  onEvent: (eventName, metadata) => {},
});

//
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

// side menu drop-down toggles
document.addEventListener('DOMContentLoaded', event => {
  const dropdowns = ['loans', 'credit-cards', 'accounts'];

  // Restore the state from local storage
  for (const dropdown of dropdowns) {
    const button = document.querySelector(`[data-collapse-toggle="dropdown-${dropdown}"]`);
    const content = document.querySelector(`#dropdown-${dropdown}`);
    const icon = button.querySelector('svg:last-child');
    const isOpen = localStorage.getItem(`dropdown-${dropdown}`) === 'true';

    if (isOpen) {
      icon.classList.add('rotate-90');
      content.classList.add('hidden');
    } else {
      icon.classList.remove('rotate-90');
      content.classList.remove('hidden');
    }

    setTimeout(() => {
      icon.classList.remove('transition-transform');
      icon.classList.remove('duration-200');
    }, 500);

    // Save the state in local storage on toggle
    button.addEventListener('click', () => {
      icon.classList.toggle('rotate-90');
      content.classList.toggle('hidden');
      const isCurrentlyOpen = icon.classList.contains('rotate-90');
      localStorage.setItem(`dropdown-${dropdown}`, isCurrentlyOpen);
    });
  }
});
