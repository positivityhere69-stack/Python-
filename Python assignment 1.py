# ============================================================
# Name: Shubham 
# Date: 2nd November 2025
# Project: Daily Calorie Tracker CLI
# ============================================================

import datetime

print("=======================================")
print("   Welcome to the Daily Calorie Tracker")
print("=======================================\n")
print("This tool helps you log your meals and track total calories consumed.")
print("You can also compare it against your daily calorie limit!\n")

# ---------------------- Task 2: Input & Data Collection ----------------------
meals = []
calories = []

num_meals = int(input("How many meals do you want to enter today? "))

for i in range(num_meals):
    meal_name = input(f"\nEnter meal {i+1} name: ")
    calorie_amount = float(input(f"Enter calories for {meal_name}: "))
    meals.append(meal_name)
    calories.append(calorie_amount)

# ---------------------- Task 3: Calorie Calculations -------------------------
total_calories = sum(calories)
average_calories = total_calories / len(calories)
daily_limit = float(input("\nEnter your daily calorie limit: "))

# ---------------------- Task 4: Exceed Limit Warning System ------------------
if total_calories > daily_limit:
    status_message = f"⚠️  You have exceeded your daily limit by {total_calories - daily_limit:.2f} calories!"
else:
    status_message = f"✅ Great job! You are within your daily limit. Remaining: {daily_limit - total_calories:.2f} calories."

# ---------------------- Task 5: Formatted Output -----------------------------
print("\n\n========= DAILY CALORIE REPORT =========\n")
print("Meal Name\tCalories")
print("---------------------------------------")

for meal, cal in zip(meals, calories):
    print(f"{meal:<15}\t{cal:.2f}")

print("---------------------------------------")
print(f"Total:\t\t{total_calories:.2f}")
print(f"Average:\t{average_calories:.2f}\n")
print(status_message)
print("\n=======================================\n")

# ---------------------- Task 6 (Bonus): Save Session Log ---------------------
save_option = input("Do you want to save this session report to a file? (yes/no): ").lower()

if save_option == "yes":
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"calorie_log_{timestamp}.txt"
    with open(filename, "w") as f:
        f.write("=== Daily Calorie Tracker Report ===\n")
        f.write(f"Date: {datetime.datetime.now()}\n\n")
        for meal, cal in zip(meals, calories):
            f.write(f"{meal:<15}\t{cal:.2f}\n")
        f.write("---------------------------------------\n")
        f.write(f"Total:\t\t{total_calories:.2f}\n")
        f.write(f"Average:\t{average_calories:.2f}\n")
        f.write(f"Status: {status_message}\n")
    print(f"\n✅ Report saved successfully as '{filename}'!")

print("\nThank you for using the Daily Calorie Tracker!")
print("Stay healthy and track wisely 💪")