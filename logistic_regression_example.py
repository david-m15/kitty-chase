import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Example use case: Predicting if a car is 'expensive' based on features
# Features: age (years), mileage (km), engine size (L), horsepower, number of owners
data = {
    "age": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2, 4, 6, 8, 10],
    "mileage": [
        1000,
        2000,
        3500,
        5000,
        6500,
        8000,
        9500,
        11000,
        12500,
        14000,
        3000,
        6000,
        9000,
        12000,
        15000,
    ],
    "engine_size": [
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        1.6,
        1.8,
        2.2,
        2.4,
        2.0,
    ],
    "horsepower": [
        150,
        148,
        145,
        143,
        140,
        138,
        135,
        133,
        130,
        128,
        120,
        125,
        140,
        150,
        135,
    ],
    "owners": [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 1, 2, 2, 3, 4],
    "price": [
        25000,
        23000,
        21000,
        19000,
        17000,
        15000,
        13000,
        11000,
        9000,
        7000,
        18000,
        16000,
        12000,
        10000,
        8000,
    ],
}
df = pd.DataFrame(data)

# Define 'expensive' as price > 17000
df["expensive"] = (df["price"] > 17000).astype(int)

X = df[["age", "mileage", "engine_size", "horsepower", "owners"]]
y = df["expensive"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Train logistic regression model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
