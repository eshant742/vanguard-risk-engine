from ml_engine import initialize_model
m = initialize_model()
print(f"Precision: {m['precision']}, Recall: {m['recall']}, F1: {m['f1_score']}")
