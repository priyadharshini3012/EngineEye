const API_BASE = 'http://localhost:5000/api';

const auth = {
    getToken: () => localStorage.getItem('authToken'),
    getUsername: () => localStorage.getItem('username'),
    setSession: (token, username) => {
        localStorage.setItem('authToken', token);
        localStorage.setItem('username', username);
    },
    logout: () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('username');
        window.location.href = 'index.html';
    },
    isLoggedIn: () => !!localStorage.getItem('authToken'),
    protectPage: () => {
        if (!localStorage.getItem('authToken')) {
            window.location.href = 'login.html';
        }
    },
    redirectIfLoggedIn: () => {
        if (localStorage.getItem('authToken')) {
            window.location.href = 'dashboard.html';
        }
    }
};

async function apiCall(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    const token = auth.getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method,
            headers,
            body: data ? JSON.stringify(data) : null
        });
        
        const result = await response.json();
        return { ok: response.ok, status: response.status, data: result };
    } catch (error) {
        console.error('API Call Error:', error);
        return { ok: false, data: { error: 'Network communication failed' } };
    }
}

function showMessage(type, message) {
    let toast = document.getElementById('messageToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'messageToast';
        toast.className = 'message-toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.className = `message-toast toast-${type === 'error' ? 'error' : 'success'}`;
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 4000);
}

function refreshIcons() {
    if (window.lucide) {
        lucide.createIcons();
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    refreshIcons();
});
