import numpy as np

from ..errors import FileFormatNotSupportedError


__all__ = ["JPK_COLUMNS",
           "JPK_SLOTS",
           "JPK_UNITS",
           "ReadJPKError",
           "find_column_dat",
           "load_dat_raw",
           "load_dat_unit",
           ]

#: Maps afmformats column names to JPK column names
JPK_COLUMNS = {
    "force": ["vDeflection"],
    "height (measured)": ["strainGaugeHeight", "capacitiveSensorHeight",
                          "measuredHeight"],
    "height (piezo)": ["height", "head-height"],
}

#: Maps afmformats column names to default JPK normalization slots
JPK_SLOTS = {
    "force": "force",
    "height (measured)": "nominal",
    "height (piezo)": "calibrated",
}

#: Maps afmformats column names to default JPK units
JPK_UNITS = {
    "force": "N",
    "height (measured)": "m",
    "height (piezo)": "m",
}


class ReadJPKError(FileFormatNotSupportedError):
    pass


def find_column_dat(loc_list, column):
    """Find a column in a list of strings

    Parameters
    ----------
    loc_list: list of str
        The segment's data location list (within the archive), e.g.

        ['segments/0/channels/height.dat',
         'segments/0/channels/vDeflection.dat',
         'segments/0/channels/strainGaugeHeight.dat']

    column: str
        afmformats column name :const:`afmformats.afm_data.known_columns`

    Returns
    -------
    name: str
        Matched column name from :const:`JPK_COLUMNS`,
        e.g. "strainGaugeHeight"
    slot: str
        Default slot location from :const:`JPK_SLOTS`
    loc: str
        Matched data location in zip file,
        e.g. "segments/0/channels/strainGaugeHeight.dat"
    """
    id_list = JPK_COLUMNS[column]
    col = None
    for dd in loc_list:
        cn = dd.rsplit("/")[-1].rsplit(".")[0]
        for vc in id_list:
            if vc == cn:
                col = vc
                break
        if col:
            break
    else:
        msg = "No data found for: {}".format(id_list)
        raise ReadJPKError(msg)
    slot = JPK_SLOTS[column]
    return col, slot, dd


def load_dat_raw(fd, name, properties):
    """Load data from binary JPK .dat files

    Parameters
    ----------
    fd: file
        Open .dat file
    name: str
        Name of the data to read (required for scale conversions)
        (valid options are values in :const:`JPK_COLUMNS`)
    properties: dict
        Property dictionary metadata (see also
        :func:`JPKReader._get_index_segment_properties`)

    Returns
    -------
    data: 1d ndarray
        A numpy array with the raw data.

    Notes
    -----
    This method tries to correctly determine the data type of the
    binary data and scales it with the `data.encoder.scaling`
    values given in the header files.

    See Also
    --------
    load_dat_unit: Includes conversion to useful units
    """
    # Multiplier
    mult_str1 = "channel.{}.data.encoder.scaling.multiplier".format(name)
    mult_str2 = "channel.{}.encoder.scaling.multiplier".format(name)
    try:
        mult = properties[mult_str1]
    except BaseException:
        mult = properties[mult_str2]

    # Offset
    off_str1 = "channel.{}.data.encoder.scaling.offset".format(name)
    off_str2 = "channel.{}.encoder.scaling.offset".format(name)
    try:
        off = properties[off_str1]
    except BaseException:
        off = properties[off_str2]

    # Data type
    enc_str1 = "channel.{}.data.encoder.type".format(name)
    enc_str2 = "channel.{}.encoder.type".format(name)
    try:
        enc = properties[enc_str1]
    except BaseException:
        enc = properties[enc_str2]
    # determine encoder
    if enc == "signedshort":
        mydtype = np.dtype(">i2")
    elif enc == "unsignedshort":
        mydtype = np.dtype(">u2")
    elif enc == "signedinteger":
        mydtype = np.dtype(">i4")
    elif enc == "unsignedinteger":
        mydtype = np.dtype(">u4")
    elif enc == "signedlong":
        mydtype = np.dtype(">i8")
    else:
        raise NotImplementedError("Data file format '{}' not supported".
                                  format(enc))

    data = np.frombuffer(fd.read(), dtype=mydtype) * mult + off
    return data


def load_dat_unit(fd, name, properties, slot="default"):
    """Load data from a JPK .dat file with a specific calibration slot

    Parameters
    ----------
    fd: file
        Open .dat file
    name: str
        Name of the data to read (required for scale conversions)
        (valid options are values in :const:`JPK_COLUMNS`)
    properties: dict
        Property dictionary metadata (see also
        :func:`JPKReader._get_index_segment_properties`)
    slot: str
        The .dat files in the JPK measurement zip files come with different
        calibration slots. Valid values are

            - For the height of the piezo crystal during measurement
              (the piezo height is not as accurate as the measured height
              from the height sensor; the piezo movement is not linear):
              "height.dat": "volts", "nominal", "calibrated"

            - For the measured height of the cantilever:
              "strainGaugeHeight.dat": "volts", "nominal", "absolute"
              "measuredHeight.dat":  "volts", "nominal", "absolute"
              "capacitiveSensorHeight": "volts", "nominal", "absolute"
              (they are all the same)

            - For the recorded cantilever deflection:
              "vDeflection.dat": "volts", "distance", "force"

    Returns
    -------
    data: 1d ndarray
        A numpy array containing the scaled data.
    unit: str
        A string representing the metric unit of the data.
    name: str
        The name of the data column.


    Notes
    -----
    The raw data (see `load_dat_raw`) is usually stored in "volts" and
    needs to be converted to e.g. "force" for "vDeflection" or "nominal"
    for "strainGaugeHeight". The conversion parameters (offset, multiplier)
    are stored in the header files and they are not stored separately for
    each slot, but the conversion parameters are stored relative to the
    slots. For instance, to compute the "force" slot from the raw "volts"
    data, one first needs to compute the "distance" slot. This conversion
    is taken care of by this method.

    This is an example header:

        channel.vDeflection.data.file.name=channels/vDeflection.dat
        channel.vDeflection.data.file.format=raw
        channel.vDeflection.data.type=short
        channel.vDeflection.data.encoder.type=signedshort
        channel.vDeflection.data.encoder.scaling.type=linear
        channel.vDeflection.data.encoder.scaling.style=offsetmultiplier
        channel.vDeflection.data.encoder.scaling.offset=-0.00728873489143207
        channel.vDeflection.data.encoder.scaling.multiplier=3.0921021713588157E-4
        channel.vDeflection.data.encoder.scaling.unit.type=metric-unit
        channel.vDeflection.data.encoder.scaling.unit.unit=V
        channel.vDeflection.channel.name=vDeflection
        channel.vDeflection.conversion-set.conversions.list=distance force
        channel.vDeflection.conversion-set.conversions.default=force
        channel.vDeflection.conversion-set.conversions.base=volts
        channel.vDeflection.conversion-set.conversion.volts.name=Volts
        channel.vDeflection.conversion-set.conversion.volts.defined=false
        channel.vDeflection.conversion-set.conversion.distance.name=Distance
        channel.vDeflection.conversion-set.conversion.distance.defined=true
        channel.vDeflection.conversion-set.conversion.distance.type=simple
        channel.vDeflection.conversion-set.conversion.distance.comment=Distance
        channel.vDeflection.conversion-set.conversion.distance.base-calibration-slot=volts
        channel.vDeflection.conversion-set.conversion.distance.calibration-slot=distance
        channel.vDeflection.conversion-set.conversion.distance.scaling.type=linear
        channel.vDeflection.conversion-set.conversion.distance.scaling.style=offsetmultiplier
        channel.vDeflection.conversion-set.conversion.distance.scaling.offset=0.0
        channel.vDeflection.conversion-set.conversion.distance.scaling.multiplier=7.000143623002982E-8
        channel.vDeflection.conversion-set.conversion.distance.scaling.unit.type=metric-unit
        channel.vDeflection.conversion-set.conversion.distance.scaling.unit.unit=m
        channel.vDeflection.conversion-set.conversion.force.name=Force
        channel.vDeflection.conversion-set.conversion.force.defined=true
        channel.vDeflection.conversion-set.conversion.force.type=simple
        channel.vDeflection.conversion-set.conversion.force.comment=Force
        channel.vDeflection.conversion-set.conversion.force.base-calibration-slot=distance
        channel.vDeflection.conversion-set.conversion.force.calibration-slot=force
        channel.vDeflection.conversion-set.conversion.force.scaling.type=linear
        channel.vDeflection.conversion-set.conversion.force.scaling.style=offsetmultiplier
        channel.vDeflection.conversion-set.conversion.force.scaling.offset=0.0
        channel.vDeflection.conversion-set.conversion.force.scaling.multiplier=0.043493666407368466
        channel.vDeflection.conversion-set.conversion.force.scaling.unit.type=metric-unit
        channel.vDeflection.conversion-set.conversion.force.scaling.unit.unit=N

    To convert from the raw "volts" data to force data, these steps are
    performed:

    - Convert from "volts" to "distance" first, because the
      "base-calibration-slot" for force is "distance".

      distance = volts*7.000143623002982E-8 + 0.0

    - Convert from "distance" to "force":

      force = distance*0.043493666407368466 + 0.0

    The multipliers shown above are the values for sensitivity and spring
    constant:
    sensitivity = 7.000143623002982E-8 m/V
    spring_constant = 0.043493666407368466 N/m
    """
    data = load_dat_raw(fd, name=name, properties=properties)

    conv = "channel.{}.conversion-set".format(name)
    if slot == "default":
        slot = properties[conv + ".conversions.default"]

    # get base unit
    base = properties[conv + ".conversions.base"]

    # Now iterate through the conversion sets until we have the base converter.
    # A list of multipliers and offsets
    converters = []
    curslot = slot

    while curslot != base:
        # Get current slot multipliers and offsets
        off_str = conv + ".conversion.{}.scaling.offset".format(curslot)
        off = properties[off_str]
        mult_str = conv + ".conversion.{}.scaling.multiplier".format(curslot)
        mult = properties[mult_str]
        converters.append([mult, off])
        sl_str = conv + ".conversion.{}.base-calibration-slot".format(curslot)
        curslot = properties[sl_str]

    # Get raw data
    for c in converters[::-1]:
        data[:] = c[0] * data[:] + c[1]

    if base == slot:
        unit_str = "channel.{}.data.encoder.scaling.unit.unit".format(name)
        unit = properties[unit_str]
    else:
        try:
            unit_str = conv + ".conversion.{}.scaling.unit".format(slot)
            unit = properties[unit_str]
        except KeyError:
            unit_str = conv + ".conversion.{}.scaling.unit.unit".format(slot)
            unit = properties[unit_str]

    name_str = conv + ".conversion.{}.name".format(slot)
    out_name = properties[name_str]
    return data, unit, "{} ({})".format(name, out_name)
