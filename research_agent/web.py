from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import shutil
import threading
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from research_agent.agent import ResearchAgent
from research_agent.config import RUNS_DIR, SESSIONS_DIR, UPLOADS_DIR
from research_agent.context import AgentContext
from research_agent.harness import AwaitConfirmation, Harness

# Initialize FastAPI app
app = FastAPI(
    title="Research Agent API",
    description="AI-powered research assistant for paper analysis and code exploration",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="research_agent/static"), name="static")
templates = Jinja2Templates(directory="research_agent/templates")

# Global state
executor = ThreadPoolExecutor(max_workers=4)
TASKS: dict[str, dict] = {}
SESSIONS: dict[str, dict] = {}
CANCELLED_TASKS: set[str] = set()
HARNESSES: dict[str, Harness] = {}
CONFIRM_EVENTS: dict[str, dict] = {}
WEBSOCKET_CONNECTIONS: dict[str, list[WebSocket]] = {}  # task_id -> [websockets]


# ============================================================================
# Pydantic Models for Request/Response Validation
# ============================================================================

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    messages: list[dict]
    artifacts: dict[str, str]
    artifact_index: list[dict]
    run_id: str
    project_name: str
    history: list[dict]


class TaskResponse(BaseModel):
    task_id: str
    mode: str
    status: str
    project_name: str
    session_id: str
    run_id: str
    progress: float
    stage: str
    message: str
    eta_seconds: int
    eta_breakdown: list[dict]
    trace: list[dict]
    artifacts: dict[str, str]
    error: str
    created_at: str
    updated_at: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    scope: list[str] = []


class RepoRequest(BaseModel):
    project_name: Optional[str] = "repo-analysis"
    repo_path: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class ResearchFullRequest(BaseModel):
    project_name: Optional[str] = "my-research"
    github_query: str = Field(..., min_length=1)
    language: Optional[str] = None
    min_stars: Optional[int] = None
    session_id: Optional[str] = None


class ConfirmRequest(BaseModel):
    choice: str = "continue"  # "continue" or "cancel"


# ============================================================================
# Helper Functions
# ============================================================================

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_session(session_id: str | None = None) -> tuple[str, dict]:
    sid = session_id or uuid.uuid4().hex[:12]
    session = SESSIONS.get(sid)
    if session is None:
        session_path = SESSIONS_DIR / f"{sid}.json"
        if session_path.exists():
            session = json.loads(session_path.read_text(encoding="utf-8"))
        else:
            session = {
                "session_id": sid,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "messages": [],
                "artifacts": {},
                "artifact_index": [],
                "run_id": "",
                "project_name": "",
                "history": [],
            }
        SESSIONS[sid] = session
    return sid, session


def build_artifact_index(artifacts: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"name": name, "kind": name.split(".")[-1], "preview": value[:160]}
        for name, value in sorted(artifacts.items())
    ]


def save_session(session: dict) -> None:
    session["updated_at"] = now_iso()
    session["artifact_index"] = build_artifact_index(session.get("artifacts", {}))
    session_path = SESSIONS_DIR / f"{session['session_id']}.json"
    session_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")


def serialize_artifacts(run_dir: Path) -> dict[str, str]:
    names = [
        "paper_preview.txt",
        "paper_digest.json",
        "summary.md",
        "summary_translated.md",
        "claims.md",
        "outline.md",
        "draft.md",
        "survey_taxonomy.md",
        "survey_evolution.md",
        "survey_comparison_table.md",
        "survey_challenges.md",
        "survey.md",
        "paper_structure.md",
        "method_card.md",
        "paper_metadata.json",
        "compare_matrix.json",
        "comparison_report.md",
        "repo_profile.json",
        "ast_analysis.json",
        "env_resolution.json",
        "run_manifest.json",
    ]
    artifacts: dict[str, str] = {}
    for name in names:
        path = run_dir / name
        if path.exists():
            artifacts[name] = path.read_text(encoding="utf-8")
    for pattern in ["paper_*_profile.md", "paper_*_profile.json", "survey_partial_*.md"]:
        for path in run_dir.glob(pattern):
            artifacts[path.name] = path.read_text(encoding="utf-8")

    # 添加图表索引
    diagram_index = run_dir / "diagrams" / "diagram_index.md"
    if diagram_index.exists():
        artifacts["diagrams/diagram_index.md"] = diagram_index.read_text(encoding="utf-8")

    return artifacts


def create_task(mode: str, project_name: str, session_id: str) -> str:
    task_id = uuid.uuid4().hex[:12]
    TASKS[task_id] = {
        "task_id": task_id,
        "mode": mode,
        "status": "queued",
        "project_name": project_name,
        "session_id": session_id,
        "run_id": "",
        "progress": 0.0,
        "stage": "queued",
        "message": "任务已提交",
        "eta_seconds": 0,
        "eta_breakdown": [],
        "trace": [],
        "artifacts": {},
        "error": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    return task_id


async def update_task(task_id: str, **payload: object) -> None:
    TASKS[task_id].update(payload)
    TASKS[task_id]["updated_at"] = now_iso()

    # Broadcast update via WebSocket
    await broadcast_task_update(task_id, TASKS[task_id])


async def broadcast_task_update(task_id: str, task_data: dict) -> None:
    """Send task update to all connected WebSocket clients for this task."""
    if task_id in WEBSOCKET_CONNECTIONS:
        dead_connections = []
        for ws in WEBSOCKET_CONNECTIONS[task_id]:
            try:
                await ws.send_json(task_data)
            except:
                dead_connections.append(ws)

        # Clean up dead connections
        for ws in dead_connections:
            WEBSOCKET_CONNECTIONS[task_id].remove(ws)


async def store_upload(file: UploadFile, session_id: str) -> Path:
    session_dir = UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or f"upload-{uuid.uuid4().hex[:8]}"
    # Sanitize filename
    filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    target = session_dir / filename

    content = await file.read()
    target.write_bytes(content)
    return target


def _estimate_total_seconds(agent: ResearchAgent, mode: str, paper_count: int = 1) -> int:
    breakdown = agent.llm.estimate_stage_breakdown(mode, paper_count)
    return sum(item["seconds"] for item in breakdown)


def _estimate_stage_breakdown(agent: ResearchAgent, mode: str, paper_count: int = 1) -> list[dict]:
    return agent.llm.estimate_stage_breakdown(mode, paper_count)


def _finalize_session(session: dict, result: AgentContext, project_name: str, message: str) -> None:
    artifacts = serialize_artifacts(result.run_dir)
    session["run_id"] = result.run_id
    session["project_name"] = project_name
    session["artifacts"] = artifacts
    session["history"].append(
        {
            "run_id": result.run_id,
            "project_name": project_name,
            "timestamp": now_iso(),
            "artifacts": sorted(artifacts.keys()),
        }
    )
    session["messages"].append({"role": "system", "content": message})
    save_session(session)


# ============================================================================
# Task Runners (run in thread pool)
# ============================================================================

def run_single_task(task_id: str, project_name: str, paper_path: Path, session_id: str) -> None:
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    total_eta = _estimate_total_seconds(agent, "single")
    breakdown = _estimate_stage_breakdown(agent, "single")
    asyncio.run(update_task(task_id, status="running", stage="starting", message="开始单论文快速分析", eta_seconds=total_eta, eta_breakdown=breakdown))
    context = AgentContext(project_name=project_name, paper_path=paper_path)

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        remaining = max(int(total_eta * (1 - progress)), 0)
        asyncio.run(update_task(task_id, stage=stage, message=message, progress=round(progress, 3), eta_seconds=remaining, trace=context.trace.copy()))

    context.progress_callback = on_progress

    try:
        result = agent.run_single(context)
        artifacts = serialize_artifacts(result.run_dir)
        asyncio.run(update_task(task_id, status="completed", run_id=result.run_id, trace=result.trace, artifacts=artifacts, progress=1.0, stage="completed", message="单论文快速分析完成", eta_seconds=0))
        _finalize_session(session, result, project_name, f"已完成单论文快速分析：{project_name}")
    except InterruptedError:
        asyncio.run(update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消"))
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        asyncio.run(update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e)))


def run_survey_task(task_id: str, project_name: str, paper_paths: list[Path], session_id: str) -> None:
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    total_eta = _estimate_total_seconds(agent, "survey", len(paper_paths))
    breakdown = _estimate_stage_breakdown(agent, "survey", len(paper_paths))
    asyncio.run(update_task(task_id, status="running", stage="starting", message="开始多论文综述", eta_seconds=total_eta, eta_breakdown=breakdown))
    context = AgentContext(project_name=project_name, paper_paths=paper_paths)

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        remaining = max(int(total_eta * (1 - progress)), 0)
        asyncio.run(update_task(task_id, stage=stage, message=message, progress=round(progress, 3), eta_seconds=remaining, trace=context.trace.copy()))

    context.progress_callback = on_progress

    try:
        result = agent.run_survey(context)
        artifacts = serialize_artifacts(result.run_dir)
        asyncio.run(update_task(task_id, status="completed", run_id=result.run_id, trace=result.trace, artifacts=artifacts, progress=1.0, stage="completed", message="多论文综述完成", eta_seconds=0))
        _finalize_session(session, result, project_name, f"已完成多论文综述：{project_name}")
    except InterruptedError:
        asyncio.run(update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消"))
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        asyncio.run(update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e)))


def run_repo_task(task_id: str, project_name: str, repo_path: Path, session_id: str) -> None:
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    total_eta = _estimate_total_seconds(agent, "repo")
    breakdown = _estimate_stage_breakdown(agent, "repo")
    asyncio.run(update_task(task_id, status="running", stage="starting", message="开始仓库分析", eta_seconds=total_eta, eta_breakdown=breakdown))
    context = AgentContext(project_name=project_name, notes={"repo_path": str(repo_path)})

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        remaining = max(int(total_eta * (1 - progress)), 0)
        asyncio.run(update_task(task_id, stage=stage, message=message, progress=round(progress, 3), eta_seconds=remaining, trace=context.trace.copy()))

    context.progress_callback = on_progress

    try:
        result = agent.inspect_repo(context)
        artifacts = serialize_artifacts(result.run_dir)
        asyncio.run(update_task(task_id, status="completed", run_id=result.run_id, trace=result.trace, artifacts=artifacts, progress=1.0, stage="completed", message="仓库分析完成", eta_seconds=0))
        _finalize_session(session, result, project_name, f"已完成仓库分析：{project_name}")
    except InterruptedError:
        asyncio.run(update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消"))
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        asyncio.run(update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e)))


def run_harness_task(task_id: str, mode: str, project_name: str, session_id: str,
                     paper_path: Path | None = None, paper_paths: list[Path] | None = None,
                     repo_path: Path | None = None, notes: dict | None = None) -> None:
    """Run a workflow via the harness, pausing at confirm nodes."""
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    asyncio.run(update_task(task_id, status="running", stage="starting", message=f"开始 harness 模式：{mode}"))

    # Build context
    if paper_path:
        context = AgentContext(project_name=project_name, paper_path=paper_path)
    elif paper_paths:
        context = AgentContext(project_name=project_name, paper_paths=paper_paths)
    elif repo_path:
        context = AgentContext(project_name=project_name, notes={"repo_path": str(repo_path)})
    elif notes:
        context = AgentContext(project_name=project_name, notes=notes)
    else:
        context = AgentContext(project_name=project_name)

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        asyncio.run(update_task(task_id, stage=stage, message=message, progress=round(progress, 3), trace=context.trace.copy()))

    context.progress_callback = on_progress

    from .workflows import BUILTIN_GRAPHS
    graph_factory = BUILTIN_GRAPHS.get(mode)
    if not graph_factory:
        asyncio.run(update_task(task_id, status="failed", error=f"Unknown mode: {mode}", stage="failed", message=f"Unknown mode: {mode}"))
        return

    graph = graph_factory()
    harness = Harness(graph=graph, registry=agent.registry, context=context, llm=agent.llm)

    try:
        _harness_run_loop(task_id, harness, context, session, project_name, mode)
    except InterruptedError:
        asyncio.run(update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消"))
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        asyncio.run(update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e)))


def _harness_run_loop(task_id: str, harness: Harness, context: AgentContext,
                      session: dict, project_name: str, mode: str) -> None:
    """Inner loop: run harness, block at confirm nodes, resume on user input."""
    call = harness.run

    while True:
        try:
            call()
            # Completed
            artifacts = serialize_artifacts(context.run_dir)
            asyncio.run(update_task(task_id, status="completed", run_id=context.run_id, trace=context.trace,
                        artifacts=artifacts, progress=1.0, stage="completed", message="任务完成", eta_seconds=0))
            _finalize_session(session, context, project_name, f"已完成 {mode} 分析：{project_name}")
            return
        except AwaitConfirmation as ac:
            # Pause: update task status and block thread
            HARNESSES[task_id] = harness
            evt = threading.Event()
            CONFIRM_EVENTS[task_id] = {"event": evt, "choice": "continue"}
            partial_artifacts = serialize_artifacts(context.run_dir)
            asyncio.run(update_task(task_id, status="awaiting_confirmation", stage=ac.node_name,
                        message=ac.message, artifacts=partial_artifacts, trace=context.trace.copy()))

            evt.wait(timeout=600)  # 10 min timeout
            choice = CONFIRM_EVENTS.pop(task_id, {}).get("choice", "continue")
            HARNESSES.pop(task_id, None)

            if choice == "cancel" or task_id in CANCELLED_TASKS:
                asyncio.run(update_task(task_id, status="cancelled", stage="cancelled", message="用户取消了任务"))
                CANCELLED_TASKS.discard(task_id)
                return

            asyncio.run(update_task(task_id, status="running", stage="resuming", message="用户已确认，继续执行"))
            # Next iteration will call resume
            call = lambda: harness.resume(choice)


# ============================================================================
# API Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/session", response_model=SessionResponse)
async def create_session():
    session_id, session = ensure_session()
    save_session(session)
    return session


@app.get("/api/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    _, session = ensure_session(session_id)
    save_session(session)
    return session


@app.get("/api/task/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/diagrams/{run_id}/{filename}")
async def get_diagram(run_id: str, filename: str):
    """Serve diagram files from workspace/runs/{run_id}/diagrams/"""
    diagram_path = Path("workspace/runs") / run_id / "diagrams" / filename
    if not diagram_path.exists():
        raise HTTPException(status_code=404, detail="Diagram not found")
    return FileResponse(diagram_path)


@app.get("/api/history")
async def list_history():
    runs = []
    for path in sorted(RUNS_DIR.glob("*/run_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        runs.append(
            {
                "run_id": payload.get("run_id", path.parent.name),
                "mode": payload.get("mode", "unknown"),
                "project_name": payload.get("project_name", "untitled"),
                "timestamp": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            }
        )
    return {"runs": runs}


@app.post("/api/single")
async def run_single(
    project_name: str = Form("untitled"),
    session_id: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    session_id, session = ensure_session(session_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    paper_path = await store_upload(file, session_id)
    task_id = create_task("single", project_name, session_id)
    session["messages"].append({"role": "user", "content": f"请快速分析论文：{paper_path.name}"})
    save_session(session)
    executor.submit(run_single_task, task_id, project_name, paper_path, session_id)
    return {"task_id": task_id, "session_id": session_id}


@app.post("/api/survey")
async def run_survey(
    project_name: str = Form("untitled"),
    session_id: Optional[str] = Form(None),
    files: list[UploadFile] = File(...)
):
    session_id, session = ensure_session(session_id)

    if not files or len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 papers required for survey")

    paper_paths = []
    for file in files:
        if file.filename:
            paper_paths.append(await store_upload(file, session_id))

    task_id = create_task("survey", project_name, session_id)
    session["messages"].append({"role": "user", "content": f"请对 {len(paper_paths)} 篇论文做综述"})
    save_session(session)
    executor.submit(run_survey_task, task_id, project_name, paper_paths, session_id)
    return {"task_id": task_id, "session_id": session_id}


@app.post("/api/repo")
async def inspect_repo(payload: RepoRequest):
    session_id, session = ensure_session(payload.session_id)

    repo_path = Path(payload.repo_path)
    if not repo_path.exists() or not repo_path.is_dir():
        raise HTTPException(status_code=400, detail=f"repo_path does not exist: {repo_path}")

    task_id = create_task("repo", payload.project_name, session_id)
    session["messages"].append({"role": "user", "content": f"请分析仓库：{repo_path}"})
    save_session(session)
    executor.submit(run_repo_task, task_id, payload.project_name, repo_path, session_id)
    return {"task_id": task_id, "session_id": session_id}


@app.post("/api/research_full")
async def run_research_full(payload: ResearchFullRequest):
    """Run the complete research workflow using harness mode."""
    session_id, session = ensure_session(payload.session_id)

    # Store research parameters in context notes
    notes = {
        "github_query": payload.github_query,
        "language": payload.language,
        "min_stars": payload.min_stars,
    }

    task_id = create_task("research_full", payload.project_name, session_id)
    session["messages"].append({
        "role": "user",
        "content": f"开始完整研究流程：{payload.github_query}"
    })
    save_session(session)

    # Run using harness mode with research_full workflow
    executor.submit(run_harness_task, task_id, "research_full", payload.project_name, session_id, notes=notes)
    return {"task_id": task_id, "session_id": session_id}


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    session_id, session = ensure_session(payload.session_id)
    session["messages"].append({"role": "user", "content": payload.message, "scope": payload.scope})
    agent = ResearchAgent()
    answer = agent.answer_question(payload.message, session.get("artifacts", {}), scope=payload.scope)
    session["messages"].append({"role": "assistant", "content": answer, "scope": payload.scope})
    save_session(session)
    return {"session_id": session_id, "answer": answer, "messages": session["messages"]}


@app.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest):
    """Streaming chat endpoint — returns an SSE stream of text chunks."""
    session_id, session = ensure_session(payload.session_id)
    session["messages"].append({"role": "user", "content": payload.message, "scope": payload.scope})
    save_session(session)

    agent = ResearchAgent()

    async def generate():
        full_answer = ""
        for chunk in agent.answer_question_stream(payload.message, session.get("artifacts", {}), scope=payload.scope):
            full_answer += chunk
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        # Final event with complete answer
        session["messages"].append({"role": "assistant", "content": full_answer, "scope": payload.scope})
        save_session(session)
        yield f"data: {json.dumps({'done': True, 'answer': full_answer}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.post("/api/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Mark a running task as cancelled."""
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] not in ("queued", "running"):
        raise HTTPException(status_code=400, detail=f"Task is already {task['status']}")
    await update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消")
    CANCELLED_TASKS.add(task_id)
    return {"ok": True, "task_id": task_id}


@app.post("/api/task/{task_id}/confirm")
async def confirm_task(task_id: str, payload: ConfirmRequest):
    """User confirms or cancels at an awaiting_confirmation node."""
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "awaiting_confirmation":
        raise HTTPException(status_code=400, detail=f"Task is not awaiting confirmation (status: {task['status']})")

    confirm_info = CONFIRM_EVENTS.get(task_id)
    if confirm_info is None:
        raise HTTPException(status_code=400, detail="No pending confirmation for this task")

    confirm_info["choice"] = payload.choice
    confirm_info["event"].set()  # unblock the background thread
    return {"ok": True, "task_id": task_id, "choice": payload.choice}


@app.post("/api/reset/{session_id}")
async def reset_session(session_id: str):
    session_path = SESSIONS_DIR / f"{session_id}.json"
    upload_path = UPLOADS_DIR / session_id
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    if session_path.exists():
        session_path.unlink()
    if upload_path.exists():
        shutil.rmtree(upload_path)
    return {"ok": True}


@app.websocket("/ws/task/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task progress updates."""
    await websocket.accept()

    # Register this connection
    if task_id not in WEBSOCKET_CONNECTIONS:
        WEBSOCKET_CONNECTIONS[task_id] = []
    WEBSOCKET_CONNECTIONS[task_id].append(websocket)

    try:
        # Send current task state immediately
        task = TASKS.get(task_id)
        if task:
            await websocket.send_json(task)

        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back or handle client messages if needed
            except WebSocketDisconnect:
                break
    finally:
        # Cleanup on disconnect
        if task_id in WEBSOCKET_CONNECTIONS:
            WEBSOCKET_CONNECTIONS[task_id].remove(websocket)
            if not WEBSOCKET_CONNECTIONS[task_id]:
                del WEBSOCKET_CONNECTIONS[task_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
