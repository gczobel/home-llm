import json
import random
from datetime import datetime
from pathlib import Path
import csv
from io import StringIO

print("SCRIPT EXECUTION STARTED: generate_training_data_custom.py")

# Helper function to extract device list from log data's system message
def extract_devices_csv_from_log_data(log_data_str: str) -> str:
    print(f"  extract_devices_csv_from_log_data: Called with log_data_str (first 100 chars): {log_data_str[:100]}")
    try:
        log_data_list = json.loads(log_data_str)
        for message_idx, message in enumerate(log_data_list):
            # print(f"    Log message {message_idx}: Role: {message.get('role')}")
            if message.get("role") == "system":
                content = message.get("content", "")
                # print(f"    Found system message. Content (first 100): {content[:100]}")
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
                         # print(f"    Found CSV marker (escaped) at index {start_index}.")
                    else:
                        # print("    CSV marker not found in system message.")
                        continue 
                else:
                    actual_start = start_index + len(csv_marker)
                    # print(f"    Found CSV marker (plain) at index {start_index}.")
                
                end_index = content.find("```", actual_start)
                if end_index != -1:
                    extracted_csv = content[actual_start:end_index].strip().replace("\\n", "\n")
                    print(f"  extract_devices_csv_from_log_data: Successfully extracted CSV data (first 100 chars): {extracted_csv[:100]}")
                    return extracted_csv
        print("  extract_devices_csv_from_log_data: No system message with device CSV found.")
        return "" 
    except json.JSONDecodeError as e:
        print(f"  extract_devices_csv_from_log_data: JSONDecodeError: {e}")
        return "" 
    except Exception as e:
        print(f"  extract_devices_csv_from_log_data: Other error: {e}")
        return "" 

# Helper function to extract tool calls and final assistant response from log data
def extract_tool_call_and_response_from_log_data(log_data_str: str):
    print(f"  extract_tool_call_and_response_from_log_data: Called with log_data_str (first 100 chars): {log_data_str[:100]}")
    tool_calls = None
    final_assistant_response = None
    try:
        log_data_list = json.loads(log_data_str)
        
        assistant_messages = [m for m in log_data_list if m.get("role") == "assistant"]
        tool_messages = [m for m in log_data_list if m.get("role") == "tool"]

        if not assistant_messages:
            print("  extract_tool_call_and_response_from_log_data: No assistant messages found.")
            return None, None

        for i, assistant_msg in enumerate(assistant_messages):
            # print(f"    Processing assistant_msg {i}: {assistant_msg}")
            current_tool_calls = assistant_msg.get("tool_calls")
            current_content = assistant_msg.get("content")

            if current_tool_calls:
                print(f"    Found tool_calls in assistant message {i}: {current_tool_calls}")
                tool_calls = current_tool_calls 
                if current_content: 
                    print(f"    Content also found in assistant message with tool_calls: {current_content}")
                    final_assistant_response = current_content # This might be a confirmation like "OK."
                
                temp_final_response_after_tool = None
                for tc_idx, tc in enumerate(tool_calls): 
                    tool_call_id = tc.get("id")
                    # print(f"      Processing tool_call {tc_idx} with id: {tool_call_id}")
                    corresponding_tool_msg = next((tm for tm in tool_messages if tm.get("tool_call_id") == tool_call_id), None)
                    if corresponding_tool_msg:
                        # print(f"      Found corresponding tool message: {corresponding_tool_msg}")
                        tool_msg_index_in_log = -1
                        try:
                            # Find index in the original log_data_list to ensure we look *after* it
                            for log_idx, log_entry in enumerate(log_data_list):
                                if log_entry.get("role") == "tool" and log_entry.get("tool_call_id") == tool_call_id:
                                    tool_msg_index_in_log = log_idx
                                    break
                        except ValueError: 
                            # print(f"      ValueError finding index for tool_msg with id {tool_call_id}")
                            continue # Should not happen if found with next()

                        if tool_msg_index_in_log != -1:
                            for j in range(tool_msg_index_in_log + 1, len(log_data_list)):
                                if log_data_list[j].get("role") == "assistant" and log_data_list[j].get("content"):
                                    temp_final_response_after_tool = log_data_list[j].get("content")
                                    # print(f"      Found subsequent assistant response: {temp_final_response_after_tool}")
                                    break 
                            if temp_final_response_after_tool: 
                                final_assistant_response = temp_final_response_after_tool
                        # else:
                            # print(f"      Tool message with id {tool_call_id} not found in original log_data_list by index.")
            
            elif current_content: # This is a text-only response
                # print(f"    Found text-only assistant message {i}: {current_content}")
                final_assistant_response = current_content
                # If this is a simple text response, there should be no active tool_calls from previous iterations.
                tool_calls = None 


    except json.JSONDecodeError as e:
        print(f"  extract_tool_call_and_response_from_log_data: JSONDecodeError: {e}")
        pass 
    except Exception as e: 
        print(f"  extract_tool_call_and_response_from_log_data: Other error: {e}")
        pass
        
    print(f"  extract_tool_call_and_response_from_log_data: Returning tool_calls: {tool_calls}, final_assistant_response: {final_assistant_response}")
    return tool_calls, final_assistant_response
