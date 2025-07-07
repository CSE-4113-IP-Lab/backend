from fastapi import APIRouter
from routers import post, schedule, admission_timeline, program, course, coursework, coursework_submission, mark

router = APIRouter(
    prefix="/api/v1",
)  

# Include the routers for different functionalities
router.include_router(post.router)
router.include_router(schedule.router)
router.include_router(admission_timeline.router)
router.include_router(program.router)
router.include_router(course.router)
router.include_router(coursework.router)
router.include_router(coursework_submission.router)
router.include_router(mark.router)
