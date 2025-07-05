from fastapi import APIRouter
from routers import admission_timeline, post, schedule

router = APIRouter(
    prefix="/api/v1",
)  

# Include the routers for different functionalities
router.include_router(post.router)
router.include_router(schedule.router)
router.include_router(admission_timeline.router)
