import zospy as zp
from itertools import groupby 


# List of columns to be ignored when listing the TDE operands
# This is due to the different reporting of operand data in the Sensitivity Analysis
# E.g. TEZI has Max# and Min# columns that aren't shown in the Sensitivity Analysis
# It might be necessary to add elements to this list as I didn't test all the possible operands
IGNORE_COLUMNS = ["Max#", "Min#"]


# Connect a ZOSAPI interactive extension via ZOSPy
# Note that ZOSPy is a community-led initiative currently not supported by ANSYS
# (i.e. don't ask ANSYS about ZOSPy)
def connect_zosapi():
    zos = zp.ZOS()
    zos.wakeup()
    zos.connect_as_extension()

    return zos.get_primary_system()

# List the operands in the TDE
def get_tde_operands(oss):
    tde_listing = []

    tde = oss.TDE
    number_of_operands = tde.NumberOfOperands

    # Loop over the operands of the TDE and get meaningful data to retrieve
    # the corresponding operand in the Sensitivity Analysis summary
    for operand_index in range(1, number_of_operands+1):
        operand = tde.GetOperandAt(operand_index)

        operand_data = {
            "Type": operand.TypeName.split()[1],
            "Int1": operand.Param1,
            "Int2": 0,
            "Int3": 0
        }

        # This is where it is necessary to filter out some Param2 and Param3 cells
        # depending on their content as it might not be displayed in the Sensitivity Analysis
        if operand.Param2Cell.Header not in IGNORE_COLUMNS:
            operand_data["Int2"] = operand.Param2
        if operand.Param3Cell.Header not in IGNORE_COLUMNS:
            operand_data["Int3"] = operand.Param3

        tde_listing.append(operand_data)

    return tde_listing

# List the worst offenders in the Sensitivity Analysis summary and their
# value, criterion, and change
def get_offenders(oss):
    offenders_listing = []
    offenses_listing = []

    # Get the Tolerance Data Viewer summary FROM A PREVIOUSLY RUN TOLERANCING!
    tolerance_data_viewer = oss.Tools.OpenToleranceDataViewer()
    tolerance_data_viewer.RunAndWaitForCompletion()
    data_summary = tolerance_data_viewer.Summary
    tolerance_data_viewer.Close()

    # Parse the summary to extract Sensitivity Analysis worst offenders
    worst_offenders = data_summary[data_summary.find("Worst offenders:"):data_summary.find("Estimated Performance Changes based upon Root-Sum-Square method")].split("\n")[2:-3]
    for offender in worst_offenders:
        offender_parse = offender.split("\t")

        offender_data = {
            "Type": offender_parse[0][:-1],
            "Int1": int(offender_parse[1]),
            "Int2": 0,
            "Int3": 0
        }

        offense_data = {
            "Change": float(offender_parse[-1]),
            "Criterion": float(offender_parse[-2]),
            "Value": float(offender_parse[-3])
        }

        # If the operand doesn't have a Param2/Int2, the summary contains an empty string
        # this is how I deal with it
        try:
            offender_data["Int2"] = int(offender_parse[2])
        except:
            pass

        # This is how I deal with a Param3/Int3
        if len(offender_parse) > 6:
            try:
                offender_data["Int3"] = int(offender_parse[3])
            except:
                pass 

        offenders_listing.append(offender_data)
        offenses_listing.append(offense_data)

    return offenders_listing, offenses_listing

# Report the worst offenders along with their corresponding TDE line number as well as
# the value, criterion, and change
def tde_operands_by_offense(tde_listing, offenders_listing, offenses_listing):
    for offender_id, offender in enumerate(offenders_listing):
        offenders_listing[offender_id]["TdeLine"] = tde_listing.index(offender)+1

    print("Sensitivity Analysis: worst offenders in order of contribution with corresponding TDE line:\n")
    print("TdeLine  Type     Int1     Int2     Int3          Value      Criterion         Change")
    print("-------------------------------------------------------------------------------------")
    for offender_id, offender in enumerate(offenders_listing):
        offense = offenses_listing[offender_id]
        print("{0:7d}: {1}    {2:5d}    {3:5d}    {4:5d}    {5:11.8f}    {6:11.8f}    {7:11.8f}".format(offender["TdeLine"],
                                                                              offender["Type"],
                                                                              offender["Int1"],
                                                                              offender["Int2"],
                                                                              offender["Int3"],
                                                                              offense["Value"],
                                                                              offense["Criterion"],
                                                                              offense["Change"]))


if __name__ == "__main__":
    # Connect the ZOSAPI with ZOSPy and get the primary optical system (oss)
    # Note that ZOSPy is a community-led initiative currently not supported by ANSYS
    # (i.e. don't ask ANSYS about ZOSPy)
    oss = connect_zosapi()

    # List the TDE operands
    tde_listing = get_tde_operands(oss)

    # List the worst offenders
    offenders_listing, offenses_listing = get_offenders(oss)

    # Report the worst offenders with the additional corresponding TDE line number
    tde_operands_by_offense(tde_listing, offenders_listing, offenses_listing)