const Modal = window.Modal;

function editAccount(accountId) {
  const modal = document.getElementById('accountEditModal');
  const modalContent = document.getElementById('accountEditModalContent');

  // Load the account form via fetch
  fetch(`/accounts/edit/${accountId}/`)
    .then(response => response.text())
    .then(html => {
      modalContent.innerHTML = html;

      // Initialize the modal using Flowbite's Modal class
      const options = {
        placement: 'center',
        backdrop: 'static',
        backdropClasses: 'bg-gray-900/50 dark:bg-gray-900/80 fixed inset-0 z-40',
        closable: true,
      };

      // Create a new Modal instance
      const modalInstance = new Modal(modal, options);
      modalInstance.show();

      // Update form action to point to the edit endpoint
      const form = modalContent.querySelector('form');
      if (form) {
        form.action = `/accounts/edit/${accountId}/`;

        // Store the original slug value to detect changes
        const originalSlug = form.querySelector('#slug').value;

        // Add event listener for the close button
        const closeButton = modal.querySelector('[data-modal-hide], [data-modal-close]');
        if (closeButton) {
          closeButton.addEventListener('click', () => {
            modalInstance.hide();
          });
        }

        // Add event listener for form submission
        form.addEventListener('submit', e => {
          e.preventDefault();

          const formData = new FormData(form);
          const newSlug = formData.get('slug');

          fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
              'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            },
          })
            .then(response => response.json())
            .then(data => {
              if (data.status === 'success') {
                // Close the modal
                modalInstance.hide();

                // If the slug has changed, redirect to the new URL
                if (newSlug !== originalSlug) {
                  // Get the current URL and replace the old slug with the new one
                  const currentPath = window.location.pathname;
                  const newPath = currentPath.replace(originalSlug, newSlug);
                  window.location.href = newPath;
                } else {
                  // If slug hasn't changed, just reload the page
                  window.location.reload();
                }
              } else {
                // Display error message
                console.error('Error updating account:', data.message);
                showToast(data.message || 'Error updating account');

                // You could add code here to show the error message to the user
                const errorDiv = document.createElement('div');
                errorDiv.className = 'mt-2 text-sm text-red-600';
                errorDiv.textContent = data.message || 'Error updating account';
                form.querySelector('button[type="submit"]').before(errorDiv);
              }
            })
            .catch(error => {
              console.error('Error processing response:', error);
            });
        });
      }
    })
    .catch(error => {
      console.error('Error loading account form:', error);
    });
}

function archiveAccount(accountId) {
  fetch(`/accounts/archive/${accountId}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
    },
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        // Close the modal
        const modal = document.getElementById('accountEditModal');
        const modalInstance = Modal.getInstance(modal);
        modalInstance.hide();

        // Refresh the page to show updated account status
        window.location.reload();
      } else {
        // Show toast message instead of alert
        showToast(`Failed to archive account: ${data.message}`);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      // Show toast message instead of alert
      showToast('An error occurred while trying to archive the account.');
    });
}
