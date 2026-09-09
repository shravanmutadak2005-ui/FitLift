import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, g
import sqlite3
from datetime import datetime
from database import (
    create_database, get_personal_records, get_exercise_history,
    get_progress_stats, log_exercise_record, delete_exercise_record,
    save_chat_message, get_chat_history, clear_chat_history, calculate_1rm,
    get_db_connection, register_user, authenticate_user, get_user_by_id,
    update_user_profile
)
from ai_advisor import generate_situational_advice, get_user_context

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fitlift_secret_key_pro_2026_auth")

# Ensure database tables exist on application startup
create_database()

@app.context_processor
def inject_user():
    """Inject current_user into all template renders."""
    user_id = session.get("user_id")
    current_user = get_user_by_id(user_id) if user_id else None
    return dict(current_user=current_user)

def login_required(f):
    """Decorator requiring active session user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


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


# ==============================================================================
# Authentication & Onboarding Routes
# ==============================================================================

@app.route("/")
def home():
    """Initial entry point: redirect to dashboard if logged in, else to login page."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Sign In page for registered users."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = authenticate_user(username_or_email, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}! 💪", "success")

            # Guide user to complete metrics if not yet completed
            if not user.get("weight") or not user.get("goal"):
                return redirect(url_for("profile"))

            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))
        else:
            flash("Invalid username/email or password. Please try again.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Sign Up page for first-time visitors."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not username or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "error")
            return render_template("register.html")

        new_user, error = register_user(name, username, password, email)
        if error:
            flash(error, "error")
            return render_template("register.html")

        # Automatically log the newly registered user in
        session["user_id"] = new_user["id"]
        session["user_name"] = new_user["name"]
        flash(f"Welcome to FitLift, {new_user['name']}! Let's set up your body metrics.", "success")
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Sign out the current user and clear session."""
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("login"))


# ==============================================================================
# User Profile & Dashboard Routes (Scoped to Logged-in User)
# ==============================================================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Manage body metrics, fitness goals, and dietary preferences for the logged-in user."""
    user_id = session["user_id"]
    user = get_user_by_id(user_id)

    if request.method == "POST":
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

        update_user_profile(
            user_id, age, gender, height, weight, goal, target_weight,
            activity_level, dietary_preference, allergies, meal_schedule
        )

        flash("Your fitness plan has been updated and calibrated!", "success")
        return redirect(url_for("dashboard"))

    return render_template("profile.html", user=user)


DEFAULT_EXERCISES = [
    {"name": "Barbell Bench Press", "category": "Chest"},
    {"name": "Incline Dumbbell Press", "category": "Chest"},
    {"name": "Dips (Chest Focus)", "category": "Chest"},
    {"name": "Cable Crossover", "category": "Chest"},
    {"name": "Push-Ups (Weighted)", "category": "Chest"},
    {"name": "Conventional Deadlift", "category": "Back"},
    {"name": "Barbell Bent-Over Row", "category": "Back"},
    {"name": "Weighted Pull-Up", "category": "Back"},
    {"name": "Lat Pulldown", "category": "Back"},
    {"name": "Seated Cable Row", "category": "Back"},
    {"name": "Barbell Back Squat", "category": "Legs"},
    {"name": "Romanian Deadlift", "category": "Legs"},
    {"name": "Leg Press", "category": "Legs"},
    {"name": "Bulgarian Split Squat", "category": "Legs"},
    {"name": "Standing Calf Raise", "category": "Legs"},
    {"name": "Overhead Barbell Press", "category": "Shoulders"},
    {"name": "Dumbbell Lateral Raise", "category": "Shoulders"},
    {"name": "Face Pull", "category": "Shoulders"},
    {"name": "Dumbbell Arnold Press", "category": "Shoulders"},
    {"name": "Barbell Bicep Curl", "category": "Arms"},
    {"name": "Incline Dumbbell Curl", "category": "Arms"},
    {"name": "Tricep Rope Pushdown", "category": "Arms"},
    {"name": "Skull Crushers (EZ Bar)", "category": "Arms"},
    {"name": "Weighted Cable Crunch", "category": "Core"},
    {"name": "Hanging Leg Raise", "category": "Core"},
    {"name": "Ab Wheel Rollout", "category": "Core"}
]


@app.route("/dashboard")
@login_required
def dashboard():
    """Personalized fitness & nutrition dashboard for the logged-in user."""
    user_id = session["user_id"]
    user = get_user_by_id(user_id)

    if not user.get("weight") or not user.get("goal"):
        flash("Please complete your body metrics to generate your custom plan.", "info")
        return redirect(url_for("profile"))

    dietary_preference = user.get("dietary_preference") or "Non-Vegetarian"
    allergies = user.get("allergies") or "None"
    meal_schedule = user.get("meal_schedule") or "Standard (4-5 Meals)"

    metrics = calculate_user_metrics(
        user["age"] or 25,
        user["gender"] or "Male",
        user["height"] or 175.0,
        user["weight"],
        user["goal"],
        user["target_weight"] or user["weight"],
        user["activity_level"] or "Moderate",
        dietary_preference,
        allergies,
        meal_schedule
    )

    top_prs = get_personal_records(user_id=user_id)[:4]

    return render_template(
        "dashboard.html",
        user_id=user_id,
        name=user["name"],
        age=user["age"],
        gender=user["gender"],
        height=user["height"],
        weight=user["weight"],
        target_weight=user["target_weight"],
        goal=user["goal"],
        activity_level=user["activity_level"],
        top_prs=top_prs,
        exercises=DEFAULT_EXERCISES,
        today=datetime.now().strftime("%Y-%m-%d"),
        **metrics
    )


@app.route("/dashboard/<int:user_id>")
@login_required
def view_dashboard(user_id):
    """Enforce data isolation: redirect users attempting to access another user's dashboard."""
    if user_id != session["user_id"]:
        return redirect(url_for("dashboard"))
    return dashboard()


@app.route("/history")
@login_required
def history():
    """Display logged-in user's profile and assessment snapshot."""
    user = get_user_by_id(session["user_id"])
    return render_template("history.html", users=[user] if user else [])


# ==============================================================================
# Progress & Personal Records (PR) Tracker Routes (Strictly Isolated to User)
# ==============================================================================

@app.route("/progress")
@login_required
def progress():
    user_id = session["user_id"]
    category = request.args.get("category", default="All")

    stats = get_progress_stats(user_id=user_id)
    personal_records = get_personal_records(user_id=user_id, category=category)
    history_list = get_exercise_history(user_id=user_id, category=category, limit=50)

    return render_template(
        "progress.html",
        selected_category=category,
        stats=stats,
        personal_records=personal_records,
        history=history_list,
        exercises=DEFAULT_EXERCISES,
        today=datetime.now().strftime("%Y-%m-%d")
    )

@app.route("/progress/add", methods=["POST"])
@login_required
def add_progress():
    user_id = session["user_id"]
    exercise_name = request.form.get("exercise_name", "").strip()
    category = request.form.get("category", "Chest").strip()
    weight = request.form.get("weight_lifted", type=float)
    reps = request.form.get("reps", type=int)
    sets = request.form.get("sets", default=1, type=int)
    notes = request.form.get("notes", "").strip()
    logged_date = request.form.get("logged_date") or datetime.now().strftime("%Y-%m-%d")
    redirect_to = request.form.get("redirect_to")

    if exercise_name and weight is not None and reps:
        new_id, is_new_pr, old_pr_weight = log_exercise_record(
            user_id, exercise_name, category, weight, reps, sets, notes, logged_date
        )
        if is_new_pr:
            flash(f"🎉 NEW PERSONAL RECORD! {exercise_name}: {weight} kg (Previous best: {old_pr_weight} kg) recorded in your PR Vault!", "success")
        else:
            flash(f"✅ Lift logged: {exercise_name} - {weight} kg × {reps} reps recorded in your PR Vault.", "info")

    if redirect_to == "dashboard":
        return redirect(url_for("dashboard"))
    return redirect(url_for("progress"))

@app.route("/progress/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_progress(record_id):
    user_id = session["user_id"]
    delete_exercise_record(record_id, user_id=user_id)
    flash("Exercise log entry deleted.", "info")
    return redirect(url_for("progress"))

# ==============================================================================
# Personal Situational AI Coach Routes (Strictly Scoped to Logged-in User)
# ==============================================================================

@app.route("/ai-coach")
@login_required
def ai_coach():
    user_id = session["user_id"]
    user_context = get_user_context(user_id)
    chat_history = get_chat_history(user_id=user_id, limit=40)

    return render_template(
        "ai_coach.html",
        user_context=user_context,
        chat_history=chat_history
    )

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    user_id = session["user_id"]
    situation_tag = data.get("situation_tag", "general")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Persist user message scoped to logged-in user
    save_chat_message(user_id, "user", message, situation_tag)

    # Generate response
    reply = generate_situational_advice(message, user_id=user_id, situation_tag=situation_tag)

    # Persist AI response scoped to logged-in user
    save_chat_message(user_id, "ai", reply, situation_tag)

    return jsonify({
        "status": "success",
        "reply": reply,
        "situation_tag": situation_tag,
        "user_id": user_id
    })

@app.route("/api/chat/history")
@login_required
def api_chat_history():
    user_id = session["user_id"]
    messages = get_chat_history(user_id=user_id, limit=50)
    return jsonify({"messages": messages})

@app.route("/api/chat/clear", methods=["POST"])
@login_required
def api_chat_clear():
    user_id = session["user_id"]
    clear_chat_history(user_id)
    return jsonify({"status": "cleared"})

@app.route("/api/user-summary/<int:user_id>")
@login_required
def api_user_summary(user_id):
    # Enforce data isolation
    if user_id != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403
    ctx = get_user_context(user_id)
    if not ctx:
        return jsonify({"error": "User not found"}), 404
    return jsonify(ctx)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)