const displayKeyModal = new Modal(document.getElementById('display-key-modal'));

async function deleteApiKey(apiKeyId) {
  const endpoint = `/api/auth/api-key/${apiKeyId}`;
  try {
    const response = await fetch(endpoint, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
    });
    if (!response.ok) {
      throw new Error('Failed to delete API key');
    }
    // Remove the deleted API key from the UI
    const apiKeyElement = document.getElementById(`api-key-${apiKeyId}`);
    if (apiKeyElement) {
      apiKeyElement.remove();
    }
  } catch (error) {
    console.error('Error deleting API key:', error);
    alert('Failed to delete API key. Please try again.');
  }
}

async function createApiKey(event) {
  event.preventDefault(); // Prevent the default form submission
  const endpoint = '/api/auth/api-key';
  const terminationDate = document.getElementById('termination-date').value || null;
  const note = document.getElementById('note').value;

  const requestBody = { note };
  if (terminationDate) {
    requestBody.termination_date = terminationDate;
  }

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error('Failed to create API key');
    }

    const data = await response.json();
    // set the value of the api key in the modal
    document.getElementById('api-key').textContent = data.key;
    displayKeyModal.show();

    // Optionally, you can refresh the list of API keys or update the UI accordingly

    // Hide the modal after successful creation
    document.querySelector('[data-modal-hide="api-key-modal"]').click();
  } catch (error) {
    console.error('Error creating API key:', error);
    alert('Failed to create API key. Please try again.');
  }
}

// Attach the createApiKey function to the form's submit event
document.querySelector('#api-key-modal form').addEventListener('submit', createApiKey);

document.getElementById('close-display-key-modal-button').addEventListener('click', () => {
  window.location.reload();
});

document.getElementById('copy-api-key').addEventListener('click', () => {
  const apiKey = document.getElementById('api-key').textContent;
  navigator.clipboard.writeText(apiKey).then(
    () => {
      alert('API key copied to clipboard!');
    },
    err => {
      console.error('Could not copy text: ', err);
    }
  );
});
