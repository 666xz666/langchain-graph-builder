from flask import Flask, request, jsonify, send_from_directory, stream_with_context
import os
from config import  *
from knowledge_base import *
# import logging
from llms import *
from flask import Response
from prompts import *
import json
from utils import *

logging = get_logging()

app = Flask(__name__)

# 创建 KnowledgeBase 类的实例
kb = KnowledgeBase()

# 创建知识库接口
@app.route('/create_kb', methods=['POST'])
def create_kb():
    kb_name = request.json.get('kb_name')
    desc = request.json.get('desc')
    if not kb_name:
        return jsonify({"code": 400, "msg": "知识库名称不能为空"})
    if not desc:
        desc = ""

    try:
        kb_uuid = kb.create_kb(kb_name, desc)
        return jsonify({"code": 200, "msg": f"知识库 {kb_name} 创建成功", "kb_uuid": kb_uuid})
    except Exception as e:
        return jsonify({"code": 400, "msg": str(e)})

# 向指定知识库上传文件接口
@app.route('/upload_file', methods=['POST'])
def upload_file():
    kb_uuid = request.form.get('kb_uuid')
    if not kb_uuid:
        return jsonify({"code": 400, "msg": "知识库 UUID 不能为空"})

    file = request.files.get('file')
    if not file:
        return jsonify({"code": 400, "msg": "未上传文件"})

    extension = file.filename.split('.')[-1]
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"code": 400, "msg": "不支持的文件类型"})

    try:
        file_uuid = kb.upload_file(kb_uuid, file, file.filename)
        return jsonify({"code": 200, "msg": "文件上传成功", "file_uuid": file_uuid})
    except Exception as e:
        return jsonify({"code": 400, "msg": str(e)})

# 获取文件内容接口
@app.route('/get_file', methods=['GET'])
def get_file():
    file_uuid = request.args.get('file_uuid')
    kb_uuid = request.args.get('kb_uuid')
    if not file_uuid:
        return jsonify({"code": 400, "msg": "文件 UUID 不能为空"})

    try:
        file_path = kb.get_file(kb_uuid, file_uuid)
        logging.info(f"File path: {file_path}")
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
    except Exception as e:
        logging.error(str(e))
        return jsonify({"code": 404, "msg": str(e)})

# 删除指定知识库接口
@app.route('/delete_kb', methods=['POST'])
def delete_kb():
    kb_uuid = request.json.get('kb_uuid')
    if not kb_uuid:
        return jsonify({"code": 400, "msg": "知识库 UUID 不能为空"})
    try:
        kb.delete_kb(kb_uuid)
        return jsonify({"code": 200, "msg": "知识库删除成功"})
    except Exception as e:
        return jsonify({"code": 400, "msg": str(e)})

# 用指定uuid知识库现有文件生成向量接口
@app.route('/generate_vectors', methods=['POST'])
def generate_vectors():
    kb_uuid = request.json.get('kb_uuid')
    if not kb_uuid:
        return jsonify({"code": 400, "msg": "知识库 UUID 不能为空"})

    try:
        kb.generate_vectors(kb_uuid)
        return jsonify({"code": 200, "msg": "知识库中的所有文件已成功向量化"})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"code": 500, "msg": str(e)})

#返回数据库信息接口
@app.route('/get_kb_info', methods=['GET'])
def get_kb_info():
    kb_uuid = request.args.get('kb_uuid')
    try:
        db_info = kb.get_kb_info(kb_uuid)
        return jsonify({"code": 200, "msg": "数据库信息获取成功", "db_info": db_info})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})



#大模型流式对话接口
@app.route('/chat/chat', methods=['POST'])
def chat_stream():
    model_name = request.json.get('model_name', 'kimi')
    logging.debug(f"model_name: {model_name}")
    try:
        llm = get_llm(model_name)
    except Exception as e:
        return jsonify({"code": 400, "msg": str(e)})

    system_prompt = request.json.get('system_prompt', CHAT_PROMPT)
    user_input = request.json.get('user_input')
    history = request.json.get('history', [])  # 获取历史对话记录，如果没有提供，则默认为空列表
    temperature = request.json.get('temperature', 0.8)
    max_tokens = request.json.get('max_tokens', 2048)
    stream = request.json.get('stream', True)

    if not user_input:
        return jsonify({"code": 400, "msg": "用户输入不能为空"})

    def generate():
        try:
            # 将 history 参数传递给 get_response 方法
            response = llm.get_response(system_prompt, user_input, history=history, temperature=temperature, max_tokens=max_tokens, stream=stream)
            yield f"{response}\n"
        except Exception as e:
            logging.error(str(e))
            yield f"Error: {str(e)}\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')


@app.route('/chat/rag', methods=['POST'])
def rag_chat():
    model_name = request.form.get('model_name', 'kimi')
    try:
        llm = get_llm(model_name)
    except Exception as e:
        return jsonify({"code": 400, "msg": str(e)})

    user_input = request.json.get('user_input')
    history = request.json.get('history', [])  # 获取历史对话记录，如果没有提供，则默认为空列表
    temperature = request.json.get('temperature', 0.8)
    max_tokens = request.json.get('max_tokens', 2048)
    stream = request.json.get('stream', True)
    top_k = request.json.get('top_k', 5)
    kb_uuid = request.json.get('kb_uuid')

    if not user_input:
        return jsonify({"code": 400, "msg": "用户输入不能为空"})
    if not kb_uuid:
        return jsonify({"code": 400, "msg": "知识库 UUID 不能为空"})

    try:
        res = kb.find_top_k_matches_in_kb(kb_uuid, user_input, top_k)
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})

    def generate():
        try:
            yield json.dumps({"code": 200, "msg": "匹配结果", "data": res}) + '\n\n'
            knowledges = ""
            for match in res:
                knowledges += f"{match[1]}\n"
            system_prompt = RAG_PROMPT.format(knowledges=knowledges)
            # 将 history 参数传递给 get_response 方法
            response = llm.get_response(system_prompt, user_input, history=history, temperature=temperature, max_tokens=max_tokens, stream=stream)
            yield json.dumps({"code": 200, "msg": "系统回复", "data": response}) + '\n\n'
        except Exception as e:
            logging.error(str(e))
            yield json.dumps({"code": 500, "msg": str(e)}) + '\n\n'

    return Response(stream_with_context(generate()), content_type='text/event-stream')

@app.route('/create_graph', methods=['POST'])
def create_graph():
    kb_uuid = request.json.get('kb_uuid')
    if not kb_uuid:
        return jsonify({"code": 400, "msg": "知识库 UUID 不能为空"})
    try:
        kb.crete_graph_kb(kb_uuid)
        return jsonify({"code": 200, "msg": "知识库图谱创建成功"})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"code": 500, "msg": str(e)})




if __name__ == '__main__':
    logging.info("Starting server...")
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.run(debug=False, port=SERVER_PORT, use_reloader=False)


