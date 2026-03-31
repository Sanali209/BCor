# get list of files and analiz his with nltk
from SLM.NLPSimple.NLPPipline import *
from SLM.fileBachOperations.BachFileOperation import BachOperationPipeline, MoveFilesByNLPTokens, EmbedNLPTokensToXMP
from SLM.groupcontext import group

work_directory = r'F:\rawimagedb\repository\safe repo\presort\mass effect'

# create paiplain
NLP_pipline = NLPPipline()
with group():
    NLP_pipline.operations.append(NLPTextReplace('.', ' '))
    NLP_pipline.operations.append(NLPTextReplace('_', ' '))
    NLP_pipline.operations.append(NLPTextReplace('-', ' '))
    NLP_pipline.operations.append(NLPTextReplace('[', ' '))
    NLP_pipline.operations.append(NLPTextReplace(']', ' '))
    NLP_pipline.operations.append(NLPTextReplace('(', ' '))
    NLP_pipline.operations.append(NLPTextReplace(')', ' '))
    NLP_pipline.operations.append(NLPTextReplace('+', ' '))
    NLP_pipline.operations.append(NLPTextReplace('=', ' '))

    NLP_pipline.operations.append(NLPTextTokenize())
    NLP_pipline.operations.append(NLPTokensToLoverCase())

    NLP_pipline.operations.append(NLPTokensDeleteStopWords())

    merge = NLPPiplineMergeBagOfWordsFromFile(r"F:\rawimagedb\repository\safe repo\filnames_bagofword.json")
    NLP_pipline.operations.append(merge)
    NLP_pipline.operations.append(NLPTokensDeleteNotInBagOfWords())

file_pipeline = BachOperationPipeline()
with group():
    muve_operation = MoveFilesByNLPTokens()
    muve_operation.nlp_pipline = NLP_pipline
    muve_operation.move_dictionary.append({'mach pattern': 'batman', 'destination': 'batman'})
    muve_operation.move_dictionary.append({'mach pattern': 'bioshock', 'destination': 'bioshock'})
    muve_operation.move_dictionary.append({'mach pattern': 'borderlands', 'destination': 'borderlands'})
    muve_operation.move_dictionary.append({'mach pattern': 'dead or alive', 'destination': 'dead or alive'})
    muve_operation.move_dictionary.append({'mach pattern': 'dota', 'destination': 'dota'})
    muve_operation.move_dictionary.append({'mach pattern': 'fallout', 'destination': 'fallout'})
    muve_operation.move_dictionary.append({'mach pattern': 'final fantasy', 'destination': 'final fantasy'})
    muve_operation.move_dictionary.append({'mach pattern': 'halo', 'destination': 'halo'})
    muve_operation.move_dictionary.append({'mach pattern': 'half life', 'destination': 'half life'})
    muve_operation.move_dictionary.append({'mach pattern': 'left 4 dead', 'destination': 'left 4 dead'})
    muve_operation.move_dictionary.append({'mach pattern': 'league of legends', 'destination': 'league of legends'})
    muve_operation.move_dictionary.append({'mach pattern': 'life is strange', 'destination': 'life is strange'})
    muve_operation.move_dictionary.append({'mach pattern': 'mass effect', 'destination': 'mass effect'})
    muve_operation.move_dictionary.append({'mach pattern': 'metal gear', 'destination': 'metal gear'})
    muve_operation.move_dictionary.append({'mach pattern': 'mortal kombat', 'destination': 'mortal kombat'})
    muve_operation.move_dictionary.append({'mach pattern': 'portal', 'destination': 'portal'})
    muve_operation.move_dictionary.append({'mach pattern': 'resident evil', 'destination': 'resident evil'})
    muve_operation.move_dictionary.append({'mach pattern': 'soul calibur', 'destination': 'soul calibur'})
    muve_operation.move_dictionary.append({'mach pattern': 'star wars', 'destination': 'star wars'})
    muve_operation.move_dictionary.append({'mach pattern': 'street fighter', 'destination': 'street fighter'})
    muve_operation.move_dictionary.append({'mach pattern': 'the elder scrolls', 'destination': 'the elder scrolls'})
    muve_operation.move_dictionary.append({'mach pattern': 'the legend of zelda', 'destination': 'the legend of zelda'})
    muve_operation.move_dictionary.append({'mach pattern': 'the witcher', 'destination': 'the witcher'})
    muve_operation.move_dictionary.append({'mach pattern': 'tomb raider', 'destination': 'tomb raider'})
    muve_operation.move_dictionary.append({'mach pattern': 'uncharted', 'destination': 'uncharted'})
    muve_operation.move_dictionary.append({'mach pattern': 'world of warcraft', 'destination': 'world of warcraft'})
    muve_operation.move_dictionary.append({'mach pattern': 'x men', 'destination': 'x men'})
    muve_operation.move_dictionary.append({'mach pattern': 'darkstalkers', 'destination': 'darkstalkers'})
    muve_operation.move_dictionary.append({'mach pattern': 'frozen', 'destination': 'frozen'})
    muve_operation.move_dictionary.append({'mach pattern': 'dragon age', 'destination': 'dragon age'})

    # file_pipeline.operations.append(muve_operation)
    embed_xmp = EmbedNLPTokensToXMP()
    embed_xmp.nlp_pipline = NLP_pipline
    file_pipeline.operations.append(embed_xmp)

file_pipeline.createFileList(work_directory, ['*.jpg', '*.png', '*.jpeg', '*.gif', '*.bmp'])
file_pipeline.run()
