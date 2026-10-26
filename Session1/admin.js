// 会員の一覧・更新・削除を行う管理画面の動き（admin.html から読み込み）
var adminEndpoint = (window.ADMIN_API_ENDPOINT || "").replace(/\/+$/, "");
var listStatus = document.getElementById("listStatus");
var editStatus = document.getElementById("editStatus");
var userRows = document.getElementById("userRows");
var editSection = document.getElementById("edit");
var editForm = document.getElementById("editForm");

// API を呼ぶ共通の関数
async function callApi(method, path, body) {
    if (!adminEndpoint) {
        throw new Error("管理 API の URL は Session4 で config.js に設定します。");
    }
    var headers = {};
    if (body) {
        headers["Content-Type"] = "application/json";
    }
    var response = await fetch(adminEndpoint + path, {
        method: method,
        headers: headers,
        body: body ? JSON.stringify(body) : undefined
    });
    // 削除に成功したときは本文がない（204）
    var result = response.status === 204 ? {} : await response.json();
    if (!response.ok) {
        throw new Error(result.message || "処理に失敗しました");
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
        await loadUsers();
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
        await loadUsers();
        listStatus.textContent = "削除しました。" + listStatus.textContent;
    } catch (error) {
        listStatus.textContent = "削除に失敗しました: " + error.message;
    }
}

document.getElementById("loadButton").addEventListener("click", loadUsers);
document.getElementById("saveButton").addEventListener("click", saveUser);
document.getElementById("cancelButton").addEventListener("click", function() {
    editSection.hidden = true;
});
