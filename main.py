#!/usr/bin/python
# -*- coding:utf-8 -*-

# This script is the main entry point for the application.
# Its purpose is to initialize and run the ServerMonitor.

from src.monitor import ServerMonitor

if __name__ == '__main__':
    monitor = ServerMonitor()
    monitor.run()
