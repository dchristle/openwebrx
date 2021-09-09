from csdr.chain.demodulator import BaseDemodulatorChain, FixedAudioRateChain, FixedIfSampleRateChain, DialFrequencyReceiver
from pycsdr.modules import FmDemod, Agc, Writer, Buffer
from pycsdr.types import Format
from digiham.modules import DstarDecoder, DcBlock, FskDemodulator, GfskDemodulator, DigitalVoiceFilter, MbeSynthesizer, NarrowRrcFilter, NxdnDecoder, DmrDecoder, WideRrcFilter, YsfDecoder
from digiham.ambe import Modes
from owrx.meta import MetaParser


class DigihamChain(BaseDemodulatorChain, FixedIfSampleRateChain, FixedAudioRateChain, DialFrequencyReceiver):
    def __init__(self, fskDemodulator, decoder, mbeMode, filter=None, codecserver: str = ""):
        self.decoder = decoder
        if codecserver is None:
            codecserver = ""
        agc = Agc(Format.SHORT)
        agc.setMaxGain(30)
        agc.setInitialGain(3)
        workers = [FmDemod(), DcBlock()]
        if filter is not None:
            workers += [filter]
        workers += [
            fskDemodulator,
            decoder,
            MbeSynthesizer(mbeMode, codecserver),
            DigitalVoiceFilter(),
            agc
        ]
        self.metaParser = None
        super().__init__(workers)

    def getFixedIfSampleRate(self):
        return 48000

    def getFixedAudioRate(self):
        return 8000

    def setMetaWriter(self, writer: Writer):
        if self.metaParser is None:
            self.metaParser = MetaParser()
            buffer = Buffer(Format.CHAR)
            self.decoder.setMetaWriter(buffer)
            self.metaParser.setReader(buffer.getReader())
        self.metaParser.setWriter(writer)

    def supportsSquelch(self):
        return False

    def setDialFrequency(self, frequency: int) -> None:
        if self.metaParser is None:
            return
        self.metaParser.setDialFrequency(frequency)

    def stop(self):
        if self.metaParser is not None:
            self.metaParser.stop()
        super().stop()


class Dstar(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=FskDemodulator(samplesPerSymbol=10),
            decoder=DstarDecoder(),
            mbeMode=Modes.DStarMode,
            codecserver=codecserver
        )


class Nxdn(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=GfskDemodulator(samplesPerSymbol=20),
            decoder=NxdnDecoder(),
            mbeMode=Modes.NxdnMode,
            filter=NarrowRrcFilter(),
            codecserver=codecserver
        )


class Dmr(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=GfskDemodulator(samplesPerSymbol=10),
            decoder=DmrDecoder(),
            mbeMode=Modes.DmrMode,
            filter=WideRrcFilter(),
            codecserver=codecserver,
        )

    def setSlotFilter(self, slotFilter: int) -> None:
        self.decoder.setSlotFilter(slotFilter)


class Ysf(DigihamChain):
    def __init__(self, codecserver: str = ""):
        super().__init__(
            fskDemodulator=GfskDemodulator(samplesPerSymbol=10),
            decoder=YsfDecoder(),
            mbeMode=Modes.YsfMode,
            filter=WideRrcFilter(),
            codecserver=codecserver
        )
