from shivi.source import process_source_request
import os

if os.path.exists('projects.json') and os.path.getsize('projects.json') == 0:
    print("projects.json is empty")

process_source_request("add source /Users/harsh/Desktop/rag_agent")