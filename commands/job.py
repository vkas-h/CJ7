from core.scheduler import scheduler
from core.command import Command


def show_jobs():
    return scheduler.show_jobs()


def cancel(job_id):
    return scheduler.cancel_job(job_id)


COMMANDS = [

    Command(
        name="jobs",
        function=show_jobs,
        description="Show all currently scheduled jobs.",
        toolset="productivity",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),

    Command(
        name="cancel",
        function=cancel,
        description="Cancel a scheduled job using its job ID.",
        toolset="productivity",
        permission="confirm",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "integer",
                    "description": "ID of the scheduled job to cancel."
                }
            },
            "required": ["job_id"]
        }
    )

]