def get_risk_assessment(text: str, classifier_pipeline) -> tuple:
    """
    Analyzes text to determine a risk level using a zero-shot classification model.
    """
    # Define the categories you want the model to check against
    candidate_labels = ["critical threat", "suspicious activity", "benign communication"]
    
    # Pass the text and the labels to the pipeline
    result = classifier_pipeline(text, candidate_labels)
    
    # Get the label with the highest score
    top_label = result['labels'][0]
    
    # Return a risk level based on the model's top choice
    if "critical" in top_label:
        return ("Critical", "High threat detected")
    elif "suspicious" in top_label:
        return ("Suspicious", "Requires further review")
    else:
        return ("Benign", "Low threat potential")