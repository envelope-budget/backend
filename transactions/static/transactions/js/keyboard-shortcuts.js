// Function to set active transaction
function setActiveTransaction(row) {
  const currentActive = document.querySelector(".transaction-active");
  if (currentActive) {
    currentActive.classList.remove("transaction-active");
  }
  row.classList.add("transaction-active");
}

// Function to toggle checkbox in the active row
function toggleCheckboxInActiveRow() {
  const activeRow = document.querySelector(".transaction-active");
  if (activeRow) {
    const checkbox = activeRow.querySelector('input[type="checkbox"]');
    if (checkbox) {
      checkbox.checked = !checkbox.checked;
    }
  }
}

// Function to delete checked rows and update active transaction
function deleteCheckedRows() {
  const tbody = document.querySelector("table tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const activeRow = document.querySelector(".transaction-active");
  let activeRowDeleted = false;

  rows.forEach((row) => {
    const checkbox = row.querySelector('input[type="checkbox"]');
    if (checkbox && checkbox.checked) {
      tbody.removeChild(row);
      if (row === activeRow) {
        activeRowDeleted = true;
      }
    }
  });

  if (activeRowDeleted) {
    const remainingRows = tbody.querySelectorAll("tr");
    if (remainingRows.length > 0) {
      const nextActiveRow = activeRow.nextElementSibling || tbody.lastElementChild;
      setActiveTransaction(nextActiveRow);
    }
  }
}

// Event listener for keyboard navigation and spacebar action
document.addEventListener("keydown", function (event) {
  if (event.key === "j" || event.key === "k") {
    const activeRow = document.querySelector(".transaction-active");
    if (activeRow) {
      let nextRow = event.key === "j" ? activeRow.nextElementSibling : activeRow.previousElementSibling;
      if (nextRow && nextRow.tagName === "TR") {
        setActiveTransaction(nextRow);
      }
    }
  } else if (event.key === "x") {
    // Toggle checkbox when x is pressed
    toggleCheckboxInActiveRow();
  } else if (event.key === "#") {
    // Delete all rows that have a checkbox checked
    deleteCheckedRows();
  }
});

// Event listener for click on table rows
document.querySelectorAll("table tbody tr").forEach((row) => {
  row.addEventListener("click", function () {
    setActiveTransaction(row);
  });
});
