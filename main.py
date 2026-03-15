

import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt


# Real-world use case: Predicting car price based on 5 features
# Features: age (years), mileage (km), engine size (L), horsepower, number of owners
data = {
    'age': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'mileage': [1000, 2000, 3500, 5000, 6500, 8000, 9500, 11000, 12500, 14000],
    'engine_size': [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
    'horsepower': [150, 148, 145, 143, 140, 138, 135, 133, 130, 128],
    'owners': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4],
    'price': [25000, 23000, 21000, 19000, 17000, 15000, 13000, 11000, 9000, 7000]
}
df = pd.DataFrame(data)

# Features and target
X = df[['age', 'mileage', 'engine_size', 'horsepower', 'owners']]
y = df['price']

# Polynomial regression (degree 5)
poly = PolynomialFeatures(degree=5)
X_poly = poly.fit_transform(X)
model = LinearRegression()
model.fit(X_poly, y)

# Predict price for a new car
new_car = np.array([[3, 30000, 2.0, 145, 1]])  # 3 years old, 30k km, 2.0L, 145hp, 1 owner
new_car_poly = poly.transform(new_car)
predicted_price = model.predict(new_car_poly)[0]

print(f"Predicted price for a 3-year-old car with 30,000 km, 2.0L engine, 145hp, 1 owner: ${predicted_price:,.2f}")

# Plotting actual vs predicted prices for the dataset
predicted_prices = model.predict(X_poly)
plt.scatter(range(len(y)), y, color='blue', label='Actual Price')
plt.scatter(range(len(y)), predicted_prices, color='red', marker='x', label='Predicted Price')
plt.xlabel('Sample Index')
plt.ylabel('Car Price')
plt.title('Polynomial Regression (Degree 5): Actual vs Predicted Car Prices')
plt.legend()
plt.show()
