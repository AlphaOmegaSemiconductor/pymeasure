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
from warnings import warn

from .instrument import Instrument
from .validators import strict_range

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class IEEE4882Mixin:
    """Mixin class for IEEE 488.2 instruments implementing the standard common (*) commands.

    Reference: https://standards.ieee.org/ieee/488.2/718/

    Commands mandated by IEEE 488.2::

        Mnemonic  Name                                  488.2 Section
        --------  ------------------------------------  -------------
        *CLS      Clear Status Command                  10.3
        *ESE      Standard Event Status Enable Command  10.10
        *ESE?     Standard Event Status Enable Query    10.11
        *ESR?     Standard Event Status Register Query  10.12
        *IDN?     Identification Query                  10.14
        *OPC      Operation Complete Command            10.18
        *OPC?     Operation Complete Query              10.19
        *RST      Reset Command                         10.32
        *SRE      Service Request Enable Command        10.34
        *SRE?     Service Request Enable Query          10.35
        *STB?     Read Status Byte Query                10.36
        *TST?     Self-Test Query                       10.38
        *WAI      Wait-to-Continue Command              10.39

    Members are declared below in the same order as the table above. The optional
    ``*OPT?`` (Option Identification Query) is additionally implemented between
    ``*OPC?`` and ``*RST``. The ``*OPC`` write form is not exposed; use
    :attr:`complete` (``*OPC?``) for synchronization.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("includeSCPI", False)  # in order not to trigger the deprecation warning
        super().__init__(*args, **kwargs)

    def clear(self):
        """Clear the instrument status byte."""
        self.write("*CLS")

    event_status_enable = Instrument.control(
        "*ESE?", "*ESE %d",
        """Control the Standard Event Status Enable register (int, 0-255).

        Each bit enables the corresponding event in the Standard Event Status Register
        to be summarized in the Status Byte (ESB bit).
        """,
        validator=strict_range,
        values=[0, 255],
        cast=int,
    )

    event_status = Instrument.measurement(
        "*ESR?",
        """Get the Standard Event Status Register value (int).

        Reading this register clears it.
        """,
        cast=int,
    )

    id = Instrument.measurement(
        "*IDN?",
        """Get the identification of the instrument.""",
        cast=str,
        maxsplit=0,
    )

    complete = Instrument.measurement(
        "*OPC?",
        """Get the synchronization bit.

        This property allows synchronization between a controller and a device. The Operation
        Complete query places an ASCII character 1 into the device's Output Queue when all pending
        selected device operations have been finished.
        """,
        cast=str,
    )

    options = Instrument.measurement(
        "*OPT?",
        """Get the device options installed.""",
        cast=str,
    )

    def reset(self):
        """Reset the instrument."""
        self.write("*RST")

    service_request_enable = Instrument.control(
        "*SRE?", "*SRE %d",
        """Control the Service Request Enable register (int, 0-255).

        Each bit enables the corresponding bit in the Status Byte to generate a
        service request.
        """,
        validator=strict_range,
        values=[0, 255],
        cast=int,
    )

    status = Instrument.measurement(
        "*STB?",
        """Get the status byte and Master Summary Status bit.""",
        cast=str,
    )

    self_test = Instrument.measurement(
        "*TST?",
        """Get the result of the instrument self-test (int, 0 means no errors).""",
        cast=int,
    )

    def wait_to_continue(self):
        """Prevent the instrument from executing further commands until all pending
        operations complete (*WAI)."""
        self.write("*WAI")


class SCPI1999Mixin(IEEE4882Mixin):
    """Mixin class for SCPI 1999 instruments.

    Inherits the IEEE 488.2 common commands via :class:`IEEE4882Mixin` and adds
    the SCPI command-tree members.

    Reference: https://www.ivifoundation.org/downloads/SCPI/scpi-99.pdf

    Required SCPI commands (command tree)::

        Mnemonic              Cmd Ref  Syntax/Style
        --------------------  -------  -----------------
        :SYSTem
            :ERRor            21.8
                [:NEXT]?      21.8.3   (Note 1) 1996
            :VERSion?         19.16    (Note 2) 1991
        :STATus               18       5
            :OPERation
                [:EVENt]?
                :CONDition?
                :ENABle
                :ENABle?
            :QUEStionable
                [:EVENt]?
                :CONDition?
                :ENABle
                :ENABle?
            :PRESet

    Members are declared below in the same order as the tree above. The
    bracketed ``[:EVENt]`` node is optional in the SCPI syntax, so the explicit
    ``:EVENt?`` form is used for the queries.
    """

    next_error = Instrument.measurement(
        "SYST:ERR?",
        """Get the next error in the queue.
        If you want to read and log all errors, use :meth:`check_errors` instead.
        """,
    )

    scpi_version = Instrument.measurement(
        "SYST:VERS?",
        """Get the SCPI version implemented by the instrument (str, e.g. ``"1999.0"``).""",
        cast=str,
    )

    operation_event = Instrument.measurement(
        "STAT:OPER:EVEN?",
        """Get the OPERation event register (int).

        Reading this register clears it.
        """,
        cast=int,
    )

    operation_condition = Instrument.measurement(
        "STAT:OPER:COND?",
        """Get the OPERation condition register (int).""",
        cast=int,
    )

    operation_enable = Instrument.control(
        "STAT:OPER:ENAB?", "STAT:OPER:ENAB %d",
        """Control the OPERation enable register (int, 0-65535).""",
        validator=strict_range,
        values=[0, 65535],
        cast=int,
    )

    questionable_event = Instrument.measurement(
        "STAT:QUES:EVEN?",
        """Get the QUEStionable event register (int).

        Reading this register clears it.
        """,
        cast=int,
    )

    questionable_condition = Instrument.measurement(
        "STAT:QUES:COND?",
        """Get the QUEStionable condition register (int).""",
        cast=int,
    )

    questionable_enable = Instrument.control(
        "STAT:QUES:ENAB?", "STAT:QUES:ENAB %d",
        """Control the QUEStionable enable register (int, 0-65535).""",
        validator=strict_range,
        values=[0, 65535],
        cast=int,
    )

    def status_preset(self):
        """Preset the SCPI status registers (``:STATus:PRESet``).

        Resets the OPERation and QUEStionable enable registers to their power-on defaults.
        """
        self.write("STAT:PRES")

    def check_errors(self):
        """ Read all errors from the instrument.

        :return: List of error entries.
        """
        errors = []
        while True:
            err = self.next_error
            if int(err[0]) != 0:
                log.error(f"{self.name}: {err[0]}, {err[1]}")
                errors.append(err)
            else:
                break
        return errors


# Backward-compatible alias. Existing drivers and user code importing ``SCPIMixin``
# continue to work unchanged. We can implement more standards if ever required
SCPIMixin = SCPI1999Mixin


class SCPIUnknownMixin(SCPIMixin):
    """Mixin which adds SCPI commands to an instrument from which it is not known whether it
    supports SCPI commands or not.
    """

    def __init__(self, *args, **kwargs):
        warn("It is not known whether this device support SCPI commands or not. Please inform "
             "the pymeasure maintainers if you know the answer.", FutureWarning)
        super().__init__(*args, **kwargs)
