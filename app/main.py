from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import admin_directories, admin_schedule, auth, home, student, teacher_schedule

app = FastAPI(title="Расписание колледжа", debug=settings.debug)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=60 * 60 * 24 * 7,
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(admin_directories.router)
app.include_router(admin_schedule.router)
app.include_router(student.router)
app.include_router(teacher_schedule.router)
