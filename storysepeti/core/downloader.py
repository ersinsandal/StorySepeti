"""
Central Thread-Safe Download Engine for StorySepeti.
Coordinates background queue execution, progress streaming, and lifecycle events.
"""

import os
import uuid
import queue
import datetime
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Callable, Literal

from storysepeti.utils.url_parser import URLType, parse_url
from storysepeti.utils.notifier import notify_desktop
from storysepeti.utils.file_namer import sanitize_filename
from storysepeti.config.settings import AppSettings
from storysepeti.cookies.manager import CookieManager
from .highlight import download_highlight
from .story import download_active_stories

TaskStatus = Literal["pending", "running", "completed", "failed", "cancelled"]

@dataclass
class DownloadTask:
    task_id: str
    title: str
    url: str
    task_type: URLType
    username: str
    output_dir: Path
    status: TaskStatus = "pending"
    progress: float = 0.0
    speed_info: str = ""
    error_message: Optional[str] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class EngineMessage:
    msg_type: Literal["task_added", "progress", "log", "status_change", "finished"]
    task_id: str
    data: Dict[str, Any] = field(default_factory=dict)

class DownloadEngine:
    def __init__(self, cookie_manager: CookieManager, settings: AppSettings):
        self.cookie_manager = cookie_manager
        self.settings = settings
        self.tasks: Dict[str, DownloadTask] = {}
        self.message_queue: queue.Queue[EngineMessage] = queue.Queue()
        self._cancelled_tasks: set[str] = set()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="StorySepetiDownloader")
        self._is_active = True

    def create_task(
        self,
        url_or_user: str,
        task_type: Optional[URLType] = None,
        custom_output_dir: Optional[Path] = None,
        title_override: Optional[str] = None
    ) -> DownloadTask:
        parsed = parse_url(url_or_user)
        if parsed.url_type in (URLType.SINGLE_STORY, URLType.SINGLE_HIGHLIGHT):
            resolved_type = parsed.url_type
        else:
            resolved_type = task_type or parsed.url_type
            if resolved_type == URLType.UNKNOWN:
                resolved_type = URLType.USER_STORIES

        username = parsed.username or "instagram_user"
        task_id = str(uuid.uuid4())[:8]

        # Determine output directory
        base_dir = custom_output_dir or Path(self.settings.output_dir)
        u_clean = sanitize_filename(username, 30)
        
        if resolved_type in (URLType.SINGLE_HIGHLIGHT, URLType.PROFILE_HIGHLIGHTS):
            final_out = base_dir / u_clean / "highlights"
        elif resolved_type == URLType.SINGLE_STORY:
            final_out = base_dir / u_clean / "stories" / "single"
        else:
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            final_out = base_dir / u_clean / "stories" / stamp

        final_out.mkdir(parents=True, exist_ok=True)

        title = title_override or f"{resolved_type.value} - @{u_clean}"

        task = DownloadTask(
            task_id=task_id,
            title=title,
            url=parsed.canonical_url or url_or_user,
            task_type=resolved_type,
            username=username,
            output_dir=final_out,
            status="pending"
        )

        self.tasks[task_id] = task
        self.message_queue.put(EngineMessage("task_added", task_id, {"task": task}))
        self._executor.submit(self._run_task, task)
        return task

    def cancel_task(self, task_id: str) -> None:
        if task_id in self.tasks:
            self._cancelled_tasks.add(task_id)
            task = self.tasks[task_id]
            if task.status == "pending":
                task.status = "cancelled"
                self.message_queue.put(EngineMessage("status_change", task_id, {"status": "cancelled"}))

    def _run_task(self, task: DownloadTask) -> None:
        if task.task_id in self._cancelled_tasks:
            task.status = "cancelled"
            self.message_queue.put(EngineMessage("status_change", task.task_id, {"status": "cancelled"}))
            return

        task.status = "running"
        self.message_queue.put(EngineMessage("status_change", task.task_id, {"status": "running"}))
        self.message_queue.put(EngineMessage("log", task.task_id, {
            "level": "info",
            "message": f"İndirme görevi başladı: {task.title}"
        }))

        def cancel_check() -> bool:
            return task.task_id in self._cancelled_tasks

        def log_cb(level: str, msg: str) -> None:
            self.message_queue.put(EngineMessage("log", task.task_id, {
                "level": level,
                "message": msg
            }))

        def progress_cb(pct: float, speed_text: str) -> None:
            task.progress = pct
            task.speed_info = speed_text
            self.message_queue.put(EngineMessage("progress", task.task_id, {
                "progress": pct,
                "speed": speed_text
            }))

        try:
            if not self.cookie_manager.is_authenticated:
                raise RuntimeError("Instagram oturumu bulunamadı. Lütfen Ayarlar veya Giriş Sihirbazından oturum açın.")

            with self.cookie_manager.temp_netscape_file() as cookie_path:
                success = False

                if task.task_type in (URLType.SINGLE_HIGHLIGHT, URLType.PROFILE_HIGHLIGHTS):
                    success = download_highlight(
                        url=task.url,
                        output_dir=task.output_dir,
                        cookie_path=cookie_path,
                        log_cb=log_cb,
                        progress_cb=progress_cb,
                        cancel_check=cancel_check,
                        quality_mode=self.settings.quality_mode,
                        concurrent_fragments=self.settings.concurrent_fragments
                    )
                else:
                    is_single = (task.task_type == URLType.SINGLE_STORY)
                    success = download_active_stories(
                        url=task.url,
                        output_dir=task.output_dir,
                        cookie_path=cookie_path,
                        is_single=is_single,
                        username=task.username,
                        log_cb=log_cb,
                        progress_cb=progress_cb,
                        cancel_check=cancel_check,
                        quality_mode=self.settings.quality_mode,
                        concurrent_fragments=self.settings.concurrent_fragments,
                        cookie_dict=self.cookie_manager.cookie_dict
                    )

            if cancel_check():
                task.status = "cancelled"
                self.message_queue.put(EngineMessage("status_change", task.task_id, {"status": "cancelled"}))
            elif success:
                task.status = "completed"
                task.progress = 100.0
                self.message_queue.put(EngineMessage("status_change", task.task_id, {"status": "completed"}))
                
                # Notify
                if self.settings.notify_on_done:
                    notify_desktop("StorySepeti", f"İndirme tamamlandı: {task.title}")
                
                # Open in Explorer if configured
                if self.settings.open_explorer_on_done and task.output_dir.exists():
                    try:
                        subprocess.Popen(["explorer", str(task.output_dir)])
                    except Exception:
                        pass
            else:
                task.status = "failed"
                task.error_message = "İşlem sırasında hata oluştu."
                self.message_queue.put(EngineMessage("status_change", task.task_id, {
                    "status": "failed",
                    "error": task.error_message
                }))

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            log_cb("error", f"Görev hatası: {e}")
            self.message_queue.put(EngineMessage("status_change", task.task_id, {
                "status": "failed",
                "error": str(e)
            }))
        finally:
            self.message_queue.put(EngineMessage("finished", task.task_id, {}))

    def shutdown(self) -> None:
        self._is_active = False
        self._executor.shutdown(wait=False, cancel_futures=True)
