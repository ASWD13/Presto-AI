import re

def get_risk_assessment(text: str, classifier_pipeline) -> tuple:
    """
    Analyzes text to determine a risk level using a zero-shot classification model.
    Returns risk level, description, and evidence text.
    """
    # Define the categories you want the model to check against
    candidate_labels = ["critical threat", "suspicious activity", "benign communication"]
    
    # Pass the text and the labels to the pipeline for overall classification
    result = classifier_pipeline(text, candidate_labels)
    
    # Get the label with the highest score
    top_label = result['labels'][0]
    
    # Determine risk level and description
    if "critical" in top_label:
        risk_level = "Critical"
        description = "High threat detected"
    elif "suspicious" in top_label:
        risk_level = "Suspicious"
        description = "Requires further review"
    else:
        risk_level = "Benign"
        description = "Low threat potential"
    
    # Find evidence by analyzing individual sentences
    evidence = find_evidence(text, top_label, classifier_pipeline, candidate_labels)
    
    return (risk_level, description, evidence)

def find_evidence(text: str, predicted_label: str, classifier_pipeline, candidate_labels: list) -> str:
    """
    Finds the most relevant sentence as evidence for the classification.
    """
    # Split text into sentences (simple regex-based approach)
    sentences = re.split(r'[.!?]+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return "No evidence available"
    
    # If only one sentence, return it directly
    if len(sentences) == 1:
        return f"Evidence: '{sentences[0]}'"
    
    best_sentence = None
    best_score = 0.0
    
    # Analyze each sentence individually
    for sentence in sentences:
        if len(sentence) < 10:  # Skip very short sentences
            continue
            
        # Run classification on individual sentence
        sentence_result = classifier_pipeline(sentence, candidate_labels)
        
        # Find the score for the predicted label
        try:
            label_index = sentence_result['labels'].index(predicted_label)
            score = sentence_result['scores'][label_index]
            
            # Update best sentence if this one has higher confidence
            if score > best_score:
                best_score = score
                best_sentence = sentence
        except ValueError:
            # Label not found in results, skip this sentence
            continue
    
    # Return the best evidence sentence
    if best_sentence:
        return f"Evidence: '{best_sentence}'"
    else:
        # Fallback: return the first sentence if no good evidence found
        return f"Evidence: '{sentences[0]}'"