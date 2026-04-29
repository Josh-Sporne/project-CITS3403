"""Seed the Plate Theory database with rich sample data for demos."""

from datetime import date, timedelta, timezone, datetime
import random

from app import create_app, db
from app.models import (
    Comment, Follower, MealPlan, MealPlanItem,
    PantryItem, Rating, Recipe, RecipeIngredient,
    SavedRecipe, User,
)

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ──────────────────────────────────────────────────
    # 1. USERS  (8 users with varied bios)
    # ──────────────────────────────────────────────────
    user_defs = [
        ("rania",   "rania@example.com",   "Obsessed with Asian fusion and late-night noodle bowls."),
        ("josh",    "josh@example.com",    "Weekend BBQ warrior and taco Tuesday devotee."),
        ("yifeng",  "yifeng@example.com",  "Plant-based chef exploring bold flavours without compromise."),
        ("olivia",  "olivia@example.com",  "Meal-prep queen. If it takes over 30 min on a weeknight, skip it."),
        ("marcus",  "marcus@example.com",  "French technique, global ingredients. Butter makes everything better."),
        ("priya",   "priya@example.com",   "Spice is life. South Indian home cooking with a modern twist."),
        ("leon",    "leon@example.com",    "Gym-bro eats — high protein, low drama, always delicious."),
        ("sofia",   "sofia@example.com",   "Pastry lover. If it involves dough, I'm there."),
    ]

    users = {}
    for username, email, bio in user_defs:
        u = User(username=username, email=email, bio=bio)
        u.set_password("password123")
        db.session.add(u)
        users[username] = u

    db.session.flush()

    rania  = users["rania"]
    josh   = users["josh"]
    yifeng = users["yifeng"]
    olivia = users["olivia"]
    marcus = users["marcus"]
    priya  = users["priya"]
    leon   = users["leon"]
    sofia  = users["sofia"]

    # ──────────────────────────────────────────────────
    # 2. RECIPES  (30 recipes, all categories)
    # ──────────────────────────────────────────────────
    recipe_data = [

        # ── BREAKFAST ──────────────────────────────────
        {
            "title": "Fluffy Banana Pancakes",
            "description": "Light and fluffy pancakes with natural banana sweetness. A weekend breakfast favourite that kids and adults both love.",
            "instructions": (
                "1. Mash bananas in a bowl and whisk in eggs and milk.\n"
                "2. Stir in flour and baking powder until just combined — a few lumps are fine.\n"
                "3. Heat a buttered pan over medium heat, pour ¼-cup scoops, and cook until bubbles form.\n"
                "4. Flip and cook another 1–2 minutes until golden.\n"
                "5. Serve stacked with maple syrup."
            ),
            "cooking_time": 20, "category": "breakfast", "creator": olivia,
            "ingredients": [
                ("flour","1.5","cups"), ("banana","2",""), ("eggs","2",""),
                ("milk","1","cup"), ("baking powder","1","tsp"), ("maple syrup","2","tbsp"),
            ],
        },
        {
            "title": "Overnight Berry Oats",
            "description": "No-cook overnight oats loaded with berries and chia seeds. Prep the night before and grab it on your way out.",
            "instructions": (
                "1. Combine oats, almond milk, and chia seeds in a jar.\n"
                "2. Top with mixed berries and a drizzle of honey.\n"
                "3. Seal and refrigerate overnight (at least 6 hours).\n"
                "4. Stir in the morning and enjoy cold."
            ),
            "cooking_time": 5, "category": "breakfast", "creator": olivia,
            "ingredients": [
                ("oats","0.5","cup"), ("almond milk","0.75","cup"), ("chia seeds","1","tbsp"),
                ("mixed berries","0.5","cup"), ("honey","1","tsp"),
            ],
        },
        {
            "title": "Shakshuka",
            "description": "Eggs poached in a spiced tomato and pepper sauce, finished with crumbled feta. Serve straight from the skillet with crusty bread.",
            "instructions": (
                "1. Sauté diced onion and garlic in olive oil until softened.\n"
                "2. Add cumin and paprika, stir for 30 seconds, then pour in canned tomatoes.\n"
                "3. Simmer for 10 minutes until the sauce thickens.\n"
                "4. Make wells, crack in eggs, cover, and cook 5–7 minutes until whites set.\n"
                "5. Crumble feta on top and serve."
            ),
            "cooking_time": 25, "category": "breakfast", "creator": olivia,
            "ingredients": [
                ("eggs","4",""), ("canned tomatoes","1","can"), ("onion","1",""),
                ("garlic","2","cloves"), ("cumin","1","tsp"), ("paprika","1","tsp"),
                ("feta cheese","50","g"),
            ],
        },
        {
            "title": "Masala Omelette",
            "description": "A spiced Indian-style omelette with green chilli, coriander, and onion. Breakfast that actually wakes you up.",
            "instructions": (
                "1. Beat eggs with salt, chilli, coriander, and diced onion.\n"
                "2. Heat oil in a pan over medium-high heat.\n"
                "3. Pour in egg mixture and cook until edges set.\n"
                "4. Fold in half and serve with toast or roti."
            ),
            "cooking_time": 10, "category": "breakfast", "creator": priya,
            "ingredients": [
                ("eggs","3",""), ("green chilli","1",""), ("coriander","2","tbsp"),
                ("onion","0.5",""), ("salt","1","pinch"), ("oil","1","tsp"),
            ],
        },
        {
            "title": "Avocado Toast with Poached Egg",
            "description": "Creamy avocado on sourdough toast topped with a perfectly poached egg and chilli flakes.",
            "instructions": (
                "1. Toast sourdough slices until golden.\n"
                "2. Mash avocado with lemon juice, salt, and pepper.\n"
                "3. Bring a pot of water to a simmer. Crack egg into a cup then slide into water. Poach 3 minutes.\n"
                "4. Spread avocado on toast, top with egg and a pinch of chilli flakes."
            ),
            "cooking_time": 12, "category": "breakfast", "creator": marcus,
            "ingredients": [
                ("sourdough bread","2","slices"), ("avocado","1",""), ("egg","1",""),
                ("lemon juice","1","tsp"), ("chilli flakes","1","pinch"), ("salt","1","pinch"),
            ],
        },

        # ── QUICK MEALS ────────────────────────────────
        {
            "title": "Garlic Butter Noodles",
            "description": "Buttery, garlicky noodles tossed in soy sauce and sesame oil. Ready in 15 minutes — the ultimate lazy dinner.",
            "instructions": (
                "1. Cook egg noodles according to packet directions, then drain.\n"
                "2. Melt butter in the same pot over medium heat and sauté minced garlic for 1 minute.\n"
                "3. Toss noodles back in with soy sauce and sesame oil.\n"
                "4. Garnish with sliced green onion and serve immediately."
            ),
            "cooking_time": 15, "category": "quick-meals", "creator": rania,
            "ingredients": [
                ("egg noodles","200","g"), ("butter","2","tbsp"), ("garlic","4","cloves"),
                ("soy sauce","2","tbsp"), ("sesame oil","1","tsp"), ("green onion","2","stalks"),
            ],
        },
        {
            "title": "Egg Fried Rice",
            "description": "Classic egg fried rice with crispy edges and tender vegetables. Best made with day-old rice for the perfect texture.",
            "instructions": (
                "1. Heat sesame oil in a wok over high heat and scramble the eggs; set aside.\n"
                "2. Stir-fry diced carrot and peas for 2 minutes.\n"
                "3. Add cold cooked rice, breaking up clumps, and fry until heated through.\n"
                "4. Return eggs, add soy sauce, toss everything together.\n"
                "5. Top with sliced green onion."
            ),
            "cooking_time": 12, "category": "quick-meals", "creator": rania,
            "ingredients": [
                ("cooked rice","3","cups"), ("eggs","2",""), ("soy sauce","2","tbsp"),
                ("sesame oil","1","tbsp"), ("peas","0.5","cup"), ("carrot","1",""),
                ("green onion","2","stalks"),
            ],
        },
        {
            "title": "Spicy Tofu Stir Fry",
            "description": "Crispy pan-fried tofu in a sweet-and-spicy sriracha glaze with colourful vegetables. Serve over steamed rice.",
            "instructions": (
                "1. Press tofu, cube it, and pan-fry in oil until golden on all sides.\n"
                "2. Remove tofu; stir-fry sliced bell pepper, broccoli, and garlic for 3 minutes.\n"
                "3. Whisk soy sauce and sriracha together and pour into the wok.\n"
                "4. Return tofu, toss to coat, and serve over rice."
            ),
            "cooking_time": 18, "category": "quick-meals", "creator": rania,
            "ingredients": [
                ("firm tofu","1","block"), ("bell pepper","1",""), ("broccoli","1","cup"),
                ("soy sauce","2","tbsp"), ("sriracha","1","tbsp"), ("garlic","3","cloves"),
                ("rice","1.5","cups"),
            ],
        },
        {
            "title": "Caprese Quesadilla",
            "description": "A crispy quesadilla filled with fresh mozzarella, tomato, and basil. Italian meets Mexican in under 10 minutes.",
            "instructions": (
                "1. Layer mozzarella slices, tomato, and basil on one tortilla half.\n"
                "2. Fold and cook in a dry pan over medium heat for 2–3 minutes each side until golden.\n"
                "3. Slice into wedges and serve with a drizzle of balsamic glaze."
            ),
            "cooking_time": 10, "category": "quick-meals", "creator": marcus,
            "ingredients": [
                ("flour tortilla","2",""), ("mozzarella","100","g"), ("tomato","1",""),
                ("basil","6","leaves"), ("balsamic glaze","1","tbsp"),
            ],
        },
        {
            "title": "Pesto Pasta",
            "description": "Five-ingredient pasta that tastes like you tried. Vibrant green pesto coats every strand in under 15 minutes.",
            "instructions": (
                "1. Cook pasta in salted boiling water until al dente.\n"
                "2. Drain, reserving ¼ cup pasta water.\n"
                "3. Toss hot pasta with pesto and pasta water until glossy.\n"
                "4. Serve topped with parmesan and pine nuts."
            ),
            "cooking_time": 15, "category": "quick-meals", "creator": marcus,
            "ingredients": [
                ("pasta","250","g"), ("pesto","4","tbsp"), ("parmesan","0.25","cup"),
                ("pine nuts","2","tbsp"), ("olive oil","1","tbsp"),
            ],
        },

        # ── DINNER ─────────────────────────────────────
        {
            "title": "Creamy Tomato Pasta",
            "description": "A velvety tomato-cream sauce over al-dente pasta, topped with fresh basil and parmesan. Pure comfort food in 25 minutes.",
            "instructions": (
                "1. Cook pasta in salted boiling water until al dente; reserve ½ cup pasta water.\n"
                "2. Sauté garlic in olive oil for 1 minute, then add canned tomatoes and simmer 10 minutes.\n"
                "3. Stir in cream and a splash of pasta water.\n"
                "4. Toss in drained pasta, top with parmesan and torn basil."
            ),
            "cooking_time": 25, "category": "dinner", "creator": josh,
            "ingredients": [
                ("pasta","250","g"), ("canned tomatoes","1","can"), ("garlic","3","cloves"),
                ("cream","0.5","cup"), ("basil","1","handful"), ("parmesan","0.25","cup"),
                ("olive oil","1","tbsp"),
            ],
        },
        {
            "title": "Thai Green Curry",
            "description": "Aromatic coconut-based green curry with tender chicken and bamboo shoots. Tastes like takeout, but better.",
            "instructions": (
                "1. Sauté green curry paste in a splash of coconut milk for 2 minutes.\n"
                "2. Add sliced chicken thigh and cook until no longer pink.\n"
                "3. Pour in remaining coconut milk and bamboo shoots; simmer 15 minutes.\n"
                "4. Stir in fresh basil leaves.\n"
                "5. Serve over steamed jasmine rice."
            ),
            "cooking_time": 30, "category": "dinner", "creator": josh,
            "ingredients": [
                ("chicken thigh","400","g"), ("coconut milk","1","can"),
                ("green curry paste","3","tbsp"), ("bamboo shoots","0.5","cup"),
                ("basil","1","handful"), ("rice","1.5","cups"),
            ],
        },
        {
            "title": "Beef Tacos",
            "description": "Seasoned ground beef tacos with all the classic toppings. A crowd-pleasing dinner that's on the table in 20 minutes.",
            "instructions": (
                "1. Brown ground beef in a skillet, breaking it apart as it cooks.\n"
                "2. Season with cumin, salt, and pepper; stir for another minute.\n"
                "3. Warm taco shells in the oven for 2 minutes.\n"
                "4. Fill shells with beef, then top with lettuce, tomato, cheese, and sour cream."
            ),
            "cooking_time": 20, "category": "dinner", "creator": josh,
            "ingredients": [
                ("ground beef","500","g"), ("taco shells","8",""), ("lettuce","1","cup"),
                ("tomato","2",""), ("cheese","0.5","cup"), ("sour cream","3","tbsp"),
                ("cumin","1","tsp"),
            ],
        },
        {
            "title": "Butter Chicken",
            "description": "Tender chicken pieces simmered in a rich, buttery tomato-cream sauce. The most-requested dish at every dinner party.",
            "instructions": (
                "1. Marinate chicken in yoghurt, garam masala, and ginger-garlic paste for 20 min.\n"
                "2. Pan-fry chicken until charred at the edges; set aside.\n"
                "3. In the same pan, sauté onion, then add tomato purée and spices; cook 10 min.\n"
                "4. Blend sauce until smooth. Return chicken, add cream, and simmer 10 min."
            ),
            "cooking_time": 45, "category": "dinner", "creator": priya,
            "ingredients": [
                ("chicken breast","500","g"), ("yoghurt","3","tbsp"), ("garam masala","2","tsp"),
                ("tomato purée","1","cup"), ("cream","0.5","cup"), ("butter","2","tbsp"),
                ("onion","1",""), ("garlic","3","cloves"), ("ginger","1","tsp"),
            ],
        },
        {
            "title": "Mushroom Risotto",
            "description": "Silky arborio rice slowly cooked with white wine and mixed mushrooms, finished with a mountain of parmesan.",
            "instructions": (
                "1. Sauté shallots and garlic in butter. Add arborio rice and toast 2 minutes.\n"
                "2. Add white wine and stir until absorbed.\n"
                "3. Add warm stock one ladle at a time, stirring constantly, for 20 minutes.\n"
                "4. Fold in sautéed mushrooms and parmesan. Rest 2 minutes and serve."
            ),
            "cooking_time": 35, "category": "dinner", "creator": marcus,
            "ingredients": [
                ("arborio rice","300","g"), ("mixed mushrooms","300","g"), ("white wine","150","ml"),
                ("vegetable stock","1","L"), ("parmesan","0.5","cup"), ("shallot","2",""),
                ("garlic","2","cloves"), ("butter","3","tbsp"),
            ],
        },
        {
            "title": "Lamb Kofta with Yoghurt Sauce",
            "description": "Spiced lamb kofta skewers grilled to perfection, served with cooling mint yoghurt and flatbreads.",
            "instructions": (
                "1. Mix lamb mince with cumin, coriander, chilli, garlic, and fresh mint.\n"
                "2. Shape around skewers and refrigerate 15 min.\n"
                "3. Grill on high heat 4 min each side.\n"
                "4. Whisk yoghurt with mint, lemon, and garlic for the sauce.\n"
                "5. Serve kofta with sauce and warm flatbreads."
            ),
            "cooking_time": 30, "category": "dinner", "creator": priya,
            "ingredients": [
                ("lamb mince","400","g"), ("cumin","1","tsp"), ("coriander","1","tsp"),
                ("chilli","1",""), ("garlic","3","cloves"), ("mint","1","handful"),
                ("yoghurt","0.5","cup"), ("flatbreads","4",""), ("lemon","1",""),
            ],
        },

        # ── VEGAN ──────────────────────────────────────
        {
            "title": "Buddha Bowl",
            "description": "A nourishing bowl of roasted sweet potato, chickpeas, and kale drizzled with creamy lemon-tahini dressing.",
            "instructions": (
                "1. Roast cubed sweet potato and drained chickpeas at 200 °C for 20 minutes.\n"
                "2. Cook quinoa according to packet directions.\n"
                "3. Massage kale with a pinch of salt until tender.\n"
                "4. Whisk tahini with lemon juice and a splash of water.\n"
                "5. Assemble bowls and drizzle with dressing."
            ),
            "cooking_time": 25, "category": "vegan", "creator": yifeng,
            "ingredients": [
                ("quinoa","0.75","cup"), ("chickpeas","1","can"), ("sweet potato","1","large"),
                ("kale","2","cups"), ("tahini","2","tbsp"), ("lemon","1",""),
            ],
        },
        {
            "title": "Lentil Soup",
            "description": "Hearty red-lentil soup with warming cumin and a squeeze of lemon. Freezes beautifully for easy meal prep.",
            "instructions": (
                "1. Sauté diced onion, carrot, and celery in olive oil for 5 minutes.\n"
                "2. Add cumin and stir for 30 seconds.\n"
                "3. Pour in red lentils and vegetable broth; bring to a boil.\n"
                "4. Reduce heat and simmer 25 minutes until lentils are soft.\n"
                "5. Squeeze in lemon juice and season to taste."
            ),
            "cooking_time": 35, "category": "vegan", "creator": yifeng,
            "ingredients": [
                ("red lentils","1","cup"), ("onion","1",""), ("carrot","2",""),
                ("celery","2","stalks"), ("cumin","1","tsp"), ("vegetable broth","4","cups"),
                ("lemon","1",""),
            ],
        },
        {
            "title": "Mango Coconut Smoothie Bowl",
            "description": "Thick blended mango and coconut smoothie topped with granola, banana, and toasted coconut flakes.",
            "instructions": (
                "1. Blend frozen mango, coconut milk, and banana until thick and smooth.\n"
                "2. Pour into a bowl.\n"
                "3. Top with granola, sliced banana, and coconut flakes."
            ),
            "cooking_time": 8, "category": "vegan", "creator": yifeng,
            "ingredients": [
                ("frozen mango","1.5","cups"), ("coconut milk","0.5","cup"), ("banana","1",""),
                ("granola","0.25","cup"), ("coconut flakes","2","tbsp"),
            ],
        },
        {
            "title": "Black Bean Tacos",
            "description": "Smoky black bean tacos with avocado, pickled red onion, and a squeeze of lime. Vegan and proud.",
            "instructions": (
                "1. Cook black beans with smoked paprika, cumin, and garlic for 5 minutes.\n"
                "2. Pickle thinly sliced red onion in lime juice for 10 minutes.\n"
                "3. Mash avocado with salt and lime.\n"
                "4. Fill warm tortillas with beans, avocado, pickled onion, and coriander."
            ),
            "cooking_time": 20, "category": "vegan", "creator": yifeng,
            "ingredients": [
                ("black beans","1","can"), ("corn tortillas","8",""), ("avocado","2",""),
                ("red onion","1",""), ("lime","2",""), ("smoked paprika","1","tsp"),
                ("coriander","1","handful"), ("cumin","1","tsp"),
            ],
        },

        # ── HIGH PROTEIN ───────────────────────────────
        {
            "title": "Chicken Teriyaki Bowl",
            "description": "Juicy chicken glazed in homemade teriyaki sauce over fluffy rice with steamed broccoli. A high-protein weeknight staple.",
            "instructions": (
                "1. Slice chicken breast and cook in a hot pan until golden.\n"
                "2. Pour teriyaki sauce over chicken and simmer until it thickens.\n"
                "3. Steam broccoli until bright green and tender-crisp.\n"
                "4. Serve chicken and broccoli over rice, sprinkled with sesame seeds and green onion."
            ),
            "cooking_time": 25, "category": "high-protein", "creator": josh,
            "ingredients": [
                ("chicken breast","300","g"), ("teriyaki sauce","3","tbsp"), ("rice","1.5","cups"),
                ("broccoli","1","cup"), ("sesame seeds","1","tsp"), ("green onion","2","stalks"),
            ],
        },
        {
            "title": "Tofu Scramble",
            "description": "A protein-packed vegan take on scrambled eggs. Turmeric gives it that classic golden colour.",
            "instructions": (
                "1. Crumble firm tofu into a pan with a little oil.\n"
                "2. Add turmeric, nutritional yeast, and garlic; stir well.\n"
                "3. Toss in diced bell pepper and spinach, cooking until wilted.\n"
                "4. Season with salt and pepper, and serve warm."
            ),
            "cooking_time": 15, "category": "high-protein", "creator": josh,
            "ingredients": [
                ("firm tofu","1","block"), ("spinach","2","cups"), ("bell pepper","1",""),
                ("nutritional yeast","2","tbsp"), ("turmeric","0.5","tsp"), ("garlic","2","cloves"),
            ],
        },
        {
            "title": "Salmon & Quinoa Power Bowl",
            "description": "Pan-seared salmon over protein-rich quinoa with edamame, cucumber, and a sesame-ginger dressing.",
            "instructions": (
                "1. Cook quinoa and let cool slightly.\n"
                "2. Season salmon with salt, pepper, and soy sauce; pan-sear skin-side down for 4 min, flip, and cook 2 more min.\n"
                "3. Whisk sesame oil, soy sauce, ginger, and rice vinegar for dressing.\n"
                "4. Assemble bowls and drizzle with dressing."
            ),
            "cooking_time": 20, "category": "high-protein", "creator": leon,
            "ingredients": [
                ("salmon fillet","2",""), ("quinoa","0.75","cup"), ("edamame","0.5","cup"),
                ("cucumber","1",""), ("soy sauce","2","tbsp"), ("sesame oil","1","tbsp"),
                ("ginger","1","tsp"), ("rice vinegar","1","tbsp"),
            ],
        },
        {
            "title": "Greek Chicken Wrap",
            "description": "Grilled lemon-herb chicken with tzatziki, cucumber, and tomato in a warm flatbread. Meal prep for 4 days straight.",
            "instructions": (
                "1. Marinate chicken breast in lemon juice, olive oil, oregano, and garlic for 30 min.\n"
                "2. Grill 6 min each side until cooked through; slice.\n"
                "3. Warm flatbreads and spread with tzatziki.\n"
                "4. Fill with chicken, cucumber, tomato, and red onion. Roll and serve."
            ),
            "cooking_time": 20, "category": "high-protein", "creator": leon,
            "ingredients": [
                ("chicken breast","400","g"), ("flatbreads","4",""), ("tzatziki","4","tbsp"),
                ("cucumber","1",""), ("tomato","2",""), ("red onion","0.5",""),
                ("lemon","1",""), ("oregano","1","tsp"),
            ],
        },

        # ── VEGETARIAN ─────────────────────────────────
        {
            "title": "Margherita Pizza",
            "description": "Thin-crust pizza with san marzano tomato sauce, fresh buffalo mozzarella, and basil. Simple is best.",
            "instructions": (
                "1. Stretch pizza dough into a thin round.\n"
                "2. Spread tomato sauce, add torn mozzarella, and bake at 250 °C for 8–10 minutes.\n"
                "3. Top with fresh basil leaves and a drizzle of olive oil."
            ),
            "cooking_time": 25, "category": "vegetarian", "creator": marcus,
            "ingredients": [
                ("pizza dough","1","ball"), ("tomato sauce","0.5","cup"), ("mozzarella","150","g"),
                ("basil","8","leaves"), ("olive oil","1","tbsp"),
            ],
        },
        {
            "title": "Spinach & Feta Stuffed Peppers",
            "description": "Roasted red peppers filled with herbed spinach, feta, and brown rice. Colourful, satisfying, and freezer-friendly.",
            "instructions": (
                "1. Halve and deseed peppers; roast cut-side up at 200 °C for 15 min.\n"
                "2. Cook brown rice; mix with sautéed spinach, feta, garlic, and herbs.\n"
                "3. Fill pepper halves with rice mixture.\n"
                "4. Return to oven for 10 more minutes."
            ),
            "cooking_time": 40, "category": "vegetarian", "creator": sofia,
            "ingredients": [
                ("red peppers","4",""), ("brown rice","1","cup"), ("spinach","2","cups"),
                ("feta cheese","100","g"), ("garlic","2","cloves"), ("mixed herbs","1","tsp"),
            ],
        },

        # ── DESSERT ─────────────────────────────────────
        {
            "title": "Fudgy Brownies",
            "description": "Rich, fudgy brownies with a crackly top and molten centre. The secret is slightly under-baking them.",
            "instructions": (
                "1. Melt dark chocolate and butter together over a double boiler.\n"
                "2. Whisk in sugar, then eggs one at a time, followed by vanilla.\n"
                "3. Fold in flour and cocoa powder — do not overmix.\n"
                "4. Pour into a lined baking tin and bake at 180 °C for 22–25 minutes.\n"
                "5. Cool completely before slicing."
            ),
            "cooking_time": 35, "category": "dessert", "creator": olivia,
            "ingredients": [
                ("dark chocolate","200","g"), ("butter","0.5","cup"), ("sugar","1","cup"),
                ("eggs","3",""), ("flour","0.5","cup"), ("vanilla extract","1","tsp"),
                ("cocoa powder","2","tbsp"),
            ],
        },
        {
            "title": "Tropical Fruit Salad",
            "description": "A refreshing medley of mango, pineapple, kiwi, and passion fruit with a zesty lime-mint dressing.",
            "instructions": (
                "1. Dice mango, pineapple, and kiwi into bite-sized pieces.\n"
                "2. Scoop out passion fruit pulp.\n"
                "3. Toss all fruit together with lime juice and torn mint leaves.\n"
                "4. Chill for 10 minutes before serving."
            ),
            "cooking_time": 10, "category": "dessert", "creator": olivia,
            "ingredients": [
                ("mango","1",""), ("pineapple","1","cup"), ("kiwi","2",""),
                ("passion fruit","2",""), ("lime juice","1","tbsp"), ("mint","6","leaves"),
            ],
        },
        {
            "title": "Classic Crème Brûlée",
            "description": "Silky vanilla custard with a satisfyingly crackly caramelised sugar top. A French classic worth the effort.",
            "instructions": (
                "1. Whisk egg yolks with sugar until pale. Warm cream with vanilla, then slowly add to yolks.\n"
                "2. Strain into ramekins and bake in a water bath at 150 °C for 35 min.\n"
                "3. Chill for at least 2 hours.\n"
                "4. Sprinkle sugar on top and torch until amber and crackling."
            ),
            "cooking_time": 60, "category": "dessert", "creator": marcus,
            "ingredients": [
                ("heavy cream","500","ml"), ("egg yolks","5",""), ("sugar","100","g"),
                ("vanilla","1","bean"), ("caster sugar","4","tbsp"),
            ],
        },
        {
            "title": "Mango Sticky Rice",
            "description": "Thai-style sweet glutinous rice drenched in coconut cream, served alongside ripe mango slices.",
            "instructions": (
                "1. Soak sticky rice for 4 hours, then steam for 20 minutes.\n"
                "2. Mix warm rice with coconut milk, sugar, and salt.\n"
                "3. Let sit 15 minutes to absorb.\n"
                "4. Serve beside sliced fresh mango, drizzled with remaining coconut milk."
            ),
            "cooking_time": 30, "category": "dessert", "creator": rania,
            "ingredients": [
                ("glutinous rice","1","cup"), ("coconut milk","1","can"), ("sugar","3","tbsp"),
                ("mango","2",""), ("salt","0.5","tsp"),
            ],
        },

        # ── ONE POT ─────────────────────────────────────
        {
            "title": "One-Pot Chicken & Rice",
            "description": "Juicy chicken thighs braised directly in seasoned rice. One pot, zero fuss, massive flavour.",
            "instructions": (
                "1. Brown chicken thighs in a heavy pot; remove and set aside.\n"
                "2. Sauté onion and garlic, then stir in rice and spices.\n"
                "3. Nestle chicken back in, pour over stock, cover, and cook 20 minutes on low.\n"
                "4. Rest 5 minutes before fluffing rice and serving."
            ),
            "cooking_time": 35, "category": "one-pot", "creator": olivia,
            "ingredients": [
                ("chicken thigh","4","pieces"), ("basmati rice","1.5","cups"),
                ("onion","1",""), ("garlic","3","cloves"), ("chicken stock","2","cups"),
                ("cumin","1","tsp"), ("paprika","1","tsp"),
            ],
        },
    ]

    recipes = {}
    for rd in recipe_data:
        r = Recipe(
            title=rd["title"],
            description=rd["description"],
            instructions=rd["instructions"],
            cooking_time=rd["cooking_time"],
            category=rd["category"],
            creator_id=rd["creator"].id,
        )
        db.session.add(r)
        db.session.flush()
        r.generate_slug()

        for name, qty, unit in rd["ingredients"]:
            db.session.add(RecipeIngredient(
                recipe_id=r.id, name=name, quantity=qty, unit=unit,
            ))

        recipes[rd["title"]] = r

    db.session.flush()

    # ──────────────────────────────────────────────────
    # 3. RATINGS  (80+ ratings with realistic spread)
    # ──────────────────────────────────────────────────
    # Each user rates ~10 recipes; scores reflect genuine preferences
    rating_data = [
        # rania
        (rania, "Fluffy Banana Pancakes", 5),
        (rania, "Shakshuka", 4),
        (rania, "Thai Green Curry", 5),
        (rania, "Beef Tacos", 4),
        (rania, "Buddha Bowl", 3),
        (rania, "Fudgy Brownies", 5),
        (rania, "Lentil Soup", 4),
        (rania, "Chicken Teriyaki Bowl", 5),
        (rania, "Mango Sticky Rice", 5),
        (rania, "Butter Chicken", 5),

        # josh
        (josh, "Garlic Butter Noodles", 4),
        (josh, "Egg Fried Rice", 5),
        (josh, "Spicy Tofu Stir Fry", 3),
        (josh, "Buddha Bowl", 4),
        (josh, "Overnight Berry Oats", 3),
        (josh, "Fudgy Brownies", 5),
        (josh, "Tropical Fruit Salad", 4),
        (josh, "Lentil Soup", 3),
        (josh, "One-Pot Chicken & Rice", 5),
        (josh, "Greek Chicken Wrap", 4),

        # yifeng
        (yifeng, "Fluffy Banana Pancakes", 4),
        (yifeng, "Garlic Butter Noodles", 5),
        (yifeng, "Creamy Tomato Pasta", 4),
        (yifeng, "Shakshuka", 5),
        (yifeng, "Tofu Scramble", 5),
        (yifeng, "Tropical Fruit Salad", 5),
        (yifeng, "Overnight Berry Oats", 4),
        (yifeng, "Spicy Tofu Stir Fry", 5),
        (yifeng, "Mango Coconut Smoothie Bowl", 5),
        (yifeng, "Black Bean Tacos", 5),

        # olivia
        (olivia, "Thai Green Curry", 4),
        (olivia, "Beef Tacos", 5),
        (olivia, "Egg Fried Rice", 4),
        (olivia, "Chicken Teriyaki Bowl", 4),
        (olivia, "Buddha Bowl", 5),
        (olivia, "Lentil Soup", 4),
        (olivia, "Pesto Pasta", 5),
        (olivia, "Caprese Quesadilla", 4),
        (olivia, "Margherita Pizza", 5),
        (olivia, "Spinach & Feta Stuffed Peppers", 4),

        # marcus
        (marcus, "Shakshuka", 4),
        (marcus, "Creamy Tomato Pasta", 5),
        (marcus, "Mushroom Risotto", 5),
        (marcus, "Thai Green Curry", 4),
        (marcus, "Butter Chicken", 5),
        (marcus, "Lamb Kofta with Yoghurt Sauce", 5),
        (marcus, "Classic Crème Brûlée", 5),
        (marcus, "Fudgy Brownies", 4),
        (marcus, "Avocado Toast with Poached Egg", 4),
        (marcus, "Buddha Bowl", 3),

        # priya
        (priya, "Butter Chicken", 5),
        (priya, "Lamb Kofta with Yoghurt Sauce", 5),
        (priya, "Masala Omelette", 5),
        (priya, "Shakshuka", 4),
        (priya, "Lentil Soup", 4),
        (priya, "Black Bean Tacos", 3),
        (priya, "Buddha Bowl", 4),
        (priya, "Chicken Teriyaki Bowl", 4),
        (priya, "Mango Sticky Rice", 5),
        (priya, "Tropical Fruit Salad", 4),

        # leon
        (leon, "Salmon & Quinoa Power Bowl", 5),
        (leon, "Greek Chicken Wrap", 5),
        (leon, "Chicken Teriyaki Bowl", 5),
        (leon, "Tofu Scramble", 4),
        (leon, "Egg Fried Rice", 4),
        (leon, "One-Pot Chicken & Rice", 5),
        (leon, "Beef Tacos", 5),
        (leon, "Spicy Tofu Stir Fry", 4),
        (leon, "Buddha Bowl", 3),
        (leon, "Pesto Pasta", 4),

        # sofia
        (sofia, "Fudgy Brownies", 5),
        (sofia, "Classic Crème Brûlée", 5),
        (sofia, "Tropical Fruit Salad", 4),
        (sofia, "Mango Sticky Rice", 5),
        (sofia, "Fluffy Banana Pancakes", 5),
        (sofia, "Overnight Berry Oats", 4),
        (sofia, "Spinach & Feta Stuffed Peppers", 5),
        (sofia, "Margherita Pizza", 5),
        (sofia, "Avocado Toast with Poached Egg", 4),
        (sofia, "Shakshuka", 4),
    ]

    for user, title, score in rating_data:
        db.session.add(Rating(
            user_id=user.id, recipe_id=recipes[title].id, score=score,
        ))

    # ──────────────────────────────────────────────────
    # 4. COMMENTS  (40 comments across 20 recipes)
    # ──────────────────────────────────────────────────
    comment_data = [
        (rania,  "Thai Green Curry",              "Made this last night, amazing! Even my picky flatmate asked for seconds."),
        (josh,   "Garlic Butter Noodles",         "Added extra garlic — no regrets. This is dangerously good."),
        (olivia, "Egg Fried Rice",                "Perfect for meal prep. I make a double batch every Sunday."),
        (yifeng, "Buddha Bowl",                   "The tahini dressing is everything. I could drink it."),
        (rania,  "Fudgy Brownies",                "Took these to a potluck and came home with an empty tray."),
        (josh,   "Shakshuka",                     "Pro tip: serve with sourdough for dipping. Game changer."),
        (olivia, "Spicy Tofu Stir Fry",           "Didn't think I'd like tofu but this recipe converted me."),
        (yifeng, "Creamy Tomato Pasta",           "Used oat cream to keep it vegan and it was still incredible."),
        (rania,  "Overnight Berry Oats",          "So convenient for early morning classes. Just grab and go."),
        (josh,   "Beef Tacos",                    "Used smoked paprika instead of cumin — highly recommend the swap."),
        (olivia, "Thai Green Curry",              "I added baby corn and it worked perfectly in this."),
        (yifeng, "Lentil Soup",                   "Made a big pot and froze half. Even better reheated the next day."),
        (rania,  "Chicken Teriyaki Bowl",         "The homemade teriyaki glaze makes all the difference."),
        (josh,   "Fluffy Banana Pancakes",        "My kids demolished these in minutes. New weekend tradition."),
        (olivia, "Fudgy Brownies",                "Under-baking tip is legit — gooey centre is perfection."),
        (marcus, "Butter Chicken",                "Restaurant quality, genuinely. I've made this three weeks in a row."),
        (priya,  "Masala Omelette",               "Finally, a recipe that gets the spice level right. Authentic."),
        (leon,   "Salmon & Quinoa Power Bowl",    "My Sunday meal-prep staple. Easy macros, tastes incredible."),
        (sofia,  "Classic Crème Brûlée",          "The torching is therapeutic. Came out perfectly first try."),
        (rania,  "Mango Sticky Rice",             "Brings me right back to Bangkok street food. Absolute comfort dish."),
        (marcus, "Mushroom Risotto",              "Stirring for 20 minutes is worth it. Trust the process."),
        (priya,  "Lamb Kofta with Yoghurt Sauce", "The mint yoghurt really pulls the whole dish together."),
        (leon,   "Greek Chicken Wrap",            "Meal-prepped 4 of these for the week. Held up perfectly in the fridge."),
        (sofia,  "Spinach & Feta Stuffed Peppers","Froze a batch and they reheated brilliantly. Great meal prep."),
        (yifeng, "Mango Coconut Smoothie Bowl",   "This is my go-to after a morning run. Thick and tropical."),
        (josh,   "One-Pot Chicken & Rice",        "Minimal washing up = maximum happiness. A keeper."),
        (olivia, "Pesto Pasta",                   "Five ingredients and it tastes gourmet. How?"),
        (rania,  "Avocado Toast with Poached Egg","Finally mastered the poached egg. This recipe helped a lot."),
        (marcus, "Margherita Pizza",              "Simple done right. The quality of the tomatoes really matters."),
        (yifeng, "Black Bean Tacos",              "The pickled onion takes 10 minutes and is absolutely worth it."),
        (leon,   "Tofu Scramble",                 "High protein, takes 15 minutes. What more could you want?"),
        (sofia,  "Tropical Fruit Salad",          "Light, refreshing, zero guilt. Brought to a BBQ and it vanished."),
        (priya,  "Butter Chicken",                "The marinating step makes a huge difference to the tenderness."),
        (rania,  "Black Bean Tacos",              "Never thought vegan tacos could be this satisfying. Converted."),
        (josh,   "Chicken Teriyaki Bowl",         "This got me into meal prepping. So simple once you nail the sauce."),
        (sofia,  "Mango Sticky Rice",             "My Thai flatmate said it tasted authentic. High praise."),
        (leon,   "Beef Tacos",                    "Easy win for taco night. Kids love assembling their own."),
        (marcus, "Avocado Toast with Poached Egg","The technique notes are really helpful — nail it every time now."),
        (priya,  "Shakshuka",                     "A staple in my household. I add a little harissa for extra depth."),
        (olivia, "One-Pot Chicken & Rice",        "Saved me so much time midweek. The whole family loved it."),
    ]

    for user, title, body in comment_data:
        db.session.add(Comment(
            user_id=user.id, recipe_id=recipes[title].id, body=body,
        ))

    # ──────────────────────────────────────────────────
    # 5. MEAL PLANS  (4 users, varied plans)
    # ──────────────────────────────────────────────────
    today  = date.today()
    monday = today - timedelta(days=today.weekday())

    def make_plan(user, items_def):
        plan = MealPlan(user_id=user.id, week_start=monday)
        db.session.add(plan)
        db.session.flush()
        for day, meal_type, recipe_title_or_text, is_custom in items_def:
            if is_custom:
                item = MealPlanItem(
                    mealplan_id=plan.id, day_of_week=day,
                    meal_type=meal_type, custom_text=recipe_title_or_text,
                )
            else:
                item = MealPlanItem(
                    mealplan_id=plan.id, day_of_week=day,
                    meal_type=meal_type, recipe_id=recipes[recipe_title_or_text].id,
                )
            db.session.add(item)

    make_plan(rania, [
        (0, "breakfast", "Overnight Berry Oats",     False),
        (0, "dinner",    "Thai Green Curry",          False),
        (1, "breakfast", "Masala Omelette",           False),
        (1, "lunch",     "Garlic Butter Noodles",     False),
        (2, "dinner",    "Creamy Tomato Pasta",        False),
        (3, "lunch",     "Leftovers",                 True),
        (3, "dinner",    "Mango Sticky Rice",          False),
        (4, "dinner",    "Beef Tacos",                False),
        (5, "breakfast", "Shakshuka",                 False),
        (5, "dinner",    "Butter Chicken",             False),
        (6, "breakfast", "Fluffy Banana Pancakes",     False),
        (6, "dinner",    "Eating out 🍣",              True),
    ])

    make_plan(josh, [
        (0, "dinner",    "Chicken Teriyaki Bowl",     False),
        (1, "lunch",     "Greek Chicken Wrap",        False),
        (2, "dinner",    "Beef Tacos",                False),
        (3, "dinner",    "One-Pot Chicken & Rice",    False),
        (4, "lunch",     "Egg Fried Rice",            False),
        (5, "dinner",    "Thai Green Curry",          False),
        (6, "lunch",     "Meal prep Sunday 🥡",       True),
    ])

    make_plan(yifeng, [
        (0, "breakfast", "Mango Coconut Smoothie Bowl", False),
        (1, "dinner",    "Black Bean Tacos",           False),
        (2, "dinner",    "Buddha Bowl",                False),
        (3, "lunch",     "Lentil Soup",               False),
        (4, "dinner",    "Spicy Tofu Stir Fry",       False),
        (5, "breakfast", "Overnight Berry Oats",      False),
        (6, "dinner",    "Tofu Scramble",             False),
    ])

    make_plan(leon, [
        (0, "breakfast", "Avocado Toast with Poached Egg", False),
        (1, "lunch",     "Salmon & Quinoa Power Bowl",      False),
        (2, "lunch",     "Greek Chicken Wrap",              False),
        (3, "dinner",    "One-Pot Chicken & Rice",          False),
        (4, "breakfast", "Masala Omelette",                 False),
        (5, "dinner",    "Lamb Kofta with Yoghurt Sauce",   False),
    ])

    # ──────────────────────────────────────────────────
    # 6. PANTRY ITEMS
    # ──────────────────────────────────────────────────
    pantry_data = {
        "rania":  ["eggs", "spinach", "rice", "garlic", "soy sauce", "butter",
                   "onion", "sesame oil", "green onion", "canned tomatoes"],
        "olivia": ["pasta", "canned tomatoes", "onion", "cheese", "eggs",
                   "flour", "butter", "olive oil", "garlic"],
        "yifeng": ["tofu", "soy sauce", "garlic", "lemon", "chickpeas",
                   "quinoa", "coconut milk", "tahini"],
        "marcus": ["butter", "garlic", "olive oil", "parmesan", "eggs",
                   "cream", "white wine", "shallot"],
        "priya":  ["garlic", "onion", "cumin", "coriander", "yoghurt",
                   "ginger", "garam masala", "tomato purée"],
        "leon":   ["rice", "eggs", "soy sauce", "sesame oil", "chicken breast",
                   "broccoli", "green onion"],
    }

    for username, items in pantry_data.items():
        u = users[username]
        for name in items:
            db.session.add(PantryItem(user_id=u.id, ingredient_name=name))

    # ──────────────────────────────────────────────────
    # 7. FOLLOW RELATIONSHIPS
    # ──────────────────────────────────────────────────
    follow_data = [
        (rania, josh), (rania, olivia), (rania, priya),
        (josh,  rania), (josh, yifeng), (josh, leon),
        (yifeng, rania), (yifeng, josh), (yifeng, olivia), (yifeng, priya),
        (olivia, rania), (olivia, yifeng),
        (marcus, priya), (marcus, rania), (marcus, sofia),
        (priya, rania), (priya, yifeng), (priya, marcus),
        (leon, josh), (leon, rania), (leon, marcus),
        (sofia, olivia), (sofia, rania), (sofia, marcus), (sofia, priya),
    ]

    for follower, followed in follow_data:
        db.session.add(Follower(
            follower_id=follower.id, followed_id=followed.id,
        ))

    # ──────────────────────────────────────────────────
    # 8. SAVED RECIPES  (5 per user)
    # ──────────────────────────────────────────────────
    saved_data = [
        (rania,  ["Thai Green Curry", "Fudgy Brownies", "Buddha Bowl",
                  "Butter Chicken", "Mango Sticky Rice"]),
        (josh,   ["Garlic Butter Noodles", "Shakshuka", "Lentil Soup",
                  "One-Pot Chicken & Rice", "Chicken Teriyaki Bowl"]),
        (yifeng, ["Overnight Berry Oats", "Creamy Tomato Pasta", "Tropical Fruit Salad",
                  "Mango Coconut Smoothie Bowl", "Black Bean Tacos"]),
        (olivia, ["Egg Fried Rice", "Chicken Teriyaki Bowl", "Spicy Tofu Stir Fry",
                  "Pesto Pasta", "Margherita Pizza"]),
        (marcus, ["Mushroom Risotto", "Butter Chicken", "Classic Crème Brûlée",
                  "Lamb Kofta with Yoghurt Sauce", "Avocado Toast with Poached Egg"]),
        (priya,  ["Butter Chicken", "Lamb Kofta with Yoghurt Sauce", "Shakshuka",
                  "Masala Omelette", "Lentil Soup"]),
        (leon,   ["Salmon & Quinoa Power Bowl", "Greek Chicken Wrap",
                  "One-Pot Chicken & Rice", "Chicken Teriyaki Bowl", "Beef Tacos"]),
        (sofia,  ["Fudgy Brownies", "Classic Crème Brûlée", "Tropical Fruit Salad",
                  "Spinach & Feta Stuffed Peppers", "Margherita Pizza"]),
    ]

    for user, titles in saved_data:
        for title in titles:
            db.session.add(SavedRecipe(
                user_id=user.id, recipe_id=recipes[title].id,
            ))

    # ──────────────────────────────────────────────────
    # COMMIT
    # ──────────────────────────────────────────────────
    db.session.commit()

    print("=" * 50)
    print("  Plate Theory — Database Seeded Successfully")
    print("=" * 50)
    print(f"  Users:            {User.query.count()}")
    print(f"  Recipes:          {Recipe.query.count()}")
    print(f"  Ingredients:      {RecipeIngredient.query.count()}")
    print(f"  Ratings:          {Rating.query.count()}")
    print(f"  Comments:         {Comment.query.count()}")
    print(f"  Meal Plans:       {MealPlan.query.count()}")
    print(f"  Meal Plan Items:  {MealPlanItem.query.count()}")
    print(f"  Pantry Items:     {PantryItem.query.count()}")
    print(f"  Followers:        {Follower.query.count()}")
    print(f"  Saved Recipes:    {SavedRecipe.query.count()}")
    print("=" * 50)
