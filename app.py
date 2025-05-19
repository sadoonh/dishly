import streamlit as st
import pandas as pd
import json
import plotly.express as px # Added for pie chart]
import plotly.graph_objects as go

# Calorie Calculator Class
class CalorieCalculator:
    _POUNDS_TO_KG_FACTOR = 0.453592
    _INCHES_TO_CM_FACTOR = 2.54
    _FEET_TO_INCHES_FACTOR = 12

    _ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "extra_active": 1.9
    }
    _VALID_SEX_OPTIONS = ["male", "female"]

    def __init__(self, weight_lbs: float, height_ft: int, height_in: int, age_years: int, sex: str, activity_level: str):
        # --- Input Validation ---
        if not (isinstance(weight_lbs, (int, float)) and weight_lbs > 0):
            raise ValueError("Weight must be a positive number.")
        if not (isinstance(height_ft, int) and height_ft >= 0):
            raise ValueError("Height (feet) must be a non-negative integer.")
        if not (isinstance(height_in, int) and 0 <= height_in < self._FEET_TO_INCHES_FACTOR):
            raise ValueError(f"Height (inches) must be an integer between 0 and {self._FEET_TO_INCHES_FACTOR - 1}.")
        if not (isinstance(age_years, int) and age_years > 0):
            raise ValueError("Age must be a positive integer.")

        processed_sex = sex.lower()
        if processed_sex not in self._VALID_SEX_OPTIONS:
            raise ValueError(f"Invalid sex. Choose from: {', '.join(self._VALID_SEX_OPTIONS)}.")

        processed_activity_level = activity_level.lower()
        if processed_activity_level not in self._ACTIVITY_MULTIPLIERS:
            raise ValueError(f"Invalid activity level. Choose from: {', '.join(self._ACTIVITY_MULTIPLIERS.keys())}.")

        # --- Store processed and converted values ---
        self._weight_kg = weight_lbs * self._POUNDS_TO_KG_FACTOR

        total_inches = (height_ft * self._FEET_TO_INCHES_FACTOR) + height_in
        self._height_cm = total_inches * self._INCHES_TO_CM_FACTOR

        self._age_years = age_years
        self._sex = processed_sex
        self._activity_level = processed_activity_level

    def _calculate_bmr(self) -> float:
        bmr: float
        if self._sex == "male":
            bmr = (10 * self._weight_kg) + (6.25 * self._height_cm) - (5 * self._age_years) + 5
        else: # female
            bmr = (10 * self._weight_kg) + (6.25 * self._height_cm) - (5 * self._age_years) - 161
        return bmr

    def get_maintenance_calories(self) -> float:
        """
        Calculates the Total Daily Energy Expenditure (TDEE) or maintenance calories.
        """
        bmr = self._calculate_bmr()
        multiplier = self._ACTIVITY_MULTIPLIERS[self._activity_level]
        tdee = bmr * multiplier
        return tdee

# Function to load CSS from file
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found. Styling may be affected.")


# Function to load and process data from JSON file into a Pandas DataFrame
@st.cache_data
def load_and_process_data(file_path):
    try:
        df = pd.read_json(file_path)

        if df.empty:
            st.warning(f"The file {file_path} was loaded but is empty.")
            return df

        if 'dish_name' not in df.columns:
            st.error(f"Critical Error: The 'dish_name' column is missing in {file_path}. Cannot proceed.")
            return None

        df = df.drop_duplicates(subset=['dish_name'], keep='first')

        return df
    except FileNotFoundError:
        st.error(f"Error: The file {file_path} was not found. Please make sure it's in the same directory as app.py.")
        return None
    except ValueError as ve:
        st.error(f"Error: Could not decode JSON from {file_path}. It might be malformed. Details: {ve}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while loading data: {e}")
        return None


def styled_field(label, value, label_size="16px", value_size="20px", label_color="#EEA179", value_color="#FFFFFF"):
    """
    Create a styled field with label and value stacked vertically
    """
    return f"""
        <div class='styled-field' style='margin-bottom: 15px; font-family: Roboto, sans-serif;'>
            <div class='styled-field-label' style='font-size: {label_size};  color: {label_color}; margin-bottom: 5px; font-family: Roboto, sans-serif;'>
                {label}
            </div>
            <div class='styled-field-value' style='font-size: {value_size}; font-weight: bold; color: {value_color}; margin-left: 15px; font-family: Roboto, sans-serif;'>
                {value}
            </div>
        </div>
    """

# Function to extract calories from different possible formats
def extract_calories(calories_value):
    """
    Extract numeric calories from various formats like "150 calories", "150", 150, etc.
    Returns 0 if extraction fails.
    """
    if calories_value is None:
        return 0
    
    try:
        # If it's already a number
        if isinstance(calories_value, (int, float)):
            return float(calories_value)
        
        # If it's a string, try to extract the number
        if isinstance(calories_value, str):
            # Remove common words and whitespace, then extract number
            import re
            numbers = re.findall(r'\d+\.?\d*', calories_value)
            if numbers:
                return float(numbers[0])
    except (ValueError, TypeError):
        pass
    
    return 0

# --- Streamlit App ---
st.set_page_config(layout="wide")

# Load CSS from external file
load_css('styles.css')

# Remove top margin/padding
st.markdown("""
<style>
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        margin-top: 0rem;
    }
</style>
""", unsafe_allow_html=True)

# Display the logo with st.image for better size control
col1_logo, col2_logo, col3_logo, col4_logo, col5_logo, col6_logo, col7_logo = st.columns([1, 1, 1, 1, 1, 1, 1])
with col4_logo: # Using a unique name for logo column
    st.image("icons8-dish-64.png", width=160)

# Load the data
dishes_df = load_and_process_data("dishes.json")

if dishes_df is not None and not dishes_df.empty:
    dish_col, calc_col, gap_col = st.columns([1.2, 2.2, 0.6])
    with dish_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<h3 style="padding-left: 80px;">Select a Dish</h3>', unsafe_allow_html=True)
        dish_names = sorted(dishes_df["dish_name"].tolist())
        options = [""] + dish_names
        selected_dish_name = st.selectbox("", options, key="dish_select", label_visibility="collapsed")
            
    with calc_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.expander("📐 Calculate Your Daily Calories", expanded=True):
            # Create three columns for the calculator inputs
            calc_col1_input, calc_col2_input, calc_col3_input, calc_col4_input, calc_col5_input = st.columns(5) # Renamed for clarity

            # First row
            with calc_col1_input:
                weight_lbs = st.number_input("Weight (lbs)", min_value=1.0, value=180.0, step=1.0, format="%.0f")

            with calc_col2_input:
                # Generate height options from 4'0" to 7'0"
                height_options = []
                height_values = {}  # Maps display string to (feet, inches) tuple

                for feet in range(4, 8):  # 4 to 7 feet
                    for inches in range(12):  # 0 to 11 inches
                        display_text = f"{feet}'{inches}\""
                        height_options.append(display_text)
                        height_values[display_text] = (feet, inches)

                selected_height = st.selectbox("Height", height_options, index=height_options.index("5'10\"") if "5'10\"" in height_options else 0) # Default to 5'10"
                height_ft, height_in = height_values[selected_height]

            with calc_col3_input:
                age_years = st.number_input("Age (years)", min_value=1, value=28, step=1)

            with calc_col4_input:
                sex = st.selectbox("Gender", ["Male", "Female"])

            calc_col_activity, calc_col_button_spacer = st.columns([1.2, 0.8]) # Renamed for clarity

            with calc_col_activity:
            # Second row - Activity level takes full width
                activity_level = st.selectbox("Activity Level", [
                    "Sedentary (little/no exercise)",
                    "Light (light exercise 1-3 days/week)",
                    "Moderate (moderate exercise 3-5 days/week)",
                    "Active (hard exercise 6-7 days/week)",
                    "Extra Active (very hard exercise/physical job)"
                ])

            # Map activity level display to internal values
            activity_map = {
                "Sedentary (little/no exercise)": "sedentary",
                "Light (light exercise 1-3 days/week)": "light",
                "Moderate (moderate exercise 3-5 days/week)": "moderate",
                "Active (hard exercise 6-7 days/week)": "active",
                "Extra Active (very hard exercise/physical job)": "extra_active"
            }

            # Initialize session state for calculator results
            if 'maintenance_calories' not in st.session_state:
                st.session_state.maintenance_calories = None
            if 'calc_error' not in st.session_state:
                st.session_state.calc_error = None

            if st.button("Calculate Maintenance Calories", type="primary"):
                try:
                    calculator = CalorieCalculator(
                        weight_lbs=int(weight_lbs),
                        height_ft=int(height_ft),
                        height_in=int(height_in),
                        age_years=int(age_years),
                        sex=sex.lower(),
                        activity_level=activity_map[activity_level]
                    )

                    maintenance_calories = calculator.get_maintenance_calories()

                    # Store results in session state
                    st.session_state.maintenance_calories = maintenance_calories
                    st.session_state.calc_error = None

                except ValueError as e:
                    st.session_state.calc_error = f"Error: {e}"
                    st.session_state.maintenance_calories = None
                except Exception as e:
                    st.session_state.calc_error = f"An unexpected error occurred: {e}"
                    st.session_state.maintenance_calories = None

            # Display stored results
            if st.session_state.maintenance_calories is not None:
                st.success(f"Your daily maintenance calories: **{st.session_state.maintenance_calories:.0f} calories**")

                # Additional information
                st.info(f"""
                **Calorie Goals:**
                - **Maintain weight:** {st.session_state.maintenance_calories:.0f} calories/day
                - **Lose weight:** {st.session_state.maintenance_calories - 500:.0f} calories/day (lose 1 lb/week)
                - **Gain weight:** {st.session_state.maintenance_calories + 500:.0f} calories/day (gain 1 lb/week)
                """)

            # Display stored errors
            if st.session_state.calc_error is not None:
                st.error(st.session_state.calc_error)

    if selected_dish_name and selected_dish_name != "--- Select a Dish ---":
        selected_dish_series = dishes_df.loc[dishes_df["dish_name"] == selected_dish_name].iloc[0]

        # Improved auto-scroll to food section
        st.components.v1.html(f"""
        <script>
        setTimeout(function() {{
            let targetElement = document.getElementById('food-section');
            if (targetElement) {{
                targetElement.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'start',
                    inline: 'nearest'
                }});
            }} else {{
                // Fallback if ID not found, scroll by a fixed amount or to a more generic element
                const dishHeadings = document.querySelectorAll('h1');
                if (dishHeadings.length > 0) {{
                    // Attempt to find the h1 with the dish name
                    for (let heading of dishHeadings) {{
                        if (heading.textContent && heading.textContent.trim() === "{selected_dish_name.replace("'", "\\'")}") {{
                            heading.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                            return;
                        }}
                    }}
                    // If specific heading not found, scroll to the last h1 (likely the dish name)
                    dishHeadings[dishHeadings.length-1].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }} else {{
                     window.scrollBy({{ top: 600, behavior: 'smooth' }}); // Generic fallback
                }}
            }}
        }}, 500); // Increased delay to ensure content is rendered
        </script>
        """, height=0)

        st.markdown(f"<h2 style='text-align: center;' id='food-section'>{selected_dish_series['dish_name']}</h2>", unsafe_allow_html=True)
        st.divider()

        col_details_macros, col_ingredients, col_instructions = st.columns([1.3, 1, 1.7]) # Adjusted column names for clarity

        with col_details_macros:
            # Details expander
            with st.expander("**🔍 Details**", expanded=True):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(styled_field("Calories", selected_dish_series.get('calories', 'N/A'), value_color="#E8E8E8", label_color= '#BEBDB8'), unsafe_allow_html=True)
                    st.markdown(styled_field("Cost", selected_dish_series.get('cost', 'N/A'), value_color="#E8E8E8", label_color= '#BEBDB8'), unsafe_allow_html=True)
                    st.markdown(styled_field("Healthy Option", selected_dish_series.get('healthy_flag', 'N/A'), value_color="#E8E8E8", label_color= '#BEBDB8'), unsafe_allow_html=True)
                
                with col2:
                    # --- MODIFIED SECTION FOR DAILY CALORIC INTAKE PIE CHART (Minimalist) ---
                    dish_calories_val = selected_dish_series.get('calories')
                    
                    if dish_calories_val > 0:
                        # Use calculated maintenance calories if available, otherwise default to 2000
                        daily_target_calories = st.session_state.maintenance_calories if st.session_state.maintenance_calories is not None else 2000
                        
                        if daily_target_calories <= 0:
                            st.warning("Daily calorie target is not positive. Cannot render intake chart.")
                        else:
                            # Calculate the percentage of the dish relative to the daily target
                            dish_percentage_of_daily = (dish_calories_val / daily_target_calories) * 100
                            
                            pie_chart_labels = []
                            pie_chart_values = []
                            pie_chart_colors = []
                            custom_text_for_slices = []
                            pull_values = []

                            if dish_calories_val <= daily_target_calories:
                                pie_chart_labels = ['This Dish', 'Remaining']
                                pie_chart_values = [dish_calories_val, daily_target_calories - dish_calories_val]
                                pie_chart_colors = ['#EEA179','#a9a9a9']
                                custom_text_for_slices = [f'{dish_percentage_of_daily:.0f}%', '']
                                pull_values = [0.1, 0]  # Pull out "This Dish" slice slightly
                            else: # Dish exceeds daily calories
                                pie_chart_labels = ['This Dish']
                                pie_chart_values = [dish_calories_val]
                                pie_chart_colors = ['#D57D83']
                                custom_text_for_slices = [f'{dish_percentage_of_daily:.1f}%']
                                pull_values = [0.15]  # Pull out the exceeding slice more prominently
                            
                            # Create pie chart using go.Figure
                            fig_daily = go.Figure(data=[go.Pie(
                                labels=pie_chart_labels,
                                values=pie_chart_values,
                                pull=pull_values,
                                hole=0.35,
                                text=custom_text_for_slices,
                                textinfo='text',
                                textposition='inside',
                                insidetextorientation='auto',
                                textfont=dict(size=16, color='white'),
                                marker=dict(
                                    colors=pie_chart_colors,
                                    line=dict(color='#2E353B', width=4)
                                )
                            )])
                            
                            fig_daily.update_layout(
                                showlegend=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                margin=dict(l=0, r=0, t=5, b=0),
                                height=200
                            )
                            
                            # Display the chart
                            st.plotly_chart(fig_daily, use_container_width=True)
                            
                    else: # dish_calories_val <= 0
                        st.markdown(
                            "<p style='text-align: center; color: #BEBDB8; font-size: 14px; font-family: Roboto, sans-serif;'>"
                            "No calorie data available for daily intake calculation</p>",
                            unsafe_allow_html=True
                        )

            # Macros expander
            st.write("") # Adds a little space above the expander
            with st.expander("**🥕 Macros**", expanded=True):
                col1, col2 = st.columns([1, 1])
                with col1:
                    macros_data = selected_dish_series.get('macros') # Use .get for safety

                    if isinstance(macros_data, dict):
                        # Helper function to safely convert macro values to float
                        def get_macro_value(value_input):
                            if value_input is None:
                                return 0.0
                            value_str = str(value_input).strip().lower()
                            if value_str == 'n/a' or value_str == '':
                                return 0.0
                            try:
                                # Remove 'g' if present before converting
                                if isinstance(value_str, str) and value_str.endswith('g'):
                                    value_str = value_str[:-1].strip()
                                return float(value_str)
                            except (ValueError, TypeError):
                                return 0.0

                        protein_g_val = get_macro_value(macros_data.get('protein_g'))
                        carbs_g_val = get_macro_value(macros_data.get('carbs_g'))
                        fat_g_val = get_macro_value(macros_data.get('fat_g'))

                        # Display the styled fields for individual macro values
                        protein_display = f"{protein_g_val:.0f}g" if protein_g_val > 0 or (isinstance(macros_data.get('protein_g'), (int, float)) and macros_data.get('protein_g') == 0) else "N/A"
                        carbs_display = f"{carbs_g_val:.0f}g" if carbs_g_val > 0 or (isinstance(macros_data.get('carbs_g'), (int, float)) and macros_data.get('carbs_g') == 0) else "N/A"
                        fat_display = f"{fat_g_val:.0f}g" if fat_g_val > 0 or (isinstance(macros_data.get('fat_g'), (int, float)) and macros_data.get('fat_g') == 0) else "N/A"

                        st.markdown(styled_field("Protein", protein_display,  value_color="#E8E8E8", label_color= '#BEBDB8'), unsafe_allow_html=True)
                        st.markdown(styled_field("Carbohydrates", carbs_display, value_color="#E8E8E8", label_color= '#BEBDB8'), unsafe_allow_html=True)
                        st.markdown(styled_field("Fat", fat_display, value_color="#E8E8E8", label_color= '#BEBDB8'), unsafe_allow_html=True)
                
                with col2:
                    # Prepare data for pie chart (only include macros with positive gram values)
                    macro_names_for_chart = []
                    macro_values_for_chart = []

                    if protein_g_val > 0:
                        macro_names_for_chart.append('Protein')
                        macro_values_for_chart.append(protein_g_val)
                    if carbs_g_val > 0:
                        macro_names_for_chart.append('Carbs')
                        macro_values_for_chart.append(carbs_g_val)
                    if fat_g_val > 0:
                        macro_names_for_chart.append('Fat')
                        macro_values_for_chart.append(fat_g_val)

                    if sum(macro_values_for_chart) > 0: # Ensure there's something to plot
                        # Define colors - trying to match your app's aesthetic
                        # Order: Protein, Carbs, Fat (if present)
                        color_sequence = ['#EEA179', '#8ACC99', '#D57D83']

                        fig = px.pie(
                            names=macro_names_for_chart,
                            values=macro_values_for_chart,
                            hole=0.35, # Creates a donut chart
                            color_discrete_sequence=color_sequence[:len(macro_names_for_chart)] # Use only as many colors as needed
                        )

                        fig.update_traces(
                            textposition='inside',
                            textinfo='percent+label', # Shows "Protein 30%" etc.
                            texttemplate='%{label}<br>%{percent:.0%}',
                            insidetextorientation='auto', # Plotly chooses best orientation
                            textfont_size=16, # Slightly increased for better readability
                            textfont_color='white', # <<< CHANGED: Set text color inside slices to white
                            marker=dict(line=dict(color='#2E353B', width=4)) # Line between slices
                        )

                        fig.update_layout(
                            # title_text="Macronutrient Distribution", # <<< REMOVED: Title
                            # title_x=0.5,
                            # title_font_color="#EEA179",
                            # legend_title_font_color="#EEA179",
                            showlegend=False, # <<< ADDED: Remove legend
                            font_color="#FFFFFF",
                            paper_bgcolor='rgba(0,0,0,0)', # Transparent background
                            plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area
                            margin=dict(l=0, r=0, t=0, b=0), # Adjusted top margin due to no title
                            height=230, # Can adjust height as needed
                            # legend=dict( # <<< REMOVED: Legend configuration
                            #     orientation="h",
                            #     yanchor="bottom",
                            #     y=1.05,
                            #     xanchor="center",
                            #     x=0.5,
                            #     font=dict(size=12, color="#FFFFFF"),
                            #     bgcolor='rgba(0,0,0,0)'
                            # )
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown("<p style='font-size: 16px; color: #FFFFFF; font-family: Roboto, sans-serif; text-align: center;'>No macronutrient data (grams > 0) to display chart.</p>", unsafe_allow_html=True)
                    


        with col_ingredients:
            # Ingredients expander
            with st.expander("**📋Ingredients**", expanded=True):
                ingredients_list = selected_dish_series.get('ingredients') # Use .get for safety
                if isinstance(ingredients_list, list):
                    # Initialize session state for ingredient checkboxes if not exists
                    session_key_ingredients = f'ingredients_{selected_dish_name.replace(" ", "_")}' # Make key safer
                    if session_key_ingredients not in st.session_state:
                        st.session_state[session_key_ingredients] = {ing: False for ing in ingredients_list}

                    # Create checkboxes for each ingredient
                    for i, ingredient in enumerate(ingredients_list):
                        # Create unique key for each ingredient checkbox
                        checkbox_key = f"{selected_dish_name.replace(' ', '_')}_ingredient_{i}_{ingredient.replace(' ', '_')}"

                        # Create columns for checkbox and Amazon link
                        col_checkbox, col_amazon = st.columns([4, 1])
                        with col_checkbox:
                            # Create checkbox with custom styling
                            is_checked = st.checkbox(
                                ingredient,
                                key=checkbox_key,
                                # value=st.session_state[session_key_ingredients].get(ingredient, False)
                            )                            # Store the state
                            st.session_state[session_key_ingredients][ingredient] = is_checked

                        with col_amazon:
                            # Amazon Fresh link button
                            amazon_url = f"https://www.amazon.com/s?k={ingredient.replace(' ', '+')}&i=amazonfresh&crid=3F664Y5LIIAMQ&sprefix={ingredient.replace(' ', '%2C').lower()}%2Camazonfresh%2C128&ref=nb_sb_noss_1"
                            st.markdown(f"""
                                <a href='{amazon_url}' target='_blank' style='text-decoration: none;'>
                                    <button style='
                                        background-color: #8ACC99;
                                        color: white;
                                        border: none;
                                        padding: 7px 10px;
                                        border-radius: 20px;
                                        cursor: pointer;
                                        font-size: 12px;
                                        font-family: Roboto, sans-serif;
                                    ' onmouseover='this.style.backgroundColor="#9DD9AA"' onmouseout='this.style.backgroundColor="#8ACC99"'>
                                        Buy
                                    </button>
                                </a>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("<p style='font-size: 26px; color: #FFFFFF; font-family: Roboto, sans-serif;'>Ingredients data is not in the expected list format or is missing.</p>", unsafe_allow_html=True)

        with col_instructions:
            # Cooking Instructions expander
            with st.expander("**👩‍🍳 Cooking Instructions**", expanded=True):
                instruction_field_options = [
                    'cooking_instructions',
                    'cookingInstructions',
                    'instructions',
                    'cooking_steps',
                    'recipe_steps',
                    'preparation'
                ]

                instructions = None
                found_field = None

                for field in instruction_field_options:
                    if field in selected_dish_series and selected_dish_series[field] is not None:
                        instructions = selected_dish_series[field]
                        found_field = field
                        break

                if instructions is not None:
                    instruction_list = []
                    if isinstance(instructions, str):
                        # Split by common delimiters like comma, newline, or period followed by space
                        # This handles simple comma-separated strings or multi-line strings better
                        import re
                        instruction_list = [instr.strip() for instr in re.split(r'[,\n\.]\s*(?=[A-Z0-9])|(?<=\.)\s+|\s*-\s*', instructions) if instr.strip()]
                        if not instruction_list and len(instructions) > 20: # If regex split fails for a long string, treat as single step
                            instruction_list = [instructions.strip()]
                    elif isinstance(instructions, list):
                        instruction_list = [str(instr).strip() for instr in instructions if str(instr).strip()] # Ensure all items are strings
                    else:
                        st.warning(f"Cooking instructions format is unexpected: {type(instructions)}")

                    if instruction_list:
                        instructions_html = "<ol style='font-size: 16px; color: #FFFFFF; margin-left: 20px; font-family: Roboto, sans-serif;'>"
                        for instruction_item in instruction_list:
                            instructions_html += f"<li style='margin-bottom: 12px; font-family: Roboto, sans-serif;'>{instruction_item}</li>"
                        instructions_html += "</ol>"
                        st.markdown(instructions_html, unsafe_allow_html=True)
                    else: # If list ends up empty after processing
                        st.markdown("<p style='font-size: 18px; font-family: Roboto, sans-serif; color: #FFFFFF;'>No cooking instructions provided in a parsable format.</p>", unsafe_allow_html=True)

                else:
                    st.markdown("<p style='font-size: 18px; font-family: Roboto, sans-serif; color: #FFFFFF;'>No cooking instructions available for this dish.</p>", unsafe_allow_html=True)

        st.divider()

    elif selected_dish_name == "--- Select a Dish ---":
        # You can add a placeholder message here if you want
        # st.info("Select a dish from the dropdown to see its details.")
        pass

elif dishes_df is None:
    # Error message is already handled by load_and_process_data
    pass
elif dishes_df.empty:
    st.info("No dish data is available to display.")