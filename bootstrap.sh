#!/usr/bin/env bash

sudo apt-get update
for i in python3 default-jre default-jdk; do
  sudo apt-get install $i -y
done