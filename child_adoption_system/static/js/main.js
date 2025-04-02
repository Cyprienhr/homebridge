/**
 * Main JavaScript for Child Adoption System
 */
document.addEventListener("DOMContentLoaded", function () {
  // Initialize all Bootstrap tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize all Bootstrap popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-hide alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // Toggle password visibility
  const togglePasswordButtons = document.querySelectorAll(".toggle-password");
  togglePasswordButtons.forEach(function (button) {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const passwordField = document.querySelector(
        this.getAttribute("data-target")
      );
      const type =
        passwordField.getAttribute("type") === "password" ? "text" : "password";
      passwordField.setAttribute("type", type);

      // Toggle icon
      const icon = this.querySelector("i");
      if (type === "password") {
        icon.classList.remove("bi-eye-slash");
        icon.classList.add("bi-eye");
      } else {
        icon.classList.remove("bi-eye");
        icon.classList.add("bi-eye-slash");
      }
    });
  });

  // Form validation
  const forms = document.querySelectorAll(".needs-validation");
  forms.forEach(function (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  });

  // Initialize date pickers
  const datePickers = document.querySelectorAll(".datepicker");
  datePickers.forEach(function (input) {
    input.setAttribute("type", "date");
  });

  // Initialize datetime pickers
  const datetimePickers = document.querySelectorAll(".datetimepicker");
  datetimePickers.forEach(function (input) {
    input.setAttribute("type", "datetime-local");
  });

  // Back button functionality
  const backButtons = document.querySelectorAll(".btn-back");
  backButtons.forEach(function (button) {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      window.history.back();
    });
  });

  // Confirm delete operations
  const deleteButtons = document.querySelectorAll(".confirm-delete");
  deleteButtons.forEach(function (button) {
    button.addEventListener("click", function (e) {
      if (
        !confirm(
          "Are you sure you want to delete this item? This action cannot be undone."
        )
      ) {
        e.preventDefault();
      }
    });
  });

  // Copy to clipboard functionality
  const copyButtons = document.querySelectorAll(".copy-to-clipboard");
  copyButtons.forEach(function (button) {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const text = document.querySelector(
        this.getAttribute("data-target")
      ).innerText;
      navigator.clipboard
        .writeText(text)
        .then(function () {
          // Show success message
          const tooltip = bootstrap.Tooltip.getInstance(button);
          const originalTitle = button.getAttribute("data-bs-original-title");

          button.setAttribute("data-bs-original-title", "Copied!");
          tooltip.show();

          setTimeout(function () {
            button.setAttribute("data-bs-original-title", originalTitle);
            tooltip.hide();
          }, 1000);
        })
        .catch(function (err) {
          console.error("Could not copy text: ", err);
        });
    });
  });

  // Image preview on file select
  const imageInputs = document.querySelectorAll(".image-upload");
  imageInputs.forEach(function (input) {
    input.addEventListener("change", function () {
      const previewContainer = document.querySelector(
        this.getAttribute("data-preview")
      );
      if (previewContainer && this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewContainer.src = e.target.result;
          previewContainer.style.display = "block";
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  });
});

// Password visibility toggle
function togglePasswordVisibility(inputId) {
  const passwordInput = document.getElementById(inputId);
  const type =
    passwordInput.getAttribute("type") === "password" ? "text" : "password";
  passwordInput.setAttribute("type", type);
}

// Form validation
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return true;

  let isValid = true;
  const requiredFields = form.querySelectorAll("[required]");

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      field.classList.add("is-invalid");
      isValid = false;
    } else {
      field.classList.remove("is-invalid");
    }
  });

  return isValid;
}

// Show/hide alert messages
function showAlert(message, type = "success") {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
  document.body.insertBefore(alertDiv, document.body.firstChild);

  // Auto dismiss after 5 seconds
  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}

// Confirm delete action
function confirmDelete(message = "Are you sure you want to delete this item?") {
  return confirm(message);
}

// Initialize tooltips
document.addEventListener("DOMContentLoaded", function () {
  const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
  tooltips.forEach((tooltip) => {
    new bootstrap.Tooltip(tooltip);
  });
});

// Handle file input change
function handleFileInput(inputId, previewId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);

  if (input && preview) {
    input.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }
}

// Handle dynamic form fields
function addFormField(containerId, templateId) {
  const container = document.getElementById(containerId);
  const template = document.getElementById(templateId);

  if (container && template) {
    const newField = template.content.cloneNode(true);
    container.appendChild(newField);
  }
}

// Handle dynamic table rows
function addTableRow(tableId, templateId) {
  const table = document.getElementById(tableId);
  const template = document.getElementById(templateId);

  if (table && template) {
    const tbody = table.querySelector("tbody");
    const newRow = template.content.cloneNode(true);
    tbody.appendChild(newRow);
  }
}

// Handle search functionality
function handleSearch(inputId, tableId) {
  const searchInput = document.getElementById(inputId);
  const table = document.getElementById(tableId);

  if (searchInput && table) {
    searchInput.addEventListener("keyup", function () {
      const searchText = this.value.toLowerCase();
      const rows = table.querySelectorAll("tbody tr");

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchText) ? "" : "none";
      });
    });
  }
}

// Handle pagination
function handlePagination(pageNumber, totalPages) {
  const pagination = document.querySelector(".pagination");
  if (!pagination) return;

  pagination.innerHTML = "";

  // Previous button
  pagination.innerHTML += `
        <li class="page-item ${pageNumber === 1 ? "disabled" : ""}">
            <a class="page-link" href="?page=${pageNumber - 1}">Previous</a>
        </li>
    `;

  // Page numbers
  for (let i = 1; i <= totalPages; i++) {
    pagination.innerHTML += `
            <li class="page-item ${pageNumber === i ? "active" : ""}">
                <a class="page-link" href="?page=${i}">${i}</a>
            </li>
        `;
  }

  // Next button
  pagination.innerHTML += `
        <li class="page-item ${pageNumber === totalPages ? "disabled" : ""}">
            <a class="page-link" href="?page=${pageNumber + 1}">Next</a>
        </li>
    `;
}

// Wait for the DOM to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Handle form submissions with AJAX
  document.querySelectorAll('form[data-ajax="true"]').forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const submitButton = form.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;

      // Show loading state
      submitButton.disabled = true;
      submitButton.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

      // Send AJAX request
      fetch(this.action, {
        method: this.method,
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Show success message
            showAlert(
              "success",
              data.message || "Operation completed successfully"
            );

            // Handle redirect if specified
            if (data.redirect_url) {
              window.location.href = data.redirect_url;
            }
          } else {
            // Show error message
            showAlert("danger", data.message || "An error occurred");
          }
        })
        .catch((error) => {
          // Show error message
          showAlert(
            "danger",
            "An error occurred while processing your request"
          );
        })
        .finally(() => {
          // Reset button state
          submitButton.disabled = false;
          submitButton.innerHTML = originalButtonText;
        });
    });
  });

  // Handle delete confirmations
  document
    .querySelectorAll("[data-confirm-delete]")
    .forEach(function (element) {
      element.addEventListener("click", function (e) {
        e.preventDefault();

        const message =
          this.getAttribute("data-confirm-delete") ||
          "Are you sure you want to delete this item?";

        if (confirm(message)) {
          window.location.href = this.href;
        }
      });
    });

  // Handle file input changes
  document.querySelectorAll('input[type="file"]').forEach(function (input) {
    input.addEventListener("change", function () {
      const fileName = this.files[0]?.name;
      if (fileName) {
        const label = this.nextElementSibling;
        if (label && label.classList.contains("custom-file-label")) {
          label.textContent = fileName;
        }
      }
    });
  });

  // Handle dynamic form fields
  document.querySelectorAll("[data-add-form-field]").forEach(function (button) {
    button.addEventListener("click", function () {
      const template = document.querySelector(
        this.getAttribute("data-add-form-field")
      );
      const container = document.querySelector(
        this.getAttribute("data-target")
      );
      const newField = template.content.cloneNode(true);

      // Update field names and IDs
      const totalForms = container.querySelectorAll(".form-field").length;
      newField.querySelectorAll("[name]").forEach(function (input) {
        const name = input.getAttribute("name");
        input.setAttribute("name", name.replace("-0-", `-${totalForms}-`));
      });

      newField.querySelectorAll("[id]").forEach(function (input) {
        const id = input.getAttribute("id");
        input.setAttribute("id", id.replace("-0-", `-${totalForms}-`));
      });

      container.appendChild(newField);
    });
  });

  // Handle dynamic table rows
  document.querySelectorAll("[data-add-table-row]").forEach(function (button) {
    button.addEventListener("click", function () {
      const template = document.querySelector(
        this.getAttribute("data-add-table-row")
      );
      const tbody = document.querySelector(this.getAttribute("data-target"));
      const newRow = template.content.cloneNode(true);

      // Update row IDs and names
      const totalRows = tbody.querySelectorAll("tr").length;
      newRow.querySelectorAll("[name]").forEach(function (input) {
        const name = input.getAttribute("name");
        input.setAttribute("name", name.replace("-0-", `-${totalRows}-`));
      });

      newRow.querySelectorAll("[id]").forEach(function (input) {
        const id = input.getAttribute("id");
        input.setAttribute("id", id.replace("-0-", `-${totalRows}-`));
      });

      tbody.appendChild(newRow);
    });
  });

  // Handle search functionality
  const searchInput = document.querySelector("[data-search]");
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener("input", function () {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        const searchTerm = this.value.toLowerCase();
        const searchTarget = document.querySelector(
          this.getAttribute("data-search")
        );

        searchTarget.querySelectorAll("tr").forEach(function (row) {
          const text = row.textContent.toLowerCase();
          row.style.display = text.includes(searchTerm) ? "" : "none";
        });
      }, 300);
    });
  }

  // Handle sorting functionality
  document.querySelectorAll("[data-sort]").forEach(function (header) {
    header.addEventListener("click", function () {
      const table = this.closest("table");
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));
      const index = Array.from(this.parentElement.children).indexOf(this);
      const isAsc = this.classList.contains("asc");

      // Update sort direction
      table
        .querySelectorAll("th")
        .forEach((th) => th.classList.remove("asc", "desc"));
      this.classList.toggle("asc");
      this.classList.toggle("desc");

      // Sort rows
      rows.sort((a, b) => {
        const aValue = a.children[index].textContent.trim();
        const bValue = b.children[index].textContent.trim();

        if (isAsc) {
          return aValue.localeCompare(bValue);
        } else {
          return bValue.localeCompare(aValue);
        }
      });

      // Reorder rows
      rows.forEach((row) => tbody.appendChild(row));
    });
  });
});

// Utility function to show alerts
function showAlert(type, message) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  const container = document.querySelector(".container");
  container.insertBefore(alertDiv, container.firstChild);

  // Auto dismiss after 5 seconds
  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}

// Utility function to format dates
function formatDate(dateString) {
  const options = {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };

  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", options);
}

// Utility function to handle file uploads
function handleFileUpload(input, previewElement) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();

    reader.onload = function (e) {
      previewElement.src = e.target.result;
    };

    reader.readAsDataURL(input.files[0]);
  }
}

// Utility function to handle pagination
function handlePagination(url, page) {
  window.location.href = `${url}?page=${page}`;
}

// Utility function to handle filters
function handleFilter(form) {
  const formData = new FormData(form);
  const params = new URLSearchParams(formData);
  window.location.href = `${window.location.pathname}?${params.toString()}`;
}

// Export utility functions for use in other files
window.utils = {
  showAlert,
  formatDate,
  handleFileUpload,
  validateForm,
  handlePagination,
  handleFilter,
};
