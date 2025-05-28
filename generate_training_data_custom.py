import json
import random
from datetime import datetime
from pathlib import Path
import csv
from io import StringIO

# Helper function to extract device list from log data's system message
def extract_devices_csv_from_log_data(log_data_str: str) -> str:
    try:
        log_data_list = json.loads(log_data_str)
        for message in log_data_list:
            if message.get("role") == "system":
                content = message.get("content", "")
                csv_marker = "Available Devices:\n```csv\n"
                # Handle escaped newlines that might appear in JSON strings
                csv_marker_escaped = csv_marker.replace("\n", "\\n")
                
                start_index = content.find(csv_marker)
                if start_index == -1: # Try with escaped newline
                    start_index = content.find(csv_marker_escaped)
                    if start_index != -1:
                         actual_start = start_index + len(csv_marker_escaped)
                    else:
                        continue # Marker not found
                else:
                    actual_start = start_index + len(csv_marker)
                
                end_index = content.find("```", actual_start)
                if end_index != -1:
                    # Replace escaped newlines in the CSV data itself back to normal newlines
                    return content[actual_start:end_index].strip().replace("\\n", "\n")
        return "" # Return empty if no system message with CSV found
    except json.JSONDecodeError:
        return "" # Return empty if log_data_str is not valid JSON
    except Exception:
        return "" # Catch any other error during parsing

# Helper function to extract tool calls and final assistant response from log data
def extract_tool_call_and_response_from_log_data(log_data_str: str):
    tool_calls = None
    final_assistant_response = None
    try:
        log_data_list = json.loads(log_data_str)
        
        assistant_messages = [m for m in log_data_list if m.get("role") == "assistant"]
        tool_messages = [m for m in log_data_list if m.get("role") == "tool"]

        if not assistant_messages:
            return None, None

        # Iterate through assistant messages to find relevant tool calls and responses
        for i, assistant_msg in enumerate(assistant_messages):
            current_tool_calls = assistant_msg.get("tool_calls")
            current_content = assistant_msg.get("content")

            if current_tool_calls:
                tool_calls = current_tool_calls 
                if current_content: 
                    final_assistant_response = current_content
                
                temp_final_response_after_tool = None
                for tc in tool_calls: 
                    tool_call_id = tc.get("id")
                    corresponding_tool_msg = next((tm for tm in tool_messages if tm.get("tool_call_id") == tool_call_id), None)
                    if corresponding_tool_msg:
                        tool_msg_index_in_log = -1
                        try:
                            tool_msg_index_in_log = log_data_list.index(corresponding_tool_msg)
                        except ValueError: 
                            continue

                        for j in range(tool_msg_index_in_log + 1, len(log_data_list)):
                            if log_data_list[j].get("role") == "assistant" and log_data_list[j].get("content"):
                                temp_final_response_after_tool = log_data_list[j].get("content")
                                break 
                        if temp_final_response_after_tool: 
                            final_assistant_response = temp_final_response_after_tool
            
            elif current_content: # This is a text-only response
                final_assistant_response = current_content
                tool_calls = None # Reset tool_calls if this is a pure text response

    except json.JSONDecodeError:
        pass 
    except Exception: 
        pass
        
    return tool_calls, final_assistant_response
