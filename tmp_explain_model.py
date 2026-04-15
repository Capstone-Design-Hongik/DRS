import pandas as pd
from pycaret.classification import load_model

def main():
    try:
        # Load the PyCaret pipeline
        model = load_model('c:/Users/jiho/Desktop/26DRS/DRS/pycaret_automl_example/weekly_momentum_model')
        
        # In PyCaret 3, the model is a Pipeline. The last step is the estimator.
        estimator = model.steps[-1][1]
        
        # Get feature importances if available
        if hasattr(estimator, 'feature_importances_'):
            importances = estimator.feature_importances_
            
            # Use original feature names roughly (excluding Target/Date/Future_Return)
            features = ['ROC_5', 'ROC_20', 'ROC_60', 'Dist_SMA10', 'Dist_SMA20', 'Dist_SMA50', 'Dist_High52', 'Vol_Ratio', 'RSI_14']
            
            # Note: PyCaret might rename them or we can just pair them if length matches
            if len(importances) == len(features):
                df = pd.DataFrame({'Feature': features, 'Importance': importances})
                df = df.sort_values(by='Importance', ascending=False)
                print(df.to_string(index=False))
            else:
                print(f"Feature length mismatch: importances({len(importances)}), features({len(features)})")
                print(importances)
        else:
            print("Estimator does not support feature importances.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
