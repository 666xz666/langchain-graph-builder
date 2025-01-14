# langchain-graph-builder

[英文文档](./README_en.md)

## 项目简介

langchain-graph-builder 是一个基于 FastAPI 构建的后端服务项目，旨在为知识库的创建、管理以及与之相关的对话功能提供接口支持。通过该项目，用户可以方便地创建知识库、上传文件至知识库、获取文件内容、删除知识库、生成知识库文件向量、获取知识库信息、进行大模型流式对话以及 RAG/GraphRAG 对话等操作，同时还支持创建知识库图谱。

## 已经实现的功能

### 1. 知识库

- 上传文件构建知识库

- 知识库向量化

- 利用大模型结构化输出从向量库构建知识图谱
- 以不同的level删除知识库

### 2. 对话

- 流式对话

- RAG对话

- 联网解析网页对话

- GraphRAG对话

## 快速启动

### 1. 配置环境

```shell
git clone https://github.com/666xz666/langchain-graph-builder.git
cd langchain-graph-builder

conda create -n lgb python=3.11 -y
conda activate lgb

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 复制配置文件

```shell
python config_tool.py --copy
```

### 3. 配置模型

配置大模型api key

embedding模型下载:

 https://pan.baidu.com/s/1XKQfFnSLbF0AjTLy_BCeFQ?pwd=fkrv 

### 4. 配置neo4j

安装neo4j 5.21.0, 配置apoc

https://blog.csdn.net/m0_63593482/article/details/133096869

### 5. 配置路径信息

知识库存储目录，日志目录, 模型路径等

### 6. 启动app

```shell
python app.py
```

## 文档

启动后在`<host>:<port>/redoc`能查看文档

![fa48a08dea405ac3d0b043960cb1102](./assets/fa48a08dea405ac3d0b043960cb1102.png)

## Q&A

### 1.  “No module named pwd”（for Windows）

https://blog.csdn.net/qq_40821260/article/details/137644996