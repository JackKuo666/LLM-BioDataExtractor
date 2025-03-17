# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import re
import math
import os
import csv


def extract_data_table(data_text):
    # Use regex to find all lines that start and end with "|" and exclude lines containing "---"
    table_data = re.findall(r'(?m)^\|.*?\|.*$', data_text)
    # table_data = re.findall(r'^\|.*\|$', data_text)
    # Filter out lines containing "---"
    table_data = [line for line in table_data if '---' not in line]
    # Merge the matched lines into a single string
    table_data_str = '\n'.join(table_data)

    # print(table_data)
    # Use StringIO to simulate a file
    data_io = StringIO(table_data_str)

    # Read the table data, with "|" as the separator, and adjust parameters to avoid reading incorrect columns
    df = pd.read_csv(data_io, sep='\|', engine='python', header=0,
                     usecols=lambda column: column not in ['Unnamed: 0', 'Unnamed: 14'], skipinitialspace=True)

    # Strip spaces from the column headers
    df.columns = df.columns.str.strip()
    
    # Remove content within parentheses from the column headers
    df.columns = [re.sub(r'\s*\([^)]*\)', '', col).strip() for col in df.columns]

    return df


def replace_with_na_wt(value):
    """
    Replace formats of NA to NA, and WT to WT.

    Parameters:
    value: The value to be checked against the predefined list of 'NA' or 'WT' strings.

    Returns:
    The original value or 'NA/WT' if the value is a string that matches the list.
    """
    # List of strings to be interpreted as NA
    na_values = [
        'na', 'nan', 'nd', 'nda', 'n.a.', 'n.d.a.', 'n.d.', '-', 'none', 'not provided', 'not specified',
        'not determined',
        'not available', 'not detected', 'not detectable', 'not applicable'
    ]

    wt_values = ['wt', 'wildtype', 'wild type', 'wild-type']

    # Check if the value is a string and if its lowercase form is in the list
    if isinstance(value, str) and value.lower().strip() in na_values:
        return 'NA'  # Convert to NA if it matches NA criteria
    elif isinstance(value, str) and value.lower().strip() in wt_values:
        return 'WT'  # Convert to WT if it matches WT criteria
    else:
        return value  # Return the original value if not matched


def extract_operator(input_value):
    # operator pattern
    pattern = r"^(<=|>=|<<|>>|<|>|=|~)"
    match = re.match(pattern, input_value.strip())
    if match:
        return match.group(0)
    else:
        return ""


def clean_value(input_value):
    """
    Attempts to clean the given input value by matching it against various regular expression patterns.
    If a match is found, converts the value to a float in base 10 notation.
    If no match is found, returns 'NA'.
    """
    input_value = str(input_value).replace(" ", "").replace(",", "").replace("x", "×").replace("*", "×").replace("脳", "×")

    # get operators
    operator = extract_operator(input_value)
    if operator:
        # 如果提取到运算符，去掉运算符以便处理数值
        input_value = input_value[len(operator):]

    if 'e' in input_value.lower():  # Directly handle scientific notation, e.g., 1.9e-03, Use lower to handle both 'e' and 'E'
        match = re.match(r'^(-?\d+(\.\d+)?([eE][-+]?\d+)?)', input_value)
        if match:
            try:
                return operator, float(match.group(0))  # No operator found here
            except ValueError:
                pass

    # Remove all parts of the string that contain letters after the first numerical part, including spaces
    input_value = re.sub(r'(?<=\d)[a-zA-Z\s].*', '', input_value)

    # Define regular expression patterns for various expected formats
    patterns = [
        # With error in parentheses and exponent, e.g., (4.0 ± 0.3) × 10^5
        (r'\((\d+(\.\d+)?)±(\d+(\.\d+)?)\)×10(?:\^(-?\d+))?',
         lambda m: float(m.group(1)) * (10 ** (int(m.group(5)) if m.group(5) else 1))),

        # With error not in parentheses, and exponent, e.g., 4.0 ± 0.3 × 10^5
        (r'(\d+(\.\d+)?)±(\d+(\.\d+)?)×10(?:\^(-?\d+))?',
         lambda m: float(m.group(1)) * (10 ** (int(m.group(5)) if m.group(5) else 1))),

        # With exponent terms in error term, e.g., 4.0 × 10^5 ± 0.3 × 10^5
        (r'(\d+(\.\d+)?)×10(?:\^(-?\d+))?±(\d+(\.\d+)?)×10(?:\^(-?\d+))?',
         lambda m: float(m.group(1)) * (10 ** (int(m.group(3)) if m.group(3) else 1))),

        # With value and exponent, without error term, e.g., 4.0 × 10^5 or 4.0 × 10
        (r'(\d+(\.\d+)?)×10(?:\^(-?\d+))?',
         lambda m: float(m.group(1)) * (10 ** (int(m.group(3)) if m.group(3) else 1))),

        # Values in parentheses with optional exponent in parentheses, e.g., (9.0) × 10^(-3)
        (r'\((\d+(\.\d+)?)\)\s*×\s*10\^\((\-?\d+)\)',
         lambda m: float(m.group(1)) * (10 ** (int(m.group(3)) if m.group(3) else 1))),

        # Values in parentheses with optional exponent, e.g., (4.0) × 10^5 or (4.0) × 10
        (r'\((\d+(\.\d+)?)\)\s*×\s*10(?:\^(-?\d+))?',
         lambda m: float(m.group(1)) * (10 ** (int(m.group(3)) if m.group(3) else 1))),

        # Integers or floating-point numbers in parentheses, e.g., (36.2)
        (r'\((\d+(\.\d+)?)\)',
         lambda m: float(m.group(1))),

        # With value and optional error but no exponent, e.g., 36.2±4.2
        (r'(\d+(\.\d+)?)\s*±\s*(\d+(\.\d+)?)?',
         lambda m: float(m.group(1))),

        # With values with error in parentheses, e.g., 36.2(4.2)
        (r'(\d+(\.\d+)?)(\((\d+(\.\d+)?)\))',
         lambda m: float(m.group(1))),

        # Integers or floating-point numbers, e.g., 36.2
        (r'^-?\d+(?:\.\d+)?$',
         lambda m: float(m.group(0)))
    ]

    # Attempt to match each pattern and return the cleaned value if a match is found
    for pattern, action in patterns:
        match = re.match(pattern, input_value)
        if match:
            return operator, action(match)

    # If no patterns match, return 'NA'
    return operator, 'NA'


def convert_unit(operator, value, original_unit):
    """
    Converts the given value from the original_unit to the standard unit.
    Handles conversions for Km, Kcat, and Kcat/Km values based on their units.
    This function ensures output values are displayed as regular decimals without scientific notation.
    Returns 'NA' for both value and unit if the value is a non-numeric string indicating data is not available.
    """
    # Check if original_unit is 'NA' or NaN
    if original_unit == 'NA' or (isinstance(original_unit, (float, int)) and math.isnan(original_unit)):
        return 'NA', 'NA'

    # Check if value is 'NA' or NaN
    if str(value).strip().lower() == 'na' or (isinstance(value, (float, int)) and math.isnan(value)):
        return 'NA', 'NA'
    # Normalize the input value to lowercase for comparison
    normalized_value = str(value).lower().replace(" ", "")

    # Check if the input value is in the list of non-numeric values
    if normalized_value == 'na':
        return 'NA', 'NA'

    # Check if the unit was in log scale
    pattern = r'log\(([^)]+)\)'
    match = re.match(pattern, original_unit)
    if match:
        value = 10 ** float(normalized_value)
        original_unit = re.sub(pattern, r'\1', original_unit)

    # Normalize unit string to simplify comparisons
    pattern = "[   ()·.•]"
    normalized_unit = re.sub(pattern, "", original_unit)

    # substitute sec to s, substitute ⁻¹ to ^-1
    normalized_unit = normalized_unit.replace("S", "s").replace("sec", "s").replace("⁻¹", "^-1")

    # Check for units for Vmax and return 'NA' for both value and unit
    if 'mg' in normalized_unit.lower():
        return 'NA', 'NA'
    # check if scientific notation was in the units
    unit_factor = 1
    pattern = r'(?:[×x\*])?(10\^(-?\d+))(?:[×x\*])?'
    match = re.search(pattern, normalized_unit)
    if match:
        unit_factor = 10 ** int(match.group(2))
        normalized_unit = re.sub(pattern, '', normalized_unit)

    # Determine the conversion factor and the target unit
    conversion_factor = 1
    target_unit = original_unit

    # Km Conversion
    if normalized_unit in ['μM', 'µM', 'uM']:
        conversion_factor, target_unit = 0.001, 'mM'
    elif normalized_unit in ['M', 'mol/L']:
        conversion_factor, target_unit = 1000, 'mM'
    elif normalized_unit in ['mM', 'mmol/L']:
        target_unit = 'mM'

    # Kcat Conversion
    elif normalized_unit == 'min^-1':
        conversion_factor, target_unit = 1 / 60, 's^-1'
    elif normalized_unit == 's^-1':
        target_unit = 's^-1'

    # Kcat/Km Conversion
    elif normalized_unit in ['M^-1s^-1', 's^-1M^-1', 'M^-1·s^-1', 's^-1·M^-1', 'M^-1×s^-1', 's^-1×M^-1', 'M^-1脳s^-1',
                             's^-1脳M^-1',
                             'M^-1路s^-1', 's^-1路M^-1', 'M^-1*s^-1', 's^-1*M^-1', 'M^-1.s^-1', 's^-1.M^-1',
                             's^-1/M', 'M^-1/s', 'L/mol/s', '/Ms', '/M/s', '/s/M']:
        conversion_factor, target_unit = 0.001, 'mM^-1s^-1'
    elif normalized_unit in ['μM^-1s^-1', 's^-1μM^-1', 'μM^-1·s^-1', 's^-1·μM^-1', 'μM^-1×s^-1', 's^-1×μM^-1',
                             'μM^-1脳s^-1', 's^-1脳μM^-1',
                             'μM^-1路s^-1', 's^-1路μM^-1', 'μM^-1*s^-1', 's^-1*μM^-1', 'μM^-1.s^-1', 's^-1.μM^-1',
                             'µM^-1s^-1', 's^-1µM^-1', 'µM^-1·s^-1', 's^-1·µM^-1', 'µM^-1×s^-1', 's^-1×µM^-1',
                             'µM^-1脳s^-1', 's^-1脳µM^-1',
                             'µM^-1路s^-1', 's^-1路µM^-1', 'µM^-1*s^-1', 's^-1*µM^-1', 'µM^-1.s^-1', 's^-1.µM^-1',
                             'uM^-1s^-1', 's^-1uM^-1', 'uM^-1·s^-1', 's^-1·uM^-1', 'uM^-1×s^-1', 's^-1×uM^-1',
                             'uM^-1脳s^-1', 's^-1脳uM^-1',
                             'uM^-1路s^-1', 's^-1路uM^-1', 'uM^-1*s^-1', 's^-1*uM^-1', 'uM^-1.s^-1', 's^-1.uM^-1',
                             's^-1/µM', 'µM^-1/s', 'L/µmol/s', '/µMs', '/µM/s', '/s/µM']:
        conversion_factor, target_unit = 1000, 'mM^-1s^-1'
    elif normalized_unit in ['nM^-1s^-1', 's^-1nM^-1', 'nM^-1·s^-1', 's^-1·nM^-1', 'nM^-1×s^-1', 's^-1×nM^-1',
                             'nM^-1脳s^-1', 's^-1脳nM^-1',
                             'nM^-1路s^-1', 's^-1路nM^-1', 'nM^-1*s^-1', 's^-1*nM^-1', 'nM^-1.s^-1', 's^-1.nM^-1',
                             'min^-1/nM', 'nM^-1/min', 'L/nmol/min', '/nMs', '/nM/s', '/s/nM']:
        conversion_factor, target_unit = 1000000, 'mM^-1s^-1'
    elif normalized_unit in ['mM^-1min^-1', 'min^-1mM^-1', 'mM^-1·min^-1', 'min^-1·mM^-1', 'mM^-1×min^-1',
                             'min^-1×mM^-1', 'mM^-1脳min^-1', 'min^-1脳mM^-1',
                             'mM^-1路min^-1', 'min^-1路mM^-1', 'mM^-1*min^-1', 'min^-1*mM^-1', 'mM^-1.min^-1',
                             'min^-1.mM^-1',
                             'min^-1/mM', 'mM^-1/min', 'L/mmol/min', '/mMmin', '/mM/min', '/min/mM']:
        conversion_factor, target_unit = 1 / 60, 'mM^-1s^-1'
    elif normalized_unit in ['μM^-1min^-1', 'min^-1μM^-1', 'μM^-1·min^-1', 'min^-1·μM^-1', 'μM^-1×min^-1',
                             'min^-1×μM^-1', 'μM^-1脳min^-1', 'min^-1脳μM^-1',
                             'μM^-1路min^-1', 'min^-1路μM^-1', 'μM^-1*min^-1', 'min^-1*μM^-1', 'μM^-1.min^-1',
                             'min^-1.μM^-1',
                             'µM^-1min^-1', 'min^-1µM^-1', 'µM^-1·min^-1', 'min^-1·µM^-1', 'µM^-1×min^-1',
                             'min^-1×µM^-1', 'µM^-1脳min^-1', 'min^-1脳µM^-1',
                             'µM^-1路min^-1', 'min^-1路µM^-1', 'µM^-1*min^-1', 'min^-1*µM^-1', 'µM^-1.min^-1',
                             'min^-1.µM^-1',
                             'uM^-1min^-1', 'min^-1uM^-1', 'uM^-1·min^-1', 'min^-1·uM^-1', 'uM^-1×min^-1',
                             'min^-1×uM^-1', 'uM^-1脳min^-1', 'min^-1脳uM^-1',
                             'uM^-1路min^-1', 'min^-1路uM^-1', 'uM^-1*min^-1', 'min^-1*uM^-1', 'uM^-1.min^-1',
                             'min^-1.uM^-1',
                             'min^-1/µM', 'µM^-1/min', 'L/µmol/min', '/µMmin', '/µM/min', '/min/µM']:
        conversion_factor, target_unit = (1000 / 60), 'mM^-1s^-1'
    elif normalized_unit in ['M^-1min^-1', 'min^-1M^-1', 'M^-1·min^-1', 'min^-1·M^-1', 'M^-1×min^-1',
                             'min^-1×M^-1', 'M^-1脳min^-1', 'min^-1脳M^-1',
                             'M^-1路min^-1', 'min^-1路M^-1', 'M^-1*min^-1', 'min^-1*M^-1', 'M^-1.min^-1',
                             'min^-1.M^-1',
                             'min^-1/M', 'M^-1/min', 'L/mol/min', '/Mmin', '/M/min', '/min/M']:
        conversion_factor, target_unit = (0.001 / 60), 'mM^-1s^-1'
    elif normalized_unit in ['mM^-1s^-1', 's^-1mM^-1', 'mM^-1·s^-1', 's^-1·mM^-1', 'mM^-1×s^-1', 's^-1×mM^-1',
                             'mM^-1脳s^-1', 's^-1脳mM^-1',
                             'mM^-1路s^-1', 's^-1路mM^-1', 'mM^-1*s^-1', 's^-1*mM^-1', 'mM^-1.s^-1', 's^-1.mM^-1',
                             's^-1/mM', 'mM^-1/s', 'L/mmol/s', '(mM×s)^-1', '/mMs', '/mM/s', '/s/mM']:
        target_unit = 'mM^-1s^-1'

    # Convert the value and format output to avoid scientific notation
    new_value = value * conversion_factor * unit_factor
    formatted_value = f"{new_value:.6f}"  # Adjust the precision as needed
    return operator + formatted_value.rstrip('0').rstrip('.'), target_unit


def csv_organize(df):
    """
    Organizes and cleans a DataFrame extracted from an LLM output text.

    Args:
    csv_path (str): The output text from an LLM model.

    Returns:
    pandas.DataFrame: The cleaned and organized DataFrame.
    """
    # table_data = re.findall(r'(?m)^\|.*?\|$', data_text)
    # # table_data = re.findall(r'^\|.*\|$', data_text)
    # # Filter out lines containing "---"
    # table_data = [line for line in table_data if '---' not in line]
    # # Merge the matched lines into a single string
    # table_data_str = '\n'.join(table_data)

    # # print(table_data)
    # # Use StringIO to simulate a file
    # data_io = StringIO(table_data_str)

    # # Read the table data, with "|" as the separator, and adjust parameters to avoid reading incorrect columns
    # df = pd.read_csv(data_io, sep='\|', engine='python', header=0,
    #                  usecols=lambda column: column not in ['Unnamed: 0', 'Unnamed: 14'], skipinitialspace=True)

    # Extract table from LLM output
    # df = pd.read_csv(data_text, sep='|', header=0,
    #                  usecols=lambda column: column not in ['Unnamed: 0', 'Unnamed: 14'], skipinitialspace=True)

    # Strip spaces from the column headers
    df.columns = df.columns.str.strip()

    # Remove content within parentheses from the column headers
    df.columns = [re.sub(r'\s*\([^)]*\)', '', col).strip() for col in df.columns]

    # Check if 'Enzyme' column is present
    if 'Enzyme' not in df.columns:
        return pd.DataFrame()  # Return an empty DataFrame

    if len(df.columns) == 13:
        new_headers = ['Enzyme', 'Organism', 'Substrate', 'Km', 'Unit_Km', 'Kcat', 'Unit_Kcat', 'Kcat/Km',
                       'Unit_Kcat/Km', 'Commentary[Temp]', 'Commentary[pH]', 'Commentary[Mutant]',
                       'Commentary[Cosubstrate]']
        df.columns = new_headers
    else:
        print("The DataFrame does not have exactly 13 columns.")
        return pd.DataFrame()  # Return an empty DataFrame

    # Apply the function to each element in the DataFrame
    df = df.fillna('NA')
    df = df.apply(lambda x: x.map(replace_with_na_wt))

    df = df.dropna(how='all')
    # Apply the cleaning and conversion functions
    df['Km'] = df.apply(lambda row: convert_unit(*clean_value(row['Km']), row['Unit_Km']), axis=1)
    df['Kcat'] = df.apply(lambda row: convert_unit(*clean_value(row['Kcat']), row['Unit_Kcat']), axis=1)
    df['Kcat/Km'] = df.apply(lambda row: convert_unit(*clean_value(row['Kcat/Km']), row['Unit_Kcat/Km']), axis=1)

    # Separate the tuples of values and units into their respective columns
    df[['Km', 'Unit_Km']] = df['Km'].apply(pd.Series)
    df[['Kcat', 'Unit_Kcat']] = df['Kcat'].apply(pd.Series)
    df[['Kcat/Km', 'Unit_Kcat/Km']] = df['Kcat/Km'].apply(pd.Series)

    df.loc[df['Unit_Km'] != 'mM', ['Km', 'Unit_Km']] = 'NA'
    df.loc[df['Unit_Kcat'] != 's^-1', ['Kcat', 'Unit_Kcat']] = 'NA'
    df.loc[df['Unit_Kcat/Km'] != 'mM^-1s^-1', ['Kcat/Km', 'Unit_Kcat/Km']] = 'NA'

    # Print the DataFrame to verify the output
    # print(df['Kcat/Km'])

    # Optionally save the cleaned and converted data to a new CSV file
    # df.to_csv('converted_table.csv', index=False)

    return df


def convert_unit1(value, original_unit):
    """
    Converts the given value from the original_unit to the standard unit.
    Handles conversions for Km, Kcat, and Kcat/Km values based on their units.
    This function ensures output values are displayed as regular decimals without scientific notation.
    Returns 'NA' for both value and unit if the value is a non-numeric string indicating data is not available.
    """
    print(value)
    # Check if original_unit is 'NA' or NaN
    if original_unit == 'NA' or (isinstance(original_unit, (float, int)) and math.isnan(original_unit)):
        return 'NA', 'NA'

    # Check if value is 'NA' or NaN
    if str(value).strip().lower() == 'na' or (isinstance(value, (float, int)) and math.isnan(value)):
        return 'NA', 'NA'
    # Normalize the input value to lowercase for comparison
    normalized_value = str(value).lower().replace(" ", "")

    # Check if the input value is in the list of non-numeric values
    if normalized_value == 'na':
        return 'NA', 'NA'
    
    # Check if the unit was in log scale
    pattern = r'log\(([^)]+)\)'
    match = re.match(pattern, original_unit)
    if match:
        value = 10**float(normalized_value)
        original_unit = re.sub(pattern, r'\1', original_unit)
    # Normalize unit string to simplify comparisons
    pattern = "[ ()·]"
    normalized_unit = re.sub(pattern, "", original_unit)
    
    # substitute sec to s, substitute ⁻¹ to ^-1
    normalized_unit = normalized_unit.replace("sec", "s").replace("⁻¹", "^-1")


    # Check for specific units and return 'NA' for both value and unit
    if normalized_unit.lower() in ['u-mg^-1', 'umg^-1', 'pkat/mg']:
        return 'NA', 'NA'
    # check if scientific notation was in the units
    unit_factor = 1
    pattern = r'(?:[×x\*])?(10\^(-?\d+))(?:[×x\*])?'
    match = re.search(pattern, normalized_unit)
    if match:
        unit_factor = 10 ** int(match.group(2))
        normalized_unit = re.sub(pattern, '', normalized_unit)
    
    # Determine the conversion factor and the target unit
    conversion_factor = 1
    target_unit = original_unit

    # Km Conversion
    if normalized_unit in ['μM', 'µM', 'uM']:
        conversion_factor, target_unit = 0.001, 'mM'
    elif normalized_unit in ['M', 'mol/L']:
        conversion_factor, target_unit = 1000, 'mM'
    elif normalized_unit in ['mM', 'mmol/L']:
        target_unit = 'mM'

    # Kcat Conversion
    elif normalized_unit == 'min^-1':
        conversion_factor, target_unit = 1 / 60, 's^-1'
    elif normalized_unit == 's^-1':
        target_unit = 's^-1'

    # Kcat/Km Conversion
    elif normalized_unit in ['M^-1s^-1', 's^-1M^-1', 'M^-1·s^-1', 's^-1·M^-1', 'M^-1×s^-1', 's^-1×M^-1', 'M^-1脳s^-1',
                             's^-1脳M^-1',
                             'M^-1路s^-1', 's^-1路M^-1', 'M^-1*s^-1', 's^-1*M^-1', 'M^-1.s^-1', 's^-1.M^-1',
                             's^-1/M', 'M^-1/s', 'L/mol/s']:
         conversion_factor, target_unit = 0.001, 'mM^-1s^-1'
    elif normalized_unit in ['μM^-1s^-1', 's^-1μM^-1', 'μM^-1·s^-1', 's^-1·μM^-1', 'μM^-1×s^-1', 's^-1×μM^-1',
                             'μM^-1脳s^-1', 's^-1脳μM^-1',
                             'μM^-1路s^-1', 's^-1路μM^-1', 'μM^-1*s^-1', 's^-1*μM^-1', 'μM^-1.s^-1', 's^-1.μM^-1',
                             'µM^-1s^-1', 's^-1µM^-1', 'µM^-1·s^-1', 's^-1·µM^-1', 'µM^-1×s^-1', 's^-1×µM^-1',
                             'µM^-1脳s^-1', 's^-1脳µM^-1',
                             'µM^-1路s^-1', 's^-1路µM^-1', 'µM^-1*s^-1', 's^-1*µM^-1', 'µM^-1.s^-1', 's^-1.µM^-1',
                             'uM^-1s^-1', 's^-1uM^-1', 'uM^-1·s^-1', 's^-1·uM^-1', 'uM^-1×s^-1', 's^-1×uM^-1',
                             'uM^-1脳s^-1', 's^-1脳uM^-1',
                             'uM^-1路s^-1', 's^-1路uM^-1', 'uM^-1*s^-1', 's^-1*uM^-1', 'uM^-1.s^-1', 's^-1.uM^-1',
                             's^-1/µM', 'µM^-1/s', 'L/µmol/s']:
        conversion_factor, target_unit = 1000, 'mM^-1s^-1'
    elif normalized_unit in ['nM^-1s^-1', 's^-1nM^-1', 'nM^-1·s^-1', 's^-1·nM^-1', 'nM^-1×s^-1', 's^-1×nM^-1',
                             'nM^-1脳s^-1', 's^-1脳nM^-1',
                             'nM^-1路s^-1', 's^-1路nM^-1', 'nM^-1*s^-1', 's^-1*nM^-1', 'nM^-1.s^-1', 's^-1.nM^-1',
                             'min^-1/nM', 'nM^-1/min', 'L/nmol/min']:
        conversion_factor, target_unit = 1000000, 'mM^-1s^-1'
    elif normalized_unit in ['mM^-1min^-1', 'min^-1mM^-1', 'mM^-1·min^-1', 'min^-1·mM^-1', 'mM^-1×min^-1',
                             'min^-1×mM^-1', 'mM^-1脳min^-1', 'min^-1脳mM^-1',
                             'mM^-1路min^-1', 'min^-1路mM^-1', 'mM^-1*min^-1', 'min^-1*mM^-1', 'mM^-1.min^-1',
                             'min^-1.mM^-1',
                             'min^-1/mM', 'mM^-1/min', 'L/mmol/min']:
        conversion_factor, target_unit = 1 / 60, 'mM^-1s^-1'
    elif normalized_unit in ['μM^-1min^-1', 'min^-1μM^-1', 'μM^-1·min^-1', 'min^-1·μM^-1', 'μM^-1×min^-1',
                             'min^-1×μM^-1', 'μM^-1脳min^-1', 'min^-1脳μM^-1',
                             'μM^-1路min^-1', 'min^-1路μM^-1', 'μM^-1*min^-1', 'min^-1*μM^-1', 'μM^-1.min^-1',
                             'min^-1.μM^-1',
                             'µM^-1min^-1', 'min^-1µM^-1', 'µM^-1·min^-1', 'min^-1·µM^-1', 'µM^-1×min^-1',
                             'min^-1×µM^-1', 'µM^-1脳min^-1', 'min^-1脳µM^-1',
                             'µM^-1路min^-1', 'min^-1路µM^-1', 'µM^-1*min^-1', 'min^-1*µM^-1', 'µM^-1.min^-1',
                             'min^-1.µM^-1',
                             'uM^-1min^-1', 'min^-1uM^-1', 'uM^-1·min^-1', 'min^-1·uM^-1', 'uM^-1×min^-1',
                             'min^-1×uM^-1', 'uM^-1脳min^-1', 'min^-1脳uM^-1',
                             'uM^-1路min^-1', 'min^-1路uM^-1', 'uM^-1*min^-1', 'min^-1*uM^-1', 'uM^-1.min^-1',
                             'min^-1.uM^-1',
                             'min^-1/µM', 'µM^-1/min', 'L/µmol/min']:
        conversion_factor, target_unit = (1000 / 60), 'mM^-1s^-1'
    elif normalized_unit in ['M^-1min^-1', 'min^-1M^-1', 'M^-1·min^-1', 'min^-1·M^-1', 'M^-1×min^-1',
                             'min^-1×M^-1', 'M^-1脳min^-1', 'min^-1脳M^-1',
                             'M^-1路min^-1', 'min^-1路M^-1', 'M^-1*min^-1', 'min^-1*M^-1', 'M^-1.min^-1',
                             'min^-1.M^-1',
                             'min^-1/M', 'M^-1/min', 'L/mol/min']:
        conversion_factor, target_unit = (0.001 / 60), 'mM^-1s^-1'
    elif normalized_unit in ['mM^-1s^-1', 's^-1mM^-1', 'mM^-1·s^-1', 's^-1·mM^-1', 'mM^-1×s^-1', 's^-1×mM^-1',
                             'mM^-1脳s^-1', 's^-1脳mM^-1',
                             'mM^-1路s^-1', 's^-1路mM^-1', 'mM^-1*s^-1', 's^-1*mM^-1', 'mM^-1.s^-1', 's^-1.mM^-1',
                             's^-1/mM', 'mM^-1/s', 'L/mmol/s']:
        target_unit = 'mM^-1s^-1'

    # Convert the value and format output to avoid scientific notation
    new_value = value * conversion_factor * unit_factor
    print(normalized_value,value,conversion_factor,unit_factor)
    formatted_value = f"{new_value:.6f}"  # Adjust the precision as needed
    return float(formatted_value.rstrip('0').rstrip('.')), target_unit

def csv_organize_ribozyme(df):
    """
    Organizes and cleans a DataFrame extracted from an LLM output text.

    Args:
    csv_path (str): The output text from an LLM model.

    Returns:
    pandas.DataFrame: The cleaned and organized DataFrame.
    """
    # table_data = re.findall(r'(?m)^\|.*?\|$', data_text)
    # # table_data = re.findall(r'^\|.*\|$', data_text)
    # # Filter out lines containing "---"
    # table_data = [line for line in table_data if '---' not in line]
    # # Merge the matched lines into a single string
    # table_data_str = '\n'.join(table_data)
    
    # # print(table_data)
    # # Use StringIO to simulate a file
    # data_io = StringIO(table_data_str)

    # # Read the table data, with "|" as the separator, and adjust parameters to avoid reading incorrect columns
    # df = pd.read_csv(data_io, sep='\|', engine='python', header=0,
    #                  usecols=lambda column: column not in ['Unnamed: 0', 'Unnamed: 14'], skipinitialspace=True)

    # Extract table from LLM output
    # df = pd.read_csv(data_text, sep='|', header=0,
    #                  usecols=lambda column: column not in ['Unnamed: 0', 'Unnamed: 14'], skipinitialspace=True)

    # Strip spaces from the column headers
    df.columns = df.columns.str.strip()

    # Remove content within parentheses from the column headers
    df.columns = [re.sub(r'\s*\([^)]*\)', '', col).strip() for col in df.columns]
    print(df['km'])
    # Check if 'Enzyme' column is present
    # if 'Enzyme' not in df.columns:
    #     return pd.DataFrame()  # Return an empty DataFrame

    # if len(df.columns) == 13:
    #     new_headers = ['Enzyme', 'Organism', 'Substrate', 'Km', 'Unit_Km', 'Kcat', 'Unit_Kcat', 'Kcat/Km',
    #                    'Unit_Kcat/Km', 'Commentary[Temp]', 'Commentary[pH]', 'Commentary[Mutant]',
    #                    'Commentary[Cosubstrate]']
    #     df.columns = new_headers
    # else:
    #     print("The DataFrame does not have exactly 13 columns.")
    #     return pd.DataFrame()  # Return an empty DataFrame

    # Apply the function to each element in the DataFrame
    df = df.fillna('NA')
    df = df.apply(lambda x: x.map(replace_with_na_wt))

    df = df.dropna(how='all')
    # Apply the cleaning and conversion functions
    # try:
        
    df['Km'] = df.apply(lambda row: convert_unit1(clean_value(row['km']), row['Unit_Km']), axis=1)
    df['Kcat'] = df.apply(lambda row: convert_unit1(clean_value(row['kcat']), row['Unit_Kcat']), axis=1)
    df['Km_kcat'] = df.apply(lambda row: convert_unit1(clean_value(row['km_kcat']), row['Unit_Kcat/Km']), axis=1)
    # except:
    #     df['Km'] = df.apply(lambda row: convert_unit1(clean_value(row['Km']), row['Unit_Km']), axis=1)
    #     df['Kcat'] = df.apply(lambda row: convert_unit1(clean_value(row['Kcat']), row['Unit_Kcat']), axis=1)
    #     df['Km_kcat'] = df.apply(lambda row: convert_unit1(clean_value(row['Kcat/Km']), row['Unit_Kcat/Km']), axis=1)
    df['Kobs'] = df.apply(lambda row: convert_unit1(clean_value(row['Kobs']), row['Unit_Kobs']), axis=1)
    df['Kcleav'] = df.apply(lambda row: convert_unit1(clean_value(row['Kcleav']), row['Unit_Kcleav']), axis=1)

    # Separate the tuples of values and units into their respective columns
    df[['Km', 'Unit_Km']] = df['Km'].apply(pd.Series)
    df[['Kcat', 'Unit_Kcat']] = df['Kcat'].apply(pd.Series)
    df[['Km_kcat', 'Unit_Kcat/Km']] = df['Km_kcat'].apply(pd.Series)
    df[['Kobs', 'Unit_Kcat/Kobs']] = df['Kobs'].apply(pd.Series)
    df[['Kcleav', 'Unit_Kcat/Kcleav']] = df['Kcleav'].apply(pd.Series)

    # Print the DataFrame to verify the output
    # print(df['Kcat/Km'])

    # Optionally save the cleaned and converted data to a new CSV file
    # df.to_csv('converted_table.csv', index=False)

    return df

# Extract df from output text of LLM
# llm_text = """
# Here is some virtual data output text by LLM:
# | Enzyme | Organism             | Substrate | Km    | Unit_Km | Kcat             | Unit_Kcat | Kcat/Km            | Unit_Kcat/Km   | Commentary[Temp] | Commentary[pH] | Commentary[Mutant] | Commentary[Cosubstrate] |
# |--------|----------------------|-----------|-------|---------|------------------|-----------|--------------------|----------------|------------------|----------------|--------------------|-------------------------|
# | KpCld  | Klebsiella pneumoniae | Chlorite  | 1900 | μM      | 5.72              | U-mg^-1   | (2.5 ± 0.4) × 10^6 | M^-1s^-1       | 20°C             | 5.0            | NA                 | None                      |
# | KpCld  | Klebsiella pneumoniae | Chlorite  | NA | M       | (2.0 ± 0.6) × 10^4 | min^-1  | 3.6 ± 0.4          | min^-1 μM^-1   | 4°C              | 5.2            | DaCld              | Not Determined                      |
# Please note that the 'Km' values are not provided in the text, and 'NA' is used to indicate that the data is not available. The 'Commentary[Temp]' and 'Commentary[pH]' are based on the conditions mentioned in the text for the respective 'Kcat' and 'Kcat/Km' values. Since no mutants or cosubstrates are specifically mentioned in the context of the kinetic parameters, 'NA' is used for 'Commentary[Mutant]' and 'Commentary[Cosubstrate]'. The 'Unit_Km', 'Unit_Kcat', and 'Unit_Kcat/Km' are left blank as the units are not provided in the text, but the scientific notation and units for 'Kcat/Km' are preserved as instructed. 
# """

# 20483909_response.csv

# path = r'D:\wenxian\BrendaExtraction-1\extract_response\39篇_md_一步走_p_1_0620_kimi-32k\20670441_response.csv'
# with open(path) as f:
#     llm_text = f.readlines()
# # data = csv_organize(''.join(llm_text))
# new_data = []
# for data in llm_text:
#     if data[0]!='|' and '|' in data:
#         print(data)
#         if data[-2]!='|':
#             new_data.append('|'+data[:-1]+'|'+data[-1])
#         else:
#             new_data.append('|'+data)
#     else:
#         new_data.append(data)

# data = extract_data_table(''.join(new_data))


# data = data.applymap(replace_with_na_wt)


# def test(input_value):
#     input_value = str(input_value).replace(" ", "").replace(",", "")
#     if 'e' in input_value:
#         try:
#             return float(input_value)
#         except ValueError:
#             pass

#     # Define regular expression patterns for various expected formats
#     patterns = [
#         # With parentheses and exponent
#         (r'\((\d+(\.\d+)?)±(\d+(\.\d+)?)\)×10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(5)))),
#         (r'\((\d+(\.\d+)?)±(\d+(\.\d+)?)\)脳10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(5)))),
#         # With exponent and error term
#         (r'(\d+(\.\d+)?)±(\d+(\.\d+)?)×10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(4)))),
#         (r'(\d+(\.\d+)?)±(\d+(\.\d+)?)脳10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(4)))),
#         # With exponent for value and error term
#         (r'(\d+(\.\d+)?)×10\^(-?\d+)±(\d+(\.\d+)?)×10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(3)))),
#         (r'(\d+(\.\d+)?)脳10\^(-?\d+)±(\d+(\.\d+)?)脳10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(3)))),
#         # With value and exponent, without error term
#         (r'(\d+(\.\d+)?)×10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(3)))),
#         (r'(\d+(\.\d+)?)脳10\^(-?\d+)', lambda m: float(m.group(1)) * (10 ** int(m.group(3)))),
#         # With value and optional error but no exponent
#         (r'(\d+(\.\d+)?)(±(\d+(\.\d+)?)?)?$', lambda m: float(m.group(1))),
#         # Integers or floating-point numbers
#         (r'^-?\d+(?:\.\d+)?$', lambda m: float(m.group(0)))
#     ]


#     # Attempt to match each pattern and return the cleaned value if a match is found
#     for pattern, action in patterns:
#         match = re.match(pattern, input_value)
#         if match:
#             return action(match)
#     # return re.match(r'(\d+(\.\d+)?)×10\^(-?\d+)', input_value)
#     return input_value
# data = csv_organize(''.join(new_data))
# print(data['Kcat/Km'].tolist())
# print(data['Unit_Kcat/Km'].tolist())
# # print(new_data)
# # print(re.findall(r'(?m)^\|.*?\|$', ''.join(new_data)))

# # print(test(data['Kcat/Km'].tolist()[0]))




