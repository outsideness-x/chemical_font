"""Vertical metrics and the skeleton lines derived from them.

Ink lines are where the marker's ink ends; skeleton lines are where the centre
of the pen has to travel so that its ink lands on those ink lines.
"""

UPM = 1000

# ink lines
CAP = 700
XH = 565  # tall lowercase: mixing cases looks natural
ASC = 775  # b d h k l rise a little above the capitals
DESC = -220

PEN = 84.0  # marker width
THIN = 26.0  # fineliner width (ss01)

# half of the ink a horizontal stroke adds above/below its centre line
HV = 35.0

# skeleton lines
B = HV  # baseline
XT = XH - HV  # x-height
CT = CAP - HV  # cap height
AT = ASC - HV  # ascender
DB = DESC + HV  # descender
OS = 11.0  # overshoot of round shapes

# font-wide vertical metrics
ASCENDER = 950
DESCENDER = -290
LINE_GAP = 0
