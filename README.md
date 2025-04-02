# Property Scraper

## Jobs Server
### Setup Jobs Server
- sudo apt install python3.12-venv
- python3 -m venv myenv
- source myenv/bin/activate
- pip install [packages]
- [install google chrome]
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  sudo dpkg -i google-chrome-stable_current_amd64.deb
  sudo apt-get install -f
  google-chrome-stable --version

### Start Jobs Server
- source myenv/bin/activate
- sudo nohup env PYTHONUNBUFFERED=1 $(which python3) ./jobs.py > output.log 2>&1 &

### Stop Jobs Server
- ps aux | grep python3
  Find the process ID (PID) of the Python script
- kill [PID]


## Drone Server
### Setup Drone Server
- sudo apt install python3.12-venv
- python3 -m venv myenv
- source myenv/bin/activate
- pip install [packages]
- [install google chrome]
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  sudo dpkg -i google-chrome-stable_current_amd64.deb
  sudo apt-get install -f
  google-chrome-stable --version


### Start Drone Server
- source myenv/bin/activate
- sudo nohup  env PYTHONUNBUFFERED=1 $(which python3) ./drone.py > output.log 2>&1 &

### Stop Drone Server
- ps aux | grep python3
  Find the process ID (PID) of the Python script
- kill [PID]