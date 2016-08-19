# -*- coding: utf-8 -*-
import os
import re
import core.mining.lsimodel
import core.mining.lsisimilarity

import jieba.posseg


REJECT = re.compile('(('+')|('.join([
    u'中文', u'日期', u'汽车',
    #u'个人', u'未填写',
    #u'财务',
    #u'招聘', u'英才网', u'人力',
    u'互联网',
    ])+'))')

LINE = re.compile(ur'[\n\t]+')
WEB = re.compile(ur'\(?\s?((([hH][tT][tT][pP][sS]?|[fF][tT][pP])\:\/\/)?([\w\.\-]+(\:[\w\.\&%\$\-]+)*@)?((([^\s\(\)\<\>\\\"\.\[\]\,@;:]+)(\.[^\s\(\)\<\>\\\"\.\[\]\,@;:]+)*(\.[a-zA-Z]{2,4}))|((([1]?\d{1,2}|2[0-4]\d|25[0-5])\.){3}([1]?\d{1,2}|2[0-4]\d|25[0-5])))(\:(6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0))?((\/[^\/][\w\.\,\?\'\(\)\\\/\+&%\$#\=~_\-@]*)*[^\.\,\?\"\'\(\)\[\]!;<>{}\s\x7F-\xFF])?)\s?\)?')
SYMBOL = re.compile(ur'[- /]+')
SHORT = re.compile('(([a-z]\d{0,2})|([a-z]{1,4})|[\d\.]{1,11})$')

def jieba_cut(text):
    return jieba.posseg.cut(text)

def pos_extract(words, flags):
    return [word.word for word in words if word.flag not in flags]

def re_sub(reg, sub, text):
    """
        >>> from services.mining import *
        >>> s = "[测试计量技术及仪器]( http://www.test.com )[测试计量技术及仪器]\\n"
        >>> s += "[测试计量技术及仪器] (http://www.test.com) [测试计量技术及仪器]"
        >>> print s
        [测试计量技术及仪器]( http://www.test.com )[测试计量技术及仪器]
        [测试计量技术及仪器] (http://www.test.com) [测试计量技术及仪器]
        >>> print re_sub(LINE, ' ', s)
        [测试计量技术及仪器]( http://www.test.com )[测试计量技术及仪器] [测试计量技术及仪器] (http://www.test.com) [测试计量技术及仪器]
        >>> print re_sub(HTTP, ' ', s)
        [测试计量技术及仪器] [测试计量技术及仪器]
        [测试计量技术及仪器]   [测试计量技术及仪器]
        >>> s = "[测试计量技术及仪器] (www.test.com) [测试计量技术及仪器]"
        >>> print re_sub(HTTP, ' ', s)
        [测试计量技术及仪器]   [测试计量技术及仪器]
        >>> s = "[测试计量技术及仪器] (test123@test.com) [测试计量技术及仪器]"
        >>> print re_sub(HTTP, ' ', s)
        [测试计量技术及仪器]   [测试计量技术及仪器]
        >>> s = "--------------------\\n"
        >>> s += "英语(CET4)、普通话\\n"
        >>> s += "--------------------\\n"
        >>> print re_sub(LINE, '', re_sub(SYMBOL, '', s))
        英语(CET4)、普通话
    """
    return reg.sub(sub, text)

def silencer(document):
        FLAGS = ['x', # spaces
                 'm', # number and date
                 'a', # adverb
                 'i', 'j',
                 'nrt', 'nr', 'ns', #'nz', fails on myjnoee7.md
                 'u', # unclassified (eg. etc)
                 'f', # time and place
                 'q', # quantifier
                 'p', # preposition
                 'v', # vernicular expression
                 'ns', # city and country
                ]
        if isinstance(document, list):
            texts = document
        else:
            texts = [document]
        selected_texts = []
        for text in texts:
            text = re_sub(LINE, ' ', text)
            text = re_sub(WEB, '\n', text)
            text = re_sub(SYMBOL, ' ', text)
            words = jieba_cut(text)
            words = pos_extract(words, FLAGS)
            out = []
            for word in words:
                if REJECT.match(word):
                    continue
                if word.istitle():
                    # Can make it match SHORT later for skip (eg 'Ltd' ...)
                    word = word.lower()
                if not SHORT.match(word):
                    # Even out tools and brands (eg 'CLEARCASE' vs 'clearcase')
                    word = word.lower()
                    out.append(word)
            selected_texts.append(out)
        if isinstance(document, list):
            return selected_texts
        else:
            return selected_texts[0]


class Mining(object):

    def __init__(self, path, cvsvc, slicer=None):
        self.sim = {}
        self.path = path
        self.lsi_model = None
        self.services = {
                'default': [cvsvc.default],
                'all': cvsvc.svcls
            }
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if slicer is None:
            self.slicer = silencer
        else:
            self.slicer = slicer
        self.make_lsi(self.services['default'])

    def setup(self, name):
        assert name in self.services
        self.add(self.services[name], name)

    def make_lsi(self, service):
        self.lsi_model = None
        lsi_path = os.path.join(self.path, 'model')
        lsi = core.mining.lsimodel.LSImodel(lsi_path, slicer=self.slicer)
        try:
            lsi.load()
        except IOError:
            if lsi.build(service):
                lsi.save()
        self.lsi_model = lsi

    def add(self, svc_list, name):
        assert self.lsi_model
        save_path = os.path.join(self.path, name)
        for svc in svc_list:
            assert svc.name
            index = core.mining.lsisimilarity.LSIsimilarity(os.path.join(save_path, svc.name), self.lsi_model)
            try:
                index.load()
            except IOError:
                if index.build([svc]):
                    index.save()
            self.sim[svc.name] = index

    def update_model(self):
        updated = self.lsi_model.update(self.services['default'])
        if updated:
            self.update_sims()

    def update_sims(self):
        for name in self.services:
            for svc in self.services[name]:
                self.sim[svc.name].update([svc])
                self.sim[svc.name].save()

    def probability(self, doc, uses=None):
        if uses is None:
            uses = self.sim.keys()
        result = []
        for name in uses:
            sim = self.sim[name]
            result.extend(sim.probability(doc))
        return sorted(result, key=lambda x:float(x[1]), reverse=True)

    def probability_by_id(self, doc, id, uses=None):
        if uses is None:
            uses = self.sim.keys()
        result = tuple()
        for dbname in uses:
            sim = self.sim[dbname]
            probability = sim.probability_by_id(doc, id)
            if probability is not None:
                result = probability
                break
        return result

    def lenght(self, uses=None):
        if uses is None:
            uses = self.sim.keys()
        result = 0
        for name in uses:
            sim = self.sim[name]
            result += len(sim.names)
        return result

    def minetop(self, doc, top=None, uses=None):
        results = self.probability(doc, uses=uses)
        if top is None:
            top = len(results)
        return results[:top]

    def minelist(self, doc, lists, uses=None):
        return map(lambda x: self.probability_by_id(doc, x, uses=uses), lists)

    def minelistrank(self, doc, lists, uses=None):
        probalist = set(self.probability(doc, uses=uses))
        probalist.update(set(lists))
        ranklist = sorted(probalist, key=lambda x:float(x[1]), reverse=True)
        return map(lambda x: (x[0], ranklist.index(x)), lists)

    def default_names(self):
        return [n.name for n in self.services['default'] if n.name in self.sim.keys()]

    def addition_names(self):
        names = self.sim.keys()
        for n in self.default_names():
            names.remove(n)
        return names
