from collections import namedtuple
from collections import OrderedDict

class seriesParams():
    drill = 1.3
    annular_ring = 0.35 # overwritten by minimum pad to pad clearance.

    # Connector voltage ratings:
    # Rated voltage (III/3) 250 V
    # Rated voltage (III/2) 320 V
    # Rated voltage (II/2) 400 V
    # Rated surge voltage (III/3) 4 kV
    # Rated surge voltage (III/2) 4 kV
    # Rated surge voltage (II/2) 4 kV
    # VDE 0110-1/4.97 4kV -> 3mm clearance
    #FFKDS_min_pad_to_pad_clearance = 3.0

    #Rated surge voltage (III/3) 6 kV
    #Rated surge voltage (III/2) 6 kV
    #Rated surge voltage (II/2) 6 kV
    #Rated voltage (III/3) 400 V
    #Rated voltage (III/2) 630 V
    #Rated voltage (II/2) 630 V
    # VDE 0110-1/4.97 6kV -> 5.5mm
    #FFKDS_min_pad_to_pad_clearance = 5.5

Params = namedtuple("Params",[
    'series_name',
    'subseries',
    'style',
    'angled',
    'num_pins',
    'pin_pitch',
    'order_info',
    'side_to_pin',
    'pin_Sx',
    'pin_Sy'
])

def generate_params(num_pins, series_name, pin_pitch, angled, order_info, side_to_pin=None, min_pad_to_pad_clearance=None):

    subseries, style = series_name.split('-')
    nominal_pin_Sx = seriesParams.drill + 2 * seriesParams.annular_ring
    nominal_pin_Sy = seriesParams.drill + 2 * 1.1
    
    if side_to_pin == None:
        if pin_pitch == 2.54:
            side_to_pin = 0.9
        elif pin_pitch == 3.81:
            side_to_pin = 0.82
        elif pin_pitch == 5.08:
            side_to_pin = 0.85
        elif pin_pitch == 7.62:
            side_to_pin = 0.8
    if min_pad_to_pad_clearance == None:
        if pin_pitch == 2.54:
            min_pad_to_pad_clearance = 0 # TODO give a value !
        elif pin_pitch == 3.81:
            min_pad_to_pad_clearance = 0 # TODO give a value !
        elif pin_pitch == 5.08:
            min_pad_to_pad_clearance = 3.0 # TODO check value !
        elif pin_pitch == 7.62:
            min_pad_to_pad_clearance = 5.5 # TODO check value !
        
    return Params(
        series_name=series_name,
        subseries=subseries,
        style=style,
        angled=angled,
        num_pins=num_pins,
        pin_pitch=pin_pitch,
        order_info=order_info,
        side_to_pin=side_to_pin,
        pin_Sx=nominal_pin_Sx if (pin_pitch - nominal_pin_Sx) >= min_pad_to_pad_clearance else (pin_pitch - min_pad_to_pad_clearance),
        pin_Sy=nominal_pin_Sy
    )

all_params = {
    ###################################################################################################################
    ## Pin Pitch 2.54mm
    ###################################################################################################################
    'FFKDS_H_01x01_2.54mm' : generate_params( 1, "FFKDS-H", 2.54, True, OrderedDict([('1791826', '6A, 160V')])),
    'FFKDS_H_01x05_2.54mm' : generate_params( 5, "FFKDS-H", 2.54, True, OrderedDict([('1935501', '6A, 160V')])),
    ###################################################################################################################
    'FFKDSA1_H_01x01_2.54mm' : generate_params( 1, "FFKDSA1-H", 2.54, True, OrderedDict([('1791868', '6A, 160V')])),
    'FFKDSA1_H_01x02_2.54mm' : generate_params( 2, "FFKDSA1-H", 2.54, True, OrderedDict([('1792511', '6A, 160V'), ('1987193', '6A, 160V, MAGAZIN'), ('1991574', '6A, 160V, RD/BU'), ('1933354', '6A, 160V, VPE 100')])),
    'FFKDSA1_H_01x03_2.54mm' : generate_params( 3, "FFKDSA1-H", 2.54, True, OrderedDict([('1789317', '6A, 160V'), ('1991325', '6A, 160V, BD:1-3'), ('1822215', '6A, 160V, GY')])),
    'FFKDSA1_H_01x04_2.54mm' : generate_params( 4, "FFKDSA1-H", 2.54, True, OrderedDict([('1789139', '6A, 160V'), ('1987203', '6A, 160V, MAGAZIN')])),
    'FFKDSA1_H_01x05_2.54mm' : generate_params( 5, "FFKDSA1-H", 2.54, True, OrderedDict([('1700198', '6A, 160V'), ('1710621', '6A, 160V, MIXCGY/YE'), ('1712231', '6A, 160V, MIXCYE/GY')])),
    'FFKDSA1_H_01x06_2.54mm' : generate_params( 6, "FFKDSA1-H", 2.54, True, OrderedDict([('1789265', '6A, 160V'), ('1701827', '6A, 160V, BD:9-14'), ('1933723', '6A, 160V, VPE 100')])),
    'FFKDSA1_H_01x07_2.54mm' : generate_params( 7, "FFKDSA1-H", 2.54, True, OrderedDict([('1700208', '6A, 160V'), ('1706797', '6A, 160V, GY')])),
    'FFKDSA1_H_01x08_2.54mm' : generate_params( 8, "FFKDSA1-H", 2.54, True, OrderedDict([('1780837', '6A, 160V'), ('1701826', '6A, 160V, BD:1-8'), ('1708974', '6A, 160V, GY')])),
    'FFKDSA1_H_01x09_2.54mm' : generate_params( 9, "FFKDSA1-H", 2.54, True, OrderedDict([('1700211', '6A, 160V'), ('1701824', '6A, 160V, BD:1-9')])),
    'FFKDSA1_H_01x10_2.54mm' : generate_params(10, "FFKDSA1-H", 2.54, True, OrderedDict([('1789333', '6A, 160V')])),
    'FFKDSA1_H_01x11_2.54mm' : generate_params(11, "FFKDSA1-H", 2.54, True, OrderedDict([('1700224', '6A, 160V')])),
    'FFKDSA1_H_01x12_2.54mm' : generate_params(12, "FFKDSA1-H", 2.54, True, OrderedDict([('1871306', '6A, 160V')])),
    'FFKDSA1_H_01x13_2.54mm' : generate_params(13, "FFKDSA1-H", 2.54, True, OrderedDict([('1700237', '6A, 160V'), ('1716376', '6A, 160V, BD:1-13')])),
    'FFKDSA1_H_01x14_2.54mm' : generate_params(14, "FFKDSA1-H", 2.54, True, OrderedDict([('1870019', '6A, 160V')])),
    'FFKDSA1_H_01x15_2.54mm' : generate_params(15, "FFKDSA1-H", 2.54, True, OrderedDict([('1871322', '6A, 160V')])),
    'FFKDSA1_H_01x16_2.54mm' : generate_params(16, "FFKDSA1-H", 2.54, True, OrderedDict([('1700240', '6A, 160V')])),    
    'FFKDSA1_H_01x18_2.54mm' : generate_params(18, "FFKDSA1-H", 2.54, True, OrderedDict([('1992081', '6A, 160V')])),
    'FFKDSA1_H_01x20_2.54mm' : generate_params(20, "FFKDSA1-H", 2.54, True, OrderedDict([('1706013', '6A, 160V'), ('1834737', '6A, 160V, GY')])),
    'FFKDSA1_H_01x22_2.54mm' : generate_params(22, "FFKDSA1-H", 2.54, True, OrderedDict([('1935721', '6A, 160V')])),
    'FFKDSA1_H_01x28_2.54mm' : generate_params(28, "FFKDSA1-H", 2.54, True, OrderedDict([('1805342', '6A, 160V')])),
    'FFKDSA1_H_01x29_2.54mm' : generate_params(29, "FFKDSA1-H", 2.54, True, OrderedDict([('1810874', '6A, 160V')])),
    'FFKDSA1_H_01x30_2.54mm' : generate_params(30, "FFKDSA1-H", 2.54, True, OrderedDict([('1789346', '6A, 160V')])),
    ###################################################################################################################
    'FFKDS_V_01x01_2.54mm' : generate_params( 1, "FFKDS-V", 2.54, False, OrderedDict([('1791813', '6A, 160V'), ('1791855', '6A, 160V'), ('1986770', '6A, 160V, BK'), ('1986783', '6A, 160V, YE')])),
    ###################################################################################################################
    'FFKDSA1_V_01x01_2.54mm' : generate_params( 1, "FFKDSA1-V", 2.54, False, OrderedDict([('1888276', '6A, 160V')])),
    'FFKDSA1_V_01x02_2.54mm' : generate_params( 2, "FFKDSA1-V", 2.54, False, OrderedDict([('1789618', '6A, 160V')])),
    'FFKDSA1_V_01x03_2.54mm' : generate_params( 3, "FFKDSA1-V", 2.54, False, OrderedDict([('1789320', '6A, 160V'), ('1753695', '6A, 160V, BU'), ('1753682', '6A, 160V, RD'), ('1789605', '6A, 160V, NZ:C291')])),
    'FFKDSA1_V_01x04_2.54mm' : generate_params( 4, "FFKDSA1-V", 2.54, False, OrderedDict([('1789595', '6A, 160V'), ('1701410', '6A, 160V, BK')])),
    'FFKDSA1_V_01x05_2.54mm' : generate_params( 5, "FFKDSA1-V", 2.54, False, OrderedDict([('1789582', '6A, 160V'), ('1891700', '6A, 160V, BD:1-5'), ('1709917', '6A, 160V, MC YE/GY'), ('1859275', '6A, 160V, YE/GY PA1,2')])),
    'FFKDSA1_V_01x06_2.54mm' : generate_params( 6, "FFKDSA1-V", 2.54, False, OrderedDict([('1789579', '6A, 160V'), ('1010561', '6A, 160V, BD:X9')])),
    'FFKDSA1_V_01x07_2.54mm' : generate_params( 7, "FFKDSA1-V", 2.54, False, OrderedDict([('1789485', '6A, 160V'), ('1766543', '6A, 160V, BD:01-07Q'), ('1766556', '6A, 160V, BD:0V Q')])),
    'FFKDSA1_V_01x08_2.54mm' : generate_params( 8, "FFKDSA1-V", 2.54, False, OrderedDict([('1789472', '6A, 160V'), ('1891713', '6A, 160V, BD:1-8')])),
    'FFKDSA1_V_01x10_2.54mm' : generate_params(10, "FFKDSA1-V", 2.54, False, OrderedDict([('1789401', '6A, 160V')])),
    'FFKDSA1_V_01x12_2.54mm' : generate_params(12, "FFKDSA1-V", 2.54, False, OrderedDict([('1780950', '6A, 160V'), ('1766585', '6A, 160V, BD:0V Q'), ('1766572', '6A, 160V, BD:24V Q'), ('1766569', '6A, 160V, BD:I1-I12 Q'), ('1888904', '6A, 160V, BDNZ:X11.1'), ('1888946', '6A, 160V, BDNZ:X11.2'), ('1888959', '6A, 160V, BDNZ:X11.3'), ('1888962', '6A, 160V, BDNZ:X11.4'), ('1888975', '6A, 160V, BDNZ:X11.5'), ('1888988', '6A, 160V, BDNZ:X11.6'), ('1889013', '6A, 160V, BDNZ:X11.8')])),
    'FFKDSA1_V_01x13_2.54mm' : generate_params(13, "FFKDSA1-V", 2.54, False, OrderedDict([('1700266', '6A, 160V'), ('1715091', '6A, 160V, BD:1-13')])),
    'FFKDSA1_V_01x14_2.54mm' : generate_params(14, "FFKDSA1-V", 2.54, False, OrderedDict([('1700279', '6A, 160V')])),
    'FFKDSA1_V_01x16_2.54mm' : generate_params(16, "FFKDSA1-V", 2.54, False, OrderedDict([('1789074', '6A, 160V'), ('1717495', '6A, 160V, MIX')])),
    'FFKDSA1_V_01x17_2.54mm' : generate_params(17, "FFKDSA1-V", 2.54, False, OrderedDict([('1889877', '6A, 160V')])),
    'FFKDSA1_V_01x18_2.54mm' : generate_params(18, "FFKDSA1-V", 2.54, False, OrderedDict([('1868063', '6A, 160V')])),
    'FFKDSA1_V_01x20_2.54mm' : generate_params(20, "FFKDSA1-V", 2.54, False, OrderedDict([('1789126', '6A, 160V'), ('1709847', '6A, 160V, BD:-'), ('1934735', '6A, 160V, BD:1-20'), ('1709845', '6A, 160V, BD:20-1 SO')])),
    'FFKDSA1_V_01x22_2.54mm' : generate_params(22, "FFKDSA1-V", 2.54, False, OrderedDict([('1889880', '6A, 160V')])),
    'FFKDSA1_V_01x23_2.54mm' : generate_params(23, "FFKDSA1-V", 2.54, False, OrderedDict([('1756265', '6A, 160V')])),
    'FFKDSA1_V_01x24_2.54mm' : generate_params(24, "FFKDSA1-V", 2.54, False, OrderedDict([('1789524', '6A, 160V')])),
    'FFKDSA1_V_01x25_2.54mm' : generate_params(25, "FFKDSA1-V", 2.54, False, OrderedDict([('1934832', '6A, 160V, BD:25-1 Q SO')])),
    'FFKDSA1_V_01x26_2.54mm' : generate_params(26, "FFKDSA1-V", 2.54, False, OrderedDict([('1704884', '6A, 160V')])),
    'FFKDSA1_V_01x32_2.54mm' : generate_params(32, "FFKDSA1-V", 2.54, False, OrderedDict([('1723382', '6A, 160V')])),
    'FFKDSA1_V_01x33_2.54mm' : generate_params(33, "FFKDSA1-V", 2.54, False, OrderedDict([('1710544', '6A, 160V')])),
    ###################################################################################################################
    ## Pin Pitch 3.81mm
    ###################################################################################################################
    'FFKDS_H_01x01_3.81mm' : generate_params( 1, "FFKDS-H", 3.81, True, OrderedDict([('1789650', '12A, 160V')])),
    ###################################################################################################################
    'FFKDSA1_H_01x01_3.81mm' : generate_params( 1, "FFKDSA1-H", 3.81, True, OrderedDict([('1789634', '12A, 160V')])),
    'FFKDSA1_H_01x02_3.81mm' : generate_params( 2, "FFKDSA1-H", 3.81, True, OrderedDict([('1869363', '12A, 160V'), ('1708964', '12A, 160V, BD:1,2'), ('1708311', '12A, 160V, BD:3,4'), ('1907351', '12A, 160V, BK'), ('1933419', '12A, 160V, BSNZ:-,K'), ('1773141', '12A, 160V, RD/BU')])),
    'FFKDSA1_H_01x03_3.81mm' : generate_params( 3, "FFKDSA1-H", 3.81, True, OrderedDict([('1888221', '12A, 160V')])),
    'FFKDSA1_H_01x04_3.81mm' : generate_params( 4, "FFKDSA1-H", 3.81, True, OrderedDict([('1700282', '12A, 160V'), ('1708312', '12A, 160V, BD:3,4,5,6'), ('1708313', '12A, 160V, BD:11-14'), ('1908020', '12A, 160V, BK')])),
    'FFKDSA1_H_01x05_3.81mm' : generate_params( 5, "FFKDSA1-H", 3.81, True, OrderedDict([('1869871', '12A, 160V'), ('1736955', '12A, 160V'), ('1700999', '12A, 160V, MIXCOL')])),
    'FFKDSA1_H_01x06_3.81mm' : generate_params( 6, "FFKDSA1-H", 3.81, True, OrderedDict([('1906682', '12A, 160V')])),
    'FFKDSA1_H_01x07_3.81mm' : generate_params( 7, "FFKDSA1-H", 3.81, True, OrderedDict([('1991707', '12A, 160V')])),
    'FFKDSA1_H_01x08_3.81mm' : generate_params( 8, "FFKDSA1-H", 3.81, True, OrderedDict([('1992159', '12A, 160V'), ('1708314', '12A, 160V, BD:3-10'), ('1701003', '12A, 160V, MIXCOL')])),
    'FFKDSA1_H_01x10_3.81mm' : generate_params(10, "FFKDSA1-H", 3.81, True, OrderedDict([('1700318', '12A, 160V')])),
    'FFKDSA1_H_01x11_3.81mm' : generate_params(11, "FFKDSA1-H", 3.81, True, OrderedDict([('1700321', '12A, 160V'), ('1933406', '12A, 160V, BSNZ:H--'), ('1933396', '12A, 160V, BSNZ:+-LE')])),
    'FFKDSA1_H_01x14_3.81mm' : generate_params(14, "FFKDSA1-H", 3.81, True, OrderedDict([('1700347', '12A, 160V')])),
    'FFKDSA1_H_01x19_3.81mm' : generate_params(19, "FFKDSA1-H", 3.81, True, OrderedDict([('1703505', '12A, 160V')])),
    'FFKDSA1_H_01x23_3.81mm' : generate_params(23, "FFKDSA1-H", 3.81, True, OrderedDict([('1706586', '12A, 160V, BD:1-41')])),
    ###################################################################################################################
    'FFKDS_V_01x01_3.81mm' : generate_params( 1, "FFKDS-V", 3.81, False, OrderedDict([('1789647', '12A, 160V')])),
    ###################################################################################################################
    'FFKDSA1_V_01x01_3.81mm' : generate_params( 1, "FFKDSA1-V", 3.81, False, OrderedDict([('1789621', '12A, 160V')])),
    'FFKDSA1_V_01x02_3.81mm' : generate_params( 2, "FFKDSA1-V", 3.81, False, OrderedDict([('1890471', '12A, 160V')])),
    'FFKDSA1_V_01x03_3.81mm' : generate_params( 3, "FFKDSA1-V", 3.81, False, OrderedDict([('1890484', '12A, 160V'), ('1714511', '12A, 160V, BD:15,16,17')])),
    'FFKDSA1_V_01x04_3.81mm' : generate_params( 4, "FFKDSA1-V", 3.81, False, OrderedDict([('1724916', '12A, 160V'), ('1806668', '12A, 160V, BD:24V-0V Q'), ('1705919', '12A, 160V, BD:SO 1')])),
    'FFKDSA1_V_01x05_3.81mm' : generate_params( 5, "FFKDSA1-V", 3.81, False, OrderedDict([('1700376', '12A, 160V')])),
    'FFKDSA1_V_01x06_3.81mm' : generate_params( 6, "FFKDSA1-V", 3.81, False, OrderedDict([('1870187', '12A, 160V'), ('1806600', '12A, 160V, BD:24V-SH Q'), ('1890057', '12A, 160V, BD:BLOCK A'), ('1710312', '12A, 160V, BD:TX--VCCQSO')])),
    'FFKDSA1_V_01x07_3.81mm' : generate_params( 7, "FFKDSA1-V", 3.81, False, OrderedDict([('1700389', '12A, 160V')])),
    'FFKDSA1_V_01x08_3.81mm' : generate_params( 8, "FFKDSA1-V", 3.81, False, OrderedDict([('1705252', '12A, 160V'), ('1928039', '12A, 160V, BD:21-28')])),
    'FFKDSA1_V_01x09_3.81mm' : generate_params( 9, "FFKDSA1-V", 3.81, False, OrderedDict([('1934528', '12A, 160V'), ('1738335', '12A, 160V, BD:11-19'), ('1761076', '12A, 160V, BD:7-13')])),
    'FFKDSA1_V_01x10_3.81mm' : generate_params(10, "FFKDSA1-V", 3.81, False, OrderedDict([('1991794', '12A, 160V'), ('1738322', '12A, 160V, BD:1-10'), ('1761063', '12A, 160V, BD:15-1')])),
    'FFKDSA1_V_01x11_3.81mm' : generate_params(11, "FFKDSA1-V", 3.81, False, OrderedDict([('1991231', '12A, 160V'), ('1708145', '12A, 160V, BD:1-11'), ('1928042', '12A, 160V, BD:29-39')])),
    'FFKDSA1_V_01x12_3.81mm' : generate_params(12, "FFKDSA1-V", 3.81, False, OrderedDict([('1706992', '12A, 160V'), ('1931437', '12A, 160V, BD:1-12')])),
    'FFKDSA1_V_01x13_3.81mm' : generate_params(13, "FFKDSA1-V", 3.81, False, OrderedDict([('1700392', '12A, 160V'), ('1931424', '12A, 160V, BD:1-13'), ('1928945', '12A, 160V, NZ:165143')])),
    'FFKDSA1_V_01x14_3.81mm' : generate_params(14, "FFKDSA1-V", 3.81, False, OrderedDict([('1928026', '12A, 160V, BD:7-20')])),
    'FFKDSA1_V_01x16_3.81mm' : generate_params(16, "FFKDSA1-V", 3.81, False, OrderedDict([('1700428', '12A, 160V'), ('1713201', '12A, 160V, GY')])),
    'FFKDSA1_V_01x17_3.81mm' : generate_params(17, "FFKDSA1-V", 3.81, False, OrderedDict([('1890015', '12A, 160V')])),
    'FFKDSA1_V_01x18_3.81mm' : generate_params(18, "FFKDSA1-V", 3.81, False, OrderedDict([('1907791', '12A, 160V, BD:NZ490')])),
    'FFKDSA1_V_01x19_3.81mm' : generate_params(19, "FFKDSA1-V", 3.81, False, OrderedDict([('1707441', '12A, 160V')])),
    'FFKDSA1_V_01x20_3.81mm' : generate_params(20, "FFKDSA1-V", 3.81, False, OrderedDict([('1109868', '12A, 160V')])),
    ###################################################################################################################
    ## Pin Pitch 5.08mm
    ###################################################################################################################
    'FFKDS_H1_01x01_5.08mm' : generate_params( 1, "FFKDS-H1", 5.08, True, OrderedDict([('1790335', '15A, 320V')])),
    ###################################################################################################################
    'FFKDSA1_H1_01x02_5.08mm' : generate_params( 2, "FFKDSA1-H1", 5.08, True, OrderedDict([('1780808', '15A, 320V'), ('1708707', '15A, 320V, BD:1,2'), ('1725478', '15A, 320V, BD:+,-')])),
    'FFKDSA1_H1_01x03_5.08mm' : generate_params( 3, "FFKDSA1-H1", 5.08, True, OrderedDict([('1907348', '15A, 320V'), ('1930098', '15A, 320V, BD:PE,L1,L2'), ('1109676', '15A, 320V, BS:-LQ SO')])),
    'FFKDSA1_H1_01x04_5.08mm' : generate_params( 4, "FFKDSA1-H1", 5.08, True, OrderedDict([('1791282', '15A, 320V'), ('1930205', '15A, 320V, BD:PE,L1-L3'), ('1995457', '15A, 320V, BD:U,V,W,PE')])),
    'FFKDSA1_H1_01x05_5.08mm' : generate_params( 5, "FFKDSA1-H1", 5.08, True, OrderedDict([('1791295', '15A, 320V'), ('1904752', '15A, 320V, BD:+BRRI-BPEQSO')])),
    'FFKDSA1_H1_01x06_5.08mm' : generate_params( 6, "FFKDSA1-H1", 5.08, True, OrderedDict([('1991383', '15A, 320V'), ('1930108', '15A, 320V, BD:R+PEUVW')])),
    'FFKDSA1_H1_01x07_5.08mm' : generate_params( 7, "FFKDSA1-H1", 5.08, True, OrderedDict([('1700431', '15A, 320V')])),
    'FFKDSA1_H1_01x08_5.08mm' : generate_params( 8, "FFKDSA1-H1", 5.08, True, OrderedDict([('1890358', '15A, 320V'), ('1109679', '15A, 320V, BS:1-8Q'), ('1109678', '15A, 320V, BS:8-1Q SO')])),
    'FFKDSA1_H1_01x09_5.08mm' : generate_params( 9, "FFKDSA1-H1", 5.08, True, OrderedDict([('1991396', '15A, 320V'), ('1704761', '15A, 320V, NZ:INTRON')])),
    'FFKDSA1_H1_01x10_5.08mm' : generate_params(10, "FFKDSA1-H1", 5.08, True, OrderedDict([('1890950', '15A, 320V'), ('1109680', '15A, 320V, BS:1-10Q')])),
    'FFKDSA1_H1_01x12_5.08mm' : generate_params(12, "FFKDSA1-H1", 5.08, True, OrderedDict([('1932708', '15A, 320V')])),
    'FFKDSA1_H1_01x14_5.08mm' : generate_params(14, "FFKDSA1-H1", 5.08, True, OrderedDict([('1700460', '15A, 320V'), ('1109681', '15A, 320V, BS:3-16Q')])),
    'FFKDSA1_H1_01x15_5.08mm' : generate_params(15, "FFKDSA1-H1", 5.08, True, OrderedDict([('1700473', '15A, 320V')])),
    'FFKDSA1_H1_01x16_5.08mm' : generate_params(16, "FFKDSA1-H1", 5.08, True, OrderedDict([('1906417', '15A, 320V'), ('1109677', '15A, 320V, BS:1-16Q')])),
    'FFKDSA1_H1_01x17_5.08mm' : generate_params(17, "FFKDSA1-H1", 5.08, True, OrderedDict([('1081777', '15A, 320V')])),
    'FFKDSA1_H1_01x23_5.08mm' : generate_params(23, "FFKDSA1-H1", 5.08, True, OrderedDict([('1111019', '15A, 320V')])),
    ###################################################################################################################
    'FFKDS_H2_01x01_5.08mm' : generate_params( 1, "FFKDS-H2", 5.08, True, OrderedDict([('1790461', '15A, 320V')])),
    ###################################################################################################################
    'FFKDSA1_H2_01x02_5.08mm' : generate_params( 2, "FFKDSA1-H2", 5.08, True, OrderedDict([('1700486', '15A, 320V')])),
    'FFKDSA1_H2_01x03_5.08mm' : generate_params( 3, "FFKDSA1-H2", 5.08, True, OrderedDict([('1791392', '15A, 320V, HAUCH')])),
    'FFKDSA1_H2_01x04_5.08mm' : generate_params( 4, "FFKDSA1-H2", 5.08, True, OrderedDict([('1700509', '15A, 320V')])),
    'FFKDSA1_H2_01x05_5.08mm' : generate_params( 5, "FFKDSA1-H2", 5.08, True, OrderedDict([('1700512', '15A, 320V')])),
    'FFKDSA1_H2_01x06_5.08mm' : generate_params( 6, "FFKDSA1-H2", 5.08, True, OrderedDict([('1700499', '15A, 320V')])),
    'FFKDSA1_H2_01x07_5.08mm' : generate_params( 7, "FFKDSA1-H2", 5.08, True, OrderedDict([('1700538', '15A, 320V')])),
    'FFKDSA1_H2_01x08_5.08mm' : generate_params( 8, "FFKDSA1-H2", 5.08, True, OrderedDict([('1891823', '15A, 320V')])),
    'FFKDSA1_H2_01x10_5.08mm' : generate_params(10, "FFKDSA1-H2", 5.08, True, OrderedDict([('1700554', '15A, 320V')])),
    ###################################################################################################################
    'FFKDS_V1_01x01_5.08mm' : generate_params( 1, "FFKDS-V1", 5.08, False, OrderedDict([('1790319', '15A, 400V'), ('1928987', '15A, 400V, BK'), ('1705399', '15A, 400V, BU'), ('1705396', '15A, 400V, GY'), ('1705401', '15A, 400V, OG'), ('1716599', '15A, 400V, RD')])),
    ###################################################################################################################
    'FFKDSA_V1_01x02_5.08mm' : generate_params( 2, "FFKDSA-V1", 5.08, False, OrderedDict([('1790526', '15A, 400V')])),
    'FFKDSA_V1_01x03_5.08mm' : generate_params( 3, "FFKDSA-V1", 5.08, False, OrderedDict([('1790937', '15A, 400V')])),
    'FFKDSA_V1_01x04_5.08mm' : generate_params( 4, "FFKDSA-V1", 5.08, False, OrderedDict([('1790539', '15A, 400V')])),
    'FFKDSA_V1_01x05_5.08mm' : generate_params( 5, "FFKDSA-V1", 5.08, False, OrderedDict([('1791596', '15A, 400V')])),
    'FFKDSA_V1_01x06_5.08mm' : generate_params( 6, "FFKDSA-V1", 5.08, False, OrderedDict([('1791732', '15A, 400V')])),
    'FFKDSA_V1_01x07_5.08mm' : generate_params( 7, "FFKDSA-V1", 5.08, False, OrderedDict([('1791774', '15A, 400V')])),
    'FFKDSA_V1_01x09_5.08mm' : generate_params( 9, "FFKDSA-V1", 5.08, False, OrderedDict([('1933794', '15A, 400V, BD:1-9')])),
    'FFKDSA_V1_01x10_5.08mm' : generate_params(10, "FFKDSA-V1", 5.08, False, OrderedDict([('1888056', '15A, 400V, BD:30-39'), ('1888069', '15A, 400V, BD:40-49')])),
    'FFKDSA_V1_01x14_5.08mm' : generate_params(14, "FFKDSA-V1", 5.08, False, OrderedDict([('1780811', '15A, 400V')])),
    'FFKDSA_V1_01x29_5.08mm' : generate_params(29, "FFKDSA-V1", 5.08, False, OrderedDict([('1888043', '15A, 400V, BD:1-29')])),
    ###################################################################################################################
    'FFKDSAL_V1_01x02_5.08mm' : generate_params( 2, "FFKDSAL-V1", 5.08, False, OrderedDict([('1710760', '15A, 400V, BN/BU'), ('1710758', '15A, 400V, RD/WH')])),
    'FFKDSAL_V1_01x03_5.08mm' : generate_params( 3, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789922', '15A, 400V')])),
    'FFKDSAL_V1_01x04_5.08mm' : generate_params( 4, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789919', '15A, 400V')])),
    'FFKDSAL_V1_01x05_5.08mm' : generate_params( 5, "FFKDSAL-V1", 5.08, False, OrderedDict([('1036880', '15A, 400V')])),
    'FFKDSAL_V1_01x06_5.08mm' : generate_params( 6, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789896', '15A, 400V'), ('1888917', '15A, 400V, BD:1-6'), ('1889039', '15A, 400V, BD:13-18'), ('1889042', '15A, 400V, BD:19-24'), ('1889071', '15A, 400V, BD:37-42'), ('1889084', '15A, 400V, BD:43-48')])),
    'FFKDSAL_V1_01x07_5.08mm' : generate_params( 7, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789883', '15A, 400V'), ('1888454', '15A, 400V, BD:1-6,6A')])),
    'FFKDSAL_V1_01x08_5.08mm' : generate_params( 8, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789870', '15A, 400V')])),
    'FFKDSAL_V1_01x09_5.08mm' : generate_params( 9, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789867', '15A, 400V')])),
    'FFKDSAL_V1_01x12_5.08mm' : generate_params(12, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789838', '15A, 400V')])),
    'FFKDSAL_V1_01x14_5.08mm' : generate_params(14, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789375', '15A, 400V'), ('1888467', '15A, 400V, BD:7-20'), ('1888470', '15A, 400V, BD:21-34'), ('1888483', '15A, 400V, BD:35-48'), ('1888496', '15A, 400V, BD:49-62'), ('1888522', '15A, 400V, BD:91-104')])),
    'FFKDSAL_V1_01x16_5.08mm' : generate_params(16, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789825', '15A, 400V')])),
    'FFKDSAL_V1_01x18_5.08mm' : generate_params(18, "FFKDSAL-V1", 5.08, False, OrderedDict([('1789812', '15A, 400V')])),
    ###################################################################################################################
    'FFKDSA1_V_01x01_5.08mm' : generate_params( 1, "FFKDSA1-V", 5.08, False, OrderedDict([('1789812', '15A, 400V')])),
    ###################################################################################################################
    'FFKDSA1_V1_01x02_5.08mm' : generate_params( 2, "FFKDSA1-V1", 5.08, False, OrderedDict([('1789210', '15A, 400V'), ('1711273', '15A, 400V, BD:-24VE'), ('1712462', '15A, 400V, BD:-24VI'), ('1724190', '15A, 400V, BD:1-2'), ('1701246', '15A, 400V, BD:R1,R2'), ('1005454', '15A, 400V, BD:X3'), ('1005458', '15A, 400V, BD:X7'), ('1210435', '15A, 400V, BK'), ('1710759', '15A, 400V, BK/GY'), ('1702201', '15A, 400V, BKBDWH1,2Q'), ('1715994', '15A, 400V, BU'), ('1708067', '15A, 400V, MC BK/RD'), ('1706918', '15A, 400V, NZ:C446-2-6'), ('1706921', '15A, 400V, NZ:C447-2-6'), ('1715995', '15A, 400V, RD'), ('1713902', '15A, 400V, SVT/GY')])),
    'FFKDSA1_V1_01x03_5.08mm' : generate_params( 3, "FFKDSA1-V1", 5.08, False, OrderedDict([('1704376', '15A, 400V'), ('1709783', '15A, 400V, BD:1-3'), ('1888030', '15A, 400V, BD:10-12'), ('1711266', '15A, 400V, BD:I-C1'), ('1711265', '15A, 400V, BD:I-C2'), ('1711267', '15A, 400V, BD:I-C3'), ('1711269', '15A, 400V, BD:I-C4'), ('1701245', '15A, 400V, BD:L2-PE SO'), ('1742172', '15A, 400V, BD:NZ451'), ('1742185', '15A, 400V, BD:NZ453'), ('1711270', '15A, 400V, BD:O-C5'), ('1711272', '15A, 400V, BD:O-C6'), ('1706625', '15A, 400V, BD:T+-0V'), ('1701244', '15A, 400V, BD:W-U SO'), ('1005456', '15A, 400V, BD:X2'), ('1109682', '15A, 400V, BS:1-3Q SO')])),
    'FFKDSA1_V1_01x04_5.08mm' : generate_params( 4, "FFKDSA1-V1", 5.08, False, OrderedDict([('1789113', '15A, 400V'), ('1702506', '15A, 400V, BD:1-4Q'), ('1741335', '15A, 400V, BD:NZ448'), ('1005459', '15A, 400V, BD:X4'), ('1741348', '15A, 400V, BD:NZ449'), ('1741351', '15A, 400V, BD:NZ450'), ('1709471', '15A, 400V, GN/BK'), ('1708069', '15A, 400V, MC GY/BK'), ('1716468', '15A, 400V, MCSVT/GY')])),
    'FFKDSA1_V1_01x05_5.08mm' : generate_params( 5, "FFKDSA1-V1", 5.08, False, OrderedDict([('1751565', '15A, 400V'), ('1705854', '15A, 400V, NZ:C437'), ('1706879', '15A, 400V, NZ:C442-2-6'), ('1706882', '15A, 400V, NZ:C443-2-6')])),
    'FFKDSA1_V1_01x06_5.08mm' : generate_params( 6, "FFKDSA1-V1", 5.08, False, OrderedDict([('1780662', '15A, 400V'), ('1928013', '15A, 400V, BD:1-6'), ('1161843', '15A, 400V, BD:1-6Q'), ('1933781', '15A, 400V, BD:43-52'), ('1704635', '15A, 400V, BS:6-1 SO'), ('1109687', '15A, 400V, BS:15-10SO'), ('1705867', '15A, 400V, NZ:C438'), ('1705870', '15A, 400V, NZ:C439')])),
    'FFKDSA1_V1_01x07_5.08mm' : generate_params( 7, "FFKDSA1-V1", 5.08, False, OrderedDict([('1791981', '15A, 400V'), ('1888014', '15A, 400V, BD:1-7'), ('1907788', '15A, 400V, BD:NZ490'), ('1712501', '15A, 400V, BS:7-1 SO')])),
    'FFKDSA1_V1_01x08_5.08mm' : generate_params( 8, "FFKDSA1-V1", 5.08, False, OrderedDict([('1791790', '15A, 400V'), ('1702984', '15A, 400V, BD:1-8Q'), ('1704606', '15A, 400V, BD:8-1 SO'), ('1711037', '15A, 400V, BD:9-16Q'), ('1711038', '15A, 400V, BD:17-24Q'), ('1706531', '15A, 400V, BD:T+-0V Q'), ('1704651', '15A, 400V, BS:8- SO'), ('1702202', '15A, 400V, GYBKBDWHQ'), ('1715988', '15A, 400V, MIX GN-BK'), ('1706895', '15A, 400V, NZ:C444-2-6'), ('1706905', '15A, 400V, NZ:C445-2-6'), ('1709470', '15A, 400V, SVT/GY')])),
    'FFKDSA1_V1_01x09_5.08mm' : generate_params( 9, "FFKDSA1-V1", 5.08, False, OrderedDict([('1751578', '15A, 400V'), ('1741186', '15A, 400V, BD:1-9Q'), ('1991312', '15A, 400V, BD:1-9SO'), ('1109684', '15A, 400V, BS:9-1SO')])),
    'FFKDSA1_V1_01x10_5.08mm' : generate_params(10, "FFKDSA1-V1", 5.08, False, OrderedDict([('1751581', '15A, 400V'), ('1741173', '15A, 400V, BD:1-10Q'), ('1706530', '15A, 400V, BD10-SERD Q'), ('1715986', '15A, 400V, BK'), ('1702203', '15A, 400V, BKGYBDWHQSO'), ('1704622', '15A, 400V, BS:M- SO'), ('1704619', '15A, 400V, BS:P+ SO'), ('1715997', '15A, 400V, MC BU-GN'), ('1715987', '15A, 400V, RD')])),
    'FFKDSA1_V1_01x11_5.08mm' : generate_params(11, "FFKDSA1-V1", 5.08, False, OrderedDict([('1700622', '15A, 400V'), ('1706898', '15A, 400V, BD:1-11'), ('1780918', '15A, 400V, BDNZ0872819'), ('1704648', '15A, 400V, BS:8-P SO')])),
    'FFKDSA1_V1_01x12_5.08mm' : generate_params(12, "FFKDSA1-V1", 5.08, False, OrderedDict([('1751594', '15A, 400V'), ('1706620', '15A, 400V, NZ:C421-2-6')])),
    'FFKDSA1_V1_01x13_5.08mm' : generate_params(13, "FFKDSA1-V1", 5.08, False, OrderedDict([('1700635', '15A, 400V'), ('1994076', '15A, 400V, NZ:RDGYGN')])),
    'FFKDSA1_V1_01x14_5.08mm' : generate_params(14, "FFKDSA1-V1", 5.08, False, OrderedDict([('1751604', '15A, 400V'), ('1701027', '15A, 400V, BD:1-14')])),
    'FFKDSA1_V1_01x15_5.08mm' : generate_params(15, "FFKDSA1-V1", 5.08, False, OrderedDict([('1700648', '15A, 400V')])),
    'FFKDSA1_V1_01x16_5.08mm' : generate_params(16, "FFKDSA1-V1", 5.08, False, OrderedDict([('1868623', '15A, 400V'), ('1705262', '15A, 400V, BD:1-16'), ('1109683', '15A, 400V, BS:Q-BSO')])),
    'FFKDSA1_V1_01x17_5.08mm' : generate_params(17, "FFKDSA1-V1", 5.08, False, OrderedDict([('1731167', '15A, 400V')])),
    'FFKDSA1_V1_01x18_5.08mm' : generate_params(18, "FFKDSA1-V1", 5.08, False, OrderedDict([('1751620', '15A, 400V')])),
    'FFKDSA1_V1_01x20_5.08mm' : generate_params(20, "FFKDSA1-V1", 5.08, False, OrderedDict([('1729551', '15A, 400V')])),
    'FFKDSA1_V1_01x22_5.08mm' : generate_params(22, "FFKDSA1-V1", 5.08, False, OrderedDict([('1715990', '15A, 400V'), ('1715991', '15A, 400V, BU')])),
    'FFKDSA1_V1_01x24_5.08mm' : generate_params(24, "FFKDSA1-V1", 5.08, False, OrderedDict([('1731718', '15A, 400V')])),
    'FFKDSA1_V1_01x25_5.08mm' : generate_params(25, "FFKDSA1-V1", 5.08, False, OrderedDict([('1715993', '15A, 400V')])),
    'FFKDSA1_V1_01x26_5.08mm' : generate_params(26, "FFKDSA1-V1", 5.08, False, OrderedDict([('1768363', '15A, 400V')])),
    'FFKDSA1_V1_01x38_5.08mm' : generate_params(38, "FFKDSA1-V1", 5.08, False, OrderedDict([('1716065', '15A, 400V, BU')])),
    'FFKDSA1_V1_01x48_5.08mm' : generate_params(48, "FFKDSA1-V1", 5.08, False, OrderedDict([('1716066', '15A, 400V')])),
    ###################################################################################################################
    'FFKDS_V2_01x01_5.08mm' : generate_params( 1, "FFKDS-V2", 5.08, False, OrderedDict([('1790348', '15A, 320V'), ('1847494', '15A, 320V, BK')])),
    ###################################################################################################################
    'FFKDSA1_V2_01x02_5.08mm' : generate_params( 2, "FFKDSA1-V2", 5.08, False, OrderedDict([('1986592', '15A, 320V'), ('1727362', '15A, 320V, BK'), ('1741995', '15A, 320V, GY LCBK BD')])),
    'FFKDSA1_V2_01x03_5.08mm' : generate_params( 3, "FFKDSA1-V2", 5.08, False, OrderedDict([('1890167', '15A, 320V'), ('1722707', '15A, 320V, BD:1-3'), ('1891687', '15A, 320V, BD:1-3'), ('1705414', '15A, 320V, NZ:Z18-C396')])),
    'FFKDSA1_V2_01x04_5.08mm' : generate_params( 4, "FFKDSA1-V2", 5.08, False, OrderedDict([('1700651', '15A, 320V'), ('1707784', '15A, 320V, BD:1-4'), ('1722668', '15A, 320V, BD:1-4'), ('1704783', '15A, 320V, BD:NZ789')])),
    'FFKDSA1_V2_01x05_5.08mm' : generate_params( 5, "FFKDSA1-V2", 5.08, False, OrderedDict([('1722697', '15A, 320V, BD:1-5'), ('1891690', '15A, 320V, BD:1-5'), ('1722697', '15A, 320V, GY BD:1-5')])),
    'FFKDSA1_V2_01x06_5.08mm' : generate_params( 6, "FFKDSA1-V2", 5.08, False, OrderedDict([('1730913', '15A, 320V, VWA.BS:C393')])),
    'FFKDSA1_V2_01x07_5.08mm' : generate_params( 7, "FFKDSA1-V2", 5.08, False, OrderedDict([('1890154', '15A, 320V')])),
    'FFKDSA1_V2_01x08_5.08mm' : generate_params( 8, "FFKDSA1-V2", 5.08, False, OrderedDict([('1700677', '15A, 320V'), ('1904817', '15A, 320V, BD:1-8')])),
    'FFKDSA1_V2_01x16_5.08mm' : generate_params(16, "FFKDSA1-V2", 5.08, False, OrderedDict([('1930771', '15A, 320V'), ('1030241', '15A, 320V, BD:1-16'), ('1030241', '15A, 320V, BD:17-32'), ('1030242', '15A, 320V, BD:17-32'), ('1030243', '15A, 320V, BD:33-48')])),
    ###################################################################################################################
    'FFKDSA1L_V2_01x06_5.08mm' : generate_params( 6, "FFKDSA1L-V2", 5.08, False, OrderedDict([('1730900', '15A, 320V, VWA.C394')])),
    ###################################################################################################################
    ## Pin Pitch 7.62mm
    ###################################################################################################################
    'FFKDSA_H1_01x01_7.62mm' : generate_params( 1, "FFKDSA-H1", 7.62, True, OrderedDict([('1790351', '17.5A, 630V'), ('1929261', '17.5A, 630V, BK')])),
    'FFKDSA_H1_01x03_7.62mm' : generate_params( 3, "FFKDSA-H1", 7.62, True, OrderedDict([('1934007', '17.5A, 630V')])),
    ###################################################################################################################
    'FFKDSA1_H1_01x01_7.62mm' : generate_params( 1, "FFKDSA1-H1", 7.62, True, OrderedDict([('1790513', '17.5A, 630V'), ('1928990', '17.5A, 630V, BK')])),
    'FFKDSA1_H1_01x02_7.62mm' : generate_params( 2, "FFKDSA1-H1", 7.62, True, OrderedDict([('1700758', '17.5A, 630V')])),
    'FFKDSA1_H1_01x03_7.62mm' : generate_params( 3, "FFKDSA1-H1", 7.62, True, OrderedDict([('1700761', '17.5A, 630V'), ('1932847', '17.5A, 630V, BD:L1,L2,L3'), ('1845894', '17.5A, 630V, GY')])),
    'FFKDSA1_H1_01x04_7.62mm' : generate_params( 4, "FFKDSA1-H1", 7.62, True, OrderedDict([('1929973', '17.5A, 630V')])),
    'FFKDSA1_H1_01x05_7.62mm' : generate_params( 5, "FFKDSA1-H1", 7.62, True, OrderedDict([('1929740', '17.5A, 630V'), ('1932850', '17.5A, 630V, BD:R,+,UVW')])),
    'FFKDSA1_H1_01x06_7.62mm' : generate_params( 6, "FFKDSA1-H1", 7.62, True, OrderedDict([('1929753', '17.5A, 630V'), ('1846961', '17.5A, 630V, MIX GN-BK')])),
    'FFKDSA1_H1_01x07_7.62mm' : generate_params( 7, "FFKDSA1-H1", 7.62, True, OrderedDict([('1929766', '17.5A, 630V')])),
    'FFKDSA1_H1_01x08_7.62mm' : generate_params( 8, "FFKDSA1-H1", 7.62, True, OrderedDict([('1846974', '17.5A, 630V, MIX GN-BK')])),
    ###################################################################################################################
    'FFKDSA_H2_01x01_7.62mm' : generate_params( 1, "FFKDSA-H2", 7.62, True, OrderedDict([('1790458', '17.5A, 630V')])),
    ###################################################################################################################
    'FFKDSA1_H2_01x01_7.62mm' : generate_params( 1, "FFKDSA1-H2", 7.62, True, OrderedDict([('1790500', '17.5A, 630V')])),
    'FFKDSA1_H2_01x02_7.62mm' : generate_params( 2, "FFKDSA1-H2", 7.62, True, OrderedDict([('1700787', '17.5A, 630V')])),
    'FFKDSA1_H2_01x03_7.62mm' : generate_params( 3, "FFKDSA1-H2", 7.62, True, OrderedDict([('1700790', '17.5A, 630V')])),
    'FFKDSA1_H2_01x04_7.62mm' : generate_params( 4, "FFKDSA1-H2", 7.62, True, OrderedDict([('1700800', '17.5A, 630V')])),
    ###################################################################################################################
    'FFKDSA_V1_01x01_7.62mm' : generate_params( 1, "FFKDSA-V1", 7.62, False, OrderedDict([('1790364', '17.5A, 630V'), ('1705137', '17.5A, 630V, VPE500')])),
    ###################################################################################################################
    'FFKDSA1_V1_01x01_7.62mm' : generate_params( 1, "FFKDSA1-V1", 7.62, False, OrderedDict([('1790490', '17.5A, 630V'), ('1800170', '17.5A, 630V, BK'), ('1705400', '17.5A, 630V, BU'), ('1705398', '17.5A, 630V, GY'), ('1705402', '17.5A, 630V, OG'), ('1716598', '17.5A, 630V, RD')])),
    'FFKDSA1_V1_01x02_7.62mm' : generate_params( 2, "FFKDSA1-V1", 7.62, False, OrderedDict([('1891399', '17.5A, 630V')])),
    'FFKDSA1_V1_01x03_7.62mm' : generate_params( 3, "FFKDSA1-V1", 7.62, False, OrderedDict([('1780549', '17.5A, 630V'), ('1706917', '17.5A, 630V, BD:C,NO,NC'), ('1706916', '17.5A, 630V, BD:N-ERDE'), ('1714072', '17.5A, 630V, MIXC WH/RD'), ('1715001', '17.5A, 630V, RD')])),
    'FFKDSA1_V1_01x04_7.62mm' : generate_params( 4, "FFKDSA1-V1", 7.62, False, OrderedDict([('1700855', '17.5A, 630V'), ('1711785', '17.5A, 630V, BD:5-8 Q')])),
    'FFKDSA1_V1_01x05_7.62mm' : generate_params( 5, "FFKDSA1-V1", 7.62, False, OrderedDict([('1868115', '17.5A, 630V')])),
    'FFKDSA1_V1_01x06_7.62mm' : generate_params( 6, "FFKDSA1-V1", 7.62, False, OrderedDict([('1700868', '17.5A, 630V')])),
    'FFKDSA1_V1_01x07_7.62mm' : generate_params( 7, "FFKDSA1-V1", 7.62, False, OrderedDict([('1700871', '17.5A, 630V')])),
    'FFKDSA1_V1_01x08_7.62mm' : generate_params( 8, "FFKDSA1-V1", 7.62, False, OrderedDict([('1700884', '17.5A, 630V')])),
    'FFKDSA1_V1_01x14_7.62mm' : generate_params(14, "FFKDSA1-V1", 7.62, False, OrderedDict([('1712051', '17.5A, 630V')])),
    ###################################################################################################################
    'FFKDSAL_V1_01x01_7.62mm' : generate_params( 1, "FFKDSAL-V1", 7.62, False, OrderedDict([('1791758', '17.5A, 630V')])),
    ###################################################################################################################
    'FFKDSA_V2_01x01_7.62mm' : generate_params( 1, "FFKDSA-V2", 7.62, False, OrderedDict([('1790377', '17.5A, 630V')])),
    ###################################################################################################################
    'FFKDSA1_V2_01x01_7.62mm' : generate_params( 1, "FFKDSA1-V2", 7.62, False, OrderedDict([('1790487', '17.5A, 630V'), ('1800172', '17.5A, 630V, BK')])),
    'FFKDSA1_V2_01x02_7.62mm' : generate_params( 2, "FFKDSA1-V2", 7.62, False, OrderedDict([('1700897', '17.5A, 630V')])),
    'FFKDSA1_V2_01x03_7.62mm' : generate_params( 3, "FFKDSA1-V2", 7.62, False, OrderedDict([('1700907', '17.5A, 630V')])),
    'FFKDSA1_V2_01x04_7.62mm' : generate_params( 4, "FFKDSA1-V2", 7.62, False, OrderedDict([('1700432', '17.5A, 630V, BD:T1-SERD'), ('1706532', '17.5A, 630V, BD-SERD QSO')])),
    'FFKDSA1_V2_01x08_7.62mm' : generate_params( 8, "FFKDSA1-V2", 7.62, False, OrderedDict([('1700952', '17.5A, 630V')])),
}

def dimensions(params):

    if params.pin_pitch == 2.54:
        lenght = params.num_pins*params.pin_pitch + 2.5
        if params.angled:
            width = 13.6
            upper_to_pin = -3.02
        else:
            if params.style == "V" or params.style == "V1":
                width = 12.6
                upper_to_pin = -4.71
        left_to_pin = -0.9
    elif params.pin_pitch == 3.81:
        lenght = params.num_pins*params.pin_pitch + 2.5
        if params.angled:
            width = 13.65
            upper_to_pin = -1.83
        else:
            if params.style == "V" or params.style == "V1":
                width = 12.7
                upper_to_pin = -3.68
        left_to_pin = -0.82
    elif params.pin_pitch == 5.08:
        lenght = params.num_pins*params.pin_pitch + 2.54
        if params.angled:
            width = 13.65
            upper_to_pin = -1.93
        else:
            if params.style == "V" or params.style == "V1":
                width = 12.7
                upper_to_pin = -3.58
            elif params.style == "V2":
                width = 10
                upper_to_pin = -0.95
        left_to_pin = -0.85 if params.angled else -3.5
    elif params.pin_pitch == 7.62:
        lenght = params.num_pins*params.pin_pitch
        if params.angled:
            width = 13.6
            upper_to_pin = -1.97
        else:
            if params.style == "V" or params.style == "V1":
                width = 12.7
                upper_to_pin = -3.58
            elif params.style == "V2":
                width = 10
                upper_to_pin = -0.95
        left_to_pin = -0.8
    
    inner_len = params.num_pins*params.pin_pitch-1.6 + (0 if params.pin_pitch>5.08 else 2)
    
    return lenght, width, upper_to_pin, left_to_pin, inner_len

def generate_description(params, mpn):
    d = "Generic Phoenix Contact connector footprint for: " + mpn + "; number of pins: " + ("%02d" %params.num_pins) + "; pin pitch: " + (('%.2f' % params.pin_pitch)) + "mm" + ('; Angled' if params.angled else '; Vertical')
    for order_num, info in params.order_info.items():
        d += " || order number: " + order_num + " " + info
    return d
