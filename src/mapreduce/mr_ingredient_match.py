from mrjob.job import MRJob
import json
import os
import re

class MRIngredientMatch(MRJob):
    """Matches recipe ingredients in TripAdvisor restaurant comments."""
    
    def mapper_init(self):
        # Load ingredients list from shipped file or local seed file
        self.ingredients = set()
        paths = ['ingredients.json', 'src/crawler/seed/ingredients.json', '../seed/ingredients.json']
        loaded = False
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            ing = item.get('strIngredient') or item.get('name')
                            if ing:
                                self.ingredients.add(ing.lower().strip())
                    loaded = True
                    break
                except Exception:
                    pass
        
        # If still empty, use a fallback list of common ingredients
        if not loaded or not self.ingredients:
            self.ingredients = {
                "beef", "chicken", "pork", "duck", "shrimp", "prawn", "fish", "crab", "squid", "lobster",
                "rice", "noodle", "noodles", "egg", "eggs", "cheese", "garlic", "ginger", "onion", "chili",
                "pepper", "salt", "sugar", "sauce", "basil", "mint", "cilantro", "lime", "lemon", "coconut"
            }
        
        # Build a single compiled regex pattern for all ingredients
        # Sort by length descending to match longer multi-word ingredients first
        sorted_ingredients = sorted(self.ingredients, key=len, reverse=True)
        escaped_ingredients = [re.escape(ing) for ing in sorted_ingredients if ing]
        self.pattern = re.compile(r'\b(' + '|'.join(escaped_ingredients) + r')\b')

    def mapper(self, _, line):
        try:
            data = json.loads(line)
            # Only process restaurants (they have reviews)
            reviews = data.get('reviews', [])
            if not reviews:
                return
                
            for review in reviews:
                comment = review.get('comment')
                if not comment:
                    continue
                
                comment_lower = comment.lower()
                matches = self.pattern.findall(comment_lower)
                for match in matches:
                    yield match, 1
        except Exception:
            pass

    def combiner(self, ingredient, counts):
        yield ingredient, sum(counts)

    def reducer(self, ingredient, counts):
        yield ingredient, sum(counts)

if __name__ == '__main__':
    MRIngredientMatch.run()
