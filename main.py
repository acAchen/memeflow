import os
import threading
import logging

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    send_from_directory,
)

from meme_service import (
    generate_video_from_input,
    generate_script_from_input,
    generate_video_from_script,
)


# ---------------- 日志配置 ---------------- #

# 统一设置日志格式和等级，保证异常会以 ERROR 级别打印
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message).500s",
)
logger = logging.getLogger(__name__)


class VideoGeneratorApp:
    """保存应用运行状态的简单类"""

    def __init__(self):
        self.is_generating = False
        self.generation_status = "idle"
        self.generation_message = ""
        self.video_path = os.path.join("results", "Final_Story.mp4")

    def shutdown_server(self):
        """延迟退出进程，避免还没返回响应就退出"""
        def _shutdown():
            import time
            time.sleep(1)
            os._exit(0)

        threading.Thread(target=_shutdown, daemon=True).start()


app = Flask(__name__, template_folder="templates")
app_state = VideoGeneratorApp()


# ---------------- 基础路由：页面 & 静态资源 ---------------- #

@app.route("/")
def index():
    """主页面"""
    logger.info("GET / 请求主页面")
    return render_template("index.html")


@app.route("/styles.css")
def styles():
    """从 templates 目录下返回 CSS（因为你把 css 放在 templates 里）"""
    return send_from_directory("templates", "styles.css", mimetype="text/css")


@app.route("/main.js")
def main_js():
    """从 templates 目录下返回 JS"""
    return send_from_directory("templates", "main.js", mimetype="application/javascript")


# ---------------- 生成相关接口 ---------------- #

@app.route("/generate-video", methods=["POST"])
def generate_video_route():
    """原来的“一键从文本生成视频”接口（可选保留）"""
    try:
        data = request.get_json() or {}
        input_text = data.get("text", "").strip()
        logger.info("POST /generate-video 请求，文本长度=%d", len(input_text))

        if not input_text:
            logger.warning("POST /generate-video 文本为空")
            return jsonify({
                "success": False,
                "message": "请输入文本内容",
            })

        app_state.generation_status = "generating"
        app_state.generation_message = "视频生成中，请稍候..."

        success = generate_video_from_input(input_text)

        if success:
            app_state.generation_status = "success"
            app_state.generation_message = "视频生成成功！"
            logger.info("视频生成成功，文件路径=%s", app_state.video_path)
            return jsonify({
                "success": True,
                "message": "视频生成成功！",
                "video_path": app_state.video_path,
            })
        else:
            app_state.generation_status = "error"
            app_state.generation_message = "视频生成失败"
            logger.error("视频生成失败（generate_video_from_input 返回 False）")
            return jsonify({
                "success": False,
                "message": "视频生成失败，请稍后重试",
            })

    except Exception as e:
        # 这里会把异常（包括 get_text() 参数错误这类）完整记录为 ERROR
        app_state.generation_status = "error"
        app_state.generation_message = f"视频生成出错: {e}"
        logger.exception("处理 /generate-video 请求时发生异常: %s", e)
        return jsonify({
            "success": False,
            "message": f"视频生成出错: {e}",
        })


@app.route("/generate-script", methods=["POST"])
def generate_script_route():
    """根据用户输入先生成脚本(jsonl)，返回给前端查看/修改。"""
    try:
        data = request.get_json() or {}
        input_text = data.get("text", "").strip()
        logger.info("POST /generate-script 请求，文本长度=%d", len(input_text))

        if not input_text:
            logger.warning("POST /generate-script 文本为空")
            return jsonify({
                "success": False,
                "message": "请输入文本内容",
            })

        success, result = generate_script_from_input(input_text)

        if success:
            logger.info("脚本生成成功，长度=%d 字符", len(result) if isinstance(result, str) else -1)
            return jsonify({
                "success": True,
                "message": "脚本生成成功！请检查后再生成视频。",
                "script": result,
            })
        else:
            # 这里通常会包含类似 get_text() got an unexpected keyword argument 'input_file' 的错误信息
            logger.error("脚本生成失败：%s", result)
            return jsonify({
                "success": False,
                "message": str(result),
            })

    except Exception as e:
        # 确保诸如 get_text() got an unexpected keyword argument 'input_file' 这类异常
        # 会在日志中以 ERROR 级别记录下来
        logger.exception("处理 /generate-script 请求时发生异常: %s", e)
        return jsonify({
            "success": False,
            "message": f"脚本生成出错: {e}",
        })


@app.route("/generate-video-from-script", methods=["POST"])
def generate_video_from_script_route():
    """使用前端传回的脚本文本生成视频。"""
    try:
        data = request.get_json() or {}
        script_text = data.get("script", "").strip()
        logger.info("POST /generate-video-from-script 请求，脚本文本长度=%d", len(script_text))

        if not script_text:
            logger.warning("POST /generate-video-from-script 脚本为空")
            return jsonify({
                "success": False,
                "message": "脚本内容为空，请先生成脚本",
            })

        app_state.generation_status = "generating"
        app_state.generation_message = "视频生成中，请稍候..."

        success = generate_video_from_script(script_text)

        if success:
            app_state.generation_status = "success"
            app_state.generation_message = "视频生成成功！"
            logger.info("根据脚本生成视频成功，文件路径=%s", app_state.video_path)
            return jsonify({
                "success": True,
                "message": "视频生成成功！",
                "video_path": app_state.video_path,
            })
        else:
            app_state.generation_status = "error"
            app_state.generation_message = "视频生成失败"
            logger.error("根据脚本生成视频失败（generate_video_from_script 返回 False）")
            return jsonify({
                "success": False,
                "message": "视频生成失败，请检查脚本格式是否正确",
            })

    except Exception as e:
        app_state.generation_status = "error"
        app_state.generation_message = f"视频生成出错: {e}"
        logger.exception("处理 /generate-video-from-script 请求时发生异常: %s", e)
        return jsonify({
            "success": False,
            "message": f"视频生成出错: {e}",
        })


# ---------------- 视频文件 & 状态 ---------------- #

@app.route("/video/<filename>")
def serve_video(filename):
    """返回生成好的视频，目前只支持 Final_Story.mp4"""
    logger.info("GET /video/%s", filename)

    if filename != "Final_Story.mp4":
        logger.warning("请求了不支持的文件名: %s", filename)
        return jsonify({
            "success": False,
            "message": "不支持的文件名",
        }), 404

    if not os.path.exists(app_state.video_path):
        logger.warning("请求视频文件不存在: %s", app_state.video_path)
        return jsonify({
            "success": False,
            "message": "视频文件不存在，请先生成视频",
        }), 404

    return send_file(app_state.video_path, mimetype="video/mp4")


@app.route("/check-video")
def check_video():
    """检查是否已有生成好的视频"""
    exists = os.path.exists(app_state.video_path)
    logger.info("GET /check-video，exists=%s", exists)
    return jsonify({
        "exists": exists,
        "video_path": app_state.video_path if exists else "",
    })


# ---------------- 关闭服务器 ---------------- #

@app.route("/shutdown", methods=["POST"])
def shutdown():
    """关闭 Flask 服务器"""
    logger.warning("收到 /shutdown 请求，服务器即将关闭")
    app_state.shutdown_server()
    return jsonify({"success": True, "message": "服务器即将关闭"})


if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    logger.info("启动 Flask 应用，监听 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
