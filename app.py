from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from database import create_database

app = Flask(__name__)

# Ensure database table exists on application startup
create_database()


def get_diet_meals(goal, dietary_preference="Non-Vegetarian", allergies="None", meal_schedule="Standard (4-5 Meals)"):
    """
    Return structured meal plan tailored to:
    - User's Goal (Muscle Gain, Weight Loss, Strength Gain, Maintenance)
    - Dietary Preference (Non-Vegetarian, Vegetarian, Eggetarian, Vegan, Keto)
    - Food Allergies (Dairy-Free, Nut-Free, Gluten-Free)
    - Meal Schedule (Standard 5 meals, Intermittent Fasting 16/8, 3 Meals)
    """
    is_dairy_free = "Dairy-Free" in allergies
    is_nut_free = "Nut-Free" in allergies
    is_gluten_free = "Gluten-Free" in allergies

    # Helpers for allergy-safe food substitutes
    milk_sub = "Fortified Almond or Soy Milk" if is_dairy_free else "Low-Fat / Whole Milk"
    curd_sub = "Coconut or Soy Yogurt" if is_dairy_free else "Fresh Probiotic Curd / Greek Yogurt"
    nut_sub = "Roasted Pumpkin & Sunflower Seeds" if is_nut_free else "Peanut Butter & Mixed Almonds"
    bread_sub = "Gluten-Free Toast / Corn Tortilla" if is_gluten_free else "Whole Wheat Toast"
    grain_sub = "Quinoa or Steamed Brown Rice" if is_gluten_free else "Whole Wheat Rotis or Brown Rice"

    # =========================================================================
    # 1. KETO / LOW-CARB DIET PLAN
    # =========================================================================
    if dietary_preference == "Keto":
        protein_item = "Pan-seared Chicken / Salmon" if dietary_preference == "Non-Vegetarian" else "Grilled Paneer or Seasoned Firm Tofu"
        meals = [
            {
                "title": "Keto Power Breakfast",
                "timing": "Morning (8:00 AM)",
                "icon": "fa-solid fa-egg",
                "items": f"3 whole eggs scrambled in extra virgin olive oil/butter with spinach and 1/2 avocado (Zero Sugar)."
            },
            {
                "title": "Keto Fuel Snack",
                "timing": "Mid-Morning (11:00 AM)",
                "icon": "fa-solid fa-seedling",
                "items": f"{'Roasted pumpkin and chia seeds' if is_nut_free else 'Handful of raw walnuts, macadamias, and cucumber slices'}."
            },
            {
                "title": "High-Fat Lunch",
                "timing": "Afternoon (1:30 PM)",
                "icon": "fa-solid fa-bowl-rice",
                "items": f"{protein_item} served with a large olive oil salad, sautéed broccoli, avocado, and {curd_sub}."
            },
            {
                "title": "Pre-Workout Energy",
                "timing": "1 Hour Before Workout",
                "icon": "fa-solid fa-bolt",
                "items": f"Black coffee or green tea with MCT oil or coconut oil, plus a pinch of pink Himalayan salt."
            },
            {
                "title": "Keto Satiety Dinner",
                "timing": "Evening (8:00 PM)",
                "icon": "fa-solid fa-utensils",
                "items": f"Grilled herb paneer/chicken/tofu with buttered asparagus, cauliflower mash, and leafy greens."
            }
        ]

    # =========================================================================
    # 2. VEGAN (100% PLANT-BASED) DIET PLAN
    # =========================================================================
    elif dietary_preference == "Vegan":
        if goal == "Weight Loss":
            meals = [
                {
                    "title": "Plant-Protein Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Rolled oats cooked in {milk_sub}, topped with chia seeds, scoop of plant protein, and fresh berries."
                },
                {
                    "title": "Mid-Morning Snack",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Crisp green apple or guava with {'pumpkin seeds' if is_nut_free else '10 raw almonds'}."
                },
                {
                    "title": "Lean Green Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-seedling",
                    "items": f"Thick yellow lentil dal, pan-sautéed firm tofu with turmeric, steamed broccoli, and {grain_sub}."
                },
                {
                    "title": "Pre-Workout Carb Snack",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": "1 medium banana with black coffee or green tea."
                },
                {
                    "title": "Post-Workout Recovery",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"Soy milk or plant protein shake blended with spinach and 1/2 banana."
                },
                {
                    "title": "High-Fiber Dinner",
                    "timing": "Evening (7:30 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Spiced chickpea (chana) or black bean bowl with sautéed bell peppers, cucumber salad, and {grain_sub}."
                }
            ]
        else:  # Muscle Gain, Strength Gain, Maintenance
            meals = [
                {
                    "title": "High-Calorie Vegan Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Hearty bowl of oatmeal in {milk_sub} with {nut_sub}, chia seeds, sliced bananas, and plant protein."
                },
                {
                    "title": "Mid-Morning Snack",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Seasonal fruit paired with {'roasted sunflower and flax seeds' if is_nut_free else '2 tbsp peanut butter on apple slices'}."
                },
                {
                    "title": "Anabolic Plant Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-seedling",
                    "items": f"High-protein soya chunks & green pea curry, generous portion of brown rice, thick dal, and raw salad."
                },
                {
                    "title": "Pre-Workout Fuel",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": f"2 bananas with {bread_sub} and {'sunflower seed butter' if is_nut_free else 'peanut butter'}."
                },
                {
                    "title": "Post-Workout Rebuild",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"High-protein smoothie ({milk_sub} + plant protein + hemp seeds + banana)."
                },
                {
                    "title": "Nutrient-Dense Dinner",
                    "timing": "Evening (8:00 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Pan-seared sesame tofu stir-fry with broccoli, edamame, dal, and {grain_sub}."
                },
                {
                    "title": "Before Bed",
                    "timing": "Night (10:30 PM)",
                    "icon": "fa-solid fa-moon",
                    "items": f"Warm {milk_sub} with a pinch of turmeric and cinnamon."
                }
            ]

    # =========================================================================
    # 3. VEGETARIAN DIET PLAN (NO EGGS, NO MEAT)
    # =========================================================================
    elif dietary_preference == "Vegetarian":
        paneer_item = "Seasoned Firm Tofu" if is_dairy_free else "Fresh Cottage Cheese (Paneer)"
        if goal == "Weight Loss":
            meals = [
                {
                    "title": "High-Protein Veg Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Oats porridge cooked in {milk_sub}, topped with pumpkin seeds, cinnamon, and a bowl of fresh papaya/berries."
                },
                {
                    "title": "Mid-Morning Snack",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Green apple with {'sunflower seeds' if is_nut_free else 'small portion of raw almonds'} and green tea."
                },
                {
                    "title": "Balanced Vegetarian Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Grilled {paneer_item} (100g), thick yellow moong dal, generous steamed vegetables, and {grain_sub}."
                },
                {
                    "title": "Pre-Workout Energy",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": "1 banana or seasonal fruit with green tea."
                },
                {
                    "title": "Post-Workout Refuel",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"Bowl of {curd_sub} or protein shake with a light fruit snack."
                },
                {
                    "title": "Light Protein Dinner",
                    "timing": "Evening (7:30 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Spiced chickpea (chana) or soya bhurji, mixed vegetable soup, and {grain_sub}."
                }
            ]
        else:  # Muscle Gain, Strength Gain, Maintenance
            meals = [
                {
                    "title": "Power Vegetarian Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Rolled oats with {milk_sub}, sliced bananas, honey, and {'pumpkin/chia seeds' if is_nut_free else 'handful of chopped almonds & walnuts'}."
                },
                {
                    "title": "Mid-Morning Fuel",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Fresh fruit with {curd_sub} and {'pumpkin seeds' if is_nut_free else '2 tbsp peanut butter'}."
                },
                {
                    "title": "High-Protein Veg Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Grilled {paneer_item} (150g), rich dal makhani or rajma, steamed rice, fresh salad, and {curd_sub}."
                },
                {
                    "title": "Pre-Workout Boost",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": f"2 bananas with {bread_sub} and {'seed butter' if is_nut_free else 'peanut butter'}."
                },
                {
                    "title": "Post-Workout Anabolic Shake",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"{milk_sub} or whey protein shake, sliced {paneer_item}, and a banana."
                },
                {
                    "title": "Wholesome Protein Dinner",
                    "timing": "Evening (8:00 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"{paneer_item} or soya chunks curry, seasonal green vegetables, dal, and {grain_sub}."
                },
                {
                    "title": "Slow-Release Bedtime",
                    "timing": "Night (10:30 PM)",
                    "icon": "fa-solid fa-moon",
                    "items": f"Warm cup of {milk_sub} with a pinch of turmeric and honey."
                }
            ]

    # =========================================================================
    # 4. EGGETARIAN DIET PLAN (EGGS + DAIRY + VEG, NO MEAT)
    # =========================================================================
    elif dietary_preference == "Eggetarian":
        if goal == "Weight Loss":
            meals = [
                {
                    "title": "Lean Egg Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-egg",
                    "items": f"3 egg whites + 1 whole boiled egg, rolled oats in warm water/{milk_sub}, and fresh berries."
                },
                {
                    "title": "Mid-Morning Snack",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Crisp green apple with {'roasted pumpkin seeds' if is_nut_free else '8 raw almonds'}."
                },
                {
                    "title": "Metabolic Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"2 whole boiled eggs, yellow dal, large garden salad, and {grain_sub}."
                },
                {
                    "title": "Pre-Workout Snack",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": "1 medium banana with black coffee or green tea."
                },
                {
                    "title": "Post-Workout Recovery",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"3 boiled egg whites with light {curd_sub}."
                },
                {
                    "title": "Light Egg/Paneer Dinner",
                    "timing": "Evening (7:30 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Egg white bhurji (scramble) or grilled paneer with sautéed spinach, dal, and {grain_sub}."
                }
            ]
        else:  # Muscle Gain, Strength Gain, Maintenance
            meals = [
                {
                    "title": "Muscle Egg Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-egg",
                    "items": f"3 whole scrambled eggs in olive oil, bowl of oatmeal in {milk_sub}, banana, and honey."
                },
                {
                    "title": "Mid-Morning Fuel",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Fresh seasonal fruit with {'sunflower seeds' if is_nut_free else 'peanut butter'} and {curd_sub}."
                },
                {
                    "title": "High-Protein Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Spiced egg curry (3 eggs) or grilled paneer, steamed brown rice, thick dal, and salad."
                },
                {
                    "title": "Pre-Workout Pump",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": f"2 bananas with {bread_sub} and {'seed butter' if is_nut_free else 'peanut butter'}."
                },
                {
                    "title": "Post-Workout Rebuild",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"{milk_sub} or whey protein shake, 2 boiled eggs, and a banana."
                },
                {
                    "title": "Satiating Dinner",
                    "timing": "Evening (8:00 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Paneer or egg scramble with mixed vegetables, dal, and {grain_sub}."
                },
                {
                    "title": "Bedtime Recovery",
                    "timing": "Night (10:30 PM)",
                    "icon": "fa-solid fa-moon",
                    "items": f"Warm cup of {milk_sub} or fresh unsweetened {curd_sub}."
                }
            ]

    # =========================================================================
    # 5. NON-VEGETARIAN DIET PLAN (CHICKEN, FISH, EGGS, DAIRY)
    # =========================================================================
    else:
        if goal == "Weight Loss":
            meals = [
                {
                    "title": "Lean Non-Veg Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-egg",
                    "items": f"2 whole boiled eggs, rolled oats in warm water/{milk_sub}, and fresh berries."
                },
                {
                    "title": "Mid-Morning Snack",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Crisp green apple with {'roasted pumpkin seeds' if is_nut_free else '8-10 raw almonds'}."
                },
                {
                    "title": "Lean Chicken Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Grilled skinless chicken breast (150g), light dal, generous steamed vegetables, and {grain_sub}."
                },
                {
                    "title": "Pre-Workout Energy",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": "1 medium banana with black coffee or green tea."
                },
                {
                    "title": "Post-Workout Refuel",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"3 egg whites with light {curd_sub}."
                },
                {
                    "title": "Clean Protein Dinner",
                    "timing": "Evening (7:30 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Grilled fish or lemon chicken with steamed broccoli, dal soup, and {grain_sub}."
                }
            ]
        else:  # Muscle Gain, Strength Gain, Maintenance
            meals = [
                {
                    "title": "Anabolic Breakfast",
                    "timing": "Morning (8:00 AM)",
                    "icon": "fa-solid fa-egg",
                    "items": f"Oats cooked in {milk_sub}, 3 whole scrambled/boiled eggs, and a large banana."
                },
                {
                    "title": "Mid-Morning Snack",
                    "timing": "Mid-Morning (11:00 AM)",
                    "icon": "fa-solid fa-apple-whole",
                    "items": f"Fresh seasonal fruit with {'sunflower/pumpkin seeds' if is_nut_free else '2 tbsp peanut butter & almonds'}."
                },
                {
                    "title": "Muscle Fuel Lunch",
                    "timing": "Afternoon (1:30 PM)",
                    "icon": "fa-solid fa-bowl-rice",
                    "items": f"Steamed rice, thick dal, mixed vegetables, grilled chicken breast (180g), and {curd_sub}."
                },
                {
                    "title": "Pre-Workout Boost",
                    "timing": "1 Hour Before Workout",
                    "icon": "fa-solid fa-bolt",
                    "items": f"1-2 ripe bananas with {bread_sub} and {'seed butter' if is_nut_free else 'peanut butter'}."
                },
                {
                    "title": "Post-Workout Recovery",
                    "timing": "Within 30 Mins After Workout",
                    "icon": "fa-solid fa-dumbbell",
                    "items": f"Glass of {milk_sub} or whey protein, 2 boiled eggs, and a banana."
                },
                {
                    "title": "High-Protein Dinner",
                    "timing": "Evening (8:00 PM)",
                    "icon": "fa-solid fa-utensils",
                    "items": f"Whole wheat rotis, grilled chicken or fish, sautéed green vegetables, and dal."
                },
                {
                    "title": "Bedtime Nutrition",
                    "timing": "Night (10:30 PM)",
                    "icon": "fa-solid fa-moon",
                    "items": f"Warm {milk_sub} or unsweetened {curd_sub} for sustained nighttime amino acid release."
                }
            ]

    # =========================================================================
    # MEAL SCHEDULE ADJUSTMENTS (Intermittent Fasting or 3 Meals Only)
    # =========================================================================
    if meal_schedule == "Intermittent Fasting (16/8 Window)":
        final_meals = [
            {
                "title": "Fast-Breaking Feast (12:00 PM)",
                "timing": "Start of 8-Hour Eating Window",
                "icon": "fa-solid fa-utensils",
                "food": f"Large feast: {meals[0].get('items', meals[0].get('food', ''))} combined with {meals[2].get('items', meals[2].get('food', ''))}."
            },
            {
                "title": "Pre-Workout / Midday Energy (4:00 PM)",
                "timing": "Mid-Window Fuel",
                "icon": "fa-solid fa-bolt",
                "food": f"{meals[3].get('items', meals[3].get('food', ''))} along with hydrated electrolytes."
            },
            {
                "title": "Nutrient-Dense Dinner Feast (7:30 PM)",
                "timing": "End of 8-Hour Eating Window (Fast begins 8 PM)",
                "icon": "fa-solid fa-moon",
                "food": f"Final meal: {meals[-2].get('items', meals[-2].get('food', ''))} plus {'plant milk' if is_dairy_free else 'warm milk or curd'}."
            }
        ]
    elif meal_schedule == "3 Meals Only":
        # Keep only Breakfast, Lunch, and Dinner
        final_meals = [
            meals[0],   # Breakfast
            meals[2],   # Lunch
            meals[-2] if len(meals) > 5 else meals[-1]  # Dinner
        ]
    else:
        final_meals = meals

    # Ensure both 'food' and 'items' keys are populated on every meal dict
    for m in final_meals:
        val = m.get("food") or m.get("items") or ""
        m["food"] = val
        m["items"] = val

    return final_meals


def get_workout_routine(goal):
    """Return tailored weekly workout routine based on user's goal."""
    if goal == "Muscle Gain":
        return [
            {
                "day": "Day 1",
                "name": "Push (Chest, Shoulders, Triceps)",
                "focus": "Hypertrophy & Upper Body Press",
                "exercises": [
                    {"name": "Barbell / Dumbbell Flat Bench Press", "sets": "4 sets x 8-10 reps", "rest": "90s"},
                    {"name": "Incline Dumbbell Chest Press", "sets": "3 sets x 10-12 reps", "rest": "75s"},
                    {"name": "Seated Dumbbell Shoulder Press", "sets": "3 sets x 10-12 reps", "rest": "75s"},
                    {"name": "Dumbbell Lateral Raises (Side Delts)", "sets": "4 sets x 12-15 reps", "rest": "60s"},
                    {"name": "Cable Tricep Pushdowns", "sets": "3 sets x 12-15 reps", "rest": "60s"}
                ]
            },
            {
                "day": "Day 2",
                "name": "Pull (Back & Biceps)",
                "focus": "Back Width & Arm Thickness",
                "exercises": [
                    {"name": "Lat Pulldowns or Wide-Grip Pull-Ups", "sets": "4 sets x 8-10 reps", "rest": "90s"},
                    {"name": "Bent-Over Barbell Rows", "sets": "4 sets x 8-10 reps", "rest": "90s"},
                    {"name": "Seated Cable Rows", "sets": "3 sets x 10-12 reps", "rest": "75s"},
                    {"name": "Incline Dumbbell Bicep Curls", "sets": "3 sets x 10-12 reps", "rest": "60s"},
                    {"name": "Hammer Curls (Forearms & Brachialis)", "sets": "3 sets x 12 reps", "rest": "60s"}
                ]
            },
            {
                "day": "Day 3",
                "name": "Legs & Core",
                "focus": "Lower Body Power & Midsection",
                "exercises": [
                    {"name": "Barbell Back Squats", "sets": "4 sets x 8-10 reps", "rest": "120s"},
                    {"name": "Romanian Deadlifts (Hamstrings)", "sets": "3 sets x 10 reps", "rest": "90s"},
                    {"name": "Leg Press Machine", "sets": "3 sets x 12 reps", "rest": "75s"},
                    {"name": "Standing Calf Raises", "sets": "4 sets x 15 reps", "rest": "60s"},
                    {"name": "Hanging Knee / Leg Raises", "sets": "3 sets x 15 reps", "rest": "60s"}
                ]
            },
            {
                "day": "Day 4",
                "name": "Upper Body Hypertrophy",
                "focus": "Symmetry & Muscle Pump",
                "exercises": [
                    {"name": "Dumbbell Incline Flyes", "sets": "3 sets x 12 reps", "rest": "60s"},
                    {"name": "Chest-Supported Dumbbell Rows", "sets": "3 sets x 10-12 reps", "rest": "75s"},
                    {"name": "Rear Delt Rope Face Pulls", "sets": "4 sets x 15 reps", "rest": "60s"},
                    {"name": "EZ-Bar Skull Crushers & Bicep 21s", "sets": "3 sets x 12 reps", "rest": "60s"}
                ]
            }
        ]
    elif goal == "Weight Loss":
        return [
            {
                "day": "Day 1",
                "name": "Full Body Metabolic Circuit",
                "focus": "Max Calorie Burn & Heart Rate",
                "exercises": [
                    {"name": "Dumbbell Goblet Squats into Press", "sets": "4 sets x 12-15 reps", "rest": "45s"},
                    {"name": "Push-Ups into Plank Hold", "sets": "3 sets x 15 reps", "rest": "45s"},
                    {"name": "Kettlebell or Dumbbell Swings", "sets": "4 sets x 20 reps", "rest": "45s"},
                    {"name": "Mountain Climbers", "sets": "3 sets x 40 seconds", "rest": "30s"},
                    {"name": "HIIT Treadmill / Jump Rope Intervals", "sets": "15 mins (30s sprint/30s walk)", "rest": "60s"}
                ]
            },
            {
                "day": "Day 2",
                "name": "Core & Lower Body Tone",
                "focus": "Legs, Glutes & Abs Definition",
                "exercises": [
                    {"name": "Walking Dumbbell Lunges", "sets": "3 sets x 16 total steps", "rest": "45s"},
                    {"name": "Dumbbell Romanian Deadlifts", "sets": "4 sets x 12 reps", "rest": "45s"},
                    {"name": "Bodyweight Jump Squats", "sets": "3 sets x 15 reps", "rest": "45s"},
                    {"name": "Bicycle Crunches & Russian Twists", "sets": "3 sets x 20 reps", "rest": "30s"},
                    {"name": "Incline Treadmill Fast Walk", "sets": "20 mins steady state", "rest": "None"}
                ]
            },
            {
                "day": "Day 3",
                "name": "Upper Body Sculpt & Cardio",
                "focus": "Lean Muscle & Endurance",
                "exercises": [
                    {"name": "Dumbbell Overhead Shoulder Press", "sets": "4 sets x 12 reps", "rest": "45s"},
                    {"name": "Lat Pulldown or Resistance Band Rows", "sets": "4 sets x 12 reps", "rest": "45s"},
                    {"name": "Bicep Curl to Tricep Kickbacks Combo", "sets": "3 sets x 12 reps", "rest": "45s"},
                    {"name": "Burpees or Battle Ropes", "sets": "4 rounds x 40 seconds", "rest": "30s"},
                    {"name": "Rowing Machine or Cycling", "sets": "15 mins steady pace", "rest": "None"}
                ]
            },
            {
                "day": "Day 4",
                "name": "Active Recovery & Mobility",
                "focus": "Flexibility & Fat Oxidation",
                "exercises": [
                    {"name": "Dynamic Bodyweight Warm-Up", "sets": "10 minutes", "rest": "30s"},
                    {"name": "Plank & Side Plank Holds", "sets": "3 sets x 45s each", "rest": "45s"},
                    {"name": "Light Jog or Outdoor Cycling", "sets": "25-30 minutes", "rest": "None"},
                    {"name": "Full Body Foam Rolling & Stretching", "sets": "15 minutes", "rest": "None"}
                ]
            }
        ]
    elif goal == "Strength Gain":
        return [
            {
                "day": "Day 1",
                "name": "Heavy Squat & Lower Body Power",
                "focus": "Max Strength & Core Rigidity",
                "exercises": [
                    {"name": "Barbell Back Squats", "sets": "5 sets x 5 reps (Heavy)", "rest": "180s"},
                    {"name": "Leg Press Machine", "sets": "3 sets x 8 reps", "rest": "90s"},
                    {"name": "Barbell Good Mornings", "sets": "3 sets x 8 reps", "rest": "90s"},
                    {"name": "Weighted Core Planks", "sets": "3 sets x 60 seconds", "rest": "60s"}
                ]
            },
            {
                "day": "Day 2",
                "name": "Heavy Bench Press & Upper Push",
                "focus": "Horizontal Press Power",
                "exercises": [
                    {"name": "Barbell Flat Bench Press", "sets": "5 sets x 5 reps (Heavy)", "rest": "180s"},
                    {"name": "Standing Overhead Military Press", "sets": "4 sets x 6 reps", "rest": "120s"},
                    {"name": "Close-Grip Tricep Bench Press", "sets": "3 sets x 8 reps", "rest": "90s"},
                    {"name": "Heavy Dumbbell Shrugs", "sets": "4 sets x 10 reps", "rest": "75s"}
                ]
            },
            {
                "day": "Day 3",
                "name": "Deadlift & Posterior Chain",
                "focus": "Whole Body Pulling Power",
                "exercises": [
                    {"name": "Conventional or Sumo Deadlift", "sets": "5 sets x 3-5 reps (Heavy)", "rest": "180s"},
                    {"name": "Pendlay / Heavy Barbell Rows", "sets": "4 sets x 6 reps", "rest": "120s"},
                    {"name": "Pull-Ups (Weighted if possible)", "sets": "4 sets x 6-8 reps", "rest": "90s"},
                    {"name": "Heavy Farmer's Walk", "sets": "4 sets x 40 meters", "rest": "90s"}
                ]
            },
            {
                "day": "Day 4",
                "name": "Overhead Press & Auxiliary Volume",
                "focus": "Vertical Press & Armor Building",
                "exercises": [
                    {"name": "Push Press / Standing Barbell OHP", "sets": "4 sets x 6 reps", "rest": "120s"},
                    {"name": "Parallel Bar Dips (Weighted)", "sets": "4 sets x 8 reps", "rest": "90s"},
                    {"name": "Barbell Bicep Curls", "sets": "4 sets x 8 reps", "rest": "75s"},
                    {"name": "Face Pulls for Shoulder Health", "sets": "4 sets x 15 reps", "rest": "60s"}
                ]
            }
        ]
    else:  # Weight Maintenance
        return [
            {
                "day": "Day 1",
                "name": "Upper Body Strength & Posture",
                "focus": "Balanced Torso & Joint Health",
                "exercises": [
                    {"name": "Dumbbell Flat or Incline Press", "sets": "3 sets x 10 reps", "rest": "60s"},
                    {"name": "Seated Cable Rows", "sets": "3 sets x 10 reps", "rest": "60s"},
                    {"name": "Dumbbell Lateral Shoulder Raises", "sets": "3 sets x 12 reps", "rest": "45s"},
                    {"name": "Bench Tricep Dips", "sets": "3 sets x 12 reps", "rest": "45s"}
                ]
            },
            {
                "day": "Day 2",
                "name": "Lower Body Mobility & Strength",
                "focus": "Legs, Glutes & Hip Stability",
                "exercises": [
                    {"name": "Goblet Squats", "sets": "3 sets x 10 reps", "rest": "60s"},
                    {"name": "Dumbbell Romanian Deadlifts", "sets": "3 sets x 10 reps", "rest": "60s"},
                    {"name": "Glute Bridge Holds", "sets": "3 sets x 12 reps", "rest": "45s"},
                    {"name": "Forearm Plank Hold", "sets": "3 sets x 45 seconds", "rest": "45s"}
                ]
            },
            {
                "day": "Day 3",
                "name": "Conditioning & Core Endurance",
                "focus": "Cardiovascular Health",
                "exercises": [
                    {"name": "Kettlebell Clean & Press", "sets": "3 sets x 10 reps", "rest": "45s"},
                    {"name": "Push-Up with Rotation", "sets": "3 sets x 10 reps", "rest": "45s"},
                    {"name": "Hanging Knee Raises", "sets": "3 sets x 12 reps", "rest": "45s"},
                    {"name": "Moderate Jogging, Cycling or Swimming", "sets": "20-25 minutes", "rest": "None"}
                ]
            }
        ]


def get_grocery_list(goal, dietary_preference="Non-Vegetarian", allergies="None"):
    """Return categorized weekly grocery checklist tailored to dietary needs."""
    is_dairy_free = "Dairy-Free" in allergies
    is_nut_free = "Nut-Free" in allergies
    is_gluten_free = "Gluten-Free" in allergies

    # Protein items tailored to preference
    if dietary_preference == "Vegan":
        proteins = [
            "Organic Firm Tofu (1 kg)",
            "High-Protein Soya Chunks (500g)",
            "Fortified Soy or Almond Milk (2-3 liters)",
            "Edamame & Green Peas (500g)",
            "Black Beans, Chickpeas & Yellow Lentils (1 kg)"
        ]
    elif dietary_preference == "Vegetarian":
        proteins = [
            "Organic Firm Tofu" if is_dairy_free else "Fresh Cottage Cheese (Paneer) (1 kg)",
            "Fortified Plant Milk (2L)" if is_dairy_free else "Low-Fat / Whole Milk (2-3 liters)",
            "Coconut / Soy Yogurt" if is_dairy_free else "Greek Yogurt / Fresh Probiotic Curd (1 kg)",
            "Yellow Moong & Black Lentils / Dal (1 kg)",
            "Chickpeas (Kabuli Chana) & Rajma (1 kg)"
        ]
    elif dietary_preference == "Eggetarian":
        proteins = [
            "Fresh Farm Eggs & Liquid Egg Whites (2-3 dozen)",
            "Firm Tofu" if is_dairy_free else "Fresh Cottage Cheese / Paneer (500g)",
            "Fortified Plant Milk" if is_dairy_free else "Fresh Milk (2 liters)",
            "Probiotic Greek Curd (1 kg)" if not is_dairy_free else "Plant Yogurt",
            "Lentils & Beans / Dal (1 kg)"
        ]
    elif dietary_preference == "Keto":
        proteins = [
            "Whole Farm Eggs (2-3 dozen)",
            "Chicken Thighs or Salmon / Fatty Fish (1.5 kg)" if dietary_preference != "Vegetarian" else "Paneer & Tofu (1.5 kg)",
            "Cheddar / Parmesan Hard Cheese" if not is_dairy_free else "Nutritional Yeast",
            "Bacon / Lean Meats" if dietary_preference == "Non-Vegetarian" else "Hemp Seeds & Edamame"
        ]
    else:  # Non-Vegetarian
        proteins = [
            "Fresh Farm Eggs (2-3 dozen)",
            "Skinless Chicken Breast or Salmon (1.5 kg)",
            "Plant Milk" if is_dairy_free else "Low-Fat Milk (2-3 liters)",
            "Greek Yogurt / Curd (1 kg)" if not is_dairy_free else "Plant-based Yogurt",
            "Yellow & Red Lentils (1 kg)"
        ]

    # Carbohydrate items tailored to preference
    if dietary_preference == "Keto":
        carbs = [
            "Avocados (4-5 ripe)",
            "Ground Flaxseeds & Chia Seeds",
            "Low-Carb Almond Flour" if not is_nut_free else "Sunflower Seed Flour",
            "Cauliflower (for rice/mash substitutes)"
        ]
    elif is_gluten_free:
        carbs = [
            "Certified Gluten-Free Rolled Oats (1 kg)",
            "Organic Brown Rice or Jasmine Rice (1 kg)",
            "Quinoa (500g)",
            "Millet / Jowar Flour or Corn Tortillas",
            "Sweet Potatoes (1 kg)"
        ]
    else:
        carbs = [
            "Rolled or Steel-Cut Oats (1 kg)",
            "Brown Rice or Basmati Rice (1 kg)",
            "Whole Wheat Flour (Atta) or Whole Grain Bread",
            "Sweet Potatoes or Potatoes (1 kg)"
        ]

    # Healthy Fats tailored to allergies
    if is_nut_free:
        fats = [
            "Raw Pumpkin Seeds (250g)",
            "Sunflower Seeds (250g)",
            "Cold-Pressed Extra Virgin Olive Oil",
            "Pure Desi Ghee or Virgin Coconut Oil"
        ]
    else:
        fats = [
            "100% Natural Peanut Butter (No added sugar)",
            "Raw Whole Almonds (250g)",
            "Raw Walnuts (200g)",
            "Cold-Pressed Extra Virgin Olive Oil or Pure Ghee"
        ]

    return [
        {
            "category": "Targeted Proteins",
            "icon": "fa-solid fa-drumstick-bite",
            "food_items": proteins
        },
        {
            "category": "Complex Carbohydrates",
            "icon": "fa-solid fa-wheat-awn",
            "food_items": carbs
        },
        {
            "category": "Healthy Fats",
            "icon": "fa-solid fa-bottle-droplet",
            "food_items": fats
        },
        {
            "category": "Fresh Produce & Greens",
            "icon": "fa-solid fa-apple-whole",
            "food_items": [
                "Fresh Bananas (1-2 bunches)",
                "Apples or Berries / Papaya (1 kg)",
                "Baby Spinach & Kale (500g)",
                "Broccoli, Cauliflower & Bell Peppers",
                "Cucumbers & Tomatoes (for fresh salads)"
            ]
        },
        {
            "category": "Hydration & Pantry Essentials",
            "icon": "fa-solid fa-mug-hot",
            "food_items": [
                "Green Tea Bags or High-Grade Coffee",
                "Pink Himalayan Salt & Black Pepper",
                "Ground Turmeric & Cinnamon",
                "Bottled Water or Electrolytes for gym workouts"
            ]
        }
    ]


def calculate_user_metrics(age, gender, height, weight, goal, target_weight, activity_level, dietary_preference="Non-Vegetarian", allergies="None", meal_schedule="Standard (4-5 Meals)"):
    """Calculate all metabolic targets, macros, BMI, and customized plans."""
    # BMR Calculation (Mifflin-St Jeor)
    if gender == "Male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    # Activity Level Multiplier
    if activity_level == "Low":
        multiplier = 1.2
    elif activity_level == "Moderate":
        multiplier = 1.55
    else:
        multiplier = 1.725

    # Maintenance Calories (TDEE)
    tdee = bmr * multiplier

    # Goal Based Target Calories
    if goal == "Weight Loss":
        calories = max(1200.0, tdee - 300)
    elif goal == "Muscle Gain":
        calories = tdee + 300
    elif goal == "Strength Gain":
        calories = tdee + 200
    else:
        calories = tdee

    # Macronutrients
    if dietary_preference == "Keto":
        # Keto macro distribution: 70% Fat, 25% Protein, 5% Carbs
        fat_calories = calories * 0.70
        fat = fat_calories / 9
        protein_calories = calories * 0.25
        protein = protein_calories / 4
        carbs_calories = calories * 0.05
        carbs = carbs_calories / 4
    else:
        protein = weight * 2
        protein_calories = protein * 4
        fat = (calories * 0.25) / 9
        fat_calories = fat * 9
        carbs_calories = max(0.0, calories - protein_calories - fat_calories)
        carbs = carbs_calories / 4

    # Percentage distribution for progress bars
    protein_pct = round((protein_calories / calories) * 100, 1) if calories > 0 else 0
    carbs_pct = round((carbs_calories / calories) * 100, 1) if calories > 0 else 0
    fat_pct = round((fat_calories / calories) * 100, 1) if calories > 0 else 0

    # BMI Calculation
    height_m = height / 100.0
    bmi = round(weight / (height_m ** 2), 1) if height_m > 0 else 0
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25.0:
        bmi_category = "Normal"
    elif bmi < 30.0:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"

    # Hydration (in liters)
    water_liters = round(max(2.5, weight * 0.035), 1)

    # Generated Plans Customized According to User Requirements
    diet_meals = get_diet_meals(goal, dietary_preference, allergies, meal_schedule)
    workout_routine = get_workout_routine(goal)
    grocery_list = get_grocery_list(goal, dietary_preference, allergies)

    return {
        "bmr": bmr,
        "tdee": tdee,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "protein_pct": protein_pct,
        "carbs_pct": carbs_pct,
        "fat_pct": fat_pct,
        "bmi": bmi,
        "bmi_category": bmi_category,
        "water_liters": water_liters,
        "diet_meals": diet_meals,
        "workout_routine": workout_routine,
        "grocery_list": grocery_list,
        "dietary_preference": dietary_preference,
        "allergies": allergies,
        "meal_schedule": meal_schedule
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        name = request.form["name"].strip()
        age = int(request.form["age"])
        gender = request.form["gender"]
        height = float(request.form["height"])
        weight = float(request.form["weight"])
        goal = request.form["goal"]
        target_weight = float(request.form["target_weight"])
        activity_level = request.form["activity_level"]
        dietary_preference = request.form.get("dietary_preference", "Non-Vegetarian")
        allergies = request.form.get("allergies", "None")
        meal_schedule = request.form.get("meal_schedule", "Standard (4-5 Meals)")

        # Save user data in SQLite
        conn = sqlite3.connect("fitlift.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users
            (name, age, gender, height, weight, goal, target_weight, activity_level, dietary_preference, allergies, meal_schedule, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (name, age, gender, height, weight, goal, target_weight, activity_level, dietary_preference, allergies, meal_schedule))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        metrics = calculate_user_metrics(
            age, gender, height, weight, goal, target_weight, activity_level,
            dietary_preference, allergies, meal_schedule
        )

        return render_template(
            "dashboard.html",
            user_id=user_id,
            name=name,
            age=age,
            gender=gender,
            height=height,
            weight=weight,
            target_weight=target_weight,
            goal=goal,
            activity_level=activity_level,
            **metrics
        )

    return render_template("profile.html")


@app.route("/dashboard/<int:user_id>")
def view_dashboard(user_id):
    """Load a specific user's plan from the database."""
    conn = sqlite3.connect("fitlift.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, age, gender, height, weight, goal, target_weight, activity_level,
               dietary_preference, allergies, meal_schedule
        FROM users WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return redirect(url_for("history"))

    _, name, age, gender, height, weight, goal, target_weight, activity_level, dietary_preference, allergies, meal_schedule = row
    
    # Handle older rows where these might be None
    dietary_preference = dietary_preference or "Non-Vegetarian"
    allergies = allergies or "None"
    meal_schedule = meal_schedule or "Standard (4-5 Meals)"

    metrics = calculate_user_metrics(
        age, gender, height, weight, goal, target_weight, activity_level,
        dietary_preference, allergies, meal_schedule
    )

    return render_template(
        "dashboard.html",
        user_id=user_id,
        name=name,
        age=age,
        gender=gender,
        height=height,
        weight=weight,
        target_weight=target_weight,
        goal=goal,
        activity_level=activity_level,
        **metrics
    )


@app.route("/history")
def history():
    """Display all saved profiles from the database."""
    conn = sqlite3.connect("fitlift.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, age, gender, height, weight, goal, target_weight, activity_level,
               dietary_preference, allergies, meal_schedule, created_at
        FROM users
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    users = []
    for r in rows:
        users.append({
            "id": r[0],
            "name": r[1],
            "age": r[2],
            "gender": r[3],
            "height": r[4],
            "weight": r[5],
            "goal": r[6],
            "target_weight": r[7],
            "activity_level": r[8],
            "dietary_preference": r[9] or "Non-Vegetarian",
            "allergies": r[10] or "None",
            "meal_schedule": r[11] or "Standard (4-5 Meals)",
            "created_at": str(r[12]) if r[12] else ""
        })

    return render_template("history.html", users=users)


if __name__ == "__main__":
    app.run(debug=True)