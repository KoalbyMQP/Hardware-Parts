import sigrokdecode as srd

#from typing import List, Optional


class Sample():
    def __init__(self,data, start, end):
        self.data = data
        self.start = start
        self.end = end

class Memory():
    def __init__(self,Type,Bytes,ROM,RAM,Default,Max,Min,Perm):
        self.Type = Type
        self.Bytes = Bytes
        self.ROM = ROM
        self.RAM = RAM
        self.Default = Default
        self.Max = Max
        self.Min = Min
        self.Perm = Perm


class Decoder(srd.Decoder):
    api_version = 3
    id = 'herkulex'
    name = 'HerkuleX'
    longname = 'HerkuleX'
    desc = 'HerkuleX Servo Protocol Decoder'
    license = 'gplv2+'
    inputs = ['uart']      # stack on top of UART
    outputs = []
    tags = ['Remote Control', 'Embedded/industrial', 'Debug/trace']

    MIN_SAMPLERATE = 2000000

    DataIndex = 0
    FrameIndex = 0

    # Herkulex packet data
    Header = 0xFF

    #Record----
    RecordData = []
    RecordLength = 0
    RecordIndex = 0

    commands = {
        0x01: 'EEP_WRITE',
        0x02: 'EEP_READ',
        0x03: 'RAM_WRITE',
        0x04: 'RAM_READ',
        0x05: 'I_JOG',
        0x06: 'S_JOG',
        0x07: 'STAT',
        0x08: 'ROLLBACK',
        0x09: 'REBOOT'
    }

    RamData = {
        0: 'ID',
        1: 'ACK Policy',
        2: 'Alarm LED Policy',
        3: 'Torque Policy',
        4: 'Reserved',
        5: 'Max Temperature',
        6: 'Min Voltage',
        7: 'Max Voltage',
        8: 'Acceleration Ratio',
        9: 'Max Acceleration Time',
        10: 'Dead Zone',
        11: 'Saturator Offset',
        12: 'Saturator Slope',
        14: 'PWM Offset',
        15: 'Min PWM',
        16: 'Max PWM',
        18: 'Overload PWM Threshold',
        20: 'Min Position',
        22: 'Max Position',
        24: 'Position Kp',
        26: 'Position Kd',
        28: 'Position Ki',
        30: 'Position Feedforward Gain 1',
        32: 'Position Feedforward Gain 2',
        38: 'LED Blink Period',
        39: 'ADC Fault Check Period',
        40: 'Packet Garbage Check Period',
        41: 'Stop Detection Period',
        42: 'Overload Detection Period',
        43: 'Stop Threshold',
        44: 'Inposition Margin',
        46: 'Calibration Difference Byte 1',
        47: 'Calibration Difference Byte 2',
        48: 'Status Error',
        49: 'Status Detail',
        52: 'Torque Control',
        53: 'LED Control',
        54: 'Voltage',
        55: 'Temperature',
        56: 'Current Control Mode',
        57: 'Tick',
        58: 'Calibrated Position',
        60: 'Absolute Position',
        62: 'Differential Position',
        64: 'PWM',
        68: 'Absolute Goal Position',
        72: 'Desired Velocity',

    }

    # Annotation definitions
    annotations = (
        ('herkulex', 'HerkuleX data'),  # index 0
        ('invalid', 'Invalid/Error packet'),  # index 1
    )

    annotation_rows = (
        ('data_row', 'HerkuleX', (0,)),  # row for normal packets
        ('error_row', 'Errors', (1,)),  # row for invalid/error packets
    )

    def __init__(self):
        self.reset()

    def reset(self):

        self.RecordData = []
        self.RecordLength = 0
        self.RecordIndex = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def Record(self, number, ss, es):
        # --- Header area (expect two 0xFF bytes) ---
        if self.RecordIndex < 2:
            if number == self.Header:
                self.RecordData.append(Sample(number, ss, es))
                self.RecordIndex += 1
            else:
                # reset and *re-check* current byte as potential first header byte
                self.reset()
                if number == self.Header:
                    self.RecordData.append(Sample(number, ss, es))
                    self.RecordIndex = 1
            return

        # --- Length byte (index == 2) ---
        if self.RecordIndex == 2:
            self.RecordData.append(Sample(number, ss, es))
            self.RecordIndex += 1

            # Basic validation: length must be at least header+length fields (e.g. 3 or more)
            # and must not be ridiculously large (adjust max_len to your protocol)
            max_len = 256
            if number < 3 or number > max_len:
                # invalid length -> drop and resync
                self.reset()
                return

            self.RecordLength = number  # total length (including header)
            # If length equals number of bytes we already have, decode immediately
            if len(self.RecordData) == self.RecordLength:
                self.decode_packet()
            return

        # --- Data bytes (including checksums and payload) ---
        # Append the byte
        self.RecordData.append(Sample(number, ss, es))
        self.RecordIndex += 1

        # If we've reached the expected total length, decode now (do it in the same call)
        if len(self.RecordData) == self.RecordLength:
            self.decode_packet()
        return

    def decode_packet(self):

        for i in range(1,self.RecordLength):
            if i==1: #header
                start = self.RecordData[0].start
                end =  self.RecordData[i].end

                long_text = "Header %d" % len(self.RecordData)
                mid_text = "Head"
                short_text = "H"
                self.put(start, end, self.out_ann, [0, [long_text,mid_text,short_text]])

            if i==2:
                start = self.RecordData[i].start
                end = self.RecordData[i].end
                number = self.RecordData[i].data

                long_text = "Length %d" % number
                mid_text = "Len %d" % number
                short_text = "%d" % number
                self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])

            if i==3:
                start = self.RecordData[i].start
                end = self.RecordData[i].end
                number = self.RecordData[i].data

                if (number == 254):
                    long_text = "All Servos"
                    mid_text = "All"
                    short_text = "All"
                else:
                    long_text = "Servo ID %d" % number
                    mid_text = "ID %d" % number
                    short_text = "%d" % number
                self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])

            if i==4:
                start = self.RecordData[i].start
                end = self.RecordData[i].end
                number = self.RecordData[i].data

                command_name = self.commands.get(number, "UNKNOWN")
                long_text = command_name
                mid_text = "%d" % number
                short_text = "%d" % number
                self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])



                if command_name == "UNKNOWN":
                    long_text = command_name
                    mid_text = command_name
                    short_text = command_name
                else:
                    long_text = "Valid"
                    mid_text = "Valid"
                    short_text = "Valid"

                self.put(start, end, self.out_ann, [1, [long_text, mid_text, short_text]])


            if i==5:
                start = self.RecordData[i].start
                end = self.RecordData[i].end
                number = self.RecordData[i].data

                long_text = "Checksum1 %d" % number
                mid_text = "CS1 %d" % number
                short_text = "%d" % number

                self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])

                if (self.validCheckSum1() == number):
                    long_text = "Valid"
                    mid_text = "Valid"
                    short_text = "Valid"
                else:
                    long_text = "Invalid"
                    mid_text = "Invalid"
                    short_text = "Invalid"

                self.put(start, end, self.out_ann, [1, [long_text, mid_text, short_text]])

            if i == 6:
                start = self.RecordData[i].start
                end = self.RecordData[i].end
                number = self.RecordData[i].data

                long_text = "Checksum2 %d" % number
                mid_text = "CS2 %d" % number
                short_text = "%d" % number

                self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])


                if (self.validCheckSum2() == number):
                    long_text = "Valid"
                    mid_text = "Valid"
                    short_text = "Valid"
                else:
                    long_text = "Invalid"
                    mid_text = "Invalid"
                    short_text = "Invalid"

                self.put(start, end, self.out_ann, [1, [long_text, mid_text, short_text]])

            if i > 6:



                # if command_name == "EEP_WRITE":
                #     self.ROM_Write()
                #     break
                # elif command_name == "EEP_READ":
                #     self.ROM_Read()
                #     break
                # elif command_name == "RAM_WRITE":
                #     self.RAM_Write()
                #     break
                # elif command_name == "RAM_READ":
                #     self.RAM_Read()
                #     break
                # elif command_name == "I_JOG":
                #     self.I_JOG()
                #     break
                # elif command_name == "S_JOG":
                #     self.S_JOG()
                #     break
                # elif command_name == "STAT":
                #     self.STAT()
                #     break
                # elif command_name == "ROLLBACK":
                #     self.ROLLBACK()
                #     break
                # elif command_name == "REBOOT":
                #     self.REBOOT()
                #     break
                # else:
                long_text = "Packet data %d  " % number
                mid_text = "Pd %d" % number
                short_text = "%d" % number

                self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])


        self.reset()


    def validCheckSum1(self):
        return self.validCheckSumSub()&0xFE

    def validCheckSum2(self):
        return (~(self.validCheckSumSub())) & 0xFE


    def validCheckSumSub(self):
        PacketSize = self.RecordData[2].data
        PID = self.RecordData[3].data
        CMD = self.RecordData[4].data

        Sum = PacketSize^PID^CMD

        for i in range(7,self.RecordLength):
         Sum = Sum ^ self.RecordData[i].data

        return Sum



    def ROM_Write(self):
        start = self.RecordData[7].start
        end = self.RecordData[7].end
        number = self.RecordData[7].data

        RamName = self.RamData.get(number, "UNKNOWN")

        long_text = RamName
        mid_text = RamName
        short_text = RamName

        self.put(start, end, self.out_ann, [0, [long_text, mid_text, short_text]])
        return

    def ROM_Read(self):
        return

    def RAM_Write(self):

        return

    def RAM_Read(self):
        return

    def I_JOG(self):
        return

    def S_JOG(self):
        return

    def STAT(self):
        return

    def ROLLBACK(self):
        return

    def REBOOT(self):
        return










    def decode(self, ss, es, data):
        """
        ss, es: start/end sample numbers provided by stacked UART decoder
        data: packets forwarded by the UART decoder (e.g. 'DATA', 'FRAME', etc.)
        """
        if not data:
            return
        if not isinstance(data, (list, tuple)) or len(data) < 1:
            return

        ptype = data[0]

        # STARTBIT
        # if ptype == 'STARTBIT':
        #     self.Index = 0
        #     self.PacketData = []
        #     return

        # DATA: ['DATA', rxtx, (value, databits_list)]
        if ptype == 'DATA':
            try:
                payload = data[2]
                val = payload[0] if isinstance(payload, (list, tuple)) else int(payload)
            except Exception:
                # Post to error row
                self.put(ss, es, self.out_ann, [1, ["Invalid DATA payload", "Bad payload"]])
                return

            #self.decode_byte_Collect(val, ss, es)


            return

        # FRAME: ['FRAME', rxtx, (value, valid)]
        if ptype == 'FRAME':
            try:
                val, valid = data[2]
            except Exception:
                return

            #printing = ["Error", "E", "E"]
            # if (self.DataIndex < 7):
            #printing = self.decode_byte_Check(ss,es)
            self.Record(val, ss, es)
            # else:
            #     long_text = "Data: 0x%02X" % val
            #     mid_text = "D: 0x%02X" % val
            #     short_text = "0x%02X" % val
            #     printing = [long_text, mid_text, short_text]

            #self.put(ss, es, self.out_ann, [0, printing])
            # self.put(ss, es, self.out_ann, [1, "%d" % (self.Index-1)])


            # if valid:
            #     long_text = "Frame: 0x%02X" % val
            #     short_text = "%02X" % val
            #     self.put(ss, es, self.out_ann, [0, [long_text, short_text]])
            # else:
            #     long_text = "Frame error: 0x%02X" % val
            #     short_text = "Frame err"
            #     self.put(ss, es, self.out_ann, [1, [long_text, short_text]])
            return

        # PARITY ERROR
        if ptype == 'PARITY ERROR':
            try:
                expected, actual = data[2]
            except Exception:
                return
            long_text = "Parity error exp=%d act=%d" % (expected, actual)
            short_text = "Parity err"
            self.put(ss, es, self.out_ann, [1, [long_text, short_text]])
            return

        # INVALID STARTBIT / STOPBIT
        if ptype == 'INVALID STARTBIT':
            try:
                val = data[2]
            except Exception:
                val = None
            long_text = "Invalid start bit: %s" % str(val)
            short_text = "Start err"
            self.put(ss, es, self.out_ann, [1, [long_text, short_text]])
            return

        if ptype == 'INVALID STOPBIT':
            try:
                val = data[2]
            except Exception:
                val = None
            long_text = "Invalid stop bit: %s" % str(val)
            short_text = "Stop err"
            self.put(ss, es, self.out_ann, [1, [long_text, short_text]])
            return

        # BREAK
        if ptype == 'BREAK':
            self.put(ss, es, self.out_ann, [0, ["Break condition", "Break"]])
            return

        # IDLE
        if ptype == 'IDLE':
            #self.put(ss, es, self.out_ann, [0, ["Idle", "Idle"]])
            return

        # fallback (debug)
        # self.put(ss, es, self.out_ann, [1, ["Unknown pkt:%s" % ptype, str(data)]])




