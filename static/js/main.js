// Main JavaScript for AnoPus
document.addEventListener("DOMContentLoaded", function () {
  // Auto-hide flash messages after 5 seconds
  const flashMessages = document.querySelectorAll(".flash-message");
  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.style.opacity = "0";
      message.style.transform = "translateY(-20px)";
      setTimeout(() => message.remove(), 300);
    }, 5000);
  });

  // Password confirmation validation
  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirm_password");

  if (password && confirmPassword) {
    function validatePassword() {
      if (password.value !== confirmPassword.value) {
        confirmPassword.setCustomValidity("Password tidak cocok");
      } else {
        confirmPassword.setCustomValidity("");
      }
    }

    password.addEventListener("change", validatePassword);
    confirmPassword.addEventListener("keyup", validatePassword);
  }
});
