import os
import sys
import time
import random
import requests

class Elutil():
    @staticmethod
    def launch_anime(message=""):
        base_text = "[INFO] RDTP - Launch Progress"
        frames = [
            ".", 
            "..", 
            ".. _", 
            ".. _(", 
            ".. _(:", 
            ".. _(:3", 
            ".. _(:3  |", 
            ".. _(:3  |_", 
            ".. _(:3  |_)", 
            ".. _(:3  |_)_", 
            ".. _(:3  |_)_.", 
            ".. _(:3  |_)_.. [OK]"
        ]

        for frame in frames:
            sys.stdout.write(f"\r{base_text}{frame}")
            sys.stdout.flush()
            time.sleep(0.15)
        print(message)
        print("===========================================")
        print()

    @staticmethod
    def show_message(message=""):
        print("[INFO] "+message)
        print("===========================================")
        print()
