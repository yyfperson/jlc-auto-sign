# 脚本失效通知

由于嘉立创把登录滑块验证改为了阿里云 v2 无感滑块方案，导致本脚本的“自动登录抓包 AccessToken”逻辑失效，使得签到不成功。

本脚本相比其他同类脚本的优势正是在于自动抓包，省去手动更新 token 的麻烦，现在该部分逻辑已失效，继续更新脚本没有意义。

因此该仓库暂时停更，直到有破解阿里云 v2 滑块的方法，欢迎有解决方案的逆向大佬联系我，也欢迎各位大佬修改 `jlc.py` 让它焕发第二春。

---

## 同类脚本推荐（需要手动抓包）
- https://github.com/Foticing/LC-AutoSign
- https://github.com/sudojia/AutoTaskScript/

[查看本脚本原README](./readme.md)

---

## 附：自编抓包脚本

使用时打开 `m.jlc.com` 并确保处于登录状态，然后将以下代码全部粘贴至浏览器控制台（F12 → Console），回车执行，AccessToken 会自动复制到剪贴板。

```javascript
(function() {
    const host = window.location.hostname;
    const styleTitle = "font-size: 14px; font-weight: bold; color: #1E90FF;";
    const styleSuccess = "font-size: 14px; font-weight: bold; color: #2E8B57;";
    const styleError = "font-size: 14px; font-weight: bold; color: #DC143C;";
    const styleInfo = "color: #555;";

    console.clear();
    console.log("%c JLC自动抓包脚本 By zhangMonday", styleTitle);

    let resultValue = "";
    let resultType = "";

    // 嘉立创 m.jlc.com 提取 localStorage 中的 Token
    if (host.includes("m.jlc.com")) {
        const possibleKeys = ['X-JLC-AccessToken', 'token', 'accessToken', 'Authorization'];
        let token = "";
        
        for (let key of possibleKeys) {
            token = localStorage.getItem(key);
            if (token) break;
        }

        if (token) {
            token = token.replace(/^Bearer\s+/i, "");
            resultValue = token;
            resultType = "JLC Token (X-JLC-AccessToken)";
        } else {
            console.log("%c❌ 未在 localStorage 中找到 Token，请确认已登录。", styleError);
            return;
        }
    } 
    
    // 开源平台 oshwhub.com 提取 Cookie
    else if (host.includes("oshwhub.com")) {
        const cookie = document.cookie;
        if (cookie && cookie.length > 0) {
            resultValue = cookie;
            resultType = "开源平台 Cookie";
        } else {
            console.log("%c❌ 未找到 Cookie，请确认已登录。", styleError);
            return;
        }
    } 
    
    // 域名不匹配
    else {
        console.log(`%c⚠️ 当前域名 (${host}) 不支持。`, styleError);
        console.log("%c本脚本仅支持:\n1. m.jlc.com (提取Token)\n2. oshwhub.com (提取Cookie)", styleInfo);
        return;
    }

    // 输出结果
    if (resultValue) {
        console.log(`%c✅ 成功提取 ${resultType}:`, styleSuccess);
        console.log("---------------------------------------------------");
        console.log(resultValue);
        console.log("---------------------------------------------------");
        
        // 尝试自动复制到剪贴板
        try {
            const input = document.createElement('textarea');
            input.value = resultValue;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            console.log("%c📋 已自动复制到剪贴板！", "color: blue; font-style: italic;");
        } catch (err) {
            console.log("自动复制失败，请手动复制上面的值。");
        }
    }
})();
