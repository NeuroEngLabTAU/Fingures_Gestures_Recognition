# Fingers Gestures Recognition
## Hand Gesture Prediction using sEMG and Ultraleap Motion Controller 2

This repository implements a pipeline for collecting reliable surface electromyography (sEMG) data from a 16-electrode array by Xtrodes Ltd, synchronized with hand gesture data using the Ultraleap Motion Controller 2. The collected data will be used in future machine learning models for predicting hand gestures based on sEMG signals.

## Table of Contents
- [Project Overview](#project-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
- [Data Collection](#data-collection)
  - [Hardware Setup](#hardware-setup)
  - [Data Acquisition](#data-acquisition)
  - [Data Synchronization](#data-synchronization)
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Project Overview
The goal of this project is to create a reliable pipeline for collecting sEMG data and synchronizing it with accurate hand gesture labels from the Ultraleap Motion Controller 2. This labeled dataset will serve as the foundation for future machine learning models aimed at predicting hand gestures using sEMG signals.

*Include a brief description of the project's significance, the challenges addressed, and potential applications.*

## Getting Started

### Prerequisites
- Python 3.8
- Required Python packages (listed in `requirements.txt`)
- Ultraleap Motion Controller 2
- Xtrodes Ltd sEMG electrode array (16 electrodes)
- Xtrodes Ltd Bluetooth-enabled data acquisition unit (DAU)
- Xtrodes Ltd custom "Bluetooth Low Energy C# sample" Windows application


### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/NeuroEngLabTAU/Fingers_Gestures_Recognition.git

2. Navigate to the project directory:
   ```bash
   cd Fingers_Gestures_Recognition

3. Install the required packages:
   ```bash
   pip install -r requirements.txt

## Usage
*Provide instructions on how to run the data collection scripts, train the model, and evaluate the results.*

## Data Collection
### Hardware Setup
*Provide detailed instructions on setting up the Xtrodes Ltd sEMG electrodes and the Ultraleap Motion Controller 2, including connection details and positioning.*
- Set up the Xtrodes Ltd sEMG electrode array and attach the electrodes on the forearm.
- Connect the electrodes to the Bluetooth DAU.
- Set up the Ultraleap Motion Controller 2 and ensure it is positioned to capture finger movements.

### Data Acquisition
*Explain how to use the scripts to start data collection. Include details about the Bluetooth integration with the DAU and how to initiate simultaneous recording with the Leap Motion Controller 2.*
- Open data_collection.py script. Verify the parameters (num_repetition, gesture_duration, rest_duration) are set as desired.
  - num_repetition: Defines the number of times each gesture image will be shown. For example, setting it to 5, means each image will be shown 5 times throughout the experiment.
  - gesture_duration: Duration (in seconds) for which the participant should perform the hand gesture. This determines how long each gesture image will be displayed.
  - rest_duration: Duration (in seconds) for which the participant should relax their palm between gestures.
- Ensure the correct gesture images are in the ‘images’ folder.

- The Bluetooth DAU will transmit the sEMG data to your machine, while the Leap Motion Controller will record hand gestures.

### Data Synchronization
*Describe how the data from the sEMG electrodes and the Leap Motion Controller 2 are synchronized, including any time-stamping or alignment techniques used.*
The EMG and visual data are collected by running two separate processes on the same computer during recording, to establish synchrony.

### Saved Data Files
- Data is saved in a folder labeled with the participant’s serial number. Each session is stored in a subfolder named S# (e.g., S1), with four subfolders for each hand position P# (P1, P2, P3, and P4). 
  - If a participant completes multiple sessions, all data is saved in the corresponding session folder (e.g., S1, S2).
  - The folder size for a single session is approximately 160 MB.

- Each of the hand-position folders (P#) contain the following files:
  - EMG data is saved in an EDF file, named as follows:
    “fpe_pos{position number}_{subject number}_S{session number}_rep0_BT”
  - Hand-tracking data is saved in a CSV file, named:
    “fpe_pos{position number}_{subject number}_S{session number}_rep0_BT_full”
  - A log file, log.txt, contains metadata about the session.

- Example data files are located in finger_pose_estimation/data_aquisition/dataset directory.


## Repository Structure
   ```bash
   Fingers_Gestures_Recognition/
   │
   ├── finger_pose_estimation/    # Python scripts for data collection
   ├── LeapSDK/                   # files for integrating Ultraleap camera with python
   ├── leapc/                     # files for integrating Ultraleap camera with python
   ├── requirements.txt           # Python package dependencies
   └── README.md                  # Project documentation
```

*Provide additional details about the directory structure if necessary.*

## Contributing
*Guidelines for contributing to the project, including how to report issues and submit pull requests.*

## License
*Specify the license under which the project is distributed.*

## Acknowledgements
*Mention any funding sources, collaborators, or external resources that were instrumental in the completion of the project.*
