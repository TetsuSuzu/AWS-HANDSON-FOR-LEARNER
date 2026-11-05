// 会員登録フォームと料理のおすすめの動きを担当します（index.html から読み込み）
document.getElementById("registerButton").addEventListener("click", async function() {
    var form = document.getElementById("registrationForm");
    var status = document.getElementById("registrationStatus");
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
        // ルート POST / を呼ぶため、URL の末尾に / を付けて送る（ステージ名だけの URL では届かない）
        var response = await fetch(apiEndpoint + "/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(user)
        });
        var result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || "登録に失敗しました");
        }
        status.textContent = "登録が完了しました。";
        status.className = "success-message";
        alert("会員登録しました。");
        form.reset();
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
