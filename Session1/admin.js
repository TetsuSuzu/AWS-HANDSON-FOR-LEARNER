// 会員の一覧・更新・削除を行う管理画面の動き（admin.html から読み込み）
var adminEndpoint = (window.ADMIN_API_ENDPOINT || "").replace(/\/+$/, "");
var listStatus = document.getElementById("listStatus");
var editStatus = document.getElementById("editStatus");
var userRows = document.getElementById("userRows");
var editSection = document.getElementById("edit");
var editForm = document.getElementById("editForm");
var searchInput = document.getElementById("searchId");
// 直前に表示した内容（検索したユーザID。空なら全件）。更新・削除のあとに同じ表示へ戻すために覚えておく
var lastSearchId = "";

// config.js の COGNITO_CLIENT_ID が空の間（Session5 より前）は、従来どおりログインなしで使う
function isCognitoEnabled() {
    return typeof window.COGNITO_CLIENT_ID === "string" && window.COGNITO_CLIENT_ID !== "";
}

// ログイン後の ID トークン。画面を開いている間だけメモリに持ち、保存や表示はしない
var idToken = "";
var loginSection = document.getElementById("loginSection");
var loginForm = document.getElementById("loginForm");
var loginStatus = document.getElementById("loginStatus");
var logoutArea = document.getElementById("logoutArea");
var mainSections = [document.getElementById("auth"), document.getElementById("users"), logoutArea];

// ログイン画面と管理画面（一覧・更新）を切り替える。ログインが無効のときは何もしない
function showLoggedIn(isLoggedIn) {
    if (!isCognitoEnabled()) {
        return;
    }
    loginSection.hidden = isLoggedIn;
    mainSections.forEach(function(section) {
        section.hidden = !isLoggedIn;
    });
    if (!isLoggedIn) {
        editSection.hidden = true;
    }
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
}

// ログインの失敗を画面に出す文にする。Cognito のエラー名は日本語にし、それ以外は元のメッセージを使う
function loginErrorMessage(error) {
    switch (error.name) {
        case "NotAuthorizedException":
            return "ユーザIDまたはパスワードが正しくありません。";
        case "UserNotFoundException":
            return "このユーザIDは登録されていません。";
        case "UserNotConfirmedException":
            return "メールアドレスの確認が済んでいません。会員サイトで確認コードを入力してください。";
        case "InvalidParameterException":
            return "入力内容に誤りがあります。ユーザIDとパスワードを確認してください。";
        case "LimitExceededException":
        case "TooManyRequestsException":
            return "操作の回数が多すぎます。しばらく待ってからもう一度お試しください。";
        case "TypeError":
            return "通信に失敗しました。ネットワークを確認してもう一度お試しください。";
        default:
            return error.message || "ログインに失敗しました。";
    }
}

// API を呼ぶ共通の関数
async function callApi(method, path, body) {
    if (!adminEndpoint) {
        throw new Error("管理 API の URL は Session4 で config.js に設定します。");
    }
    var headers = {};
    if (body) {
        headers["Content-Type"] = "application/json";
    }
    if (isCognitoEnabled()) {
        if (!idToken) {
            throw new Error("ログインしてください");
        }
        headers["Authorization"] = idToken;
    }
    var response = await fetch(adminEndpoint + path, {
        method: method,
        headers: headers,
        body: body ? JSON.stringify(body) : undefined
    });
    // 削除に成功したときは本文がない（204）
    var result = response.status === 204 ? {} : await response.json();
    if (!response.ok) {
        var message = result.message || "処理に失敗しました";
        if (isCognitoEnabled() && response.status === 401) {
            // トークンの期限切れ。ログイン画面に戻す
            idToken = "";
            showLoggedIn(false);
            message = "ログインの有効期限が切れました。もう一度ログインしてください。";
            loginStatus.textContent = message;
        }
        var error = new Error(message);
        error.status = response.status;
        throw error;
    }
    return result;
}

// 一覧の 1 行を作る。登録された内容はそのまま HTML にせず、textContent で文字として入れる
function addCell(row, text) {
    var cell = document.createElement("td");
    cell.textContent = text;
    row.appendChild(cell);
}

function addButton(cell, label, onClick) {
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", onClick);
    cell.appendChild(button);
}

function renderUsers(users) {
    userRows.textContent = "";
    users.forEach(function(user) {
        var row = document.createElement("tr");
        ["id", "name", "email", "age", "address", "tel"].forEach(function(field) {
            addCell(row, user[field]);
        });
        var actions = document.createElement("td");
        addButton(actions, "編集", function() { startEdit(user); });
        addButton(actions, "削除", function() { deleteUser(user); });
        row.appendChild(actions);
        userRows.appendChild(row);
    });
}

async function loadUsers() {
    lastSearchId = "";
    listStatus.className = "";
    listStatus.textContent = "取得しています...";
    try {
        var users = [];
        var path = "/users?limit=100";
        // 100 件を超えるときは、nextToken で次のページを続けて取る
        while (path) {
            var result = await callApi("GET", path);
            users = users.concat(result.users);
            path = result.nextToken ? "/users?limit=100&nextToken=" + encodeURIComponent(result.nextToken) : null;
        }
        renderUsers(users);
        listStatus.textContent = users.length + " 件の会員が登録されています。";
    } catch (error) {
        userRows.textContent = "";
        listStatus.textContent = "取得に失敗しました: " + error.message;
    }
}

// ユーザIDで 1 件だけ取得して表示する（GET /users/{id}）
async function searchUser() {
    var id = searchInput.value.trim();
    if (!id) {
        listStatus.textContent = "ユーザIDを入力してください。";
        return;
    }
    lastSearchId = id;
    listStatus.className = "";
    listStatus.textContent = "検索しています...";
    try {
        var user = await callApi("GET", "/users/" + encodeURIComponent(id));
        renderUsers([user]);
        listStatus.textContent = "ユーザID「" + id + "」の会員が見つかりました。";
    } catch (error) {
        userRows.textContent = "";
        listStatus.textContent = error.status === 404
            ? "ユーザID「" + id + "」の会員は見つかりませんでした。"
            : "検索に失敗しました: " + error.message;
    }
}

// 更新・削除のあと、直前と同じ表示（検索結果または全件）に戻す
async function refreshList() {
    if (lastSearchId) {
        await searchUser();
    } else {
        await loadUsers();
    }
}

// 表・メッセージ・検索欄・更新フォームを空に戻す（データは消えない。画面の表示だけ）
function clearView() {
    lastSearchId = "";
    userRows.textContent = "";
    searchInput.value = "";
    listStatus.textContent = "";
    editStatus.textContent = "";
    editSection.hidden = true;
}

function startEdit(user) {
    editStatus.textContent = "";
    editForm.elements.id.value = user.id;
    editForm.elements.name.value = user.name;
    editForm.elements.email.value = user.email;
    editForm.elements.age.value = user.age;
    editForm.elements.address.value = user.address;
    editForm.elements.tel.value = user.tel;
    editSection.hidden = false;
    editSection.scrollIntoView();
}

async function saveUser() {
    if (!editForm.reportValidity()) {
        return;
    }
    var user = Object.fromEntries(new FormData(editForm).entries());
    user.age = Number(user.age);
    editStatus.className = "";
    editStatus.textContent = "更新しています...";
    try {
        await callApi("PUT", "/users/" + encodeURIComponent(user.id), user);
        editSection.hidden = true;
        await refreshList();
        listStatus.textContent = "更新しました。" + listStatus.textContent;
    } catch (error) {
        editStatus.textContent = "更新に失敗しました: " + error.message;
    }
}

async function deleteUser(user) {
    if (!confirm("「" + user.name + "」（" + user.id + "）を削除します。元に戻せません。よろしいですか？")) {
        return;
    }
    listStatus.className = "";
    listStatus.textContent = "削除しています...";
    try {
        await callApi("DELETE", "/users/" + encodeURIComponent(user.id));
        await refreshList();
        listStatus.textContent = "削除しました。" + listStatus.textContent;
    } catch (error) {
        listStatus.textContent = "削除に失敗しました: " + error.message;
    }
}

document.getElementById("loadButton").addEventListener("click", loadUsers);
document.getElementById("clearButton").addEventListener("click", clearView);
document.getElementById("searchButton").addEventListener("click", searchUser);
searchInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        searchUser();
    }
});
document.getElementById("saveButton").addEventListener("click", saveUser);
document.getElementById("cancelButton").addEventListener("click", function() {
    editSection.hidden = true;
});

if (isCognitoEnabled()) {
    showLoggedIn(false);
    loginForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        var username = loginForm.elements.username.value.trim();
        var password = loginForm.elements.password.value;
        if (!username || !password) {
            loginStatus.textContent = "ユーザIDとパスワードを入力してください。";
            return;
        }
        loginStatus.textContent = "ログインしています...";
        try {
            await login(username, password);
            loginStatus.textContent = "";
            clearView();
            showLoggedIn(true);
        } catch (error) {
            loginStatus.textContent = loginErrorMessage(error);
        } finally {
            loginForm.elements.password.value = "";
        }
    });
    document.getElementById("logoutButton").addEventListener("click", function() {
        idToken = "";
        clearView();
        showLoggedIn(false);
        loginStatus.textContent = "ログアウトしました。";
    });
}
