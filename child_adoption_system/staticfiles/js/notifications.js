// Function to update notification badge
function updateNotificationBadge() {
  fetch("/notifications/unread-count/")
    .then((response) => response.json())
    .then((data) => {
      const badge = document.getElementById("notification-badge");
      if (badge) {
        badge.textContent = data.count;
        badge.style.display = data.count > 0 ? "inline" : "none";
      }
    })
    .catch((error) =>
      console.error("Error fetching notification count:", error)
    );
}

// Function to mark notification as read
function markAsRead(notificationId) {
  fetch(`/notifications/${notificationId}/mark-read/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        updateNotificationBadge();
        // Update UI to show notification as read
        const notification = document.querySelector(
          `[data-notification-id="${notificationId}"]`
        );
        if (notification) {
          notification.classList.remove("active");
          const markReadBtn = notification.querySelector(".mark-read-btn");
          if (markReadBtn) {
            markReadBtn.remove();
          }
        }
      }
    })
    .catch((error) =>
      console.error("Error marking notification as read:", error)
    );
}

// Function to delete notification
function deleteNotification(notificationId) {
  if (!confirm("Are you sure you want to delete this notification?")) {
    return;
  }

  fetch(`/notifications/${notificationId}/delete/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        // Remove notification from UI
        const notification = document.querySelector(
          `[data-notification-id="${notificationId}"]`
        );
        if (notification) {
          notification.remove();
        }
        updateNotificationBadge();
      }
    })
    .catch((error) => console.error("Error deleting notification:", error));
}

// Function to mark all notifications as read
function markAllAsRead() {
  fetch("/notifications/mark-all-read/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        // Update UI to show all notifications as read
        document
          .querySelectorAll(".notification-item.active")
          .forEach((notification) => {
            notification.classList.remove("active");
            const markReadBtn = notification.querySelector(".mark-read-btn");
            if (markReadBtn) {
              markReadBtn.remove();
            }
          });
        updateNotificationBadge();
      }
    })
    .catch((error) =>
      console.error("Error marking all notifications as read:", error)
    );
}

// Helper function to get CSRF token from cookies
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

// Auto-refresh notification count every 30 seconds
setInterval(updateNotificationBadge, 30000);

// Initial notification count update
document.addEventListener("DOMContentLoaded", updateNotificationBadge);
