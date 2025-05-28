import json
import random

# Configuration
NUM_EXAMPLES = 100  # Number of synthetic examples to generate
OUTPUT_FILE = "training_data_ha_synthetic.jsonl"

# Predefined lists for generating varied data
ASSISTANT_RESPONSES_TEMPLATES = [
    "Sure, I've {} the {}.",
    "Okay, the {} is now {}.",
    "Done. The {} has been {}.",
    "No problem, {} the {} for you.",
    "Alright, {} the {}."
]

USER_REQUEST_TEMPLATES = [
    "Can you turn {} the {} in the {}?",
    "Please {} the {} in the {}.",
    "I'd like to {} the {} in the {}.",
    "Set the {} in the {} to {}.",
    "{} the {} in the {} for me."
]

ACTIONS_STATES = {
    "turn_on": "on",
    "turn_off": "off",
    "increase": "increased",
    "decrease": "decreased",
    "set": "set" # General set, can be for brightness, temp, etc.
}

ENTITIES_WITH_PROPERTIES = {
    "lights": {"actions": ["turn_on", "turn_off", "set"], "properties": ["brightness"]},
    "fan": {"actions": ["turn_on", "turn_off", "increase", "decrease"], "properties": ["speed"]},
    "thermostat": {"actions": ["set"], "properties": ["temperature"]},
    "TV": {"actions": ["turn_on", "turn_off"]},
    "speakers": {"actions": ["turn_on", "turn_off", "set"], "properties": ["volume"]},
    "window": {"actions": ["open", "close"]}, # Assuming "open" and "close" map to "on" and "off" states or similar
    "door": {"actions": ["open", "close"]},
    "coffee_maker": {"actions": ["turn_on", "turn_off"]},
    "security_camera": {"actions": ["turn_on", "turn_off"]},
    "vacuum_cleaner": {"actions": ["turn_on", "turn_off", "start_cleaning", "dock"]}, # More specific actions
}

LOCATIONS = ["living room", "bedroom", "kitchen", "office", "bathroom", "hallway", "garage", "patio"]

def generate_plausible_user_request():
    """Generates a more plausible and varied user request."""
    entity_name = random.choice(list(ENTITIES_WITH_PROPERTIES.keys()))
    entity_info = ENTITIES_WITH_PROPERTIES[entity_name]
    action = random.choice(entity_info["actions"])
    location = random.choice(LOCATIONS)
    template = random.choice(USER_REQUEST_TEMPLATES)

    # Map action to a state for response generation
    state = ACTIONS_STATES.get(action, action) # Default to action if no specific state

    # Handle templates with different numbers of placeholders
    if template.count("{}") == 3: # e.g., "Can you turn {} the {} in the {}?" or "Set the {} in the {} to {}."
        if action == "set" and "properties" in entity_info:
            # For "set" actions, pick a property and a value
            prop = random.choice(entity_info["properties"])
            value = ""
            if prop == "brightness":
                value = f"{random.randint(10, 100)}%"
            elif prop == "temperature":
                value = f"{random.randint(18, 25)} degrees"
            elif prop == "volume":
                value = f"{random.randint(20, 80)}%"
            elif prop == "speed":
                value = random.choice(["low", "medium", "high"])
            # Adjust user request for "set" actions to be more natural
            if "Set the {} in the {} to {}." == template: # "Set the [entity] in the [location] to [value/state]."
                 user_request = template.format(f"{prop} of the {entity_name}", location, value)
                 # Adjust state for assistant response to reflect property being set
                 state = f"{prop} to {value}"
            else: # Other 3-placeholder templates, e.g. "Can you turn {} the {} in the {}?" - this is less ideal for "set"
                  # Fallback to using action and entity for these if "set" is chosen.
                  user_request = template.format(action, entity_name, location)
        else: # For actions other than "set" or if "set" has no specific properties
            user_request = template.format(action.replace("_", " "), entity_name, location)

    elif template.count("{}") == 2: # e.g. "Please {} the {}." (Location might be omitted or implied)
        # This template format might not always include location explicitly in the user request
        # For simplicity, we'll assume the request implies a general context or a previously discussed location.
        # The generated response, however, can still include a location for clarity.
        user_request = template.format(action.replace("_", " "), entity_name)

    else: # Fallback for any other template structure (should ideally not happen with defined templates)
        user_request = f"{action.replace('_', ' ').capitalize()} the {entity_name} in the {location}."

    return user_request, entity_name, location, state

def generate_assistant_response(entity_name, location, state):
    """Generates an assistant response based on the action's state."""
    template = random.choice(ASSISTANT_RESPONSES_TEMPLATES)
    # Adjust state for "open/close" to sound more natural if needed
    if state in ["open", "close"]:
        # Example: "Okay, the window is now open." instead of "Okay, the window is now on."
        # This depends on how ACTIONS_STATES maps these. If "open" maps to "opened", this is fine.
        # For now, we assume state is correctly representing the final status.
        pass # State is already "open" or "close"

    # Fill the template
    if template.count("{}") == 2: # e.g., "Sure, I've {} the {}." or "Okay, the {} is now {}."
        # Determine if the template expects action/state first or entity first
        if "I've" in template or "for you" in template or "Alright," in template : # Expects state then entity
            response = template.format(state, f"{entity_name} in the {location}")
        else: # Expects entity then state
            response = template.format(f"{entity_name} in the {location}", state)
    else: # Fallback for other template structures
        response = f"Okay, the {entity_name} in the {location} is now {state}."
    return response

def generate_conversation_data(num_examples):
    """Generates conversation data."""
    examples = []
    for _ in range(num_examples):
        user_request, entity, location, state_for_response = generate_plausible_user_request()
        assistant_response = generate_assistant_response(entity, location, state_for_response)

        examples.append({
            "messages": [
                {"role": "user", "content": user_request},
                {"role": "assistant", "content": assistant_response}
            ]
        })
    return examples

if __name__ == "__main__":
    synthetic_examples = generate_conversation_data(NUM_EXAMPLES)

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for example in synthetic_examples:
                f.write(json.dumps(example) + '\n')
        print(f"Successfully generated and saved {len(synthetic_examples)} synthetic examples to '{OUTPUT_FILE}'.")
    except IOError as e:
        print(f"Error writing to file '{OUTPUT_FILE}': {e}")
