import time
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

import pymongo
import logging
from jaeger_client import Config
from flask_pymongo import PyMongo
from prometheus_flask_exporter import PrometheusMetrics
from opentracing.ext import tags
# from opentracing.propagation import Format
import opentracing

app = Flask(__name__)
CORS(app)   # Enable CORS for all routes
metrics = PrometheusMetrics(app)

def init_tracer(service):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
            "reporter_batch_size": 1,  # Send traces immediately
        },
        service_name=service,
    )
    # this call also sets opentracing.tracer
    return config.initialize_tracer()

tracer = init_tracer('backend-service')
opentracing.tracer = tracer  # Set the global tracer, best practice

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)


@app.route("/")
def homepage():
    with tracer.start_span("homepage") as span:
        span.set_tag(tags.HTTP_METHOD, "GET")
        span.set_tag(tags.HTTP_URL, "/")
        span.log_kv({"event": "homepage accessed"})
        span.set_tag(tags.HTTP_STATUS_CODE, 200)
        return "Hello World"


@app.route("/api")
def my_api():
    with tracer.start_span("my_api") as span:
        span.set_tag(tags.HTTP_METHOD, "GET")
        span.set_tag(tags.HTTP_URL, "/api")
        span.log_kv({"event": "api accessed"})
        answer = "something"
        span.set_tag(tags.HTTP_STATUS_CODE, 200)
        return jsonify(response=answer)


@app.route("/star", methods=["POST"])
def add_star():
    with tracer.start_span("add_star") as span:
        span.set_tag(tags.HTTP_METHOD, "POST")
        span.set_tag(tags.HTTP_URL, "/star")
        span.log_kv({"event": "add_star accessed"})

        # Step 1: Extract data
        with tracer.start_span("extract_data", child_of=span) as child_span:
            child_span.log_kv({"event": "extracting data from request"})
            # Extract data from the request
            name = request.json["name"]
            distance = request.json["distance"]
        
        # Step 2: Validate data
        with tracer.start_span("validate_data", child_of=span) as validate_span:
            validate_span.log_kv({"event": "validating data"})
            # Validate the data
            if not name or not distance:
                validate_span.log_kv({"error": "Invalid input"})
                validate_span.set_tag(tags.HTTP_STATUS_CODE, 400)
                validate_span.finish()
                return jsonify({"error": "Invalid input"}), 400
            if not isinstance(distance, (int, float)):
                validate_span.log_kv({"error": "Distance must be a number"})
                validate_span.set_tag(tags.HTTP_STATUS_CODE, 400)
                validate_span.finish()
                return jsonify({"error": "Distance must be a number"}), 400
            if distance < 0:
                validate_span.log_kv({"error": "Distance must be a positive number"})
                validate_span.set_tag(tags.HTTP_STATUS_CODE, 400)
                validate_span.finish() 
                return jsonify({"error": "Distance must be a positive number"}), 400
            validate_span.log_kv({"event": "data validated"})
        
        # Step 3: Insert data
        with tracer.start_span("insert_data", child_of=span) as insert_span:
            # star = mongo.db.stars
            # star_id = star.insert({"name": name, "distance": distance})
            # new_star = star.find_one({"_id": star_id})    
            # output = {"name": new_star["name"], "distance": new_star["distance"]}

            # Simulate database interaction 
            insert_span.log_kv({"event": "simulate inserting data into database"})
            span.log_kv({"name": name, "distance": distance})
            time.sleep(0.0001) # Simulate a delay
            insert_span.set_tag(tags.HTTP_STATUS_CODE, 200)

        # Set final status code
        span.set_tag(tags.HTTP_STATUS_CODE, 200)  # Set final status code
        # return jsonify({"result": output})
        return jsonify({"result": f"{name} {distance}"})


if __name__ == "__main__":
    app.run()
