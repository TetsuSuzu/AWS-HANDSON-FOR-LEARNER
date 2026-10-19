(function() {
    var TOKEN_KEY = "handson_access_token";
    var EXPIRY_KEY = "handson_token_expiry";
    var STATE_KEY = "handson_oauth_state";
    var VERIFIER_KEY = "handson_pkce_verifier";

    function config() {
        return {
            domain: (window.COGNITO_DOMAIN || "").replace(/\/+$/, ""),
            clientId: window.COGNITO_CLIENT_ID || "",
            callbackUrl: window.COGNITO_CALLBACK_URL || window.location.origin + window.location.pathname
        };
    }

    function base64Url(bytes) {
        var binary = Array.from(bytes, function(value) {
            return String.fromCharCode(value);
        }).join("");
        return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    }

    async function sha256(value) {
        var data = new TextEncoder().encode(value);
        return base64Url(new Uint8Array(await crypto.subtle.digest("SHA-256", data)));
    }

    function randomValue() {
        var bytes = new Uint8Array(32);
        crypto.getRandomValues(bytes);
        return base64Url(bytes);
    }

    function clearSession() {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(EXPIRY_KEY);
    }

    function accessToken() {
        var expiry = Number(sessionStorage.getItem(EXPIRY_KEY) || 0);
        if (expiry <= Date.now()) {
            clearSession();
            return "";
        }
        return sessionStorage.getItem(TOKEN_KEY) || "";
    }

    async function handleCallback() {
        var params = new URLSearchParams(window.location.search);
        var code = params.get("code");
        if (!code) {
            return;
        }

        var state = params.get("state");
        var savedState = sessionStorage.getItem(STATE_KEY);
        var verifier = sessionStorage.getItem(VERIFIER_KEY);
        sessionStorage.removeItem(STATE_KEY);
        sessionStorage.removeItem(VERIFIER_KEY);
        if (!state || state !== savedState || !verifier) {
            throw new Error("ログイン状態を確認できません。もう一度ログインしてください。");
        }

        var settings = config();
        var body = new URLSearchParams({
            grant_type: "authorization_code",
            client_id: settings.clientId,
            code: code,
            redirect_uri: settings.callbackUrl,
            code_verifier: verifier
        });
        var response = await fetch(settings.domain + "/oauth2/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: body
        });
        var result = await response.json();
        if (!response.ok || !result.access_token) {
            throw new Error(result.error_description || result.error || "ログインに失敗しました");
        }

        sessionStorage.setItem(TOKEN_KEY, result.access_token);
        sessionStorage.setItem(EXPIRY_KEY, String(Date.now() + result.expires_in * 1000));
        window.history.replaceState({}, document.title, settings.callbackUrl);
    }

    async function login() {
        var settings = config();
        if (!settings.domain || !settings.clientId) {
            throw new Error("Cognito の設定がありません。Session5 の手順を確認してください。");
        }

        var verifier = randomValue() + randomValue();
        var state = randomValue();
        sessionStorage.setItem(STATE_KEY, state);
        sessionStorage.setItem(VERIFIER_KEY, verifier);
        var challenge = await sha256(verifier);
        var url = new URL(settings.domain + "/oauth2/authorize");
        url.search = new URLSearchParams({
            client_id: settings.clientId,
            response_type: "code",
            scope: "openid email profile",
            redirect_uri: settings.callbackUrl,
            state: state,
            code_challenge_method: "S256",
            code_challenge: challenge
        }).toString();
        window.location.assign(url.toString());
    }

    function logout() {
        var settings = config();
        clearSession();
        if (!settings.domain || !settings.clientId) {
            window.location.reload();
            return;
        }
        var url = new URL(settings.domain + "/logout");
        url.search = new URLSearchParams({
            client_id: settings.clientId,
            logout_uri: settings.callbackUrl
        }).toString();
        window.location.assign(url.toString());
    }

    window.apiFetch = async function(url, options, requiresLogin) {
        var requestOptions = options || {};
        var headers = new Headers(requestOptions.headers || {});
        var token = requiresLogin ? accessToken() : "";
        if (token) {
            headers.set("Authorization", "Bearer " + token);
        }
        return fetch(url, Object.assign({}, requestOptions, { headers: headers }));
    };

    document.addEventListener("DOMContentLoaded", async function() {
        var loginButton = document.getElementById("loginButton");
        var logoutButton = document.getElementById("logoutButton");
        var status = document.getElementById("authStatus");
        var callbackError = "";

        try {
            await handleCallback();
        } catch (error) {
            callbackError = error.message;
        }

        var authenticated = Boolean(accessToken());
        if (loginButton) {
            loginButton.hidden = authenticated;
            loginButton.addEventListener("click", function() {
                login().catch(function(error) {
                    if (status) {
                        status.textContent = error.message;
                    }
                });
            });
        }
        if (logoutButton) {
            logoutButton.hidden = !authenticated;
            logoutButton.addEventListener("click", logout);
        }
        if (status) {
            status.textContent = callbackError || (authenticated ? "ログイン中です。" : "会員 API の利用にはログインしてください。");
        }
    });
}());
