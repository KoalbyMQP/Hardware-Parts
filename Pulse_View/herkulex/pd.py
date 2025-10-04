import sigrokdecode as srd

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
    Len = 3
    Command = 0
    Servo = 0
    Checksum1 = 0
    Checksum2 = 0
    PacketData = []

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
        self.PacketData = []
        self.DataIndex = 0
        self.FrameIndex = 0
        self.Len = 3

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            if value < self.MIN_SAMPLERATE:
                raise srd.SigrokDecoderError(
                    "Sample rate too low for HerkuleX: %d Hz (minimum %d Hz)"
                    % (value, self.MIN_SAMPLERATE)
                )
            self.samplerate = value


    def decode_byte_Collect(self, number, ss, es):
        """
        Placeholder for byte processing logic.
        """

        if self.DataIndex >= self.Len:
            self.process_frame(ss, es)



        if ( self.DataIndex < 2): # 0-1 is header zone

            if number != self.Header:
                return False

        if (self.DataIndex == 2): # 2 is packet length
            self.Len=number

        if (self.DataIndex == 3):
            self.Servo=number

        if (self.DataIndex == 4):
            self.Command=number


        if (self.DataIndex == 5):
            self.Checksum1=number


        if (self.DataIndex == 6):
            self.Checksum2=number


        if (self.DataIndex > 6):
            #self.log(1, "DEBUG:append time: %d val:%d",self.DataIndex,number)
            self.PacketData.append(number)




        self.DataIndex = self.DataIndex + 1
        return True






    def decode_byte_Check(self, ss, es):
        """
        Placeholder for byte processing logic.
        """

        if self.FrameIndex >= self.Len:
            self.reset()

        long_text = ""
        mid_text = ""
        short_text = ""

        if ( self.FrameIndex < 2): # 0-1 is header zone
            long_text = "Header"
            mid_text = "Head"
            short_text = "H"

        if (self.FrameIndex == 2): # 2 is packet length
            number = self.Len
            long_text = "Length %d" % number
            mid_text = "Len %d" % number
            short_text = "%d" % number

        if (self.FrameIndex == 3):
            number = self.Servo
            if (self.Servo == 254):
                long_text = "All Servos"
                mid_text = "All"
                short_text = "All"
            else:
                long_text = "Servo ID %d" % number
                mid_text = "ID %d" % number
                short_text = "%d" % number

        if (self.FrameIndex == 4):
            number = self.Command
            command_name = self.commands.get(number, "UNKNOWN")
            if (command_name == "UNKNOWN"):
                return False


            long_text = command_name
            mid_text = "%d" % number
            short_text = "%d" % number

        if (self.FrameIndex == 5):
            number=self.Checksum1
            long_text = "Checksum1 %d" % len(self.PacketData)
            mid_text = "CS1"
            short_text = "CS"

        if (self.FrameIndex == 6):
            number=self.Checksum2
            long_text = "Checksum2 %d" % len(self.PacketData)
            mid_text = "CS2"
            short_text = "CS"


        if (self.FrameIndex > 6):
            number = self.PacketData[self.FrameIndex-7]
            long_text = "Packet data %d  size:%d" % (number, len(self.PacketData))

            mid_text = "Pd %d" % number
            short_text = "%d" % number




        self.FrameIndex = self.FrameIndex + 1
        return [long_text,mid_text,short_text]








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

            self.decode_byte_Collect(val, ss, es)


            return

        # FRAME: ['FRAME', rxtx, (value, valid)]
        if ptype == 'FRAME':
            try:
                val, valid = data[2]
            except Exception:
                return

            printing = ["Error", "E", "E"]
            # if (self.DataIndex < 7):
            printing = self.decode_byte_Check(ss,es)
            # else:
            #     long_text = "Data: 0x%02X" % val
            #     mid_text = "D: 0x%02X" % val
            #     short_text = "0x%02X" % val
            #     printing = [long_text, mid_text, short_text]

            self.put(ss, es, self.out_ann, [0, printing])
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
