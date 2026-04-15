from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import shutil
import threading
import uuid

from flask import Flask, Response, jsonify, render_template, request
from werkzeug.utils import secure_filename

from research_agent.agent import ResearchAgent
from research_agent.config import RUNS_DIR, SESSIONS_DIR, UPLOADS_DIR
from research_agent.context import AgentContext
from research_agent.harness import AwaitConfirmation, Harness

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

executor = ThreadPoolExecutor(max_workers=4)
TASKS: dict[str, dict] = {}
SESSIONS: dict[str, dict] = {}
CANCELLED_TASKS: set[str] = set()
HARNESSES: dict[str, Harness] = {}  # task_id -> Harness (for confirm/resume)
CONFIRM_EVENTS: dict[str, dict] = {}  # task_id -> {"event": threading.Event, "choice": str}


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


def update_task(task_id: str, **payload: object) -> None:
    TASKS[task_id].update(payload)
    TASKS[task_id]["updated_at"] = now_iso()


def store_upload(file_storage, session_id: str) -> Path:
    session_dir = UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(file_storage.filename or f"upload-{uuid.uuid4().hex[:8]}")
    target = session_dir / filename
    file_storage.save(str(target))
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


def run_single_task(task_id: str, project_name: str, paper_path: Path, session_id: str) -> None:
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    total_eta = _estimate_total_seconds(agent, "single")
    breakdown = _estimate_stage_breakdown(agent, "single")
    update_task(task_id, status="running", stage="starting", message="开始单论文快速分析", eta_seconds=total_eta, eta_breakdown=breakdown)
    context = AgentContext(project_name=project_name, paper_path=paper_path)

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        remaining = max(int(total_eta * (1 - progress)), 0)
        update_task(task_id, stage=stage, message=message, progress=round(progress, 3), eta_seconds=remaining, trace=context.trace.copy())

    context.progress_callback = on_progress

    try:
        result = agent.run_single(context)
        artifacts = serialize_artifacts(result.run_dir)
        update_task(task_id, status="completed", run_id=result.run_id, trace=result.trace, artifacts=artifacts, progress=1.0, stage="completed", message="单论文快速分析完成", eta_seconds=0)
        _finalize_session(session, result, project_name, f"已完成单论文快速分析：{project_name}")
    except InterruptedError:
        update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消")
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e))


def run_survey_task(task_id: str, project_name: str, paper_paths: list[Path], session_id: str) -> None:
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    total_eta = _estimate_total_seconds(agent, "survey", len(paper_paths))
    breakdown = _estimate_stage_breakdown(agent, "survey", len(paper_paths))
    update_task(task_id, status="running", stage="starting", message="开始多论文综述", eta_seconds=total_eta, eta_breakdown=breakdown)
    context = AgentContext(project_name=project_name, paper_paths=paper_paths)

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        remaining = max(int(total_eta * (1 - progress)), 0)
        update_task(task_id, stage=stage, message=message, progress=round(progress, 3), eta_seconds=remaining, trace=context.trace.copy())

    context.progress_callback = on_progress

    try:
        result = agent.run_survey(context)
        artifacts = serialize_artifacts(result.run_dir)
        update_task(task_id, status="completed", run_id=result.run_id, trace=result.trace, artifacts=artifacts, progress=1.0, stage="completed", message="多论文综述完成", eta_seconds=0)
        _finalize_session(session, result, project_name, f"已完成多论文综述：{project_name}")
    except InterruptedError:
        update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消")
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e))


def run_repo_task(task_id: str, project_name: str, repo_path: Path, session_id: str) -> None:
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    total_eta = _estimate_total_seconds(agent, "repo")
    breakdown = _estimate_stage_breakdown(agent, "repo")
    update_task(task_id, status="running", stage="starting", message="开始仓库分析", eta_seconds=total_eta, eta_breakdown=breakdown)
    context = AgentContext(project_name=project_name, notes={"repo_path": str(repo_path)})

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        remaining = max(int(total_eta * (1 - progress)), 0)
        update_task(task_id, stage=stage, message=message, progress=round(progress, 3), eta_seconds=remaining, trace=context.trace.copy())

    context.progress_callback = on_progress

    try:
        result = agent.inspect_repo(context)
        artifacts = serialize_artifacts(result.run_dir)
        update_task(task_id, status="completed", run_id=result.run_id, trace=result.trace, artifacts=artifacts, progress=1.0, stage="completed", message="仓库分析完成", eta_seconds=0)
        _finalize_session(session, result, project_name, f"已完成仓库分析：{project_name}")
    except InterruptedError:
        update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消")
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session", methods=["POST"])
def create_session():
    session_id, session = ensure_session()
    save_session(session)
    return jsonify(session)


@app.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id: str):
    _, session = ensure_session(session_id)
    save_session(session)
    return jsonify(session)


@app.route("/api/task/<task_id>", methods=["GET"])
def get_task(task_id: str):
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@app.route("/api/history", methods=["GET"])
def list_history():
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
    return jsonify({"runs": runs})


@app.route("/api/single", methods=["POST"])
def run_single():
    project_name = request.form.get("project_name", "untitled")
    session_id = request.form.get("session_id")
    session_id, session = ensure_session(session_id)

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    paper_path = store_upload(file, session_id)
    task_id = create_task("single", project_name, session_id)
    session["messages"].append({"role": "user", "content": f"请快速分析论文：{paper_path.name}"})
    save_session(session)
    executor.submit(run_single_task, task_id, project_name, paper_path, session_id)
    return jsonify({"task_id": task_id, "session_id": session_id})


@app.route("/api/survey", methods=["POST"])
def run_survey():
    project_name = request.form.get("project_name", "untitled")
    session_id = request.form.get("session_id")
    session_id, session = ensure_session(session_id)

    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    if not files or len(files) < 2:
        return jsonify({"error": "At least 2 papers required for survey"}), 400

    paper_paths = [store_upload(file, session_id) for file in files if file.filename]
    task_id = create_task("survey", project_name, session_id)
    session["messages"].append({"role": "user", "content": f"请对 {len(paper_paths)} 篇论文做综述"})
    save_session(session)
    executor.submit(run_survey_task, task_id, project_name, paper_paths, session_id)
    return jsonify({"task_id": task_id, "session_id": session_id})


@app.route("/api/repo", methods=["POST"])
def inspect_repo():
    payload = request.get_json(silent=True) or {}
    project_name = (payload.get("project_name") or "repo-analysis").strip()
    repo_path_raw = (payload.get("repo_path") or "").strip()
    session_id = payload.get("session_id")
    session_id, session = ensure_session(session_id)

    if not repo_path_raw:
        return jsonify({"error": "repo_path is required"}), 400

    repo_path = Path(repo_path_raw)
    if not repo_path.exists() or not repo_path.is_dir():
        return jsonify({"error": f"repo_path does not exist: {repo_path}"}), 400

    task_id = create_task("repo", project_name, session_id)
    session["messages"].append({"role": "user", "content": f"请分析仓库：{repo_path}"})
    save_session(session)
    executor.submit(run_repo_task, task_id, project_name, repo_path, session_id)
    return jsonify({"task_id": task_id, "session_id": session_id})


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    question = (payload.get("message") or "").strip()
    scope = payload.get("scope") or []
    if not question:
        return jsonify({"error": "Message is required"}), 400

    session_id, session = ensure_session(session_id)
    session["messages"].append({"role": "user", "content": question, "scope": scope})
    agent = ResearchAgent()
    answer = agent.answer_question(question, session.get("artifacts", {}), scope=scope)
    session["messages"].append({"role": "assistant", "content": answer, "scope": scope})
    save_session(session)
    return jsonify({"session_id": session_id, "answer": answer, "messages": session["messages"]})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming chat endpoint — returns an SSE stream of text chunks."""
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    question = (payload.get("message") or "").strip()
    scope = payload.get("scope") or []
    if not question:
        return jsonify({"error": "Message is required"}), 400

    session_id, session = ensure_session(session_id)
    session["messages"].append({"role": "user", "content": question, "scope": scope})
    save_session(session)

    agent = ResearchAgent()

    def generate():
        full_answer = ""
        for chunk in agent.answer_question_stream(question, session.get("artifacts", {}), scope=scope):
            full_answer += chunk
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        # Final event with complete answer
        session["messages"].append({"role": "assistant", "content": full_answer, "scope": scope})
        save_session(session)
        yield f"data: {json.dumps({'done': True, 'answer': full_answer}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/task/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id: str):
    """Mark a running task as cancelled.

    Skills check ``context.notes["_cancelled"]`` before each step
    via cooperative cancellation.
    """
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    if task["status"] not in ("queued", "running"):
        return jsonify({"error": f"Task is already {task['status']}"}), 400
    update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消")
    # Signal to the running context (if it exists) via a shared flag
    CANCELLED_TASKS.add(task_id)
    return jsonify({"ok": True, "task_id": task_id})


# ------------------------------------------------------------------
# Harness-mode task runner + confirm API
# ------------------------------------------------------------------

def run_harness_task(task_id: str, mode: str, project_name: str, session_id: str,
                     paper_path: Path | None = None, paper_paths: list[Path] | None = None,
                     repo_path: Path | None = None) -> None:
    """Run a workflow via the harness, pausing at confirm nodes."""
    _, session = ensure_session(session_id)
    agent = ResearchAgent()
    update_task(task_id, status="running", stage="starting", message=f"开始 harness 模式：{mode}")

    # Build context
    if paper_path:
        context = AgentContext(project_name=project_name, paper_path=paper_path)
    elif paper_paths:
        context = AgentContext(project_name=project_name, paper_paths=paper_paths)
    elif repo_path:
        context = AgentContext(project_name=project_name, notes={"repo_path": str(repo_path)})
    else:
        context = AgentContext(project_name=project_name)

    def on_progress(stage: str, message: str, progress: float) -> None:
        if task_id in CANCELLED_TASKS:
            raise InterruptedError("任务已被用户取消")
        update_task(task_id, stage=stage, message=message, progress=round(progress, 3), trace=context.trace.copy())

    context.progress_callback = on_progress

    from .workflows import BUILTIN_GRAPHS
    graph_factory = BUILTIN_GRAPHS.get(mode)
    if not graph_factory:
        update_task(task_id, status="failed", error=f"Unknown mode: {mode}", stage="failed", message=f"Unknown mode: {mode}")
        return

    graph = graph_factory()
    harness = Harness(graph=graph, registry=agent.registry, context=context, llm=agent.llm)

    try:
        _harness_run_loop(task_id, harness, context, session, project_name, mode)
    except InterruptedError:
        update_task(task_id, status="cancelled", stage="cancelled", message="任务已被用户取消")
        CANCELLED_TASKS.discard(task_id)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e), stage="failed", message=str(e))


def _harness_run_loop(task_id: str, harness: Harness, context: AgentContext,
                      session: dict, project_name: str, mode: str) -> None:
    """Inner loop: run harness, block at confirm nodes, resume on user input."""
    # We use a simple pattern: call run/resume, catch AwaitConfirmation, block, repeat.
    call = harness.run  # first call is run()

    while True:
        try:
            call()
            # Completed
            artifacts = serialize_artifacts(context.run_dir)
            update_task(task_id, status="completed", run_id=context.run_id, trace=context.trace,
                        artifacts=artifacts, progress=1.0, stage="completed", message="任务完成", eta_seconds=0)
            _finalize_session(session, context, project_name, f"已完成 {mode} 分析：{project_name}")
            return
        except AwaitConfirmation as ac:
            # Pause: update task status and block thread
            HARNESSES[task_id] = harness
            evt = threading.Event()
            CONFIRM_EVENTS[task_id] = {"event": evt, "choice": "continue"}
            partial_artifacts = serialize_artifacts(context.run_dir)
            update_task(task_id, status="awaiting_confirmation", stage=ac.node_name,
                        message=ac.message, artifacts=partial_artifacts, trace=context.trace.copy())

            evt.wait(timeout=600)  # 10 min timeout
            choice = CONFIRM_EVENTS.pop(task_id, {}).get("choice", "continue")
            HARNESSES.pop(task_id, None)

            if choice == "cancel" or task_id in CANCELLED_TASKS:
                update_task(task_id, status="cancelled", stage="cancelled", message="用户取消了任务")
                CANCELLED_TASKS.discard(task_id)
                return

            update_task(task_id, status="running", stage="resuming", message="用户已确认，继续执行")
            # Next iteration will call resume
            call = lambda: harness.resume(choice)


@app.route("/api/task/<task_id>/confirm", methods=["POST"])
def confirm_task(task_id: str):
    """User confirms or cancels at an awaiting_confirmation node."""
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    if task["status"] != "awaiting_confirmation":
        return jsonify({"error": f"Task is not awaiting confirmation (status: {task['status']})"}), 400

    payload = request.get_json(silent=True) or {}
    choice = payload.get("choice", "continue")  # "continue" or "cancel"

    confirm_info = CONFIRM_EVENTS.get(task_id)
    if confirm_info is None:
        return jsonify({"error": "No pending confirmation for this task"}), 400

    confirm_info["choice"] = choice
    confirm_info["event"].set()  # unblock the background thread
    return jsonify({"ok": True, "task_id": task_id, "choice": choice})


@app.route("/api/reset/<session_id>", methods=["POST"])
def reset_session(session_id: str):
    session_path = SESSIONS_DIR / f"{session_id}.json"
    upload_path = UPLOADS_DIR / session_id
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    if session_path.exists():
        session_path.unlink()
    if upload_path.exists():
        shutil.rmtree(upload_path)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
