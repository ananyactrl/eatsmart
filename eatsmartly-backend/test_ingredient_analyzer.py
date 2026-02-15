"""
Test script for Ingredient Analysis Agent.
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.ingredient_analyzer import IngredientAnalysisAgent


def test_ingredient_analysis():
    """Test the ingredient analysis functionality."""

    # Initialize agent
    analyzer = IngredientAnalysisAgent()

    # Test cases
    test_cases = [
        {
            "name": "Sugar-Free Cola",
            "ingredients": "Carbonated water, caramel color, phosphoric acid, natural flavors, caffeine, sucralose, acesulfame potassium",
            "expected_warnings": True
        },
        {
            "name": "Organic Honey",
            "ingredients": "Organic honey",
            "expected_warnings": False
        },
        {
            "name": "Fruit Yogurt",
            "ingredients": "Milk, fruit puree, sugar, pectin, natural flavors",
            "expected_warnings": False
        },
        {
            "name": "Zero Sugar Energy Drink",
            "ingredients": "Carbonated water, citric acid, natural flavors, sucralose, acesulfame potassium, caffeine, niacinamide",
            "expected_warnings": True
        }
    ]

    print("Testing Ingredient Analysis Agent")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 30)

        result = analyzer.analyze_ingredients(
            ingredients=test_case['ingredients'],
            product_name=test_case['name'],
            labels=[]
        )

        print(f"Ingredients: {test_case['ingredients'][:100]}...")
        print(f"Sugar Score: {result['sugar_score']}")
        print(f"Analysis: {result['analysis']}")

        if result['warnings']:
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning['message']} (Severity: {warning['severity']})")

        if result['health_warnings']:
            print("Health Warnings:")
            for warning in result['health_warnings']:
                print(f"  - {warning['message']} (Severity: {warning['severity']})")

        if result['ml_analysis']:
            print(f"ML Analysis: {result['ml_analysis']}")

        # Check if warnings match expectation
        has_warnings = len(result['warnings']) > 0 or len(result['health_warnings']) > 0
        expected = test_case['expected_warnings']

        if has_warnings == expected:
            print("✅ PASS")
        else:
            print(f"❌ FAIL - Expected warnings: {expected}, Got: {has_warnings}")


if __name__ == "__main__":
    test_ingredient_analysis()