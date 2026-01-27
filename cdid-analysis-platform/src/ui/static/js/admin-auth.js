(() => {
  const TOKEN_KEY = "CDID_ADMIN_TOKEN";
  const USER_KEY = "CDID_ADMIN_USER";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || "";
  }

  function setToken(token) {
    if (!token) return;
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function getUser() {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function setUser(user) {
    if (!user) return;
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  async function login(username, password) {
    const response = await fetch("/api/admin/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error("用户名或密码错误");
    }

    const data = await response.json();
    setToken(data.access_token);
    setUser(data.user || { username });
    return data;
  }

  async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = new Headers(options.headers || {});
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    if (!headers.has("Content-Type") && options.body) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401 || response.status === 403) {
      clearToken();
      const error = new Error("NOT_AUTHENTICATED");
      error.code = "NOT_AUTHENTICATED";
      throw error;
    }
    return response;
  }

  function attachUserToNavbar() {
    const user = getUser();
    const el = document.querySelector("[data-admin-username]");
    if (el) {
      el.textContent = user?.username || "管理员";
    }
  }

  function openLoginModal(modalId = "adminLoginModal") {
    const modalEl = document.getElementById(modalId);
    if (!modalEl) {
      throw new Error(`Login modal not found: #${modalId}`);
    }
    // eslint-disable-next-line no-undef
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl, {
      backdrop: "static",
      keyboard: false,
    });
    modal.show();
    return modal;
  }

  function requireLogin({
    modalId = "adminLoginModal",
    formId = "adminLoginForm",
    errorId = "adminLoginError",
  } = {}) {
    attachUserToNavbar();
    if (getToken()) {
      return Promise.resolve();
    }

    const modal = openLoginModal(modalId);
    const form = document.getElementById(formId);
    const errorBox = document.getElementById(errorId);

    if (!form) {
      throw new Error(`Login form not found: #${formId}`);
    }

    return new Promise((resolve) => {
      const onSubmit = async (event) => {
        event.preventDefault();
        if (errorBox) {
          errorBox.classList.add("d-none");
          errorBox.textContent = "";
        }

        const username = form.querySelector("[name='username']")?.value?.trim();
        const password = form.querySelector("[name='password']")?.value ?? "";
        if (!username || !password) {
          if (errorBox) {
            errorBox.textContent = "请输入用户名和密码";
            errorBox.classList.remove("d-none");
          }
          return;
        }

        const submitBtn = form.querySelector("[type='submit']");
        if (submitBtn) submitBtn.disabled = true;

        try {
          await login(username, password);
          attachUserToNavbar();
          modal.hide();
          form.removeEventListener("submit", onSubmit);
          resolve();
        } catch (e) {
          if (errorBox) {
            errorBox.textContent = e?.message || "登录失败";
            errorBox.classList.remove("d-none");
          }
        } finally {
          if (submitBtn) submitBtn.disabled = false;
        }
      };

      form.addEventListener("submit", onSubmit);
    });
  }

  function logout() {
    clearToken();
    location.reload();
  }

  window.AdminAuth = {
    getToken,
    getUser,
    login,
    logout,
    apiFetch,
    requireLogin,
  };
})();

