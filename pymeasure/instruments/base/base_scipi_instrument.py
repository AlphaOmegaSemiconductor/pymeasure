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

from pymeasure.instruments import Instrument, SCPIMixin, SCPIUnknownMixin

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Generic_Manufacturer"
MODEL = "Generic_Model"

class InstrumentSCPI(Instrument, SCPIMixin):
    f''' Generic base class for SCPI instruments. Can be used as a stand in for any SCPI instrument.
    Manufacturer: {MFG}
    Model: {MODEL}
    '''
    pass


class InstrumentSCPIUnknown(Instrument, SCPIUnknownMixin):
    f''' Generic base class for Unknown SCPI instruments. Can be used as a stand in.
    Manufacturer: {MFG}
    Model: {MODEL}
    '''
    pass