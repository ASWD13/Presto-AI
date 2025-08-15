def get_entities(text: str, ner_pipeline) -> list:
    """
    Extracts named entities from text using an NER model.

    Args:
        text (str): The input text.
        ner_pipeline: The pre-loaded Hugging Face pipeline for NER.

    Returns:
        list: A list of tuples, where each tuple is (entity, label).
    """
    # Use the pre-loaded pipeline to get NER results
    ner_results = ner_pipeline(text)
    
    # Format the results into a clean list of (entity, label) tuples
    entities = []
    for item in ner_results:
        entity_label = item['entity_group']
        entities.append((item['word'], entity_label))
        
    # --- This is where you would add custom logic for specific keywords ---
    # For example, you can still look for keywords not caught by the model
    if "AK-47" in text and not any("AK-47" in e for e, l in entities):
         entities.append(("AK-47", "WEAPON"))

    return entities