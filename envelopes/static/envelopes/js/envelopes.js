const pickerOptions = { onEmojiSelect: addEmojiToName };
const picker = new EmojiMart.Picker(pickerOptions);

document.getElementById("emoji-picker").appendChild(picker);

function addEmojiToName(emoji) {
  const $name = document.getElementById("name");
  let name = $name.value;

  // If name starts with an emoji, remove the emoji first
  const emojiRegexPattern = /^[\p{Emoji}\u200d]+/u;
  name = name.replace(emojiRegexPattern, "").replace(/\s+/, "").trim();

  $name.value = `${emoji.native} ${name}`;
  $name.focus();
}

function envelopeData() {
  return {
    envelope: {
      id: "",
      name: "Test",
      balance: 0,
      category_id: "",
      note: "Test Note",
    },

    startNewEnvelope(category_id) {
      this.envelope.id = "";
      this.envelope.name = "";
      this.envelope.balance = 0;
      this.envelope.category_id = category_id;
      this.envelope.note = "";
    },

    createEnvelope() {
      const endpoint = `/api/envelopes/${window.getCookie("budget_id")}`;
      const csrfToken = window.getCookie("csrftoken");

      // Prepare the headers
      const headers = new Headers({
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      });

      // Prepare the request options
      const requestOptions = {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
          name: this.envelope.name,
          balance: this.envelope.balance,
          category_id: this.envelope.category_id,
          note: this.envelope.note,
        }),
        credentials: "include", // necessary for cookies to be sent with the request
      };

      // Post to endpoint
      fetch(endpoint, requestOptions)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          console.log("Envelope created successfully:", data);
          // Refresh the envelope data
          window.location.reload();
        })
        .catch((error) => {
          console.error("Error creating envelope:", error);
          // Handle the error case here
        });
    },
  };
}
