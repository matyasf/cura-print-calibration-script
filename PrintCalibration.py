import re

from ..Script import Script
from UM.Application import Application


class PrintCalibration(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Print Calibration",
            "key": "PrintCalibration",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "calibrate_retraction":
                {
                    "label": "Calibrate retraction",
                    "description": "Change retraction as Z increases",
                    "type": "bool",
                    "default_value": false
                },
                "retract_start_value":
                {
                    "label": "Starting retraction value",
                    "description": "Starting retraction value in mm. Applies from the second layer.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                    "minimum_value": "0",
                    "enabled": "calibrate_retraction"
                },
                "retract_end_value":
                {
                    "label": "Ending retraction value",
                    "description": "Ending retraction value in mm.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 6.0,
                    "minimum_value": "1",
                    "enabled": "calibrate_retraction"
                },
                "retract_test_height":
                {
                    "label": "Retraction test Z distance",
                    "description": "Z height in mm to reach from start to end value. Layers above with height will be printed with the ending value.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 50.0,
                    "minimum_value": "10",
                    "enabled": "calibrate_retraction"
                },
                "calibrate_temperature":
                {
                    "label": "Calibrate temperature",
                    "description": "Change temperature as Z increases",
                    "type": "bool",
                    "default_value": false
                },
                "temp_start_value":
                {
                    "label": "Starting temperature value",
                    "description": "Starting temperature value in C. Applies from the second layer.",
                    "unit": "C",
                    "type": "float",
                    "default_value": 180.0,
                    "minimum_value": "150",
                    "enabled": "calibrate_temperature"
                },
                "temp_end_value":
                {
                    "label": "Ending temperature value",
                    "description": "Ending temperature value in C.",
                    "unit": "C",
                    "type": "float",
                    "default_value": 220.0,
                    "minimum_value": "150",
                    "enabled": "calibrate_temperature"
                },
                "temp_test_height":
                {
                    "label": "Temperature test Z distance",
                    "description": "Z height in mm to reach from start to end value. Layers above with height will be printed with the ending value.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 50.0,
                    "minimum_value": "10",
                    "enabled": "calibrate_temperature"
                }
            }
        }"""

    def execute(self, data):
        if self.getSettingValueByKey("calibrate_retraction"):
            data = self.calibrate_retraction(data)
        if self.getSettingValueByKey("calibrate_temperature"):
            data = self.calibrate_temperature(data)
        return data

    def calibrate_temperature(self, data):
        layers_started = False
        for layer_number, layer in enumerate(data):
            modified_gcode = ""
            current_z = self.get_layer_z(layer)
            lines = layer.split("\n")
            for line in lines:
                modified_gcode += line + "\n"
                if ";LAYER:1" in line:  # do not mess up initial layers
                    layers_started = True
                if layers_started and ";LAYER:" in line:
                    current_layer_ratio = current_z / self.getSettingValueByKey("temp_test_height")
                    if current_layer_ratio > 1:
                        current_layer_ratio = 1
                    temp_to_set = (current_layer_ratio *
                                   (self.getSettingValueByKey("temp_end_value") -
                                    self.getSettingValueByKey("temp_start_value")) +
                                   self.getSettingValueByKey("temp_start_value"))
                    modified_gcode += "M104 S" + str(temp_to_set) + " ; temperature, Z height: " + str(current_z) + "\n"
            data[layer_number] = modified_gcode
        return data

    def calibrate_retraction(self, data):
        current_retraction = Application.getInstance().getExtruderManager().getActiveExtruderStacks()[0].getProperty(
            "retraction_amount", "value")
        layers_started = False
        last_e = 0
        for layer_number, layer in enumerate(data):
            # Check that a layer is being printed
            modified_gcode = ""
            current_z = self.get_layer_z(layer)
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:1" in line:  # do not mess up initial layers
                    layers_started = True
                # Retraction: If line looks like "G1 Zxxx Eyyy" AND E has decreased by the configured retraction value
                m = re.search('[G][01] F[0-9]* E[0-9]*', line)
                current_e = self.getValue(line, "E")
                if layers_started and m is not None and abs(last_e - current_e - current_retraction) < 0.01:
                    current_layer_ratio = current_z / self.getSettingValueByKey("retract_test_height")
                    if current_layer_ratio > 1:
                        current_layer_ratio = 1
                    retract_to_set = current_layer_ratio * (self.getSettingValueByKey("retract_end_value") -
                                                            self.getSettingValueByKey("retract_start_value"))
                    new_retract = current_e + current_retraction - retract_to_set
                    modified_gcode += self.putValue(line, E=new_retract) + "\n"
                else:
                    modified_gcode += line + "\n"
                if current_e is not None:
                    last_e = current_e
            data[layer_number] = modified_gcode
        return data

    def get_layer_z(self, layer: str) -> int:
        """
        Calculates the Z height of the layer.
        It needs to be this way because adaptive layers/Z hop can change it
        """
        lines = layer.split("\n")
        layer_z = 999999
        for line in lines:
            current_z = self.getValue(line, "Z")
            if current_z is not None:
                layer_z = min(current_z, layer_z)
        return layer_z
