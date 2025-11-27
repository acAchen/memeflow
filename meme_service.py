# meme_service.py
import os
import tempfile
from typing import Tuple

from creativity import get_text
from script import get_script  # 负责 故事 → JSONL 脚本
import asyncio
from movie import process_jsonl_story  # 负责 JSONL → 视频

DEFAULT_SCRIPT_FILE = os.path.join(os.getcwd(), "script_checked.jsonl")
DEFAULT_VIDEO_PATH = os.path.join(os.getcwd(), "results", "Final_Story.mp4")


def generate_script_from_input(input_text: str) -> Tuple[bool, str]:
    """
    接口1：自然语言输入 → JSON/JSONL 脚本字符串
    返回 (success, script_text_or_error_msg)
    """
    try:
        os.makedirs("results", exist_ok=True)

        # 用临时目录保存中间的 text.txt
        with tempfile.TemporaryDirectory() as tmpdir:
            text_path = os.path.join(tmpdir, "text.txt")
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(input_text)

            # 1) LLM 生成故事文案，写回 text_path
            get_text(input_text=input_text, output_file=text_path)

            # 2) LLM 生成 JSONL 脚本，写到 DEFAULT_SCRIPT_FILE
            script_text = get_script(input_file=text_path, output_file=DEFAULT_SCRIPT_FILE)

        if not script_text:
            return False, "LLM 未生成脚本内容"

        return True, script_text
    except Exception as e:
        return False, f"生成脚本时出错: {e}"


def generate_video_from_script(script_text: str) -> Tuple[bool, str]:
    """
    接口2：脚本字符串(JSON/JSONL) → 最终视频路径
    返回 (success, video_path_or_error_msg)
    """
    try:
        os.makedirs("results", exist_ok=True)

        # 强制把脚本写入统一的脚本文件，供 movie.py 使用
        script_file = DEFAULT_SCRIPT_FILE
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_text)

        ok = asyncio.run(process_jsonl_story(script_file))
        if not ok:
            return False, "视频生成失败"

        if not os.path.exists(DEFAULT_VIDEO_PATH):
            return False, "未找到生成的视频文件"

        return True, DEFAULT_VIDEO_PATH
    except Exception as e:
        return False, f"视频生成流程出错: {e}"


def generate_video_from_input(input_text: str) -> Tuple[bool, str]:
    """
    可选接口3：一键 从文本 → 脚本 → 视频
    主要给自己测试用，前端现在用的是分两步模式。
    """
    ok, script_or_err = generate_script_from_input(input_text)
    if not ok:
        return False, script_or_err

    return generate_video_from_script(script_or_err)
