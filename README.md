# Groups to Scorecards

This software was made to help streamline the group making process for the NorCal Rubik's Cube community. Typically, the process of turning groups to software is done manually, so this script aims to simplify the process and take out a lot of the.

## Requirements

- This program requires a `.csv` file to read data of groups from. **Please be sure to name it `groups.csv`**
- This `.csv` file must have a column called `Name`, `WCA ID`, and must have a column for each WCA event that you have assigned groups for. Take a look at `groups.csv` in the repository if you need an example of what the format should look like.
  - If you don't have this file, it's likely that you won't need these to make your scorecards - if you're using something like Delegate Dashboard or Groupifier to make your groups, you can simply generate scorecards from there, or export the scorecards `.csv` file from Delegate Dashboard (because they both use WCIF, if you made groups in Groupifier, you should be able to access them through delegate dashboard).
  - If you did want to use this custom format, you can download the nametags `.csv` file from Delegate Dashboard and use it here. An important thing to note is that the column names do not work with this script out of the box, so you'll need to edit some of the column names before running the script.
- You will need `numpy` and `pandas` for this script to work.

## Usage

1. Download the `.csv` file that has all the groups together, and name it `groups.csv` (you can see an example of one in this folder)
2. Run the script

## To-do

- [ ] Add document mail-merge directly into script