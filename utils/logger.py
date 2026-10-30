import logging
import datetime as dt

history_file = "data/history.txt"

def log_command(command) :
    current_time = dt.datetime.now().strftime("%d-%m-%y %I:%M:%S %p")
    with open(history_file , "a") as file :
        file.write(f"[{current_time}] {command} \n")


logger = logging.getLogger("CJ7")


logger.setLevel(logging.INFO)


file_handler=logging.FileHandler("data/cj7.log")

logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

formatter = logging.Formatter(
   " %(asctime)s | %(levelname)s | %(message)s "
)

file_handler.setFormatter(formatter)

logger.info("CJ7 started")
