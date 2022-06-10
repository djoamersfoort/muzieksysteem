#!/bin/bash
sudo cp mqtt.service /etc/systemd/system/mqtt.service
sudo cp visualizer.service /etc/systemd/system/visualizer.service
sudo systemctl daemon-reload
sudo systemctl enable mqtt.service visualizer.service
sudo systemctl start mqtt.service visualizer.service