
# %%

'''
PLEASE EDIT!

We need details about the competition ID because data is taken from the WCIF to create our mo3 and ao5 spreadsheets. Afterwards, you can simply run the file one by one, and this should work out fine. If you don't have the ability to run interactive notebooks, this should be runnable like a normal Python file, so you won't have to worry too much.

Please remember to run this in Python 3 (rather than Python 2). Make sure it's a version that supports type annotations as well.
'''

competition_id: str = "ClawsUpSummer2023"
has_stage: bool = False 

# %%

# Import modules

from constants import *
import pandas as pd
import numpy as np
import requests
import math

# %%

# Helper functions

def timestamp_to_string(timestamp: pd.Timestamp, cumulative=False) -> str:
    if timestamp is None: return "N/A"

    result = ""
    hours = timestamp.hour
    minutes = timestamp.minute
    seconds = timestamp.second
    hour_string = "" if not hours else f"{hours}h"
    minutes_string = "" if not minutes else f"{minutes} min"
    seconds_string = "" if not seconds else f"{seconds} sec"

    result_times = [elem for elem in [hour_string, minutes_string, seconds_string] if elem]

    for elem in result_times[:-1]:
        result = f"{result}{elem} "
    result = f"{result}{result_times[-1]}"
    return result if not cumulative else f"{result} cumulative"


# %%

# Get WCIF Data

wcif_response = requests.get(f"https://worldcubeassociation.org/api/v0/competitions/{competition_id}/wcif/public")
wcif = wcif_response.json()
wcif_events: dict = wcif["events"]
wcif_df: pd.DataFrame = pd.DataFrame.from_dict(wcif_events, orient="columns")

# %%

# Get event data from file

event_data: pd.DataFrame = pd.read_csv("event_data.csv")
ao5_events: pd.DataFrame = event_data[event_data["Type"] == "ao5"][["Event"]].values
mo3_events: pd.DataFrame = event_data[event_data["Type"] == "mo3"][["Event"]].values



# %%

# Setup reading from groups file

groups: pd.DataFrame = pd.read_csv("groups.csv")
ao5_groups: pd.DataFrame = groups.loc[:, ["Name", "WCA ID", "ID"] + [col for col in groups.columns if col in ao5_events]]
mo3_groups: pd.DataFrame = groups.loc[:, ["Name", "WCA ID", "ID"] + [col for col in groups.columns if col in mo3_events]]

ao5_groups: pd.DataFrame = None if ao5_groups.columns.size == 3 else ao5_groups
mo3_groups: pd.DataFrame = None if mo3_groups.columns.size == 3 else mo3_groups

if ao5_groups is not None: competition_ao5_labels: pd.DataFrame = ao5_groups.drop(["Name", "WCA ID", "ID"], axis=1)
if mo3_groups is not None: competition_mo3_labels: pd.DataFrame = mo3_groups.drop(["Name", "WCA ID", "ID"], axis=1)

# %%

# base function

'''
input: 
  - labels: a dataframe containing the labels for ao5/mo3 events
  - groups: a dataframe containing the current data for groups
  - num_blanks: a number containing the number of blank pages to be created
output: a dataframe that corresponds to the pages needed for each category of scorecards
'''

def add_blanks(df: pd.DataFrame, num_blanks: int) -> pd.DataFrame:
    metadata: pd.DataFrame = pd.DataFrame(
        data = {
            "cutoff": ["N/A"] * num_blanks,
            "timelimit": ["N/A"] * num_blanks,
        }
    )

    df = pd.concat([df, metadata])

    return df


def scorecard_template(labels: pd.DataFrame, groups: pd.DataFrame, num_blanks: int=DEFAULT_NUM_BLANK_PAGES) -> pd.DataFrame:
    pages: pd.DataFrame = pd.DataFrame()

    for event in labels.columns:
        current_groups: pd.DataFrame = groups[groups[event].notna()][["Name", "WCA ID", "ID", event]]
        current_groups[event] = current_groups[event].astype(int)
        current_groups = current_groups.sort_values(event)
        current_groups.reset_index(drop=True, inplace=True)
        num_people: int = len(current_groups)

        current_event_metadata: pd.DataFrame = wcif_df[wcif_df["id"] == event]

        for round in current_event_metadata["rounds"].iloc[0]:
            cutoff = round["cutoff"]
            cutoff_timestamp: pd.Timestamp = pd.to_datetime(cutoff["attemptResult"] * 10, unit="ms") if cutoff else None
            time_limit = round["timeLimit"]

            if time_limit: 
                time_limit_timestamp: pd.Timestamp = pd.to_datetime(time_limit["centiseconds"] * 10, unit="ms")
                cumulative = bool(time_limit["cumulativeRoundIds"])
            else:
                time_limit_timestamp: pd.Timestamp = None

            cutoff_string = timestamp_to_string(cutoff and cutoff_timestamp)
            time_limit_string = timestamp_to_string(time_limit and time_limit_timestamp, cumulative)

            round_number = round["id"][-1]

            if round_number == "1":
                
                permuted_groups = pd.DataFrame()

                for mod in range(4):
                    permuted_groups = pd.concat([permuted_groups, current_groups[current_groups.index % 4 == mod]])

                split_columns = np.array_split(permuted_groups, 4)

                for i in range(len(split_columns)):
                    current_number = i + 1
                    segment = split_columns[i]
                    segment.reset_index(drop=True, inplace=True)
                    new_columns = np.append(segment.columns[:-1] + f"{current_number}", np.array([f"g{current_number}"]))
                    segment.columns = new_columns

                spreadsheet_data: pd.DataFrame = split_columns[0]
            
                for i in range(len(split_columns) - 1):
                    spreadsheet_data = pd.concat([spreadsheet_data, split_columns[i + 1]], axis=1)

                num_pages: int = math.ceil(num_people / SCORECARDS_PER_PAGE)

                metadata: pd.DataFrame = pd.DataFrame(
                    data = {
                        "Event": [event_data[event_data["Event"] == current_event_metadata["id"].iloc[0]]["Name"].iloc[0]] * num_pages,
                        "R": [round_number] * num_pages,
                        "cutoff": [cutoff_string] * num_pages,
                        "timelimit": [time_limit_string] * num_pages,
                    }
                )

                current_pages: pd.DataFrame = pd.concat([metadata,spreadsheet_data], axis=1)

                pages = pd.concat([pages, current_pages])

            else:
                num_pages = math.ceil(num_people/SCORECARDS_PER_PAGE)
                metadata: pd.DataFrame = pd.DataFrame(
                    data = {
                        "Event": [event_data[event_data["Event"] == current_event_metadata["id"].iloc[0]]["Name"].iloc[0]] * num_pages,
                        "R": [round_number] * num_pages,
                        "cutoff": [cutoff_string] * num_pages,
                        "timelimit": [time_limit_string] * num_pages,
                    }
                )

                pages = pd.concat([pages, metadata])

            if round["advancementCondition"]:
                num_people = round["advancementCondition"]["level"]

    pages = add_blanks(pages, num_blanks)

    pages = pages.fillna(-1)

    for c in pages.columns:
        if pages[c].dtype == np.dtype('float64'):
            pages[c] = pages[c].astype(int)

    pages.reset_index(inplace=True)
    pages.insert(0, "Page", pages.index + 1)

    return pages.replace(to_replace=-1, value="").drop(columns=["index"])


def scorecard_template_stage(labels: pd.DataFrame, groups: pd.DataFrame, num_blanks: int=DEFAULT_NUM_BLANK_PAGES) -> pd.DataFrame:
    pages: pd.DataFrame = pd.DataFrame()

    for event in labels.columns:
        current_groups: pd.DataFrame = groups[groups[event].notna()][["Name", "WCA ID", "ID", event]]
        current_groups = current_groups.sort_values(event)
        current_groups.reset_index(drop=True, inplace=True)
        num_people: int = len(current_groups)

        current_event_metadata: pd.DataFrame = wcif_df[wcif_df["id"] == event]

        for round in current_event_metadata["rounds"].iloc[0]:
            cutoff = round["cutoff"]
            cutoff_timestamp: pd.Timestamp = pd.to_datetime(cutoff["attemptResult"] * 10, unit="ms") if cutoff else None
            time_limit = round["timeLimit"]

            if time_limit: 
                time_limit_timestamp: pd.Timestamp = pd.to_datetime(time_limit["centiseconds"] * 10, unit="ms")
                cumulative = bool(time_limit["cumulativeRoundIds"])
            else:
                time_limit_timestamp: pd.Timestamp = None

            cutoff_string = timestamp_to_string(cutoff and cutoff_timestamp)
            time_limit_string = timestamp_to_string(time_limit and time_limit_timestamp, cumulative)

            round_number = round["id"][-1]

            if round_number == "1":

                current_groups = current_groups.sort_values(event)

                permuted_groups = pd.DataFrame()

                for mod in range(4):
                    permuted_groups = pd.concat([permuted_groups, current_groups[current_groups.index % 4 == mod]])

                split_columns = np.array_split(permuted_groups, 4)
                
                for i in range(len(split_columns)):
                    current_number = i + 1
                    segment = split_columns[i]
                    segment.reset_index(drop=True, inplace=True)
                    new_columns = np.append(segment.columns[:-1] + f"{current_number}", np.array([f"g{current_number}"]))
                    segment.columns = new_columns

                spreadsheet_data: pd.DataFrame = split_columns[0]
            
                for i in range(len(split_columns) - 1):
                    spreadsheet_data = pd.concat([spreadsheet_data, split_columns[i + 1]], axis=1)

                num_pages: int = math.ceil(num_people / SCORECARDS_PER_PAGE)

                metadata: pd.DataFrame = pd.DataFrame(
                    data = {
                        "Event": [event_data[event_data["Event"] == current_event_metadata["id"].iloc[0]]["Name"].iloc[0]] * num_pages,
                        "R": [round_number] * num_pages,
                        "cutoff": [cutoff_string] * num_pages,
                        "timelimit": [time_limit_string] * num_pages,
                    }
                )

                current_pages: pd.DataFrame = pd.concat([metadata,spreadsheet_data], axis=1)

                pages = pd.concat([pages, current_pages])

            else:
                num_pages = math.ceil(num_people/SCORECARDS_PER_PAGE)
                metadata: pd.DataFrame = pd.DataFrame(
                    data = {
                        "Event": [event_data[event_data["Event"] == current_event_metadata["id"].iloc[0]]["Name"].iloc[0]] * num_pages,
                        "R": [round_number] * num_pages,
                        "cutoff": [cutoff_string] * num_pages,
                        "timelimit": [time_limit_string] * num_pages,
                    }
                )

                pages = pd.concat([pages, metadata])

            if round["advancementCondition"]:
                num_people = round["advancementCondition"]["level"]

    pages = add_blanks(pages, num_blanks)

    pages = pages.fillna(-1)

    for c in pages.columns:
        if pages[c].dtype == np.dtype('float64'):
            pages[c] = pages[c].astype(int)

    pages.reset_index(inplace=True)
    pages.insert(0, "Page", pages.index + 1)

    return pages.replace(to_replace=-1, value="").drop(columns=["index"])

# %%

# ao5 module

ao5_pages: pd.DataFrame

if has_stage:
    ao5_pages = scorecard_template_stage(competition_ao5_labels, ao5_groups, NUM_BLANK_AO5_PAGES)
else:
    ao5_pages = scorecard_template(competition_ao5_labels, ao5_groups, NUM_BLANK_AO5_PAGES)

ao5_pages.to_csv("output/ao5_pages.csv", index=False)
# %% 

# mo3 module

mo3_pages: pd.DataFrame

if has_stage:
    mo3_pages = scorecard_template_stage(competition_mo3_labels, mo3_groups, NUM_BLANK_MO3_PAGES)
else:
    mo3_pages = scorecard_template(competition_mo3_labels, mo3_groups, NUM_BLANK_MO3_PAGES)

mo3_pages.to_csv("output/mo3_pages.csv", index=False)


# %%
