"""
Train ML Model for Ingredient Analysis.
Trains a classifier to detect hidden sugars in food ingredients.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
from typing import List, Dict, Any
import requests
import json


class IngredientModelTrainer:
    """Trainer for ingredient analysis ML model."""

    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'ingredient_classifier.pkl')
        self.vectorizer_path = os.path.join(os.path.dirname(__file__), 'models', 'tfidf_vectorizer.pkl')
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

    def collect_training_data(self) -> pd.DataFrame:
        """
        Collect training data from OpenFoodFacts or use synthetic data if API fails.
        Labels products as having misleading sugar claims or not.
        """
        print("Collecting training data...")

        # Sugar-related keywords for labeling
        sugar_keywords = [
            'sugar-free', 'no sugar', 'sugarless', 'low sugar', 'reduced sugar',
            'zero sugar', 'no added sugar'
        ]

        hidden_sugars = [
            'fructose', 'sucrose', 'glucose', 'maltose', 'lactose', 'galactose',
            'acesulfame potassium', 'aspartame', 'sucralose', 'saccharin',
            'stevia', 'erythritol', 'xylitol', 'sorbitol', 'mannitol', 'isomalt',
            'high fructose corn syrup', 'corn syrup', 'agave nectar', 'honey',
            'maple syrup', 'molasses', 'fruit juice concentrate', 'dextrose',
            'maltodextrin', 'barley malt', 'rice syrup'
        ]

        data = []

        # Try OpenFoodFacts first
        try:
            categories = ['en:sugary-snacks', 'en:beverages', 'en:dairies', 'en:desserts']

            for category in categories:
                print(f"Fetching products from category: {category}")
                url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms=&tagtype_0=categories&tag_contains_0=contains&tag_0={category}&json=1&page_size=50"

                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    result = response.json()
                    products = result.get('products', [])

                    for product in products[:25]:  # Limit per category
                        ingredients = product.get('ingredients_text', '').lower()
                        product_name = product.get('product_name', '').lower()
                        labels = [label.lower() for label in product.get('labels_tags', [])]

                        if not ingredients:
                            continue

                        # Check for sugar-free claims
                        has_sugar_free_claim = any(
                            keyword in product_name or any(keyword in label for label in labels)
                            for keyword in sugar_keywords
                        )

                        # Check for hidden sugars
                        has_hidden_sugars = any(sugar in ingredients for sugar in hidden_sugars)

                        # Label: 1 if misleading claim (claims sugar-free but has hidden sugars), 0 otherwise
                        if has_sugar_free_claim and has_hidden_sugars:
                            label = 1  # Misleading
                        elif has_sugar_free_claim and not has_hidden_sugars:
                            label = 0  # Legitimate sugar-free
                        elif not has_sugar_free_claim:
                            label = 0  # No claim, so not misleading
                        else:
                            continue  # Skip unclear cases

                        data.append({
                            'ingredients': ingredients,
                            'product_name': product_name,
                            'labels': ' '.join(labels),
                            'has_sugar_free_claim': has_sugar_free_claim,
                            'has_hidden_sugars': has_hidden_sugars,
                            'misleading': label
                        })

        except Exception as e:
            print(f"OpenFoodFacts API failed: {e}")
            print("Using synthetic training data instead...")

        # If we don't have enough data, create synthetic examples
        if len(data) < 50:
            print(f"Only collected {len(data)} samples, adding synthetic data...")

            # Synthetic misleading examples (claims sugar-free but contains hidden sugars)
            misleading_examples = [
                {
                    'ingredients': 'carbonated water, sucralose, acesulfame potassium, citric acid',
                    'product_name': 'zero sugar cola',
                    'labels': 'sugar-free zero-sugar',
                    'misleading': 1
                },
                {
                    'ingredients': 'water, aspartame, sucralose, natural flavors',
                    'product_name': 'sugar free lemonade',
                    'labels': 'no-sugar-added sugar-free',
                    'misleading': 1
                },
                {
                    'ingredients': 'milk, stevia, sucralose, artificial flavors',
                    'product_name': 'low sugar yogurt',
                    'labels': 'reduced-sugar sugar-free',
                    'misleading': 1
                },
                {
                    'ingredients': 'wheat flour, sucralose, aspartame, baking powder',
                    'product_name': 'sugar free cookies',
                    'labels': 'no-sugar sugarless',
                    'misleading': 1
                },
                {
                    'ingredients': 'fruit juice concentrate, sucralose, water, citric acid',
                    'product_name': 'zero sugar fruit drink',
                    'labels': 'sugar-free zero-calorie',
                    'misleading': 1
                },
                {
                    'ingredients': 'corn syrup, sucralose, water, artificial colors',
                    'product_name': 'diet soda',
                    'labels': 'sugar-free low-calorie',
                    'misleading': 1
                },
                {
                    'ingredients': 'high fructose corn syrup, aspartame, citric acid',
                    'product_name': 'light fruit punch',
                    'labels': 'reduced-sugar sugar-free',
                    'misleading': 1
                },
                {
                    'ingredients': 'maltodextrin, sucralose, artificial sweeteners',
                    'product_name': 'sugar free energy drink',
                    'labels': 'zero-sugar no-sugar',
                    'misleading': 1
                }
            ]

            # Synthetic legitimate examples (actually sugar-free or no claims)
            legitimate_examples = [
                {
                    'ingredients': 'water, citric acid, natural flavors, stevia leaf extract',
                    'product_name': 'natural fruit water',
                    'labels': 'natural sugar-free',
                    'misleading': 0
                },
                {
                    'ingredients': 'almonds, walnuts, cashews, dried cranberries',
                    'product_name': 'mixed nuts trail mix',
                    'labels': 'natural',
                    'misleading': 0
                },
                {
                    'ingredients': 'chicken breast, salt, pepper, herbs',
                    'product_name': 'grilled chicken',
                    'labels': 'lean-protein',
                    'misleading': 0
                },
                {
                    'ingredients': 'oats, almonds, honey, cinnamon',
                    'product_name': 'granola cereal',
                    'labels': 'whole-grain',
                    'misleading': 0
                },
                {
                    'ingredients': 'spinach, kale, cucumber, lemon juice',
                    'product_name': 'green smoothie',
                    'labels': 'organic',
                    'misleading': 0
                },
                {
                    'ingredients': 'quinoa, vegetables, olive oil, garlic',
                    'product_name': 'vegetable stir fry',
                    'labels': 'gluten-free',
                    'misleading': 0
                },
                {
                    'ingredients': 'salmon, herbs, lemon, olive oil',
                    'product_name': 'baked salmon',
                    'labels': 'omega-3',
                    'misleading': 0
                },
                {
                    'ingredients': 'brown rice, vegetables, tofu, soy sauce',
                    'product_name': 'vegetable fried rice',
                    'labels': 'plant-based',
                    'misleading': 0
                }
            ]

            # Add synthetic examples
            for example in misleading_examples + legitimate_examples:
                data.append({
                    'ingredients': example['ingredients'],
                    'product_name': example['product_name'],
                    'labels': example['labels'],
                    'has_sugar_free_claim': 1 if 'sugar' in example['labels'] else 0,
                    'has_hidden_sugars': 1 if any(sugar in example['ingredients'] for sugar in hidden_sugars) else 0,
                    'misleading': example['misleading']
                })

        if len(data) < 10:
            raise ValueError("Insufficient training data. Need at least 10 samples.")

        df = pd.DataFrame(data)
        print(f"Collected {len(df)} training samples")
        print(f"Misleading claims: {df['misleading'].sum()}")
        print(f"Legitimate claims: {len(df) - df['misleading'].sum()}")

        return df
        categories = ['en:sugary-snacks', 'en:beverages', 'en:dairies', 'en:desserts']

        for category in categories:
            print(f"Fetching products from category: {category}")
            url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms=&tagtype_0=categories&tag_contains_0=contains&tag_0={category}&json=1&page_size=100"

            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    products = result.get('products', [])

                    for product in products[:50]:  # Limit per category
                        ingredients = product.get('ingredients_text', '').lower()
                        product_name = product.get('product_name', '').lower()
                        labels = [label.lower() for label in product.get('labels_tags', [])]

                        if not ingredients:
                            continue

                        # Check for sugar-free claims
                        has_sugar_free_claim = any(
                            keyword in product_name or any(keyword in label for label in labels)
                            for keyword in sugar_keywords
                        )

                        # Check for hidden sugars
                        has_hidden_sugars = any(sugar in ingredients for sugar in hidden_sugars)

                        # Label: 1 if misleading claim (claims sugar-free but has hidden sugars), 0 otherwise
                        if has_sugar_free_claim and has_hidden_sugars:
                            label = 1  # Misleading
                        elif has_sugar_free_claim and not has_hidden_sugars:
                            label = 0  # Legitimate sugar-free
                        elif not has_sugar_free_claim:
                            label = 0  # No claim, so not misleading
                        else:
                            continue  # Skip unclear cases

                        data.append({
                            'ingredients': ingredients,
                            'product_name': product_name,
                            'labels': ' '.join(labels),
                            'has_sugar_free_claim': has_sugar_free_claim,
                            'has_hidden_sugars': has_hidden_sugars,
                            'misleading': label
                        })

            except Exception as e:
                print(f"Error fetching {category}: {e}")
                continue

        df = pd.DataFrame(data)
        print(f"Collected {len(df)} training samples")
        return df

    def preprocess_data(self, df: pd.DataFrame) -> tuple:
        """Preprocess the training data."""
        # Combine text features
        df['text'] = df['ingredients'] + ' ' + df['product_name'] + ' ' + df['labels']

        # Split data
        X = df['text']
        y = df['misleading']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Vectorize text
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        return X_train_vec, X_test_vec, y_train, y_test, vectorizer

    def train_model(self, X_train, y_train, vectorizer):
        """Train the classification model."""
        print("Training Random Forest classifier...")

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X_train, y_train)
        return model

    def evaluate_model(self, model, X_test, y_test):
        """Evaluate the trained model."""
        print("Evaluating model...")

        y_pred = model.predict(X_test)

        print("Classification Report:")
        print(classification_report(y_test, y_pred))

        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))

    def save_model(self, model, vectorizer):
        """Save the trained model and vectorizer."""
        joblib.dump(model, self.model_path)
        joblib.dump(vectorizer, self.vectorizer_path)
        print(f"Model saved to {self.model_path}")
        print(f"Vectorizer saved to {self.vectorizer_path}")

    def run_training_pipeline(self):
        """Run the complete training pipeline."""
        print("Starting ingredient analysis model training...")

        # Collect data
        df = self.collect_training_data()

        if len(df) < 10:
            print("Insufficient training data. Need at least 10 samples.")
            return

        # Preprocess
        X_train, X_test, y_train, y_test, vectorizer = self.preprocess_data(df)

        # Train
        model = self.train_model(X_train, y_train, vectorizer)

        # Evaluate
        self.evaluate_model(model, X_test, y_test)

        # Save
        self.save_model(model, vectorizer)

        print("Training completed successfully!")


if __name__ == "__main__":
    trainer = IngredientModelTrainer()
    trainer.run_training_pipeline()