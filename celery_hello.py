from flask import Flask
from celery import Celery
from flask import request
import os
import time
## from task import app as celery_app
from celery.result import AsyncResult

app = Flask(__name__)
print(app.name)

# Configure Celery with the Flask app and the message broker
celery = Celery(app.name, backend='redis://localhost:6379/0', broker='redis://localhost:6379/0')



celery.conf.update(app.config)
# Define a Celery task
from celery import current_app
# `after_task_publish` is available in celery 3.1+
# for older versions use the deprecated `task_sent` signal
from celery.signals import after_task_publish

# when using celery versions older than 4.0, use body instead of headers

@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
 
    celery.backend.store_result(headers['id'], None, "SENT")

@celery.task
def add(x, y):
    time.sleep(30)
    return x + y


    
@app.route('/add/<int:x>/<int:y>')
def add_route(x, y):
    # Schedule the add task for execution
    result = add.delay(x, y)
    return result.id
    #return f'Task scheduled with ID: {result.id}'

# Decorator Which will do that ?

@app.route("/results",methods=["GET"])
def results():
    id = request.args.get("id","")
    result = AsyncResult(id,backend=celery.backend)
    if result.state == "SUCCESS":
        val = str(result.get())
        ## Processing
        ## Delete
        result.forget()
        return val
    # Only Unknown tasks will be pending. 
    elif result.state == "PENDING":
        return "Not Found"
    else:
        return "In Process"

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True, host="0.0.0.0")