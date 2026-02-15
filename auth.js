// auth.js
// 1. Point to 127.0.0.1 explicitly to match the cookie domain
const API_BASE = 'http://127.0.0.1:9000/api';

// 2. Helper to send requests with Cookies (Credentials)
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            // CRITICAL: Bypasses the Ngrok "browser warning" page
            'ngrok-skip-browser-warning': 'true' 
        },
        credentials: 'include' // CRITICAL: Sends/Receives Session Cookies
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        // Handle Session Expiration
        if (response.status === 401) {
            console.warn("Session expired or unauthorized.");
            localStorage.clear();
            if (!window.location.pathname.includes('login.html')) {
                window.location.href = 'login.html';
            }
            return { ok: false, error: "Unauthorized" };
        }

        const data = await response.json();
        return { ok: response.ok, status: response.status, data: data };
    } catch (error) {
        console.error("API Connection Error:", error);
        return { ok: false, error: "Server is offline or URL is incorrect" };
    }
}

// 3. Auth Functions
async function login(username, password) {
    const result = await apiCall('/login', 'POST', { username, password });
    if (result.ok) {
        localStorage.setItem('username', result.data.username);
        localStorage.setItem('isLoggedIn', 'true');
        window.location.href = 'index.html';
    } else {
        alert(result.data.error || "Login Failed");
    }
}

async function register(username, email, password) {
    const result = await apiCall('/register', 'POST', { username, email, password });
    if (result.ok) {
        localStorage.setItem('username', username);
        localStorage.setItem('isLoggedIn', 'true');
        window.location.href = 'index.html';
    } else {
        alert(result.data.error || 'Registration failed');
    }
}

async function logout() {
    await apiCall('/logout', 'POST');
    localStorage.clear();
    window.location.href = 'login.html';
}

async function checkAuth() {
    const result = await apiCall('/check-auth', 'GET');
    return result.ok;
}
