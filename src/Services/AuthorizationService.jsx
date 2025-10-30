


class AuthorizationService {
    constructor(username, password) {
        this.username = username;
        this.password = password;
    }

    async checkCredentials() {
        if (this.isLoggedIn()) {
            return Promise.resolve(true);
        }

        let base = process.env.NODE_ENV === 'production' ? (window.location.href + "api") : "http://localhost:5000";
        let auth_url = base + "/login";
        try {
            let response = await fetch(auth_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: this.username, password: this.password })
            });
            let data = await response.json();
            if (data.message === "Login successful.") {
                const tokenExpirationTime = 60 * 1000 * process.env.REACT_APP_SESSION_TIMEOUT_MINUTES;
                localStorage.setItem('token', data.token);
                localStorage.setItem('tokenExpiration', Date.now() + tokenExpirationTime);
                localStorage.setItem('display_name', data.user);
                window.location.reload();
            }
            return Promise.resolve(data.message);
        } catch (error) {
            console.error(error);
            return "Unknown Error Occurred.";
        }
    }

    


    isLoggedIn() {
        const APP_LOGIN_LINK = [
            "https://m365.cloud.microsoft/",
            "https://login.microsoftonline.com/"
        ];
        if (APP_LOGIN_LINK.some(link => document.referrer.startsWith(link))) {
            return true;
        }
        

        const tokenExpiration = localStorage.getItem('tokenExpiration');
        if (tokenExpiration && tokenExpiration < Date.now()) {
            localStorage.removeItem('token');
            localStorage.removeItem('tokenExpiration');
        }
        return !!localStorage.getItem('token') || !!localStorage.getItem('user');
    }

    logout() {
        this.username = "";
        this.password = "";
        localStorage.removeItem('token');
        localStorage.removeItem('tokenExpiration');
        localStorage.removeItem('display_name');
        window.location.reload();
    }
}

export default AuthorizationService;
