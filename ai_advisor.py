"""
ai_advisor.py - Personal AI Fitness Coach & Situational Advisor for FitLift.
Provides intelligent, context-aware guidance based on user biometrics, 
fitness goals, dietary needs, exercise PRs, and real-time situational inquiries.
"""

import os
import json
import re
from datetime import datetime
import sqlite3

def get_user_context(user_id):
    """Fetches user profile metrics and personal best PRs for contextual prompt injection."""
    from database import get_db_connection, get_personal_records
    
    if not user_id:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, age, gender, height, weight, goal, target_weight, 
               activity_level, dietary_preference, allergies, meal_schedule 
        FROM users WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    user = dict(row)
    
    # Calculate BMI
    height_m = user["height"] / 100.0 if user.get("height") else 1.75
    weight = user.get("weight") or 70.0
    bmi = round(weight / (height_m ** 2), 1) if height_m > 0 else 22.0
    user["bmi"] = bmi

    # Fetch top PRs
    prs = get_personal_records(user_id=user_id)
    user["personal_records"] = [
        {"exercise": p["exercise_name"], "weight": p["weight_lifted"], "reps": p["reps"], "1rm": p["estimated_1rm"]}
        for p in prs[:5]
    ]

    return user

def generate_situational_advice(user_message, user_id=None, situation_tag="general"):
    """
    Main entry point for generating personalized AI advice according to the situation.
    Uses contextual sports science reasoning engine with optional LLM augmentation.
    """
    user_context = get_user_context(user_id)
    msg_lower = user_message.lower()

    # If an external Gemini API key is configured, try calling it with the context prompt
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            return call_gemini_api(user_message, user_context, situation_tag, gemini_key)
        except Exception as e:
            # Fall back smoothly to expert reasoning engine
            print(f"[AI Advisor] Gemini API call skipped/failed ({e}), using built-in reasoning engine.")

    # Built-in High Fidelity Sports Science Reasoning Engine
    return expert_reasoning_engine(user_message, user_context, situation_tag)

def expert_reasoning_engine(message, user, situation_tag):
    """
    Built-in expert sports science and nutrition engine.
    Matches situation tags, keywords, biometrics, dietary constraints, and lift PRs.
    """
    name = user["name"] if user else "Athlete"
    goal = user["goal"] if user else "Muscle Gain & Strength"
    weight = user["weight"] if user else 70.0
    target_weight = user["target_weight"] if user else 72.0
    diet = user["dietary_preference"] if user else "Non-Vegetarian"
    allergies = user["allergies"] if user else "None"
    prs = user.get("personal_records", []) if user else []

    msg = message.lower()

    # Formulate personal PR callout text if available
    pr_summary = ""
    if prs:
        top_lifts = [f"**{p['exercise']}** ({p['weight']} kg × {p['reps']} reps)" for p in prs[:3]]
        pr_summary = f" (Current top PRs: {', '.join(top_lifts)})"

    # =========================================================================
    # SITUATION 1: Soreness, Fatigue, Recovery & DOMS
    # =========================================================================
    if situation_tag == "soreness" or (situation_tag == "general" and any(w in msg for w in ["sore", "soreness", "fatigue", "tired", "doms", "exhausted", "stiff", "rest day"])):
        return (
            f"### 🩹 FitLift Recovery & Fatigue Protocol for {name}\n\n"
            f"Muscle soreness (DOMS) is a normal response to micro-tears and novel muscular stimuli, but your actions right now determine whether you grow or overtrain.\n\n"
            f"**1. Can you work out today?**\n"
            f"- **Mild/Moderate Soreness (1-4/10)**: Yes! Perform an **Active Recovery session** or train an unaffected muscle group (e.g. if your chest/shoulders are sore from benching, focus on legs or core).\n"
            f"- **Severe Soreness (7-10/10) or Joint Aches**: Take a **Deload / Complete Rest Day**. Pushing high intensity with inflamed connective tissue raises injury risk.\n\n"
            f"**2. Accelerated Recovery Actions:**\n"
            f"- **Low-Intensity Cardio**: 15–20 minutes of brisk treadmill incline walking or light cycling to flush lactic waste and stimulate blood perfusion.\n"
            f"- **Hydration & Electrolytes**: Drink at least {round(weight * 0.04, 1)}L of water with a pinch of Himalayan pink salt or electrolytes.\n"
            f"- **Targeted Nutrition**: Ensure you hit your protein target ({round(weight * 2.0)}g) to supply essential amino acids (Leucine) for myofibrillar protein synthesis.\n"
            f"- **Sleep Hygiene**: Aim for 7.5–9 hours of deep sleep tonight; 95% of growth hormone is released during Stage 3/4 Slow-Wave Sleep."
        )

    # =========================================================================
    # SITUATION 2: Strength Plateau & Breaking Personal Records (PRs)
    # =========================================================================
    elif situation_tag == "plateau" or (situation_tag == "general" and (any(w in msg for w in ["plateau", "stuck", "can't increase", "lift heavier", "personal record", "stall", "stalled"]) or re.search(r'\bprs?\b', msg))):
        specific_lift = "your main compound lift"
        if "bench" in msg:
            specific_lift = "Barbell Bench Press"
        elif "squat" in msg:
            specific_lift = "Barbell Squat"
        elif "deadlift" in msg:
            specific_lift = "Deadlift"
        elif "press" in msg:
            specific_lift = "Overhead Press"

        return (
            f"### 🧱 PR Breakthrough & Plateau Breaker for {name}\n\n"
            f"Hitting a strength plateau on {specific_lift}{pr_summary} is a milestone—it means your central nervous system (CNS) requires a strategic stimulus shift to trigger fresh neurological and muscular adaptation.\n\n"
            f"**1. The Micro-Loading Strategy (+1.25 kg to 2.5 kg):**\n"
            f"- Stop trying to jump 5 kg or 10 kg at once. Use fractional 1.25 kg plates. Adding just 2.5 kg total to the bar each fortnight yields a **65 kg annual increase**.\n\n"
            f"**2. Periodization Wave (Step-Back to Leap Forward):**\n"
            f"- Drop the working weight by **10%** next session, but execute each rep with maximal explosive bar speed and a 2-second pause at the sticking point.\n"
            f"- Week 1: 85% of plateau weight (5 reps × 4 sets)\n"
            f"- Week 2: 90% (5 reps × 4 sets)\n"
            f"- Week 3: 95% (4 reps × 4 sets)\n"
            f"- Week 4: **PR Attempt** (Plateau weight + 2.5 kg for clean reps!)\n\n"
            f"**3. Target the Weakest Link (Accessories):**\n"
            f"- If stuck at the bottom: Add **Paused Reps** (pause 2 sec at chest/bottom of squat).\n"
            f"- If stuck at lockout: Strengthen triceps and upper back with heavy close-grip presses or rack pulls.\n\n"
            f"**4. Calorie & Sleep Audit:**\n"
            f"- Strength gain requires fuel. With your goal of **{goal}**, ensure you are eating at least a 200–300 kcal surplus on heavy lifting days."
        )

    # =========================================================================
    # SITUATION 3: Time Crunch / Express Workout (20-30 Minutes)
    # =========================================================================
    elif situation_tag == "quick_workout" or (situation_tag == "general" and any(w in msg for w in ["quick", "short on time", "20 min", "25 min", "30 min", "no time", "busy", "fast workout", "hurry"])):
        return (
            f"### ⏱️ High-Density Express Workout (25-Minute Protocol)\n\n"
            f"Short on time today, {name}? You can achieve 90% of a full session's hypertrophy and metabolic stimulus in 25 minutes using **Antagonist Paired Supersets**.\n\n"
            f"**⚡ Warm-Up (3 Minutes):**\n"
            f"- 20 Arm Circles, 15 Bodyweight Air Squats, 10 World's Greatest Stretch.\n\n"
            f"**🔥 Superset Block 1 (12 Minutes - Upper Body Antagonists):**\n"
            f"- **Exercise A1**: Dumbbell or Barbell Chest Press — 3 sets × 8–10 reps\n"
            f"- *Rest 30 seconds*\n"
            f"- **Exercise A2**: Chest-Supported Dumbbell Rows or Pull-ups — 3 sets × 8–10 reps\n"
            f"- *Rest 60 seconds and repeat for 3 rounds total.*\n\n"
            f"**💥 Superset Block 2 (10 Minutes - Lower Body & Core Density):**\n"
            f"- **Exercise B1**: Goblet Squats or Romanian Deadlifts — 3 sets × 10–12 reps\n"
            f"- *Rest 30 seconds*\n"
            f"- **Exercise B2**: Hanging Knee Raises or Plank Hold (45 sec) — 3 sets\n"
            f"- *Rest 60 seconds and repeat for 3 rounds total.*\n\n"
            f"**Coach Tip**: Keep your phone away between sets. Rest intervals must remain strictly under 60 seconds to maintain high metabolic density!"
        )

    # =========================================================================
    # SITUATION 4: Nutrition Emergency / Missed Protein / Overeating
    # =========================================================================
    elif situation_tag == "nutrition" or (situation_tag == "general" and any(w in msg for w in ["protein", "missed meal", "hunger", "hungry", "snack", "eat", "diet", "macros", "junk food", "cheat meal", "overate"])):
        # Tailor food recommendations based on dietary preferences and allergies
        if "Keto" in diet:
            snack_ideas = "• 3 Hard-Boiled Eggs with pink salt (18g protein, 0g carb)\n• 100g Canned Tuna or Salmon with avocado mayo (25g protein)\n• Handful of roasted macadamias or pumpkin seeds with cheddar cubes (15g protein)"
        elif "Vegan" in diet:
            snack_ideas = "• Plant Protein Shake (pea/rice isolate) in fortified almond milk (25g protein)\n• 150g Pan-seared Firm Tofu cubes with nutritional yeast (20g protein)\n• 1 cup Steamed Edamame or roasted spiced chickpeas (17g protein)"
        elif "Vegetarian" in diet:
            snack_ideas = "• 200g Fresh Low-Fat Cottage Cheese / Paneer or Greek Yogurt (22g protein)\n• 1 scoop Whey Isolate with oat milk (24g protein)\n• Roasted Soya Chunks with chat masala (25g protein)"
        else:
            snack_ideas = "• 150g Grilled Skinless Chicken Breast or Canned Tuna (35g protein)\n• 1 cup Plain Low-Fat Greek Yogurt with berries (20g protein)\n• 3 Whole Boiled Eggs + 2 Egg Whites (24g protein)"

        return (
            f"### 🥑 Situational Nutrition Strategy for {name}\n\n"
            f"Nutrition is about weekly consistency, not single-meal perfection. Here is how to handle your situation based on your **{diet}** preference:\n\n"
            f"**1. If You Are Short on Protein Today:**\n"
            f"{snack_ideas}\n\n"
            f"**2. If You Overate or Had an Unplanned High-Calorie Meal:**\n"
            f"- **Do NOT starve yourself tomorrow.** Extreme restriction triggers binge-eating cycles.\n"
            f"- Treat it as a 'Re-feed Day' that refilled your muscle glycogen stores. Channel that energy into hitting a heavy lift tomorrow!\n"
            f"- Drink 500ml extra water to offset sodium retention and take a 20-minute post-meal walk to blunt insulin spikes.\n\n"
            f"**3. Pre-Workout Fuel Check:**\n"
            f"- If working out in 45 minutes: Consume 25g fast-digesting carbs (1 banana or 2 rice cakes) + black coffee."
        )

    # =========================================================================
    # SITUATION 5: Joint Aches / Injury Prevention / Safe Exercise Swaps
    # =========================================================================
    elif situation_tag == "injury_recovery" or (situation_tag == "general" and any(w in msg for w in ["pain", "hurt", "hurts", "knee", "shoulder", "lower back", "elbow", "injury", "ache", "wrist"])):
        return (
            f"### 🛡️ Biomechanical Joint Relief & Safe Exercise Swaps\n\n"
            f"⚠️ *Important: If you experience sharp, shooting, or radiating nerve pain, please consult a physiotherapist or medical doctor.*\n\n"
            f"If you are dealing with common gym friction or joint discomfort, here are the gold-standard exercise substitutes:\n\n"
            f"**1. Shoulder Pain during Pressing?**\n"
            f"- **Swap**: Flat Barbell Bench Press &rarr; **Neutral-Grip Dumbbell Floor Press** or **Slight Incline (15-30°) Dumbbell Press**.\n"
            f"- *Why*: Floor pressing limits humeral extension at 90°, relieving anterior shoulder capsule impingement.\n\n"
            f"**2. Knee Discomfort during Squats?**\n"
            f"- **Swap**: Forward-knee quad squats &rarr; **Box Squats** or **Romanian Deadlifts (RDLs)**.\n"
            f"- *Why*: Box squats force a vertical shin angle and shift the loading torque to the glutes and hamstrings, offloading the patellar tendon.\n\n"
            f"**3. Lower Back Tightness during Deadlifts/Rows?**\n"
            f"- **Swap**: Bent-over Barbell Rows &rarr; **Chest-Supported Incline Dumbbell Row** or **Lat Pulldowns**.\n"
            f"- *Why*: Taking spinal erector shear stress off the lower back while isolating the lats and rhomboids."
        )

    # =========================================================================
    # SITUATION 6: Travel / Hotel / No Equipment
    # =========================================================================
    elif situation_tag == "travel" or (situation_tag == "general" and any(w in msg for w in ["travel", "traveling", "hotel", "no gym", "equipment", "holiday", "vacation", "home workout"])):
        return (
            f"### ✈️ Hotel & Travel Calisthenics Protocol for {name}\n\n"
            f"No gym? No problem. By manipulating **tempo (3-second eccentric)**, leverage, and rest intervals, you can create intense mechanical tension using zero equipment.\n\n"
            f"**The 4-Round Travel Circuit (No Equipment Needed):**\n"
            f"1. **Tempo Push-Ups (3 sec down, 1 sec pause)** — 12 to 15 reps\n"
            f"2. **Bulgarian Split Squats (Rear foot on hotel bed/chair)** — 12 reps per leg\n"
            f"3. **Pike Push-Ups or Elevated Feet Dips** — 10 to 12 reps (Shoulders & Triceps)\n"
            f"4. **Isometric Prone Back Cobras / Y-T-W Holds** — 15 reps (Upper Back & Posture)\n"
            f"5. **Hollow Body Rock or Slow Bicycle Crunches** — 45 seconds (Deep Core)\n\n"
            f"- Rest 75 seconds after completing all 5 movements. Repeat for 3 to 4 rounds total.\n"
            f"- **Coach Tip**: Pack a single light resistance loop band in your luggage—it weighs 50g and unlocks 20+ upper body pulls!"
        )

    # =========================================================================
    # SITUATION 7: 1RM / PR Attempt Warm-Up Ladder
    # =========================================================================
    elif situation_tag in ["pr_attempt", "1rm"] or (situation_tag == "general" and (any(w in msg for w in ["1rm", "max out", "test max", "attempt pr", "new pr"]) or re.search(r'\b1rm\b', msg))):
        return (
            f"### 🚀 Official 1-Rep Max (1RM) Warm-Up Ladder for {name}\n\n"
            f"When testing a new Personal Record, your warm-up must prep the nervous system without fatiguing muscle glycogen stores.\n\n"
            f"**Target PR Attempt: e.g., 100 kg Goal**\n"
            f"- **Set 1**: Empty Bar × 10 reps (Joint lubrication & groove calibration)\n"
            f"- *Rest 60 sec*\n"
            f"- **Set 2**: 50% of Goal × 5 reps (Fast, crisp bar speed)\n"
            f"- *Rest 90 sec*\n"
            f"- **Set 3**: 70% of Goal × 3 reps (Focus on bracing & foot rooting)\n"
            f"- *Rest 2 minutes*\n"
            f"- **Set 4**: 85% of Goal × 1 rep (Potentiation single)\n"
            f"- *Rest 2.5 minutes*\n"
            f"- **Set 5**: 93% of Goal × 1 rep (Confidence single)\n"
            f"- *Rest 3 to 4 minutes*\n"
            f"- **🏆 SET 6 (PR ATTEMPT)**: 100%+ × 1 to 3 Reps!\n\n"
            f"**Safety Checklist**: Set the safety spotter pins, take a big belly breath (Valsalva brace), and keep chalk or wrist wraps handy!"
        )

    # =========================================================================
    # SITUATION 8: General / Conversational Advisor Response
    # =========================================================================
    return (
        f"### 🤖 FitLift Coach Advice for {name}\n\n"
        f"Thanks for checking in! Based on your active profile ({goal}, Weight: {weight} kg, Diet: {diet}), here is my guidance:\n\n"
        f"**1. Core Assessment:**\n"
        f"Progress in fitness comes from progressive overload, precision recovery, and strategic fueling. "
        f"{f'You currently have {len(prs)} Personal Records logged in your vault.' if prs else 'Start logging your exercises in the Progress Tracker to unlock tailored load recommendations!'}\n\n"
        f"**2. Immediate Action Steps:**\n"
        f"- Ensure each workout session features at least one compound lift where you track weight and reps.\n"
        f"- Hit your targeted daily water intake ({round(weight * 0.038, 1)} Liters).\n"
        f"- If you're facing a specific challenge today (e.g. sore muscles, stuck on bench press, traveling, or low energy), tap one of the quick scenario buttons above or tell me how you feel!"
    )

def call_gemini_api(user_message, user_context, situation_tag, api_key):
    """Optional external Gemini API integration if user configures GEMINI_API_KEY."""
    import urllib.request
    
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    context_str = json.dumps(user_context or {})
    prompt = f"""
You are the elite AI Fitness Coach & Situational Advisor for the FitLift platform.
User Context: {context_str}
Situation Tag: {situation_tag}

User Query: {user_message}

Provide concise, highly motivating, scientifically validated fitness/nutrition advice tailored precisely to their current situation, goal, biometrics, and exercise PRs. Use clean markdown formatting with bullet points and bold headers.
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }
    
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=8) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["candidates"][0]["content"]["parts"][0]["text"]
