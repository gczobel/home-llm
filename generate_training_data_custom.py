import json
import random
from datetime import datetime
from pathlib import Path
import csv
from io import StringIO

print("Script starting...")

# Helper function to extract device list from log data's system message
def extract_devices_csv_from_log_data(log_data_str: str) -> str:
    # print(f"Attempting to parse log_data_str for devices: {log_data_str[:200]}...") # Print first 200 chars
    try:
        log_data_list = json.loads(log_data_str)
        for message in log_data_list:
            if message.get("role") == "system":
                content = message.get("content", "")
                # print(f"Found system message content: {content[:100]}...")
                csv_marker = "Available Devices:\n```csv\n"
                # Handle escaped newlines that might appear in JSON strings
                csv_marker_escaped = csv_marker.replace("\n", "\\n")
                
                start_index = content.find(csv_marker)
                # print(f"Plain marker search index: {start_index}")
                if start_index == -1: # Try with escaped newline
                    start_index = content.find(csv_marker_escaped)
                    # print(f"Escaped marker search index: {start_index}")
                    if start_index != -1:
                         actual_start = start_index + len(csv_marker_escaped)
                    else:
                        # print("CSV marker not found in system message.")
                        continue 
                else:
                    actual_start = start_index + len(csv_marker)
                
                end_index = content.find("```", actual_start)
                if end_index != -1:
                    extracted_csv = content[actual_start:end_index].strip().replace("\\n", "\n")
                    # print(f"Successfully extracted CSV data: {extracted_csv[:100]}...")
                    return extracted_csv
        # print("No system message with device CSV found.")
        return "" 
    except json.JSONDecodeError as e:
        # print(f"JSONDecodeError in extract_devices_csv_from_log_data: {e}")
        return "" 
    except Exception as e:
        # print(f"Other error in extract_devices_csv_from_log_data: {e}")
        return "" 
Let me know when you've pasted this part, and I'll send the next chunk.

Here's the second part of the script (the extract_tool_call_and_response_from_log_data function). Please append this to the content you've already pasted in generate_training_data_custom.py:


# Helper function to extract tool calls and final assistant response from log data
def extract_tool_call_and_response_from_log_data(log_data_str: str):
    # print(f"Attempting to parse log_data_str for tool calls/response: {log_data_str[:200]}...")
    tool_calls = None
    final_assistant_response = None
    try:
        log_data_list = json.loads(log_data_str)
        
        assistant_messages = [m for m in log_data_list if m.get("role") == "assistant"]
        tool_messages = [m for m in log_data_list if m.get("role") == "tool"]

        if not assistant_messages:
            # print("No assistant messages found in log data.")
            return None, None

        # Iterate through assistant messages to find relevant tool calls and responses
        for i, assistant_msg in enumerate(assistant_messages):
            current_tool_calls = assistant_msg.get("tool_calls")
            current_content = assistant_msg.get("content")

            if current_tool_calls:
                # print(f"Found tool_calls in assistant message: {current_tool_calls}")
                tool_calls = current_tool_calls 
                if current_content: 
                    # print(f"Content found in assistant message with tool_calls: {current_content}")
                    final_assistant_response = current_content
                
                temp_final_response_after_tool = None
                for tc in tool_calls: 
                    tool_call_id = tc.get("id")
                    # print(f"Processing tool_call_id: {tool_call_id}")
                    corresponding_tool_msg = next((tm for tm in tool_messages if tm.get("tool_call_id") == tool_call_id), None)
                    if corresponding_tool_msg:
                        # print(f"Found corresponding tool message: {corresponding_tool_msg}")
                        tool_msg_index_in_log = -1
                        try:
                            tool_msg_index_in_log = log_data_list.index(corresponding_tool_msg)
                        except ValueError: 
                            # print(f"ValueError finding index for tool_msg: {corresponding_tool_msg}")
                            continue

                        for j in range(tool_msg_index_in_log + 1, len(log_data_list)):
                            if log_data_list[j].get("role") == "assistant" and log_data_list[j].get("content"):
                                temp_final_response_after_tool = log_data_list[j].get("content")
                                # print(f"Found subsequent assistant response: {temp_final_response_after_tool}")
                                break 
                        if temp_final_response_after_tool: 
                            final_assistant_response = temp_final_response_after_tool
            
            elif current_content: # This is a text-only response
                # print(f"Found text-only assistant message: {current_content}")
                final_assistant_response = current_content
                tool_calls = None # Reset tool_calls if this is a pure text response

    except json.JSONDecodeError as e:
        # print(f"JSONDecodeError in extract_tool_call_and_response_from_log_data: {e}")
        pass 
    except Exception as e: 
        # print(f"Other error in extract_tool_call_and_response_from_log_data: {e}")
        pass
        
    # print(f"Returning tool_calls: {tool_calls}, final_assistant_response: {final_assistant_response}")
    return tool_calls, final_assistant_response
