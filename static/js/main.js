document.addEventListener("DOMContentLoaded", function () {
    // --- File Upload Visual Feedback ---
    const fileInput = document.getElementById("dataset-file");
    const fileWrapper = document.getElementById("file-upload-wrapper");
    const fileNameDisplay = document.getElementById("selected-file-name");

    if (fileInput && fileWrapper && fileNameDisplay) {
        fileInput.addEventListener("change", function () {
            if (fileInput.files.length > 0) {
                fileWrapper.classList.add("has-file");
                fileNameDisplay.textContent = `Selected File: ${fileInput.files[0].name}`;
            } else {
                fileWrapper.classList.remove("has-file");
                fileNameDisplay.textContent = "CSV, Excel, or Text files supported";
            }
        });
    }

    // --- Loading Spinner Controls ---
    const loadingOverlay = document.getElementById("loading-overlay");
    const spinnerForms = document.querySelectorAll(".show-spinner-on-submit");

    if (spinnerForms && loadingOverlay) {
        spinnerForms.forEach(form => {
            form.addEventListener("submit", function () {
                loadingOverlay.style.display = "flex";
            });
        });
    }

    // --- Authentication Tab / Form Toggling ---
    const toggleToSignup = document.getElementById("toggle-to-signup");
    const toggleToSignin = document.getElementById("toggle-to-signin");
    const signupFormCard = document.getElementById("signup-card");
    const signinFormCard = document.getElementById("signin-card");

    if (toggleToSignup && signupFormCard && signinFormCard) {
        toggleToSignup.addEventListener("click", function (e) {
            e.preventDefault();
            signinFormCard.style.display = "none";
            signupFormCard.style.display = "block";
        });
    }

    if (toggleToSignin && signupFormCard && signinFormCard) {
        toggleToSignin.addEventListener("click", function (e) {
            e.preventDefault();
            signupFormCard.style.display = "none";
            signinFormCard.style.display = "block";
        });
    }

    // --- Signup Validation ---
    const signupForm = document.getElementById("user-signup-form");
    if (signupForm) {
        signupForm.addEventListener("submit", function (e) {
            let isValid = true;
            
            // 1. Email validation
            const emailInput = document.getElementById("signup-email");
            const emailVal = emailInput.value.trim();
            if (!emailVal.endsWith("@gmail.com")) {
                showError(emailInput, "Email ID must end with @gmail.com");
                isValid = false;
            } else {
                clearError(emailInput);
            }

            // 2. Phone number validation
            const phoneInput = document.getElementById("signup-phone");
            const phoneVal = phoneInput.value.trim();
            // Expected format: Code +91 followed by 10 digit number. e.g. +91 9876543210 or +919876543210
            const phoneRegex = /^\+91\s?\d{10}$/;
            if (!phoneRegex.test(phoneVal)) {
                showError(phoneInput, "Phone number must start with +91 followed by 10 digits");
                isValid = false;
            } else {
                clearError(phoneInput);
            }

            // 3. Password requirements validation
            const passwordInput = document.getElementById("signup-password");
            const confirmInput = document.getElementById("signup-confirm-password");
            const passwordVal = passwordInput.value;
            const confirmVal = confirmInput.value;

            // Password policy: At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character
            // Example: Amma@1234
            const pwdRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
            if (!pwdRegex.test(passwordVal)) {
                showError(passwordInput, "Password must be at least 8 characters, and contain uppercase, lowercase, number, and special character (e.g. Amma@1234)");
                isValid = false;
            } else {
                clearError(passwordInput);
            }

            // 4. Confirm Password Match
            if (passwordVal !== confirmVal) {
                showError(confirmInput, "Passwords do not match");
                isValid = false;
            } else {
                clearError(confirmInput);
            }

            if (!isValid) {
                e.preventDefault();
            } else {
                if (loadingOverlay) {
                    loadingOverlay.style.display = "flex";
                }
            }
        });
    }

    // Helper functions for displaying inline errors
    function showError(inputElement, message) {
        const group = inputElement.closest(".form-group");
        let errorSpan = group.querySelector(".error-message");
        if (!errorSpan) {
            errorSpan = document.createElement("span");
            errorSpan.className = "error-message text-danger form-help";
            group.appendChild(errorSpan);
        }
        errorSpan.textContent = message;
        inputElement.style.borderColor = "var(--error)";
    }

    function clearError(inputElement) {
        const group = inputElement.closest(".form-group");
        const errorSpan = group.querySelector(".error-message");
        if (errorSpan) {
            errorSpan.remove();
        }
        inputElement.style.borderColor = "";
    }
});
