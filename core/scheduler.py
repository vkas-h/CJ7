import threading
import time
import datetime as dt
from dataclasses import dataclass
import json
JOBS_FILE ="data/jobs.json"






ACTION_MAP={}

def register_action(action_name, function):
    ACTION_MAP[action_name] = function



@dataclass
class Job:
    id:int
    run_at: dt.datetime
    action: callable
    action_name: str
    args: list[str]





class Scheduler:

    def __init__(self):
        # print(id(self))


        self.next_job_id=1

        #list of all sheduled jobs 
        self.jobs=[]

    def load_jobs(self):
        try :

            with open (JOBS_FILE , "r") as file :
                jobs_data = json.load(file)


        except (FileNotFoundError, json.JSONDecodeError):

            jobs_data = []


        for job in jobs_data:

            loaded_job= Job(

                id=job["id"],
                run_at=dt.datetime.fromisoformat(job["run_at"]),
                action=ACTION_MAP.get(job["action_name"], None),                    # We'll fix this next
                action_name=job["action_name"],
                args=job["args"]
            )


            self.jobs.append(loaded_job)

            if loaded_job.id >= self.next_job_id:
                self.next_job_id = loaded_job.id + 1




    def save_json(self):

        jobs_data = []

        for job in self.jobs:

            jobs_data.append({

                "id": job.id,

                "run_at": job.run_at.isoformat(),

                "action_name": job.action_name,

                "args": job.args

            })

        with open(JOBS_FILE, "w") as file:

            json.dump(
                jobs_data,
                file,
                indent=4
            )
        

    def add_job(self , delay , action , action_name, args=None):

        if args is None:
            args=[]


        job = Job(
            id=self.next_job_id,
            run_at=dt.datetime.now() + dt.timedelta(seconds=delay),
            action=action,
            action_name=action_name,
            args=args
        )

        self.jobs.append(job)
        self.next_job_id += 1
        self.save_json()
        print(f"[Scheduler] Job added . Runs in {delay} seconds.")

#-------------------------------------------------------------------------------


    def show_jobs(self):
        if not self.jobs:
            return "No jobs scheduled."

        lines = ["Scheduled Jobs", "-" * 55]
        now = dt.datetime.now()

        for job in self.jobs:
            remaining = job.run_at - now
            lines.append(
                f"{job.id} | {remaining} | "
                f"{job.action_name} | {' '.join(job.args)}"
            )

        return "\n".join(lines)


    def cancel_job(self, job_id):
        try:
            job_id = int(job_id)
        except (TypeError, ValueError):
            return "Job ID must be a number."

        for job in self.jobs:
            if job.id == job_id:
                self.jobs.remove(job)
                self.save_json()
                return f"Cancelled job #{job.id}"

        return f"No job found with ID {job_id}."







    def tick(self):

        now = dt.datetime.now()

        for job in self.jobs[:]:

            if now >= job.run_at:

                if job.action is not None:

                    job.action(job.args)

                self.jobs.remove(job)

                self.save_json()






    def start(self):
        thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        thread.start()





    def run (self):

        # print("[Scheduler] Thread started") ################
        while True:
            self.tick()
            time.sleep(1)

    def initialize(self):
        self.load_jobs()
        self.start()

scheduler = Scheduler()