from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from typing import List, Optional, Literal
import os
from tempfile import NamedTemporaryFile
from knowledge_base import KnowledgeBase
from llms import get_llm
from prompts import CHAT_PROMPT, RAG_PROMPT
from config import *
import json

from utils import get_logging
logging = get_logging()

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 KnowledgeBase 类的实例
kb = KnowledgeBase()

# 创建知识库接口
@app.post("/create_kb")
async def create_kb(
    kb_name: str = Body(..., description="知识库名称", examples=["1"]),
    desc: Optional[str] = Body(None, description="知识库描述", examples=["1"])
):
    if not kb_name:
        raise HTTPException(status_code=400, detail="知识库名称不能为空")
    desc = desc or ""
    try:
        kb_uuid = kb.create_kb(kb_name, desc)
        return {"code": 200, "msg": f"知识库 {kb_name} 创建成功", "kb_uuid": kb_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 向指定知识库上传文件接口
@app.post("/upload_file")
async def upload_file(
    kb_uuid: str = Form(..., description="知识库 UUID"),
    file: UploadFile = File(..., description="上传的文件")
):
    if not kb_uuid:
        raise HTTPException(status_code=400, detail="知识库 UUID 不能为空")
    if not file:
        raise HTTPException(status_code=400, detail="未上传文件")
    extension = file.filename.split('.')[-1]
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    try:
        file_uuid = await kb.upload_file(kb_uuid, file, file.filename)
        return {"code": 200, "msg": "文件上传成功", "file_uuid": file_uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 获取文件内容接口
@app.get("/get_file")
async def get_file(
    file_uuid: str = Query(..., description="文件 UUID", examples=["1"]),
    kb_uuid: str = Query(..., description="知识库 UUID", examples=["1"])
):
    if not file_uuid:
        raise HTTPException(status_code=400, detail="文件 UUID 不能为空")
    try:
        file_path = kb.get_file(kb_uuid, file_uuid)
        logging.info(f"File path: {file_path}")
        return FileResponse(file_path)
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=404, detail=str(e))

# 删除指定知识库接口
@app.post("/delete_kb")
async def delete_kb(
    kb_uuid: str = Body(..., description="知识库 UUID", examples=["1"]),
    with_graph: bool = Body(False, description="是否删除图谱", examples=[False])
):
    if not kb_uuid:
        raise HTTPException(status_code=400, detail="知识库 UUID 不能为空")
    try:
        kb.delete_kb(kb_uuid)
        return {"code": 200, "msg": "知识库删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 用指定uuid知识库现有文件生成向量接口
@app.post("/generate_vectors")
async def generate_vectors(
    kb_uuid: str = Body(..., description="知识库 UUID", examples=["1"]),
    chunk_size: int = Body(500, description="分块大小", examples=[500]),
    chunk_overlap: int = Body(100, description="分块重叠", examples=[100])
):
    if not kb_uuid:
        raise HTTPException(status_code=400, detail="知识库 UUID 不能为空")
    try:
        kb.generate_vectors(kb_uuid, chunk_size, chunk_overlap)
        return {"code": 200, "msg": "知识库中的所有文件已成功向量化"}
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# 返回数据库信息接口
@app.get("/get_kb_info")
async def get_kb_info(
    kb_uuid: str = Query(..., description="知识库 UUID", examples=["1"])
):
    try:
        db_info = kb.get_kb_info(kb_uuid)
        return {"code": 200, "msg": "数据库信息获取成功", "db_info": db_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 大模型流式对话接口
@app.post("/chat/chat")
async def chat_stream(
    model_name: str = Body("kimi", description="模型名称", examples=["1"]),
    system_prompt: str = Body(CHAT_PROMPT, description="系统提示", examples=[CHAT_PROMPT]),
    user_input: str = Body(..., description="用户输入", examples=["1"]),
    history: List[dict] = Body([], description="对话历史", examples=[[{"role": "user", "content": "你好"}]]),
    temperature: float = Body(0.8, description="温度", examples=[0.8]),
    max_tokens: int = Body(2048, description="最大 token 数", examples=[2048]),
    stream: bool = Body(True, description="是否流式", examples=[True])
):
    if not user_input:
        raise HTTPException(status_code=400, detail="用户输入不能为空")
    try:
        llm = get_llm(model_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        def generate():
            # 将 history 参数传递给 get_response 方法
            response = llm.get_response(system_prompt, user_input, history=history, temperature=temperature,
                                        max_tokens=max_tokens, stream=stream)
            yield json.dumps({"code": 200, "data": response}) + '\n\n'
        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# RAG对话接口
@app.post("/chat/rag")
async def rag_chat(
    model_name: str = Body("kimi", description="模型名称", examples=["1"]),
    user_input: str = Body(..., description="用户输入", examples=["1"]),
    history: List[dict] = Body([], description="对话历史", examples=[[{"role": "user", "content": "你好"}]]),
    temperature: float = Body(0.8, description="温度", examples=[0.8]),
    max_tokens: int = Body(2048, description="最大 token 数", examples=[2048]),
    stream: bool = Body(True, description="是否流式", examples=[True]),
    top_k: int = Body(5, description="top k", examples=[5]),
    kb_uuid: str = Body(..., description="知识库 UUID", examples=["1"])
):
    if not user_input:
        raise HTTPException(status_code=400, detail="用户输入不能为空")
    if not kb_uuid:
        raise HTTPException(status_code=400, detail="知识库 UUID 不能为空")
    try:
        res = kb.find_top_k_matches_in_kb(kb_uuid, user_input, top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    try:
        knowledges = "\n".join([match[1] for match in res])
        system_prompt = RAG_PROMPT.format(knowledges=knowledges)
        llm = get_llm(model_name)
        def generate():
            yield json.dumps({"code": 200, "msg": "匹配结果", "data": res}) + '\n\n'
            knowledges = ""
            for match in res:
                knowledges += f"{match[1]}\n"
            # 将 history 参数传递给 get_response 方法
            response = llm.get_response(system_prompt, user_input, history=history, temperature=temperature,
                                        max_tokens=max_tokens, stream=stream)
            yield json.dumps({"code": 200, "data": response}) + '\n\n'
        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

# 创建知识库图谱接口
@app.post("/create_graph")
async def create_graph(
    kb_uuid: str = Body(..., description="知识库 UUID", examples=["1"]),
    allow_nodes: Optional[List[str]] = Body(None, description="允许的节点类型", examples=[["person", "organization"]]),
    allow_relationships: Optional[List[str]] = Body(None, description="允许的关系类型", examples=[["knows", "work_for"]]),
    strict_mode: bool = Body(False, description="严格模式", examples=[False])
):
    if not kb_uuid:
        raise HTTPException(status_code=400, detail="知识库 UUID 不能为空")
    try:
        kb.create_graph_kb(kb_uuid, allow_nodes=allow_nodes, allow_relationships=allow_relationships, strict_mode=strict_mode)
        return {"code": 200, "msg": "知识库图谱创建成功"}
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)