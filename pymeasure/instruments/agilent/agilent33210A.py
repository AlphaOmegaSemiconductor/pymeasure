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
from.agilent332xx_base import Agilent332xx
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


MFG = "Agilent"
MODEL = "33210A"

class Agilent33210A(Agilent332xx):
    f"""Represents the {MFG} {MODEL} Arbitrary Waveform Generator.

    .. code-block:: python

        # Default channel for the Agilent 33220A
        wfg = {MFG}{MODEL}("GPIB::10")

        wfg.shape = "SINUSOID"          # Sets a sine waveform
        wfg.frequency = 4.7e3           # Sets the frequency to 4.7 kHz
        wfg.amplitude = 1               # Set amplitude of 1 V
        wfg.offset = 0                  # Set the amplitude to 0 V

        wfg.burst_state = True          # Enable burst mode
        wfg.burst_ncycles = 10          # A burst will consist of 10 cycles
        wfg.burst_mode = "TRIGGERED"    # A burst will be applied on a trigger
        wfg.trigger_source = "BUS"      # A burst will be triggered on TRG*

        wfg.output = True               # Enable output of waveform generator
        wfg.trigger()                   # Trigger a burst
        wfg.wait_for_trigger()          # Wait until the triggering is finished
        wfg.beep()                      # "beep"

        print(wfg.check_errors())       # Get the error queue

    """

    def __init__(self, adapter, name=f"{MFG} {MODEL} Arbitrary Waveform generator", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )
