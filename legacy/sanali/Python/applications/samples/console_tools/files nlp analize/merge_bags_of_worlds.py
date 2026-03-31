from SLM.NLPSimple.NLPPipline import NLPPipline, NLPPiplineMergeBagOfWordsFromFile, NLPTokensSaveBagOfWords

bag_ofWords_files = [r"F:\rawimagedb\repository\_art books\filnames_bagofword.json",
                     r"F:\rawimagedb\repository\safe repo\filnames_bagofword.json",
                     r"F:\rawimagedb\repository\nsfv repo\3d\_siterips\filnames_bagofword.json",
                     r"F:\rawimagedb\repository\nsfv repo\drawn\_site rip\filnames_bagofword.json",
                     r"F:\rawimagedb\repository\nsfv repo\drawn\asorted drawn images\filnames_bagofword.json",
                        r"F:\rawimagedb\repository\nsfv repo\drawn\drawn comix\filnames_bagofword.json",
                    r"F:\rawimagedb\repository\nsfv repo\drawn\drawn xxx autors\filnames_bagofword.json",
                     r"F:\rawimagedb\repository\nsfv repo\drawn\furi\filnames_bagofword.json",
                     r"F:\rawimagedb\repository\nsfv repo\drawn\presort\filnames_bagofword.json"

                     ]

save_bag_of_words_file = r"F:\rawimagedb\repository\bags_of_word.json"

NLP_pipline = NLPPipline()

for bag_ofWords_file in bag_ofWords_files:
    NLP_pipline.operations.append(NLPPiplineMergeBagOfWordsFromFile(bag_ofWords_file))

NLP_pipline.operations.append(NLPTokensSaveBagOfWords(save_bag_of_words_file))

NLP_pipline.run()
