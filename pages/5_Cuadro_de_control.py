import streamlit as st 
import requests
from utils import *
import os
import json

#apply_sidebar_style()
#mostrar_sidebar_con_logo()


json_path = os.path.join(os.path.dirname(__file__), "..", "secrets", "streamlit_bucket.json")
json_path = os.path.abspath(json_path)
with open(json_path) as f:
    secrets = json.load(f)


print(secrets)