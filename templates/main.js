let isGenerating = false;

// 字符计数
document.addEventListener("DOMContentLoaded", () => {
    const inputText = document.getElementById("inputText");
    const charCount = document.getElementById("charCount");

    inputText.addEventListener("input", function () {
        charCount.textContent = this.value.length;
    });

    // 页面加载时检查是否已有生成好的视频
    checkExistingVideo();
});

// 生成脚本
async function generateScript() {
    if (isGenerating) return;

    const inputText = document.getElementById("inputText").value.trim();
    const scriptArea = document.getElementById("scriptText");
    const btn = document.getElementById("generateScriptBtn");
    const loading = document.getElementById("loading");

    if (!inputText) {
        showStatus("请输入文本内容", "error");
        return;
    }

    isGenerating = true;
    btn.disabled = true;
    loading.style.display = "flex";
    hideStatus();

    try {
        showStatus("脚本生成中，请稍候...", "generating");

        const response = await fetch("/generate-script", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ text: inputText }),
        });

        const result = await response.json();

        if (result.success) {
            scriptArea.value = result.script || "";
            showStatus(result.message || "脚本生成成功！", "success");
        } else {
            showStatus(result.message || "脚本生成失败", "error");
        }
    } catch (error) {
        showStatus("请求失败: " + error.message, "error");
    } finally {
        isGenerating = false;
        btn.disabled = false;
        loading.style.display = "none";
    }
}

// 根据脚本生成视频
async function generateVideoFromScript() {
    if (isGenerating) return;

    const scriptText = document.getElementById("scriptText").value.trim();
    const btn = document.getElementById("generateVideoBtn");
    const loading = document.getElementById("loading");
    const videoContainer = document.getElementById("videoContainer");
    const videoPlayer = document.getElementById("videoPlayer");

    if (!scriptText) {
        showStatus("脚本为空，请先点击「生成脚本」。", "error");
        return;
    }

    isGenerating = true;
    btn.disabled = true;
    loading.style.display = "flex";
    videoContainer.style.display = "none";
    hideStatus();

    try {
        showStatus("视频生成中，请耐心等待...", "generating");

        const response = await fetch("/generate-video-from-script", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ script: scriptText }),
        });

        const result = await response.json();

        if (result.success) {
            showStatus(result.message || "视频生成成功！", "success");

            const timestamp = new Date().getTime();
            videoPlayer.src = "/video/Final_Story.mp4?t=" + timestamp;
            videoContainer.style.display = "block";
            videoPlayer.load();
        } else {
            showStatus(result.message || "视频生成失败，请检查脚本格式是否正确", "error");
        }
    } catch (error) {
        showStatus("请求失败: " + error.message, "error");
    } finally {
        isGenerating = false;
        btn.disabled = false;
        loading.style.display = "none";
    }
}

// 检查是否已有生成的视频
async function checkExistingVideo() {
    const videoContainer = document.getElementById("videoContainer");
    const videoPlayer = document.getElementById("videoPlayer");

    try {
        const response = await fetch("/check-video");
        const result = await response.json();

        if (result.exists) {
            const timestamp = new Date().getTime();
            videoPlayer.src = "/video/Final_Story.mp4?t=" + timestamp;
            videoContainer.style.display = "block";
        }
    } catch (error) {
        console.log("检查已有视频失败:", error);
    }
}

// 显示状态
function showStatus(message, type) {
    const status = document.getElementById("status");
    status.textContent = message || "";
    status.className = "status " + type;
    status.style.display = "block";
}

// 隐藏状态
function hideStatus() {
    const status = document.getElementById("status");
    status.style.display = "none";
}

// 退出应用
async function exitApp() {
    if (!confirm("确定要退出程序吗？")) {
        return;
    }
    try {
        await fetch("/shutdown", { method: "POST" });
        setTimeout(() => {
            window.close();
        }, 1000);
    } catch (error) {
        window.close();
    }
}

