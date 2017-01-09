import os
import functools

import services.mining
import services.analysis.cutword
from baseapp.multicv import SVC_MULT_CV


LSI_PATH = 'lsimodel'
CUTWORD_PATH = 'cutwords'
SVC_CUTWORD = services.analysis.cutword.Cutword(CUTWORD_PATH)
slicer = functools.partial(services.mining.silencer, cutservice=SVC_CUTWORD)
cut_word = functools.partial(services.mining.cut_word, cutservice=SVC_CUTWORD)
SVC_MIN = services.mining.Mining(LSI_PATH, SVC_MULT_CV, slicer=slicer,
                                    cutword=cut_word)
SVC_MIN.setup()
