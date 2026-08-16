# Water Treatment Nodes

## Scripts to Run
Note: below shows how to run from **project directory**.

### Virtual environment
    .\.venv\Scripts\Activate.ps1

### Run web app
    streamlit run .\greenwall_web_ui\main_app.py

This node runs the user webpage. The web app for water treatment is in the sidebar **sensor calibration app**. It helps to visualise the uncalibrated sensor voltages at real-time.  

### Run udp gateway
    python .\water_treatment\post_processing\udp_server_gateway.py

This node runs the UDP gateway. It receives from Arduino board (which the sensors are connected to), and forward the messages to the data processor and the user webpage at different ports. Check configurations at *.\water_treatment\post_processing\config\general_config.py*. 

### Run data processor
    python .\water_treatment\post_processing\raw_data_processor.py

This node processes raw readings from the sensors into calibrated, meaningful data. It then writes to InfluxDB. Check configurations at *.\water_treatment\post_processing\config\general_config.py*. 

### Run dummy sensor node for testing
    python .\greenwall_web_ui\test_udp_sender.py

This node sends messages with random dummy readings. 