from fastapi import FastAPI, WebSocket, HTTPException, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
import os
from pydantic import BaseModel
import asyncio
import json
import uuid
from typing import Optional, List, Dict, Any
import time
import re

# 导入现有的系统
from new_main import IntegratedQASystem
from auth import UserService, create_token, get_current_user, get_admin_user
from auth.models import LoginRequest, LoginResponse, UserCreate
from admin_service import AdminService

# 创建应用实例
app = FastAPI(title="问答系统API", description="集成MySQL和RAG的智能问答系统")

# 配置CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确定前端文件目录
FRONTEND_DIR = "frontend/dist" if os.path.exists("frontend/dist") else "static"
os.makedirs(FRONTEND_DIR, exist_ok=True)

# 创建全局QA系统实例
qa_system = IntegratedQASystem()

# 初始化认证服务
user_service = UserService(qa_system.mysql_client)

# 初始化管理员服务
admin_service = AdminService(qa_system.mysql_client, qa_system.vector_store)

# 日常问候用语
GREETING_PATTERNS = [
    {"pattern": r"^(你好|您好|hi|hello|嗨|哈喽|早上好|下午好|晚上好)", "response": "你好！我是智能学习助手，有什么问题可以帮你解答吗？"},
    {"pattern": r"^(你是谁|您是谁|你叫什么|你的名字|who are you)", "response": "我是你的智能学习助手，专注于知识问答和学习辅助，随时为你服务！"},
    {"pattern": r"^(在吗|在不在|有人吗)", "response": "我在呢，请随时向我提问！"},
    {"pattern": r"^(干嘛呢|你在干嘛|做什么|在做什么)", "response": "我正在等待你的提问，有什么需要了解的尽管问我！"},
    {"pattern": r"^(谢谢|多谢|感谢|thanks|thank you|3q|3Q)", "response": "不客气，有问题随时找我！"},
    {"pattern": r"^(再见|拜拜|bye|88|晚安|回头见)", "response": "再见，祝你学习顺利！"},
]


# ==================== 请求模型 ====================

class QueryRequest(BaseModel):
    query: str
    source_filter: Optional[str] = None
    session_id: Optional[str] = None


# ==================== 静态文件 ====================

assets_path = os.path.join(FRONTEND_DIR, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "EduRAG API is running. Frontend not built yet.", "docs": "/docs"}


@app.get("/favicon.svg")
async def favicon():
    favicon_path = os.path.join(FRONTEND_DIR, "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"status": "not found"}


# ==================== 认证路由 ====================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """用户登录"""
    user = user_service.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user["user_id"], user["username"], user["role"])
    return {"token": token, "username": user["username"], "role": user["role"]}


@app.post("/api/auth/signup")
async def signup(request: LoginRequest):
    """公开注册（仅普通用户角色）"""
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if len(request.password) < 3:
        raise HTTPException(status_code=400, detail="密码至少3位")
    success = user_service.create_user(request.username, request.password, role="user")
    if not success:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return {"status": "success", "username": request.username, "role": "user"}


@app.post("/api/auth/register")
async def register(request: UserCreate, admin: dict = Depends(get_admin_user)):
    """管理员创建用户（可指定角色）"""
    success = user_service.create_user(request.username, request.password, request.role)
    if not success:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return {"status": "success", "username": request.username, "role": request.role}


@app.get("/api/auth/users")
async def list_users(admin: dict = Depends(get_admin_user)):
    """管理员查看用户列表"""
    return {"users": user_service.list_users()}


@app.delete("/api/auth/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    """管理员删除用户"""
    if user_id == admin["user_id"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "success"}


@app.get("/api/auth/me")
async def current_user_info(user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"username": user["username"], "role": user["role"], "user_id": user["user_id"]}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """修改当前用户密码"""
    if len(request.new_password) < 3:
        raise HTTPException(status_code=400, detail="新密码至少3位")
    success = user_service.change_password(
        user["username"], request.old_password, request.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="原密码错误")
    return {"status": "success", "message": "密码已修改"}


# ==================== 管理员路由 ====================

@app.post("/api/admin/upload")
async def upload_file(
    file: UploadFile = File(...),
    source: str = Form(...),
    admin: dict = Depends(get_admin_user),
):
    """管理员上传文件并存入 Milvus"""
    if source not in qa_system.config.VALID_SOURCES:
        raise HTTPException(status_code=400, detail=f"无效学科: {source}，支持: {qa_system.config.VALID_SOURCES}")

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="文件为空")

        result = admin_service.process_upload(
            file_bytes=file_bytes,
            file_name=file.filename,
            source=source,
            username=admin["username"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/documents")
async def list_documents(admin: dict = Depends(get_admin_user)):
    """管理员查看已上传文档列表（按 source 汇总）"""
    return {"documents": admin_service.list_documents()}


@app.get("/api/admin/documents/{source}")
async def list_source_files(source: str, admin: dict = Depends(get_admin_user)):
    """管理员查看某学科的文件详情"""
    return {"files": admin_service.list_files(source)}


@app.delete("/api/admin/documents/{source}")
async def delete_documents(source: str, admin: dict = Depends(get_admin_user)):
    """管理员删除某学科的所有文档"""
    result = admin_service.delete_by_source(source)
    return result


# ==================== 问答路由（需要登录） ====================

@app.post("/api/create_session")
async def create_session(user: dict = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@app.get("/api/history/{session_id}")
async def get_history(session_id: str, user: dict = Depends(get_current_user)):
    try:
        history = qa_system.get_session_history(session_id, username=user.get("username"))
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@app.delete("/api/history/{session_id}")
async def clear_history(session_id: str, user: dict = Depends(get_current_user)):
    success = qa_system.clear_session_history(session_id, username=user.get("username"))
    if success:
        return {"status": "success", "message": "历史记录已清除"}
    else:
        raise HTTPException(status_code=500, detail="清除历史记录失败")


def check_greeting(query: str) -> Optional[str]:
    if not query:
        return None
    query_text = query.strip()
    for pattern_info in GREETING_PATTERNS:
        if re.match(pattern_info["pattern"], query_text, re.IGNORECASE):
            return pattern_info["response"]
    return None


@app.post("/api/query")
async def query(request: QueryRequest, user: dict = Depends(get_current_user)):
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    greeting_response = check_greeting(request.query)
    if greeting_response:
        return {
            "answer": greeting_response, "is_streaming": False,
            "session_id": session_id, "processing_time": time.time() - start_time,
        }

    answer, need_rag = qa_system.bm25_search.search(request.query, threshold=0.85)
    if need_rag:
        collected_answer = ""
        for token, is_complete in qa_system.query(
            query=request.query, source_filter=request.source_filter, session_id=session_id, username=user.get("username")
        ):
            if token:
                collected_answer += token
            if is_complete:
                break
        return {
            "answer": collected_answer or "未找到答案", "is_streaming": False,
            "session_id": session_id, "processing_time": time.time() - start_time,
        }
    return {
        "answer": answer, "is_streaming": False,
        "session_id": session_id, "processing_time": time.time() - start_time,
    }


# ==================== WebSocket 流式 ====================

@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if token:
        from auth.jwt_handler import verify_token_ws
        user = verify_token_ws(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
    else:
        # 开发模式允许无 token 连接
        user = {"username": "anonymous", "role": "user", "user_id": 0}

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)

            if request_data.get("type") == "ping":
                continue

            query = request_data.get("query")
            if not query:
                continue

            source_filter = request_data.get("source_filter")
            session_id = request_data.get("session_id", str(uuid.uuid4()))
            start_time = time.time()

            if websocket.client_state == websocket.client_state.CONNECTED:
                await websocket.send_json({"type": "start", "session_id": session_id})

            greeting_response = check_greeting(query)
            if greeting_response:
                if websocket.client_state == websocket.client_state.CONNECTED:
                    await websocket.send_json({"type": "token", "token": greeting_response, "session_id": session_id})
                    await websocket.send_json({
                        "type": "end", "session_id": session_id,
                        "is_complete": True, "processing_time": time.time() - start_time,
                    })
                continue

            collected_answer = ""
            for token, is_complete in qa_system.query(query, source_filter=source_filter, session_id=session_id, username=user.get("username")):
                collected_answer += token
                if is_complete and not collected_answer:
                    if websocket.client_state == websocket.client_state.CONNECTED:
                        await websocket.send_json({
                            "type": "end", "session_id": session_id,
                            "is_complete": True, "processing_time": time.time() - start_time,
                        })
                    break
                if token and websocket.client_state == websocket.client_state.CONNECTED:
                    await websocket.send_json({"type": "token", "token": token, "session_id": session_id})
                if is_complete:
                    if websocket.client_state == websocket.client_state.CONNECTED:
                        await websocket.send_json({
                            "type": "end", "session_id": session_id,
                            "is_complete": True, "processing_time": time.time() - start_time,
                        })
                    break
                await asyncio.sleep(0.01)
    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected: code={e.code}, reason={e.reason}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        if websocket.client_state == websocket.client_state.CONNECTED:
            await websocket.send_json({"type": "error", "error": str(e)})
    finally:
        try:
            if websocket.client_state == websocket.client_state.CONNECTED:
                await websocket.close()
        except Exception as e:
            print(f"Error closing WebSocket: {str(e)}")


# ==================== 公开接口 ====================

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/sources")
async def get_sources():
    return {"sources": qa_system.config.VALID_SOURCES}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
