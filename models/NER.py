# In NER.py

import re

def get_entities(text: str, ner_pipeline) -> list:
    """
    Extracts named entities from text, adds custom entities via regex, 
    and corrects common misclassifications.
    """
    # 1. Get initial results from the NER pipeline
    ner_results = ner_pipeline(text)
    
    # Use a list of lists to allow modifications
    entities = []
    for item in ner_results:
        entities.append([item['word'], item['entity_group']])
        
    # 2. Use regex for more powerful custom entity detection
    custom_patterns = {
        "WEAPON": r"\b(AK-47|RPG|IED)\b",
        "CALLSIGN": r"\b(Bravo Six|Alpha One|Ghost)\b"
    }
    
    for label, pattern in custom_patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Add entity only if it hasn't already been found by the model
            # This avoids duplicate entries
            if not any(match.group(0).lower() == e[0].lower() for e in entities):
                entities.append([match.group(0), label])
    
    # 3. --- NEW: Rule-based correction for common misclassifications ---
    # This map defines known words and their correct entity type.
    known_name_map = {
        "Viper": "PER",
        "Eagle": "PER",
        "Mishra": "PER",
        "Charminar": "LOC"
    }

    # Loop through the detected entities and correct their labels if they are in our map
    for entity in entities:
        # Check against the word itself and its cleaned-up version
        word = entity[0].strip()
        if word in known_name_map:
            entity[1] = known_name_map[word] # Correct the label

    # 4. Convert back to a list of tuples before returning for immutability
    return [tuple(entity) for entity in entities]