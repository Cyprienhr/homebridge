/**
 * Dashboard functionality for Child Adoption System
 */
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

  // Enhanced Sidebar Toggle Functionality - Fixed for all device sizes
  const sidebarToggler = document.getElementById("sidebarToggler");
  const body = document.body;

  // Console log for debugging
  console.log("Sidebar Toggler Element:", sidebarToggler);

  if (sidebarToggler) {
    // Check for saved sidebar state and apply it on page load
    const sidebarState = localStorage.getItem("sidebarState");
    if (sidebarState === "collapsed" && window.innerWidth >= 992) {
      body.classList.add("sidebar-collapsed");
    } else if (sidebarState === "mobile-visible" && window.innerWidth < 992) {
      body.classList.add("sidebar-mobile-visible");
    }

    // Toggle sidebar on button click
    sidebarToggler.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      console.log("Sidebar toggler clicked");

      const isMobile = window.innerWidth < 992;

      if (isMobile) {
        console.log("Mobile view - toggling sidebar-mobile-visible");
        body.classList.toggle("sidebar-mobile-visible");
        if (body.classList.contains("sidebar-mobile-visible")) {
          localStorage.setItem("sidebarState", "mobile-visible");
        } else {
          localStorage.removeItem("sidebarState");
        }
      } else {
        console.log("Desktop view - toggling sidebar-collapsed");
        body.classList.toggle("sidebar-collapsed");
        if (body.classList.contains("sidebar-collapsed")) {
          localStorage.setItem("sidebarState", "collapsed");
        } else {
          localStorage.removeItem("sidebarState");
        }
      }
    });

    // Force initialization on mobile
    if (window.innerWidth < 992) {
      console.log("Mobile view detected on load - initializing sidebar state");
      // Make sure the sidebar is hidden by default on mobile
      body.classList.remove("sidebar-collapsed");

      // Apply saved state if exists
      if (localStorage.getItem("sidebarState") === "mobile-visible") {
        body.classList.add("sidebar-mobile-visible");
      }
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener("click", function (e) {
      const isMobile = window.innerWidth < 992;
      if (isMobile && body.classList.contains("sidebar-mobile-visible")) {
        // Only if the click is outside the sidebar and not on the toggler
        if (
          !e.target.closest(".sidebar") &&
          e.target !== sidebarToggler &&
          !e.target.closest("#sidebarToggler")
        ) {
          console.log("Clicking outside sidebar - closing mobile sidebar");
          body.classList.remove("sidebar-mobile-visible");
          localStorage.removeItem("sidebarState");
        }
      }
    });

    // Adjust sidebar state on window resize
    window.addEventListener("resize", function () {
      if (window.innerWidth >= 992) {
        body.classList.remove("sidebar-mobile-visible");
        // Keep collapsed state if it was set
        if (localStorage.getItem("sidebarState") === "collapsed") {
          body.classList.add("sidebar-collapsed");
        }
      } else {
        body.classList.remove("sidebar-collapsed");
        // Check if we should show mobile sidebar
        if (localStorage.getItem("sidebarState") === "mobile-visible") {
          body.classList.add("sidebar-mobile-visible");
        }
      }
    });
  } else {
    console.error("Sidebar toggler element not found!");
  }

  // Submenu toggle functionality
  const submenuTogglers = document.querySelectorAll(
    ".nav-item.has-submenu > a"
  );
  if (submenuTogglers.length > 0) {
    submenuTogglers.forEach(function (toggler) {
      toggler.addEventListener("click", function (e) {
        e.preventDefault();
        const parent = this.parentElement;

        // Close other open submenus
        if (!parent.classList.contains("open")) {
          document
            .querySelectorAll(".nav-item.has-submenu.open")
            .forEach((item) => {
              if (item !== parent) {
                item.classList.remove("open");
              }
            });
        }

        // Toggle current submenu
        parent.classList.toggle("open");
      });
    });
  }

  // Toggle password visibility
  const togglePassword = document.querySelectorAll(".toggle-password");
  if (togglePassword) {
    togglePassword.forEach(function (button) {
      button.addEventListener("click", function () {
        const passwordInput = document.querySelector(
          this.getAttribute("data-target")
        );
        if (passwordInput.type === "password") {
          passwordInput.type = "text";
          this.querySelector("i").classList.remove("bi-eye");
          this.querySelector("i").classList.add("bi-eye-slash");
        } else {
          passwordInput.type = "password";
          this.querySelector("i").classList.remove("bi-eye-slash");
          this.querySelector("i").classList.add("bi-eye");
        }
      });
    });
  }

  // Fetch unread notification count periodically
  function fetchUnreadCount() {
    fetch("/notifications/unread-count/")
      .then((response) => response.json())
      .then((data) => {
        const badge = document.querySelector("#notification-badge");
        if (badge) {
          if (data.count > 0) {
            badge.textContent = data.count;
            badge.classList.remove("d-none");
          } else {
            badge.classList.add("d-none");
          }
        }
      })
      .catch((error) =>
        console.error("Error fetching notification count:", error)
      );
  }

  // Fetch notification count every 60 seconds
  fetchUnreadCount();
  setInterval(fetchUnreadCount, 60000);

  // Date range picker for reports and appointments
  const dateRangePickers = document.querySelectorAll(".date-range-picker");
  if (dateRangePickers.length > 0) {
    dateRangePickers.forEach(function (element) {
      const fromDate = element.querySelector(".date-from");
      const toDate = element.querySelector(".date-to");

      if (fromDate && toDate) {
        fromDate.addEventListener("change", function () {
          toDate.min = this.value;
        });

        toDate.addEventListener("change", function () {
          fromDate.max = this.value;
        });
      }
    });
  }

  // Mark notification as read when clicked
  const notificationLinks = document.querySelectorAll(".notification-link");
  if (notificationLinks.length > 0) {
    notificationLinks.forEach(function (link) {
      link.addEventListener("click", function (e) {
        const notificationId = this.getAttribute("data-notification-id");
        fetch(`/notifications/${notificationId}/mark-read/`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
          },
        })
          .then((response) => response.json())
          .then((data) => {
            // Update the UI to show the notification as read
            this.closest(".notification-item").classList.remove("unread");
            fetchUnreadCount();
          })
          .catch((error) =>
            console.error("Error marking notification as read:", error)
          );
      });
    });
  }

  // Function to get CSRF token from cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Confirm delete actions
  const deleteButtons = document.querySelectorAll(".delete-confirm");
  if (deleteButtons.length > 0) {
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
  }

  // Enable DataTables for large tables if available
  if (typeof $.fn.DataTable !== "undefined") {
    $(".datatable").DataTable({
      responsive: true,
      language: {
        search: "Search:",
        lengthMenu: "Show _MENU_ entries per page",
        info: "Showing _START_ to _END_ of _TOTAL_ entries",
        paginate: {
          first: "First",
          last: "Last",
          next: "Next",
          previous: "Previous",
        },
      },
    });
  }

  // Initialize chart.js charts if available
  if (typeof Chart !== "undefined") {
    // Example chart - Children status distribution
    const childrenStatusChart = document.getElementById("childrenStatusChart");
    if (childrenStatusChart) {
      new Chart(childrenStatusChart, {
        type: "doughnut",
        data: {
          labels: ["Available", "Pending", "Adopted"],
          datasets: [
            {
              data: [
                parseInt(
                  childrenStatusChart.getAttribute("data-available") || 0
                ),
                parseInt(childrenStatusChart.getAttribute("data-pending") || 0),
                parseInt(childrenStatusChart.getAttribute("data-adopted") || 0),
              ],
              backgroundColor: ["#4CAF50", "#FFC107", "#2196F3"],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
            },
          },
        },
      });
    }

    // Hospital dashboard - Gender Distribution chart
    const genderChart = document.getElementById("genderChart");
    if (genderChart) {
      new Chart(genderChart, {
        type: "doughnut",
        data: {
          labels: ["Male", "Female"],
          datasets: [
            {
              data: [
                parseInt(genderChart.getAttribute("data-male") || 0),
                parseInt(genderChart.getAttribute("data-female") || 0),
              ],
              backgroundColor: ["#2196F3", "#E91E63"],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
            },
          },
        },
      });
    }

    // Hospital dashboard - Newborns Chart (Monthly data)
    const newbornsChart = document.getElementById("newbornsChart");
    if (newbornsChart) {
      const monthlyData = JSON.parse(
        newbornsChart.getAttribute("data-monthly") || "[]"
      );

      const months = monthlyData.map((item) => item.month);
      const regularData = monthlyData.map((item) => item.regular);
      const abandonedData = monthlyData.map((item) => item.abandoned);

      new Chart(newbornsChart, {
        type: "bar",
        data: {
          labels: months,
          datasets: [
            {
              label: "Regular Births",
              data: regularData,
              backgroundColor: "#4CAF50",
              borderColor: "#4CAF50",
              borderWidth: 1,
            },
            {
              label: "Abandoned",
              data: abandonedData,
              backgroundColor: "#FFC107",
              borderColor: "#FFC107",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0,
              },
            },
          },
          plugins: {
            legend: {
              position: "top",
            },
          },
        },
      });
    }

    // Example chart - Applications status distribution
    const applicationsStatusChart = document.getElementById(
      "applicationsStatusChart"
    );
    if (applicationsStatusChart) {
      new Chart(applicationsStatusChart, {
        type: "doughnut",
        data: {
          labels: ["Pending", "Approved", "Rejected"],
          datasets: [
            {
              data: [
                parseInt(
                  applicationsStatusChart.getAttribute("data-pending") || 0
                ),
                parseInt(
                  applicationsStatusChart.getAttribute("data-approved") || 0
                ),
                parseInt(
                  applicationsStatusChart.getAttribute("data-rejected") || 0
                ),
              ],
              backgroundColor: ["#FFC107", "#4CAF50", "#F44336"],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
            },
          },
        },
      });
    }
  }

  // Sidebar Toggle
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener("click", function () {
      document.body.classList.toggle("sidebar-collapsed");

      // On mobile
      document.body.classList.toggle("sidebar-mobile-visible");
    });
  }

  // Check for saved sidebar state
  if (localStorage.getItem("sidebarToggle") === "true") {
    document.body.classList.add("sidebar-collapsed");
  }

  // Auto-open submenu if it contains an active link
  const activeSubmenuLinks = document.querySelectorAll(".submenu a.active");
  activeSubmenuLinks.forEach(function (link) {
    const parent = link.closest(".has-submenu");
    if (parent) {
      parent.classList.add("open");
      const submenu = parent.querySelector(".submenu");
      if (submenu) {
        submenu.style.maxHeight = submenu.scrollHeight + "px";
      }
    }
  });

  // Make parent menu item active if submenu item is active
  const activeLinks = document.querySelectorAll(
    ".nav-link.active, .submenu a.active"
  );
  activeLinks.forEach(function (link) {
    const parentMenuItem = link.closest(".has-submenu");
    if (parentMenuItem) {
      const parentMenuLink = parentMenuItem.querySelector(".nav-link");
      parentMenuLink.classList.add("active");
    }
  });

  // Scroll to top button
  const scrollTopBtn = document.querySelector(".scroll-to-top");
  if (scrollTopBtn) {
    // Show button when user scrolls down
    window.addEventListener("scroll", function () {
      if (window.pageYOffset > 300) {
        scrollTopBtn.classList.add("active");
      } else {
        scrollTopBtn.classList.remove("active");
      }
    });

    // Scroll to top when button is clicked
    scrollTopBtn.addEventListener("click", function (e) {
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    });
  }

  // Auto-hide alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert:not(.alert-important)");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const closeBtn = alert.querySelector(".btn-close");
      if (closeBtn) {
        closeBtn.click();
      } else {
        alert.style.opacity = "0";
        setTimeout(() => {
          alert.style.display = "none";
        }, 500);
      }
    }, 5000);
  });

  // Add active class to current page nav item
  const currentPath = window.location.pathname;
  // Remove any trailing slash for consistent matching
  const normalizedPath = currentPath.endsWith("/")
    ? currentPath
    : currentPath + "/";
  const sidebarLinks = document.querySelectorAll(".sidebar a");

  sidebarLinks.forEach(function (link) {
    const href = link.getAttribute("href");
    if (href) {
      // Normalize the href as well
      const normalizedHref = href.endsWith("/") ? href : href + "/";

      // Match both with and without 'core/' prefix
      // Account for both cases: URL might be /core/dashboard/admin/ or /dashboard/admin/
      const withoutCorePath = normalizedPath.replace(/^\/core/, "");

      if (
        normalizedPath === normalizedHref ||
        withoutCorePath === normalizedHref ||
        normalizedPath.startsWith(normalizedHref) ||
        withoutCorePath.startsWith(normalizedHref)
      ) {
        link.classList.add("active");

        // If in submenu, open the submenu
        const submenuParent = link.closest(".submenu");
        if (submenuParent) {
          const menuItem = submenuParent.closest(".has-submenu");
          if (menuItem) {
            menuItem.classList.add("open");
            const submenu = menuItem.querySelector(".submenu");
            if (submenu) {
              submenu.style.maxHeight = submenu.scrollHeight + "px";
            }
          }
        }
      }
    }
  });

  // Handle search in the dashboard
  const searchInput = document.querySelector(".topbar-search input");
  if (searchInput) {
    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        const searchTerm = this.value.trim();
        if (searchTerm) {
          window.location.href = `/search/?q=${encodeURIComponent(searchTerm)}`;
        }
      }
    });
  }
});
