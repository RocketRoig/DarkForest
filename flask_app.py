from flask import Flask, render_template
import threading
import logging

app = Flask(__name__)

logging.getLogger('werkzeug').setLevel(logging.ERROR)
# Shared simulation data
simulation_data = {
    "global_time": 0,
    "star_systems": [],
    "communications_list": []
}

@app.route("/")
def index():
    
    return render_template("index.html", 
                                  global_time=simulation_data["global_time"], 
                                  star_systems=simulation_data["star_systems"], 
                                  communications_list=simulation_data["communications_list"])
