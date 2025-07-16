from fastapi import APIRouter

from routers import (post, schedule, admission_timeline, program, 
                     course, coursework, coursework_submission, mark, 
                     auth, token, user, student, faculty,meeting,
                     participate,payment,research,resource, logs, room, class_schedule, exam_schedule, agent);

router = APIRouter(
    prefix="/api/v1",
)  

# Include the routers for different functionalities
router.include_router(token.router)
router.include_router(agent.router)
router.include_router(auth.router)
router.include_router(user.router)
router.include_router(student.router)
router.include_router(faculty.router)
router.include_router(logs.router)
router.include_router(post.router)
router.include_router(schedule.router)
router.include_router(admission_timeline.router)
router.include_router(program.router)
router.include_router(course.router)
router.include_router(coursework.router)
router.include_router(coursework_submission.router)
router.include_router(mark.router)
router.include_router(meeting.router)
router.include_router(participate.router)
router.include_router(payment.router)
router.include_router(research.router)
router.include_router(resource.router)
router.include_router(room.router)
router.include_router(class_schedule.router)
router.include_router(exam_schedule.router)


