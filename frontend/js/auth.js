function isLoggedIn() {
  return Boolean(getToken());
}

function logout() {
  removeToken();
  window.location.href = "./login.html";
}

function requireAuthentication() {
  if (!isLoggedIn()) {
    window.location.href = "./login.html";
  }
}

async function login(username, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  saveToken(data.token);
  return data;
}

async function register(username, password) {
  const data = await apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  saveToken(data.token);
  return data;
}

function showAuthMessage(message, type) {
  if (!authMessage) {
    return;
  }
  authMessage.textContent = message;
  authMessage.className = `auth-message ${type}`;
}

/*---------------LOGIN PAGE---------------*/
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const authMessage = document.getElementById("authMessage");

if (loginForm) {
  loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    const button = document.getElementById("loginButton");

    try {
      button.disabled = true;
      button.textContent = "Signing in...";

      await login(username, password);

      window.location.href = "/index.html";
    } catch (error) {
      showAuthMessage(error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Sign In";
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.getElementById("registerUsername").value.trim();
    const password = document.getElementById("registerPassword").value.trim();

    const button = document.getElementById("registerButton");

    try {
      button.disabled = true;
      button.textContent = "Creating account...";

      await register(username, password);

      window.location.href = "/index.html";
    } catch (error) {
      showAuthMessage(error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Create Account";
    }
  });
}