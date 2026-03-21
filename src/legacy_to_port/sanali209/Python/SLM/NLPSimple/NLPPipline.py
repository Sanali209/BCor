import json
import os
import re

import nltk
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords, wordnet

nltk.download('punkt')
nltk.download('stopwords')
stop_words = stopwords.words('english')

digit_on_end_pathern = r'(\w+)\d+\b'

test_replace_dictionary = {
    # key - replace to
    # value - replace from
    # regex patterns for mach whole word women
    # pathern:"/bwomen/b"
    'woman': ['/bwomen/b'],
    'warhamer': ['warhammer', 'war.hammer'],
    # regex patterns for mach whole word steampunk or steam punk or steam*punk
    # pathern:"/bsteampunk/b", "/bsteam.punk/b"
    'steampunk': ['/bsteam punk/b', '/bsteam.punk/b'],

    'author|WLOP': ['art of wlop', 'inspired by WLOP'],
    'author|Anne Stokes': ['inspired by Anne Stokes'],

}

extend_dictionary = {
    ',ext|world|the witcher': ['geralt of rivia', ],
    ',ext|world|the witcher|geralt of rivia': ['geralt of rivia', ],
    ',ext|world|the witcher|triss': ['triss'],
    ',ext|world|the witcher|yennefer': ['yennefer'],
    ',ext|world|league of legends': ['league of legends'],
    ',ext|world|warcraft': ['warcraft', 'world of warcraft', 'wow'],
    ',ext|world|warcraft|sylvana': ['sylvana', 'sylvanas', ],

    ',ext|world|overlord anime|albedo': ['albedo from overlord'],

    ',ext|world|god of war': ['god of war', 'kratos'],
    ',ext|world|god of war|kratos': ['kratos'],

    ',ext|world|warhammer': ['warhammer', 'warhammer40k', 'warhammer 40000', 'warhammer40000'],
    ',ext|world|diablo': ['diablo'],
    ',ext|world|diablo|star craft': ['star craft', 'starcraft'],

    ',ext|character|anime,': ['anime character'],
    ',ext|character|race|kitsune,': ['kitsune'],
    ',ext|character|race|elf': ['elf'],
    ',ext|character|race|dark elf,': ['dark elf', 'blue elf'],
    ',ext|character|race|vampire,': ['vampire'],
    ',ext|character|race|foxgirl': ['foxgirl'],
    ',ext|character|race|demon': ['demon', 'succubus'],
    ',ext|character|race|monster': ['monster'],
    ',ext|character|race|monster girl': ['monster girl'],
    ',ext|character|race|cat girl': ['catgirl'],

    ',ext|character|race|demon|succubus': ['succubus'],
    ',ext|character|race|angel': ['angel', 'archangel'],
    ',ext|character|race|dark angel': ['dark angel'],
    ',ext|character|race|orc': ['orc'],
    ',ext|character|race|human,': ['human'],
    ',ext|character|race|dwarf,': ['dwarf'],
    ',ext|character|race|goblin,': ['goblin'],
    ',ext|character|race|gnome,': ['gnome'],
    ',ext|character|race|troll,': ['troll'],
    ',ext|character|race|tauren,': ['tauren'],
    ',ext|character|race|undead,': ['undead'],
    ',ext|character|race|night elf,': ['night elf'],
    ',ext|character|race|blood elf,': ['blood elf'],
    ',ext|character|race|pandaren,': ['pandaren'],

    ',ext|character|race|dragon,': ['dragon'],
    ',ext|character|race|dragon|red dragon,': ['red dragon'],
    ',ext|character|race|dragon|black dragon,': ['black dragon'],
    ',ext|character|race|dragon|white dragon,': ['white dragon'],
    ',ext|character|race|dragon|blue dragon,': ['blue dragon', 'blue scaled dragon'],
    ',ext|character|race|dragon|green dragon,': ['green dragon'],

    ',ext|character|race|fire elemental,': ['fire elemental'],
    ',ext|character|race|insectoid,': ['insectoid'],

    ',ext|character|race|cyborg,': ['cyborg'],

    ',ext|character|gender|female': ['girl', 'female', 'woman', 'waifu'],
    ',ext|character|gender|male': ['boy', 'man'],
    ',ext|character|gender|girl': ['girl'],
    ',ext|character|gender|girl cute': ['cute girl'],
    ',ext|character|gender|boy': ['boy'],
    ',ext|character|gender|wolf|anthropomorphic': ['anthropomorphic wolf'],

    ',ext|character|class|rogue': ['rogue'],
    ',ext|character|class|warrior': ['warrior'],
    ',ext|character|class|thief': ['thief'],
    ',ext|character|class|mage': ['mage', 'archmage', 'wizard'],
    ',ext|character|class|priest': ['priest'],
    ',ext|character|class|paladin': ['paladin'],
    ',ext|character|class|hunter': ['hunter'],
    ',ext|character|class|druid': ['druid'],
    ',ext|character|class|shaman': ['shaman'],
    ',ext|character|class|warlock': ['warlock'],
    ',ext|character|class|necromancer': ['necromancer'],
    ',ext|character|class|assassin': ['assassin'],

    ',ext|character|leather suit': ['leather suit'],

    ',ext|places|forest': ['a forest'],
    ',ext|places|forest|dark forest': ['dark forest'],
    ',ext|places|forest|castle': ['a castle'],
    ',ext|places|cave': ['cave'],
    ',ext|places|cave|ice cave': ['ice cave'],
    ',ext|places|cave|lava cave': ['lava cave'],
    ',ext|places|city': ['a city'],

    ',ext|color|red': ['redhead', 'red hair'],
    ',ext|color|black': ['black hair'],
    ',ext|color|white': ['white hair'],
    ',ext|color|blue': ['blue hair'],

    ',ext|im genre|anime': ['anime'],
    ',ext|im genre|anime 90': ['1990s anime'],
    ',ext|im genre|manga': ['manga'],
    ',ext|im genre|comix': ['comix'],
    ',ext|im genre|comix|comix panel': ['comix panel'],
    ',ext|im genre|cartoon': ['cartoon'],
    ',ext|im genre|sketch': ['sketch'],
    ',ext|im genre|painting': ['painting'],
    ',ext|im genre|digital painting': ['digital painting'],
    ',ext|im genre|digital art': ['digital art'],
    ',ext|im genre|concept art': ['concept art'],
    ',ext|im genre|portrait': ['portrait'],
    ',ext|im genre|character design': ['character design'],
    ',ext|im genre|full body': ['full body'],
    ',ext|im genre|game art': ['game art'],
    ',ext|im genre|avatar imageView': ['avatar imageView'],
    ',ext|im genre|full color': ['full color'],
    ',ext|im genre|black and white': ['black and white', 'b&w'],
    ',ext|im genre|fantasy|gothic': ['gothic fantasy'],
    ',ext|im genre|fantasy|dark fantasy': ['dark fantasy'],
    ',ext|im genre|cyberpunk': ['cyberpunk'],
    ',ext|im genre|steampunk': ['steampunk'],
    ',ext|im genre|scifi': ['scifi', 'sci-fi', 'sci fi', 'science fiction'],
    ',ext|im genre|apocalypse': ['apocalypse art', 'apocalyptic art', 'apocalyptic', 'apocalypse'],
    ',ext|im genre|postapocalypse': ['postapocalypse art', 'postapocalyptic art', 'post apocalyptic', 'postapocalyptic',
                                     'postapocalypse'],

    ',ext|im genre|3d renderer': ['3d'],
    ',ext|im genre|drawn': ['a drawing', 'a painting'],
    ',ext|im genre|photo': ['a photo', 'a photograph'],
    ',ext|im genre|photo|photo manipulation': ['photo manipulation'],
    ',ext|im genre|photo|photo manipulation|photo collage': ['photo collage'],
    ',ext|im genre|scene from the movie ': ['scene from the movie '],

    ',ext|im composition|a man on a horse': ['a man on a horse'],
    ',ext|im composition|battle between good and evil': ['battle between good and evil'],

}


# POS tags list:
# CC coordinating conjunction
# CD cardinal digit
# DT determiner
# EX existential there (like: "there is" ... think of it like "there exists")
# FW foreign word
# IN preposition/subordinating conjunction
# JJ adjective 'big'
# JJR adjective, comparative 'bigger'
# JJS adjective, superlative 'biggest'
# LS list marker 1)
# MD modal could, will
# NN noun, singular 'desk'
# NNS noun plural 'desks'
# NNP proper noun, singular 'Harrison'
# NNPS proper noun, plural 'Americans'
# PDT predeterminer 'all the kids'
# POS possessive ending parent's
# PRP personal pronoun I, he, she
# PRP$ possessive pronoun my, his, hers
# RB adverb very, silently,
# RBR adverb, comparative better
# RBS adverb, superlative best
# RP particle give up
# TO to go 'to' the store.
# UH interjection errrrrrrrm
# VB verb, base form take
# VBD verb, past tense took
# VBG verb, gerund/present participle taking
# VBN verb, past participle taken
# VBP verb, sing. present, non-3d take
# VBZ verb, 3rd person sing. present takes
# WDT wh-determiner which
# WP wh-pronoun who, what
# WP$ possessive wh-pronoun whose
# WRB wh-abverb where, when

class NLPPipline:
    def __init__(self):
        self.text = ""
        self.operations = []
        self.tokens = []
        self.data = {}

        self.bagOfWords = []
        self.countedBagOfWords = {}

    def run(self):
        for operation in self.operations:
            operation.run(self)


class NLPPiplineOperation:

    def run(self, paiplain):
        pass


class NLPTextTokenize(NLPPiplineOperation):
    def run(self, paiplain):
        text = paiplain.text
        tokens = nltk.word_tokenize(text)
        paiplain.tokens = tokens


class NLPTokensPOSTag(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        tokensTagged = nltk.pos_tag(tokens)
        paiplain.data["tokensPOSTagged"] = tokensTagged


class NLPTokensLemmatization(NLPPiplineOperation):
    def run(self, paiplain):
        lemmatizer = WordNetLemmatizer()
        tokens = paiplain.tokens
        tokensLemmatized = []
        for token in tokens:
            tokensLemmatized.append(lemmatizer.lemmatize(token))


class NLPTokensNER(NLPPiplineOperation):
    # named entity recognition
    def run(self, paiplain):
        tokens = paiplain.tokens
        tokensNER = nltk.ne_chunk(tokens)
        paiplain.data["tokensNER"] = tokensNER


class NLPTokensBagOfWords(NLPPiplineOperation):

    def run(self, paiplain):

        paiplain.bagOfWords = list(set(paiplain.tokens))
        # create counted bag of words
        countedBagOfWords = {}
        for word in paiplain.tokens:
            if word in countedBagOfWords:
                countedBagOfWords[word] += 1
            else:
                countedBagOfWords[word] = 1
        # sort counted bag of words
        countedBagOfWords = dict(sorted(countedBagOfWords.items(), key=lambda item: item[1], reverse=True))

        paiplain.countedBagOfWords = countedBagOfWords


class NLPTokensBagOfWordsDeleteWithFrequency(NLPPiplineOperation):
    def __init__(self, frequency):
        self.frequency = frequency

    def run(self, paiplain):
        countedBagOfWords = paiplain.countedBagOfWords
        for word in countedBagOfWords.copy():
            if countedBagOfWords[word] <= self.frequency:
                del countedBagOfWords[word]
                # remove word from bag of words
                paiplain.bagOfWords.remove(word)
        paiplain.countedBagOfWords = countedBagOfWords


class NLPTokensSaveBagOfWords(NLPPiplineOperation):
    def __init__(self, path):
        self.path = path

    def run(self, paiplain):
        bo_data = [paiplain.bagOfWords, paiplain.countedBagOfWords]
        with open(self.path, 'w') as outfile:
            json.dump(bo_data, outfile, indent=4)


class NLPTokensLoadBagOfWords(NLPPiplineOperation):
    def __init__(self, path):
        self.path = path

    def run(self, paiplain):
        with open(self.path, 'r') as outfile:
            bo_data = json.load(outfile)
        paiplain.bagOfWords = bo_data[0]
        paiplain.countedBagOfWords = bo_data[1]


class NLPTokensSetBagOfWords(NLPPiplineOperation):
    def __init__(self, bo_data):
        self.bo_data = bo_data

    def run(self, paiplain):
        paiplain.bagOfWords = self.bo_data[0]
        paiplain.countedBagOfWords = self.bo_data[1]


def load_bag_of_words(path):
    if not os.path.exists(path):
        return [[],{}]
    with open(path, 'r') as outfile:
        bo_data = json.load(outfile)
    return bo_data


class NLPPiplineMergeBagOfWordsFromFile(NLPPiplineOperation):
    def __init__(self, path):
        self.path = path

    def run(self, paiplain):
        with open(self.path, 'r') as outfile:
            bo_data = json.load(outfile)
        aditional_bagOfWords = bo_data[0]
        aditional_countedBagOfWords = bo_data[1]
        for word in aditional_bagOfWords:
            if word not in paiplain.bagOfWords:
                paiplain.bagOfWords.append(word)
        for word in aditional_countedBagOfWords:
            if word not in paiplain.countedBagOfWords:
                paiplain.countedBagOfWords[word] = aditional_countedBagOfWords[word]
            else:
                paiplain.countedBagOfWords[word] += aditional_countedBagOfWords[word]


class NLPTokensDeleteNotInBagOfWords(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        bagOfWords = paiplain.bagOfWords
        for token in tokens.copy():
            if token not in bagOfWords:
                tokens.remove(token)
        paiplain.tokens = tokens


class NLPTextReplace(NLPPiplineOperation):
    def __init__(self, part, replaceWith):
        self.part = part
        self.replaceWith = replaceWith

    def run(self, paiplain):
        text = paiplain.text
        text = text.replace(self.part, self.replaceWith)
        paiplain.text = text


class NLPTextReplaceByDictionary(NLPPiplineOperation):
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def run(self, paiplain):
        text = paiplain.text
        for key in self.dictionary:
            text = text.replace(key, self.dictionary[key])
        paiplain.text = text


class NLPTextReplaceByRegexDict(NLPPiplineOperation):
    def __init__(self, dictionary=None):
        if dictionary is None:
            dictionary = test_replace_dictionary
        self.dictionary = dictionary

    def run(self, paiplain):
        text = paiplain.text
        for spel_item in self.dictionary.keys():
            right_text = spel_item
            for pathern in self.dictionary[spel_item]:
                # Use word boundaries \b to match whole words
                regex_pattern = pathern
                text = re.sub(regex_pattern, right_text, text)
        paiplain.text = text


class NLPTextExtendByRegexDict(NLPPiplineOperation):
    def __init__(self, dictionary=None):
        if dictionary is None:
            dictionary = extend_dictionary
        self.dictionary = dictionary

    def run(self, paiplain):
        text = paiplain.text
        for spel_item in self.dictionary.keys():
            right_text = spel_item
            for pathern in self.dictionary[spel_item]:
                right_text = pathern + right_text
                # Use word boundaries \b to match whole words
                regex_pattern = pathern
                text = re.sub(regex_pattern, right_text, text)
        paiplain.text = text


class NLPTextDeleteXMLTags(NLPPiplineOperation):
    def run(self, paiplain):
        text = paiplain.text
        # faind all xml tags
        xmlTags = re.findall(r'<[^>]+>', text)
        for xmlTag in xmlTags:
            text = text.replace(xmlTag, "")
        paiplain.text = text


class NLPTokenDeleteByName(NLPPiplineOperation):
    def __init__(self, name):
        self.name = name

    def run(self, paiplain):
        tokens = paiplain.tokens.copy()
        for token in tokens:
            if token == self.name:
                tokens.remove(token)
        paiplain.tokens = tokens


class NLPTokensDeleteStopWords(NLPPiplineOperation):
    def __init__(self):
        self.customStopWords = []

    def run(self, paiplain):
        tokens = paiplain.tokens
        for stopword in stop_words:
            for token in tokens:
                if token == stopword:
                    tokens.remove(token)
        for stopword in self.customStopWords:
            for token in tokens:
                if token == stopword:
                    tokens.remove(token)
        paiplain.tokens = tokens


class NLPTokensDeleteEmpty(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        for token in tokens:
            if token == "":
                tokens.remove(token)
        paiplain.tokens = tokens


class NLPTokensDeleteDuplicates(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        tokens = list(set(tokens))
        paiplain.tokens = tokens


class NLPTokensDeleteRandString(NLPPiplineOperation):

    def run(self, paiplain):
        # delete strings as "p2ylk0d3m8"
        tokens = paiplain.tokens
        new_tokens = []
        for token in tokens:
            #count digits groups if more than 3 delete
            regex_digit = re.compile(r'\d+')
            count = len(regex_digit.findall(token))
            if count < 3:
                new_tokens.append(token)
        paiplain.tokens = new_tokens


class NLPTokensDeleteIntegers(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        new_tokens = []
        for token in tokens:
            regex_digit = re.compile(r'\d+')
            if not regex_digit.match(token):
                new_tokens.append(token)
        paiplain.tokens = new_tokens


class NLPTokensDeleteHexadecimal(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        new_tokens = []
        for token in tokens:
            regex_hex = re.compile(r'^[0-9A-Fa-f]+$')
            if not regex_hex.match(token):
                new_tokens.append(token)
        paiplain.tokens = new_tokens


class NLPTokensDeleteShort(NLPPiplineOperation):
    def __init__(self, minlen):
        self.minlen = minlen

    def run(self, paiplain):
        tokens = paiplain.tokens
        new_tokens = []
        for token in tokens:
            if len(token) >= self.minlen:
                new_tokens.append(token)
        paiplain.tokens = new_tokens


class NLPTokensDeleteLong(NLPPiplineOperation):
    def __init__(self, maxlen):
        self.maxlen = maxlen

    def run(self, paiplain):
        tokens = paiplain.tokens
        for token in tokens:
            if len(token) > self.maxlen:
                tokens.remove(token)
        paiplain.tokens = tokens


class NLPDeleteTokensWithSymbols(NLPPiplineOperation):
    def __init__(self, symbols):
        self.symbols = symbols

    def run(self, paiplain):
        tokens = paiplain.tokens
        for token in tokens:
            for symbol in self.symbols:
                if symbol in token:
                    tokens.remove(token)
        paiplain.tokens = tokens


class NLPTokensStripSpacesOperation(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        for token in tokens:
            token = token.strip()
        paiplain.tokens = tokens


class NLPTokensToLoverCase(NLPPiplineOperation):
    def run(self, paiplain):
        tokens = paiplain.tokens
        new_tokens = []
        for token in tokens:
            new_tokens.append(token.lower())

        paiplain.tokens = new_tokens


class NLPTextInformationExtraction(NLPPiplineOperation):
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

    def run(self, paiplain):
        text = paiplain.text
        # faind all by pattern
        information = re.findall(self.pattern, text)
        if "information" not in paiplain.data:
            paiplain.data["information"] = {}
        paiplain.data["information"][self.name] = information


class NLPTokensReplaceSinonims(NLPPiplineOperation):

    def run(self, paiplain):
        tokens = paiplain.tokens
        for token in tokens.copy():
            sysnet = wordnet.synsets(token)
            if sysnet:
                synonim = sysnet[0].lemmas()[0].name()
                paiplain.tokens.append(synonim)
                paiplain.tokens.remove(token)


class NLPTokensSpellChecking(NLPPiplineOperation):
    def run(self, paiplain):
        from spellchecker import SpellChecker
        tokens = paiplain.tokens
        spell = SpellChecker()
        for token in tokens:
            corected = spell.correction(token)
            if corected != token:
                tokens.append(corected)
                tokens.remove(token)


class NLPTokensTransform(NLPPiplineOperation):
    def __init__(self, transform):
        self.transform = transform
        self.extend_dictionary = []
        self.add_tokens = []
        self.delsource = False

    def transform(self, paiplain):
        tokens = paiplain.tokens
        #chek if all items from extend_dictionary in tokens
        if all(item in tokens for item in self.extend_dictionary):
            #add add_tokens to tokens
            tokens.extend(self.add_tokens)
            #remove extend_dictionary from tokens if delsource is true
            if self.delsource:
                for item in self.extend_dictionary:
                    tokens.remove(item)
        paiplain.tokens = tokens
