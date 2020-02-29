# cura-print-calibration-script
Post Processing Script for Cura that helps calibrate your printer. It has currently 2 features:
- change toolhead temperature as the height of the print changes
- change retraction as the height of the print changes

![plugin screenshot](https://i.imgur.com/VUeNXk0.png)


Installation:    
Copy `PrintCalibation.py` to `Cura/plugins/PostProcessingPlugin/scripts` and start Cura.

Usage:     
The script will be in Extensions -> Post Processing -> Modify G-code. Here select add Script and `Print calibration`

Notes:    
Tested with Cura 4.2.1 and 4.5.0     
It changes values for the first toolhead only and might be buggy in multi-extrusion setups.

License: Apache 2.0, see https://www.apache.org/licenses/LICENSE-2.0
