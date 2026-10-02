  // Configuration: Backend API base URL
  const API_BASE_URL = 'http://localhost:5000/api';

  // ---------------- UI TAB SWITCHING ----------------
  function switchTab(tab) {
    const loginSection = document.getElementById('section-login');
    const registerSection = document.getElementById('section-register');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    if (tab === 'login') {
      loginSection.classList.remove('hidden');
      registerSection.classList.add('hidden');
      tabLogin.classList.add('active', 'border-indigo-600', 'text-indigo-600');
      tabRegister.classList.remove('active', 'border-indigo-600', 'text-indigo-600');
      tabRegister.classList.add('text-slate-500');
    } else {
      loginSection.classList.add('hidden');
      registerSection.classList.remove('hidden');
      tabRegister.classList.add('active', 'border-indigo-600', 'text-indigo-600');
      tabLogin.classList.remove('active', 'border-indigo-600', 'text-indigo-600');
      tabLogin.classList.add('text-slate-500');
    }
  }

  // Quick 1-click fill for testing
  function fillDemoUser() {
    document.getElementById('login-email').value = 'alex@example.com';
    document.getElementById('login-password').value = 'password123';
  }

  // ---------------- REGISTRATION SUBMISSION ----------------
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      // Prevent browser default redirect/reload
      e.preventDefault();

      const submitBtn = registerForm.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn ? submitBtn.innerText : 'Register';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = 'Creating account...';
      }

      // Collect data matching Flask app.py expectation
      const payload = {
        full_name: document.getElementById('reg-name')?.value.trim() || 'Alex Carter',
        email: document.getElementById('reg-email')?.value.trim(),
        password: document.getElementById('reg-password')?.value,
        age: parseInt(document.getElementById('reg-age')?.value) || 28,
        gender: document.getElementById('reg-gender')?.value || 'Male',
        clinical_baseline: document.getElementById('reg-baseline')?.value.trim() || 'None',
        device_model: document.getElementById('reg-device')?.value || 'Apple Watch'
      };

      try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
          alert('Account created successfully! Please sign in with your email and password.');
          // Pre-fill email in login tab and switch tabs
          const loginEmailField = document.getElementById('login-email');
          if (loginEmailField) loginEmailField.value = payload.email;
          switchTab('login');
        } else {
          alert('Registration Error: ' + (data.error || 'Unable to register user.'));
        }
      } catch (err) {
        console.error('Registration Network Error:', err);
        alert('Could not connect to Flask API on port 5000. Ensure "python app.py" is running in your terminal.');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerText = originalBtnText;
        }
      }
    });
  }

  // ---------------- LOGIN SUBMISSION ----------------
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      // Prevent browser default redirect/reload
      e.preventDefault();

      const submitBtn = loginForm.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn ? submitBtn.innerText : 'Sign In';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = 'Verifying...';
      }

      const email = document.getElementById('login-email')?.value.trim();
      const password = document.getElementById('login-password')?.value;

      try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
          // Persist user session data in localStorage for the dashboard
          localStorage.setItem('user_id', data.user.id);
          localStorage.setItem('user_profile', JSON.stringify(data.user));

          // Forward user to dashboard
          window.location.href = 'index.html';
        } else {
          alert('Login Failed: ' + (data.error || 'Invalid credentials.'));
        }
      } catch (err) {
        console.error('Login Network Error:', err);
        alert('Could not connect to Flask API on port 5000. Ensure "python app.py" is running in your terminal.');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerText = originalBtnText;
        }
      }
    });
  }

  // ---------------- PASSWORD STRENGTH METER ----------------
  const regPasswordInput = document.getElementById('reg-password');
  const strengthBar = document.getElementById('password-strength-bar');
  const strengthText = document.getElementById('password-strength-text');

  if (regPasswordInput && strengthBar && strengthText) {
    regPasswordInput.addEventListener('input', (e) => {
      const val = e.target.value;
      let score = 0;
      if (val.length >= 6) score++;
      if (val.length >= 10) score++;
      if (/[A-Z]/.test(val) && /[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      if (val.length === 0) {
        strengthBar.style.width = '0%';
        strengthBar.className = 'h-full transition-all duration-300 rounded-full';
        strengthText.innerText = 'None';
      } else if (score <= 1) {
        strengthBar.style.width = '25%';
        strengthBar.className = 'h-full transition-all duration-300 rounded-full bg-red-500';
        strengthText.innerText = 'Weak';
      } else if (score <= 3) {
        strengthBar.style.width = '65%';
        strengthBar.className = 'h-full transition-all duration-300 rounded-full bg-amber-500';
        strengthText.innerText = 'Moderate';
      } else {
        strengthBar.style.width = '100%';
        strengthBar.className = 'h-full transition-all duration-300 rounded-full bg-emerald-500';
        strengthText.innerText = 'Strong';
      }
    });
  }
