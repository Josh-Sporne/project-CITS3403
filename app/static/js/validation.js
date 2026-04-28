/* Plate Theory — Client-Side Form Validation */

(function () {
    'use strict';

    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function showFieldError(input, message) {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        let feedback = input.nextElementSibling;
        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
        feedback.textContent = message;
    }

    function showFieldValid(input) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        const feedback = input.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.textContent = '';
        }
    }

    function clearFieldState(input) {
        input.classList.remove('is-valid', 'is-invalid');
    }

    /* ── Register form ── */

    function validateUsername(input) {
        const val = input.value.trim();
        if (val.length < 3) {
            showFieldError(input, 'Username must be at least 3 characters.');
            return false;
        }
        if (val.length > 80) {
            showFieldError(input, 'Username must be 80 characters or fewer.');
            return false;
        }
        showFieldValid(input);
        return true;
    }

    function validateEmail(input) {
        if (!EMAIL_RE.test(input.value.trim())) {
            showFieldError(input, 'Please enter a valid email address.');
            return false;
        }
        showFieldValid(input);
        return true;
    }

    function validatePassword(input) {
        if (input.value.length < 8) {
            showFieldError(input, 'Password must be at least 8 characters.');
            return false;
        }
        showFieldValid(input);
        return true;
    }

    function validateConfirmPassword(input, passwordInput) {
        if (!input.value || input.value !== passwordInput.value) {
            showFieldError(input, 'Passwords do not match.');
            return false;
        }
        showFieldValid(input);
        return true;
    }

    function initRegisterValidation(form) {
        const username = form.querySelector('[name="username"]');
        const email = form.querySelector('[name="email"]');
        const password = form.querySelector('[name="password"]');
        const confirm = form.querySelector('[name="confirm_password"]');
        const submitBtn = form.querySelector('[type="submit"]');

        if (!username || !email || !password || !confirm) return;

        const fields = [username, email, password, confirm];

        function checkAll() {
            const allValid =
                username.value.trim().length >= 3 && username.value.trim().length <= 80 &&
                EMAIL_RE.test(email.value.trim()) &&
                password.value.length >= 8 &&
                confirm.value && confirm.value === password.value;
            if (submitBtn) submitBtn.disabled = !allValid;
            return allValid;
        }

        if (submitBtn) submitBtn.disabled = true;

        username.addEventListener('blur', () => validateUsername(username));
        email.addEventListener('blur', () => validateEmail(email));
        password.addEventListener('blur', () => {
            validatePassword(password);
            if (confirm.value) validateConfirmPassword(confirm, password);
        });
        confirm.addEventListener('blur', () => validateConfirmPassword(confirm, password));

        fields.forEach(f => f.addEventListener('input', checkAll));

        form.addEventListener('submit', (e) => {
            const results = [
                validateUsername(username),
                validateEmail(email),
                validatePassword(password),
                validateConfirmPassword(confirm, password)
            ];
            if (results.includes(false)) {
                e.preventDefault();
            }
        });
    }

    /* ── Recipe create/edit form ── */

    function validateRequired(input, label) {
        if (!input.value.trim()) {
            showFieldError(input, `${label} is required.`);
            return false;
        }
        showFieldValid(input);
        return true;
    }

    function validateIngredients(container) {
        const nameInputs = container.querySelectorAll('[name="ingredient_name[]"]');
        const hasFilled = Array.from(nameInputs).some(inp => inp.value.trim() !== '');
        if (!hasFilled) {
            nameInputs.forEach(inp => {
                showFieldError(inp, 'At least one ingredient is required.');
            });
            return false;
        }
        nameInputs.forEach(inp => {
            if (inp.value.trim()) showFieldValid(inp);
            else clearFieldState(inp);
        });
        return true;
    }

    function initRecipeValidation(form) {
        const title = form.querySelector('#title') || form.querySelector('[name="title"]');
        const instructions = form.querySelector('#instructions') || form.querySelector('[name="instructions"]');
        const ingredientContainer = form.querySelector('#ingredients-container');
        const submitBtn = form.querySelector('[type="submit"]');

        if (!title || !instructions) return;

        function checkAll() {
            const titleOk = title.value.trim().length > 0;
            const instrOk = instructions.value.trim().length > 0;
            let ingredOk = true;
            if (ingredientContainer) {
                const nameInputs = ingredientContainer.querySelectorAll('[name="ingredient_name[]"]');
                ingredOk = Array.from(nameInputs).some(inp => inp.value.trim() !== '');
            }
            if (submitBtn) submitBtn.disabled = !(titleOk && instrOk && ingredOk);
            return titleOk && instrOk && ingredOk;
        }

        if (submitBtn) submitBtn.disabled = !checkAll();

        title.addEventListener('blur', () => validateRequired(title, 'Title'));
        instructions.addEventListener('blur', () => validateRequired(instructions, 'Instructions'));

        title.addEventListener('input', checkAll);
        instructions.addEventListener('input', checkAll);

        if (ingredientContainer) {
            ingredientContainer.addEventListener('input', (e) => {
                if (e.target.matches('[name="ingredient_name[]"]')) {
                    if (e.target.value.trim()) showFieldValid(e.target);
                    else clearFieldState(e.target);
                }
                checkAll();
            });

            ingredientContainer.addEventListener('blur', (e) => {
                if (e.target.matches('[name="ingredient_name[]"]')) {
                    validateIngredients(ingredientContainer);
                }
            }, true);
        }

        form.addEventListener('submit', (e) => {
            const results = [
                validateRequired(title, 'Title'),
                validateRequired(instructions, 'Instructions')
            ];
            if (ingredientContainer) {
                results.push(validateIngredients(ingredientContainer));
            }
            if (results.includes(false)) {
                e.preventDefault();
            }
        });
    }

    /* ── Init on DOMContentLoaded ── */

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('form.needs-validation, form[action*="/register"], #register-form').forEach(form => {
            const action = form.getAttribute('action') || '';
            if (action.includes('/register') || form.id === 'register-form') {
                form.setAttribute('novalidate', '');
                initRegisterValidation(form);
            }
        });

        document.querySelectorAll('form.needs-validation, #recipe-form, form[action*="/recipe/create"], form[action*="/recipe/edit"]').forEach(form => {
            const action = form.getAttribute('action') || '';
            if (form.id === 'recipe-form' || action.includes('/recipe/create') || action.includes('/recipe/edit')) {
                form.setAttribute('novalidate', '');
                initRecipeValidation(form);
            }
        });
    });
})();
