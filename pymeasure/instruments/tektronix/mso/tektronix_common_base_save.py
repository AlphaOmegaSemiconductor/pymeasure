#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2024 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, sub_system
from pymeasure.instruments.process import set_processor_dict_map
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import DICTS


class Save(sub_system.CommandGroupSubSystem):
    """
    Represents the Save and Recall subsystem of the oscilloscope.

    Provides commands to save screen images, waveforms, setups, sessions,
    measurement event tables, plot data, masks, and reports to files on the
    instrument filesystem.
    """

    # --- SAVe:EVENTtable commands ---

    save_bus_event_table = Instrument.setting(
        'SAVe:EVENTtable:BUS "%s"',
        """Saves the bus decode results table to the specified file path (CSV).""",
    )

    save_custom_event_table = Instrument.setting(
        'SAVe:EVENTtable:CUSTom "%s"',
        """Saves the custom results table to the specified file path and name.""",
    )

    custom_event_table_comments = Instrument.control(
        'SAVe:EVENTtable:CUSTom:COMMents?', 'SAVe:EVENTtable:CUSTom:COMMents "%s"',
        """Sets or queries comments to be included in saved results table files.""",
    )

    CUSTOM_EVENT_TABLE_DATA_FORMAT = {"Scientific": "SCIentific", "Engineering": "ENGineering"}
    custom_event_table_data_format = Instrument.control(
        'SAVe:EVENTtable:CUSTom:DATAFormat?', 'SAVe:EVENTtable:CUSTom:DATAFormat %s',
        """Sets or queries the data format for saving results table data.

        Values: {SCIentific|ENGineering}
        SCIentific: Scientific notation (e.g. 5.0100E-12)
        ENGineering: Engineering notation (e.g. 5.0100ps)
        """,
        preprocess_input=set_processor_dict_map(CUSTOM_EVENT_TABLE_DATA_FORMAT),
        validator=strict_discrete_set,
        values=CUSTOM_EVENT_TABLE_DATA_FORMAT,
        map_values=True
    )

    custom_event_table_include_refs = Instrument.control(
        'SAVe:EVENTtable:CUSTom:INCLUDEREFs?', 'SAVe:EVENTtable:CUSTom:INCLUDEREFs %d',
        """Sets or queries whether to include displayed reference waveforms in saved results table files.

        Values: {1|0}
        """,
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True
    )

    save_measurement_event_table = Instrument.setting(
        'SAVe:EVENTtable:MEASUrement "%s"',
        """Saves measurement (data) results to the specified file path (CSV).""",
    )

    save_peaks_event_table = Instrument.setting(
        'SAVe:EVENTtable:PEAKS "%s"',
        """Saves the peak markers results table to the specified file path (CSV).""",
    )

    save_search_table = Instrument.setting(
        'SAVe:EVENTtable:SEARCHTable "%s"',
        """Saves the search results table to the specified file path (CSV).""",
    )

    # --- SAVe:IMAGe commands ---
        #TODO implement a validator for this input, it needs to be a valid path (windows like?) and have a supported image filetype extension suffix
    save_image = Instrument.setting(
        'SAVe:IMAGe "%s"',
        """Saves a capture of the screen contents to the specified image file.

        Use the correct file extension: .png for PNG, .bmp for BMP, .jpg for JPEG.
        """,
        # preprocess_input=lambda x: x,
        # validator=lambda x: x,
    )

    IMAGE_COMPOSITION_OPTIONS = {"Normal": "NORMal", "Inverted": "INVErted"}
    image_composition = screen_capture_colors = Instrument.control(
        'SAVe:IMAGe:COMPosition?', 'SAVe:IMAGe:COMPosition %s',
        """Sets or queries the color mode for saved screen capture images.

        Values: {NORMal|INVerted}
        NORMal: Save with normal display colors (default black background)
        INVErted: Save with inverted colors (default white background)
        """,
        preprocess_input=set_processor_dict_map(IMAGE_COMPOSITION_OPTIONS),
        validator=strict_discrete_set,
        values=IMAGE_COMPOSITION_OPTIONS,
        map_values=True
    )

    image_view_type = Instrument.control(
        'SAVe:IMAGe:VIEWTYpe?', 'SAVe:IMAGe:VIEWTYpe %s',
        """Sets or queries the view type for saved images.

        Currently only FULLScreen is supported.
        """,
        validator=strict_discrete_set,
        values=["FULLScreen"]
    )

    # --- SAVe:MASK command ---

    save_mask = Instrument.setting(
        'SAVe:MASK "%s"',
        """Saves the given Waveview Mask to the specified file.

        Segment-based masks must use .xml extension; tolerance masks must use .tol extension.
        """,
    )

    # --- SAVe:PLOTData command ---

    save_plot_data = Instrument.setting(
        'SAVe:PLOTData "%s"',
        """Saves the plot data of the currently selected plot to a CSV file.

        Use DISplay:SELect:VIEW to select the desired plot view first.
        """,
    )

    # --- SAVe:REPOrt commands ---

    save_report = Instrument.setting(
        'SAVe:REPOrt "%s"',
        """Saves a report to the specified file.

        Supported formats: PDF (.pdf), MHT web page archive (.mht).
        """,
    )

    report_comments = Instrument.control(
        'SAVe:REPOrt:COMMents?', 'SAVe:REPOrt:COMMents "%s"',
        """Sets or queries comments to be included in saved report files.""",
    )

    # --- SAVe:SESsion command ---

    save_session = Instrument.setting(
        'SAVe:SESsion "%s"',
        """Saves the state of the instrument, including reference waveforms, to a session file (.tss).""",
    )

    # --- SAVe:SETUp commands ---

    save_setup = Instrument.setting(
        'SAVe:SETUp "%s"',
        """Saves the current instrument state to the specified setup file (.set).""",
    )

    setup_include_refs = Instrument.control(
        'SAVe:SETUp:INCLUDEREFs?', 'SAVe:SETUp:INCLUDEREFs %s',
        """Sets or queries whether displayed reference waveforms are included in saved setups.

        Values: {ON|OFF}
        """,
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # --- SAVe:WAVEform commands ---

    waveform_source_list = Instrument.measurement(
        'SAVe:WAVEform:SOURCELIst?',
        """Returns a comma-separated list of available waveforms that can be saved.

        Source waveforms must have their display mode set to On to appear in this list.
        """,
    )

    WAVEFORM_GATING_OPTIONS = {
        "None": "NONe",
        "Cursors": "CURSors",
        "Screen": "SCREEN",
        "Resample": "RESAMPLE",
        "Selected": "SELected",
    }
    waveform_gating = Instrument.control(
        'SAVe:WAVEform:GATing?', 'SAVe:WAVEform:GATing %s',
        """Sets or queries the method used to save waveform data.

        Values: {NONe|CURSors|SCREEN|RESAMPLE|SELected}
        NONe: Saves the full waveform data
        CURSors: Saves waveform data between the vertical cursors
        SCREEN: Saves only the waveform data visible on screen
        RESAMPLE: Saves a resampled version with fewer data points
        SELected: Saves the currently selected history or FastFrame acquisition
        """,
        preprocess_input=set_processor_dict_map(WAVEFORM_GATING_OPTIONS),
        validator=strict_discrete_set,
        values=WAVEFORM_GATING_OPTIONS,
        map_values=True
    )

    waveform_gating_resample_rate = Instrument.control(
        'SAVe:WAVEform:GATing:RESAMPLErate?', 'SAVe:WAVEform:GATing:RESAMPLErate %d',
        """Sets or queries the resample interval when waveform_gating is set to RESAMPLE.

        Specifies how many data points to skip — e.g. 3 saves every third data point.
        Range: 1 to 1,000,000
        """,
        validator=strict_range,
        values=(1, 1000000)
    )

    def save_waveform(self, source: str, file_path: str) -> None:
        """Saves the specified waveform to a file on the instrument filesystem.

        Args:
            source: Waveform source identifier. Examples: 'CH1', 'CH2', 'MATH1',
                    'REF1', 'ALL', 'CH1_DALL' (digital), 'CH1_SV_NORMal' (spectrum).
            file_path: Destination path on the instrument. Use .wfm for Tektronix
                       internal format, .csv for spreadsheet, .mat for MATLAB format.
        """
        self.parent.write(f'SAVe:WAVEform {source},"{file_path}"')
