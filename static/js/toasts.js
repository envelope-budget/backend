function showToast(message, type = 'info') {
  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector('.fixed.right-5.bottom-3');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'z-50 fixed right-5 bottom-3 max-w-sm';
    document.body.appendChild(toastContainer);
  }

  // Create the toast element
  const toast = document.createElement('div');
  
  // Set styles based on type
  let bgClass = 'bg-gray-50 dark:bg-gray-800';
  let textClass = 'text-gray-800 dark:text-gray-300';
  let iconColor = 'dark:text-gray-300';
  
  if (type === 'error') {
    bgClass = 'bg-red-50 dark:bg-red-800';
    textClass = 'text-red-800 dark:text-red-300';
    iconColor = 'text-red-500';
  } else if (type === 'success') {
    bgClass = 'bg-green-50 dark:bg-green-800';
    textClass = 'text-green-800 dark:text-green-300';
    iconColor = 'text-green-500';
  }
  
  toast.className = `flex items-center p-4 mb-3 rounded-lg ${bgClass}`;
  toast.setAttribute('role', 'alert');

  // Set the toast content
  toast.innerHTML = `
    <svg class="flex-shrink-0 w-4 h-4 ${iconColor}"
         aria-hidden="true"
         xmlns="http://www.w3.org/2000/svg"
         fill="currentColor"
         viewBox="0 0 20 20">
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z" />
    </svg>
    <span class="sr-only">Info</span>
    <div class="ms-3 text-sm font-medium ${textClass}">${message}</div>
    <button type="button"
            class="ms-auto -mx-1.5 -my-1.5 ${bgClass} text-gray-500 rounded-lg focus:ring-2 focus:ring-gray-400 p-1.5 hover:bg-gray-200 inline-flex items-center justify-center h-8 w-8 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white"
            aria-label="Close">
      <span class="sr-only">Dismiss</span>
      <svg class="w-3 h-3"
           aria-hidden="true"
           xmlns="http://www.w3.org/2000/svg"
           fill="none"
           viewBox="0 0 14 14">
        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6" />
      </svg>
    </button>
  `;

  // Add the toast to the container
  toastContainer.appendChild(toast);

  // Add click event to close button
  const closeButton = toast.querySelector('button');
  closeButton.addEventListener('click', () => {
    toast.remove();
  });

  // Auto-remove the toast after 5 seconds
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

// Make the function available globally
window.showToast = showToast;
