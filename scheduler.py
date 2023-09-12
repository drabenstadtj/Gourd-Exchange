import schedule
import time
from datetime import datetime, timedelta
import value_updater


def your_function():
    # Your code here
    value_updater.update_values()
    print("Running your_function()")

# Define a job to run your_function() every minute on weekdays between 9:30 AM and 4:00 PM


def job():
    now = datetime.today() + timedelta(hours=-6, days=1)
    print(now)
    if now.weekday() < 5 and now >= datetime.strptime("09:30:00", "%H:%M:%S").time() and now <= datetime.strptime("16:00:00", "%H:%M:%S").time():
        your_function()


# Schedule the job to run every minute
schedule.every(1).minutes.do(your_function)


def start():
    # Run the scheduling loop
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
