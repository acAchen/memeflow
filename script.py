import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv
from prompt import PromptTemplate, script2json_prompt

load_dotenv()
backgrounds = os.listdir('./backgrounds')
meme_names = os.listdir("./meme")
backgrounds = [b.split('.')[0] for b in backgrounds]
meme_names = [m.split('.')[0] for m in meme_names]
def init_client():
    api_key = os.environ.get('SCRIPT_API_KEY')
    BASE_URL = os.environ.get('BASE_URL')

    if not api_key:
        raise ValueError("SCRIPT_API_KEY 未设置，请检查.env文件")
    return OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
    )

def read_input_file(file_path='text.txt'):
    """读取输入文本文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            raise ValueError(f"文件 {file_path} 为空")
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到输入文件: {file_path}")
    except Exception as e:
        raise Exception(f"读取文件时出错: {e}")

def save_to_jsonl(data, output_file="script.jsonl"):
    """将数据保存为JSONL格式"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 如果返回的是JSON字符串，先解析为Python对象
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    # 如果不是标准JSON，直接作为文本保存
                    f.write(json.dumps({"content": data}, ensure_ascii=False) + '\n')
                    return
            
            # 如果是列表，每条记录单独一行
            if isinstance(data, list):
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            else:
                # 如果是单个对象，直接写入
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"输出已保存到文件: {output_file}")
    except Exception as e:
        print(f"保存JSONL文件时出错: {e}")

def get_script(input_file='text.txt', output_file="script.jsonl"):
    """主函数：读取输入文件，生成脚本并保存为JSONL"""
    try:
        # 读取输入文件
        input_text = read_input_file(input_file)
        print(f"成功读取输入文件: {input_file}")
        print(f"输入内容: {input_text[:100]}...")  # 只显示前100个字符
        s2j = PromptTemplate(
            system_template=(script2json_prompt),
            user_template=("这是一段**脚本内容**，请按照要求生成json：{script}")
        )
        s2j_prompt = s2j.format_messages(script=input_text,backgrounds=backgrounds, memes=meme_names)
        print(s2j_prompt)

        MODEL = os.environ.get('MODEL')
        # 初始化客户端并调用API
        client = init_client()
        # full_prompt = fixed_prompt + input_text
        response = client.chat.completions.create(
            model=MODEL,
            messages=s2j_prompt,
            stream=False
        )
        res = response.choices[0].message.content
        
        # 打印结果到控制台
        print("\n生成的脚本内容:")
        print(res)
        
        # 保存为JSONL文件
        save_to_jsonl(res, output_file)
        
        return res
        
    except Exception as e:
        traceback.print_exc()
        print(f"处理过程中出错: {e}")
        return None

if __name__ == "__main__":
    get_script()