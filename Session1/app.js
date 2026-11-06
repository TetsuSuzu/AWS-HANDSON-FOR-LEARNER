// 会員登録（Cognito のサインアップ・ログイン）と料理のおすすめの動きを担当します（index.html から読み込み）

// ログイン後の ID トークン。画面を開いている間だけメモリに持ち、保存や表示はしない
var idToken = "";
var tokenClaims = {};

// config.js の COGNITO_CLIENT_ID が空の間（Session5 より前）は、従来どおりの登録フォームだけを使う
function isCognitoEnabled() {
    return typeof window.COGNITO_CLIENT_ID === "string" && window.COGNITO_CLIENT_ID !== "";
}

function $(id) {
    return document.getElementById(id);
}

function setStatus(element, message, isSuccess) {
    element.className = isSuccess ? "success-message" : "";
    element.textContent = message;
}

// panelName: signup / confirm / login / register
function showPanel(panelName) {
    $("signupPanel").hidden = panelName !== "signup";
    $("confirmPanel").hidden = panelName !== "confirm";
    $("loginPanel").hidden = panelName !== "login";
    $("registrationForm").hidden = panelName !== "register";
    $("registrationHeading").hidden = panelName !== "register";
}

async function cognitoCall(target, payload) {
    var response = await fetch("https://cognito-idp." + window.COGNITO_REGION + ".amazonaws.com/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService." + target
        },
        body: JSON.stringify(payload)
    });
    var result = {};
    try {
        result = await response.json();
    } catch (e) {
        result = {};
    }
    if (!response.ok) {
        var name = String(result.__type || "UnknownError").split("#").pop();
        var error = new Error(result.message || name);
        error.name = name;
        error.code = name;
        throw error;
    }
    return result;
}

async function signUp(username, email, password) {
    return cognitoCall("SignUp", {
        ClientId: window.COGNITO_CLIENT_ID,
        Username: username,
        Password: password,
        UserAttributes: [{ Name: "email", Value: email }]
    });
}

async function confirmSignUp(username, code) {
    return cognitoCall("ConfirmSignUp", {
        ClientId: window.COGNITO_CLIENT_ID,
        Username: username,
        ConfirmationCode: code
    });
}

// JWT の中身（payload）を読み取る。署名の検証は API Gateway が行う
function decodeJwtPayload(token) {
    var base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4 !== 0) {
        base64 += "=";
    }
    var binary = atob(base64);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return JSON.parse(new TextDecoder("utf-8").decode(bytes));
}

async function login(username, password) {
    var result = await cognitoCall("InitiateAuth", {
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: window.COGNITO_CLIENT_ID,
        AuthParameters: { USERNAME: username, PASSWORD: password }
    });
    if (result.ChallengeName) {
        throw new Error("追加の認証（" + result.ChallengeName + "）が必要ですが、この画面では対応していません。");
    }
    idToken = result.AuthenticationResult.IdToken;
    tokenClaims = decodeJwtPayload(idToken);
    return tokenClaims;
}

function cognitoErrorMessage(error) {
    var name = error.name || error.code;
    switch (name) {
        case "UsernameExistsException":
            return "このユーザIDはすでに使われています。別のユーザIDを入力するか、ログインしてください。";
        case "CodeMismatchException":
            return "確認コードが正しくありません。メールに届いたコードをもう一度確認してください。";
        case "ExpiredCodeException":
            return "確認コードの有効期限が切れています。確認コードを送り直してください（Session5 の「よくあるエラー」を見てください）。";
        case "InvalidPasswordException":
            return "パスワードが条件を満たしていません。長さや文字の種類（大文字・小文字・数字・記号）を確認してください。";
        case "InvalidParameterException":
            return "入力内容に誤りがあります。ユーザID・メールアドレス・パスワードを確認してください。";
        case "UserNotConfirmedException":
            return "メールアドレスの確認が済んでいません。「確認コードを入力する」から確認コードを入力してください。";
        case "NotAuthorizedException":
            return "ユーザIDまたはパスワードが正しくありません。";
        case "UserNotFoundException":
            return "このユーザIDは登録されていません。サインアップしてください。";
        case "LimitExceededException":
        case "TooManyRequestsException":
            return "操作の回数が多すぎます。しばらく待ってからもう一度お試しください。";
        case "TypeError":
            return "通信に失敗しました。ネットワークを確認してもう一度お試しください。";
        default:
            // Cognito のエラー名がない（login() が投げた Error など）ときは、元のメッセージを使う
            if (error.message && (!name || name === "Error")) {
                return error.message;
            }
            return "エラーが発生しました（" + (name || "不明") + "）。";
    }
}

// ログイン後の会員情報登録フォーム：ユーザID とメールアドレスはトークンの値を入れて変更不可にする
function prefillRegistrationForm() {
    $("id").value = tokenClaims["cognito:username"] || "";
    $("email").value = tokenClaims.email || "";
}

function setupAuth() {
    if (!isCognitoEnabled()) {
        // Session5 より前：認証の区画は隠し、従来の登録フォームをそのまま使う
        $("signupPanel").hidden = true;
        $("confirmPanel").hidden = true;
        $("loginPanel").hidden = true;
        return;
    }

    $("id").readOnly = true;
    $("email").readOnly = true;
    showPanel("signup");

    $("showLoginFromSignup").addEventListener("click", function() { showPanel("login"); });
    $("showLoginFromConfirm").addEventListener("click", function() { showPanel("login"); });
    $("showSignupFromLogin").addEventListener("click", function() { showPanel("signup"); });
    $("showConfirmFromSignup").addEventListener("click", function() {
        $("confirmUsername").value = $("signupUsername").value.trim();
        showPanel("confirm");
    });
    $("showConfirmFromLogin").addEventListener("click", function() {
        $("confirmUsername").value = $("loginUsername").value.trim();
        showPanel("confirm");
    });

    $("signupButton").addEventListener("click", async function() {
        var status = $("signupStatus");
        if (!$("signupForm").reportValidity()) {
            return;
        }
        var username = $("signupUsername").value.trim();
        setStatus(status, "サインアップしています...", false);
        try {
            await signUp(username, $("signupEmail").value.trim(), $("signupPassword").value);
            $("signupPassword").value = "";
            $("confirmUsername").value = username;
            setStatus(status, "", false);
            showPanel("confirm");
            setStatus($("confirmStatus"), "メールに確認コードを送りました。コードを入力してください。", true);
        } catch (error) {
            setStatus(status, cognitoErrorMessage(error), false);
        }
    });

    $("confirmButton").addEventListener("click", async function() {
        var status = $("confirmStatus");
        if (!$("confirmForm").reportValidity()) {
            return;
        }
        var username = $("confirmUsername").value.trim();
        setStatus(status, "確認しています...", false);
        try {
            await confirmSignUp(username, $("confirmCode").value.trim());
            $("confirmCode").value = "";
            $("loginUsername").value = username;
            setStatus(status, "", false);
            showPanel("login");
            setStatus($("loginStatus"), "確認が完了しました。ログインしてください。", true);
        } catch (error) {
            setStatus(status, cognitoErrorMessage(error), false);
        }
    });

    $("loginButton").addEventListener("click", async function() {
        var status = $("loginStatus");
        if (!$("loginForm").reportValidity()) {
            return;
        }
        setStatus(status, "ログインしています...", false);
        try {
            await login($("loginUsername").value.trim(), $("loginPassword").value);
            $("loginPassword").value = "";
            setStatus(status, "", false);
            prefillRegistrationForm();
            setStatus($("registrationStatus"), "", false);
            showPanel("register");
        } catch (error) {
            setStatus(status, cognitoErrorMessage(error), false);
        }
    });
}

setupAuth();

$("registerButton").addEventListener("click", async function() {
    var form = $("registrationForm");
    var status = $("registrationStatus");
    if (isCognitoEnabled() && !idToken) {
        showPanel("login");
        setStatus($("loginStatus"), "ログインしてください。", false);
        return;
    }
    if (!form.reportValidity()) {
        return;
    }

    var apiEndpoint = (window.API_ENDPOINT || "").replace(/\/+$/, "");
    if (!apiEndpoint) {
        status.textContent = "API URL は Session3 で設定します。";
        return;
    }

    var formData = new FormData(form);
    var user = Object.fromEntries(formData.entries());
    user.age = Number(user.age);
    status.textContent = "登録しています...";

    try {
        var headers = { "Content-Type": "application/json" };
        if (isCognitoEnabled()) {
            // Cognito の ID トークンをそのまま付ける（Bearer は付けない）
            headers.Authorization = idToken;
        }
        // ルート POST / を呼ぶため、URL の末尾に / を付けて送る（ステージ名だけの URL では届かない）
        var response = await fetch(apiEndpoint + "/", {
            method: "POST",
            headers: headers,
            body: JSON.stringify(user)
        });
        if (isCognitoEnabled() && response.status === 401) {
            idToken = "";
            tokenClaims = {};
            status.textContent = "";
            showPanel("login");
            setStatus($("loginStatus"), "ログインの有効期限が切れました。もう一度ログインしてください。", false);
            return;
        }
        var result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || "登録に失敗しました");
        }
        status.textContent = "登録が完了しました。";
        status.className = "success-message";
        alert("会員登録しました。");
        form.reset();
        if (isCognitoEnabled()) {
            // reset で空になるため、読み取り専用の ID とメールアドレスを入れ直す
            prefillRegistrationForm();
        }
    } catch (error) {
        status.className = "";
        status.textContent = "登録に失敗しました: " + error.message;
    }
});

document.getElementById("recommendationButton").addEventListener("click", async function() {
    var prompt = document.getElementById("recommendationPrompt").value.trim();
    var status = document.getElementById("recommendationStatus");
    var endpoint = (window.SEARCH_API_ENDPOINT || "").replace(/\/+$/, "");
    if (!prompt) {
        status.textContent = "希望を入力してください。";
        return;
    }
    if (!endpoint) {
        status.textContent = "料理のおすすめの API URL は Session7 で設定します。";
        return;
    }

    status.textContent = "おすすめを考えています...";
    try {
        // ルート POST / を呼ぶため、URL の末尾に / を付けて送る
        var response = await fetch(endpoint + "/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        var result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || "おすすめを取得できませんでした");
        }
        status.textContent = result.answer;
    } catch (error) {
        status.textContent = "おすすめを取得できませんでした: " + error.message;
    }
});
