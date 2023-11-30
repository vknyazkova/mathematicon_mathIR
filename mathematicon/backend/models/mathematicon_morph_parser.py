import re


def remove_double_spaces(text):
    return re.sub(r'\s+', ' ', text)


class MorphologyCorrectionHandler:
    """
    Applies different corrections to the previously parsed tokens
    """

    def __init__(self, mode='allpos+ptcp+conv'):
        try:
            from pymorphy3 import MorphAnalyzer
        except ImportError:
            raise ImportError(
                "This class requires the "
                "pymorphy2 library and dictionaries. Install them with: "
                "pip install pymorphy2"
            ) from None
        if getattr(self, "_morph", None) is None:
            self._morph = MorphAnalyzer(lang="ru")
        self.fixes = mode

    @property
    def fixes(self):
        return self._fixes

    @fixes.setter
    def fixes(self, mode):
        modes = mode.split('+')
        self._fixes = []
        for m in modes:
            mode_attr = f'{m}_corrector'
            if not hasattr(self, mode_attr):
                raise ValueError(f'Unknown mode name = {m}')
            self._fixes.append(getattr(self, mode_attr))

    # def allpos_corrector(self, token, pymorphy_parsed):
    #     pymorphy_pos = pymorphy_parsed.tag.POS
    #     if MorphologyCorrectionHandler.POS.get(pymorphy_pos) \
    #             and token.pos_ != MorphologyCorrectionHandler.POS[pymorphy_pos]:
    #         token.pos_ = MorphologyCorrectionHandler.POS[pymorphy_parsed.tag.POS]
    #     return token

    def ptcp_corrector(self, token, pymorphy_parsed):
        if token.pos_ == 'VERB' and token.morph.get('VerbForm') \
                and token.morph.get('VerbForm')[0] == 'Part':
            prtf_form = pymorphy_parsed.inflect({'sing', 'masc', 'nomn'}).word
            inf_form = pymorphy_parsed.inflect({'INFN'}).word
            token.tag_ = 'PTCP|VERB'
            token.lemma_ = prtf_form + '|' + inf_form
        return token

    def conv_corrector(self, token, pymorphy_parsed):
        if token.pos_ == 'VERB' and token.morph.get('VerbForm') \
                and token.morph.get('VerbForm') == 'Conv':
            token.tag_ = 'GRD|VERB'
        return token

    def __call__(self, doc):
        for token in doc:
            pymorphy_parsed = self._morph.parse(token.text)[0]
            for fix in self.fixes:
                try:
                    token = fix(token, pymorphy_parsed)
                except Exception as e:
                    error_msg = (
                        f'Exception "{e}" was raised on token '    
                        f'({token.text}, {token.pos_}, {token.lemma_}) '
                        f'during execution of "{fix.__name__}" function'
                    )
                    print(error_msg)
        return doc