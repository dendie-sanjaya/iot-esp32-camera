
# Smart Human Detection & IoT Integration & AI : Microcontroller ESP32  & ESP8266 

Empowering environments with intelligent human detection, this system fuses AI, IoT, WiFi connectivity, ESP8266, ESP8266, Camera  and real-time sensor data (including motion sensors) into a unified solution. Leveraging ESP32 & ESP8266 microcontrollers, advanced machine learning, and seamless connectivity, it delivers a robust platform for smart monitoring and automation across multiple disciplines. The AI mode is a combination of several techniques, designed to optimize human prediction and adapt to diverse scenarios.

Table of Contents
- [Smart Human Detection \& IoT Integration \& AI : Microcontroller ESP32  \& ESP8266](#smart-human-detection--iot-integration--ai--microcontroller-esp32---esp8266)
  - [Introduction](#introduction)
  - [System Architecture](#system-architecture)
    - [Logic Flow System](#logic-flow-system)
    - [Pin Wired Microcontroller \& Lamp](#pin-wired-microcontroller--lamp)
    - [Pin Wired Microcontroller \& Motion Sensor](#pin-wired-microcontroller--motion-sensor)
  - [Site Installation](#site-installation)
  - [Folder Structure](#folder-structure)
  - [AI Model \& Application Backend](#ai-model--application-backend)
    - [API Endpoints](#api-endpoints)
    - [How to Run](#how-to-run)
  - [Mictorcontroller \& Connectivity](#mictorcontroller--connectivity)
  - [Device Microcontroller \& Lab Simulation](#device-microcontroller--lab-simulation)
  - [MQTT Communication \& Integration](#mqtt-communication--integration)
  - [Frontend Web Dashboard](#frontend-web-dashboard)
    - [Features](#features)
    - [How to Use](#how-to-use)
    - [Dashboard](#dashboard)
  - [Video Demostration](#video-demostration)


## Introduction
This project is a multidisciplinary IoT system that combines electronics, computation, connectivity, frequency management, sensors, microcontroller-based camera, artificial intelligence, database applications, and web server technology. The goal is to create a smart system capable of human prediction using AI, with real-time data acquisition and processing from various sensors and devices.

## System Architecture
The overall architecture is designed to integrate multiple hardware and software components seamlessly. Refer to the architecture diagram in !['design/architecture.png'](design/architecture.png) for a visual overview. The system features:

- ESP32-based camera and sensors for image and data acquisition
- ESP8266 microcontroller for additional connectivity and sensor integration
- Motion sensors for real-time activity detection
- AI prediction model for human detection and analytics
- Database for history detection data storage and retrieval
- Web server & apps  for user interaction and remote monitoring (Dashboard Monitoring)
- Connectivity Using Wifi
- Protokol modules for data transmission (HTTP & MQTT )

Additional pin wiring diagrams and other design assets are available in the 'design/' folder to assist with hardware setup and integration.

### Logic Flow System 

!['ss'](design/logic-flow.png)


### Pin Wired Microcontroller & Lamp

!['ss'](design/pin-wired-lamp.png)


### Pin Wired Microcontroller & Motion Sensor

!['ss'](design/pin-wired-sensor.png)


## Site Installation

To help you get started with the system installation and setup, refer to the following screenshot for a visual guide:

- Site installation steps: !['design/site-instalasi.png'](design/site-instalasi.png)

This image provides a step-by-step overview of the installation process, making it easier to follow and replicate the setup on your own environment.


## Folder Structure
| Folder                        | Description                                                                 |
|-|--|
| ai/                         | Contains AI model code, database setup, and listener scripts                 |
| design/                     | Architecture diagram, pin wiring diagrams, and other design assets           |
| driver/                     | Windows driver for hardware interface                                       |
| frontend/                   | Web interface for user interaction                                          |
| microcontroller-camera/     | ESP32 camera firmware and code                                              |
| microcontroller-lamp/       | Lamp control firmware                                                       |
| microcontroller-motion-sensor/ | Motion sensor firmware                                                  |
| ss/                         | Screenshots and visual documentation                                        |

## AI Model & Application Backend
The AI module, located in the 'ai/' folder, is responsible for human prediction using advanced machine learning techniques. The application integrates with the database and listens for sensor data, enabling real-time analytics and decision-making.

### API Endpoints
The backend application ('app.py') exposes several API endpoints for interacting with the system, retrieving detection results, and controlling devices. These APIs allow integration with web dashboards, mobile apps, and other services.

**1. API Health Check**

!['ss/'](ss/api-healty-check.png)

**2. API Get human detection results**

!['ss/'](ss/api-get-caputer-video.png)


**3. API Get History Detection Motion**

!['ss/'](ss/api-history.png)
  
**4. API Get Status Lamp**

!['ss/'](ss/api-lamp.png)
    

**5. API Turn Off Lamp**

!['ss/'](ss/api-turn-off-lamp.png)


### How to Run

1. **Install dependencies**
   - Make sure you have Python 3 installed.
   - Install required packages:
  
    ```bash
    pip install -r ai/requirement.txt
    ```

    See the screenshot of the database setup in 

    !['ss/database-setup.png'](ss/python-venv.png)

    !['ss/database-setup.png'](ss/python-install-modul.png)

2. **Set up the database**
   - Run the database setup script:
  
    ```bash
    python ai/database_setup.py
    ```
   - This will initialize the database for storing detection history and other data.
   - See the screenshot of the database setup in 
  
    !['ss/database-setup.png'](ss/database-setup.png)

    !['ss/database-setup.png'](ss/database-table.png)

    !['ss/database-setup.png'](ss/database-table-lamp.png)

**1. Run the AI application**
   - Start the main AI prediction app:
  
    ```bash
    python ai/app.py
    ```
    
   - This script runs the AI model for human detection and serves the web dashboard.

   !['ss'](ss/python-run-app.png)
 
**2. Run the listener**
   - Start the listener to process incoming sensor data:

    ```bash
    python ai/listener.py
    ```
   - The listener receives data from microcontrollers and updates the database in real time.
   - See the listener activity screenshot in 
     
   !['ss'](ss/python-run-listener.png)
    

## Mictorcontroller & Connectivity
This system leverages a wide range of electronic components and connectivity protocols to achieve robust, real-time monitoring and automation:

- **Microcontrollers:**
  - ESP32 for camera, sensor, and WiFi integration
  - ESP8266 for additional wireless connectivity and sensor expansion


- **Sensors & Actuators:**
  **- Camera modules for image capture**

   !['ss'](ss/arduino-cameara-1.png)

   !['ss'](ss/arduino-camera-1.png)

   !['ss'](ss/arduino-camera-2.png)


  **- PIR motion sensors for activity detection**
  
   !['ss'](ss/arduino-sensor-motion.png)


  **- Lamps and relays for automated control**


- **Software & Drivers:**
  - Arduino IDE for programming ESP32 &ESP8266
  - Windows drivers for USB-to-serial hardware ('driver/' folder)
  
   !['ss'](ss/arduiono-adpeter-usb-to-serial.png)

   !['ss'](ss/arduiono-adpeter-usb-to-success.png)


## Device Microcontroller & Lab Simulation

This is Device Device Microcontroller 

!['ss'](ss/device.jpg)

This is Lab Simulation

!['ss'](ss/lab.jpg)


## MQTT Communication & Integration

MQTT (Message Queuing Telemetry Transport) is used in this system for lightweight, real-time messaging between microcontrollers, sensors, and the backend server. It enables efficient data transmission, device control, and event notifications across the IoT network.

- **MQTT Broker Setup:**

  - See how to configure and run the MQTT broker in !['ss/mqtt-broker.png'](ss/mqtt-broker.png)

  ```bash
  docker compose up -d mosquitto
  ```
    This command will start the MQTT broker in detached mode. Make sure your 'docker-compose.yml' includes a service named 'mosquitto'.

- **MQTT Client Connection:**
   connecting to MQTT: !['ss/mqtt-client.png'](ss/mqtt-client.png)


- **MQTT Data Flow:**
- 
  - Visualization of message exchange:

    !['ss'](ss/mqtt-sensor-motion.png)

    !['ss'](ss/mqtt-turn-off-lamp.png)


## Frontend Web Dashboard

The frontend, located in the 'frontend/' folder, provides a web-based dashboard for monitoring, controlling devices, and visualizing data from the IoT system. It interacts with the backend APIs and displays real-time information from sensors, cameras, and AI predictions.

### Features
- Live human detection and camera feed display
- Sensor status and activity logs
- Lamp and actuator control interface
- Historical data visualization
- Responsive design for desktop and mobile

### How to Use
1. Open 'frontend/index.html' in your web browser.
2. Ensure the backend ('ai/app.py') is running and accessible.
3. Interact with the dashboard to view live data, control devices, and access historical records.

### Dashboard 
- Dashboard main view: !['ss/frontend-dashboard.png'](ss/dashboard-1.png)
  
- Device control panel: !['ss/frontend-control.png'](ss/dashboard-2.png)
- 
- Historical data chart: !['ss/frontend-history.png'](ss/dashboard-3.png)

These images illustrate the main features and user experience of the web dashboard.


## Video Demostration

- This is Video Demostration : !['ss/demo.mp4'](ss/demo.mp4)

- Link Short Youtube :


