# get list of files and analiz his with nltk
import os
import subprocess
import time

import pandas as pd

from SLM.FuncModule import get_files
from SLM.NLPSimple.NLPPipline import *
import gradio as gr

replace_dictionary = {
    # black list
    ' ': [r'\\u0444\\u044d\\u043d\\u0434\\u043e\\u043c\\u044b', r"\\u676f\\u5177\\u87ba\\u65cb\\u4e38"],
    # speling part
    ' fileext|jpg': ['.jpeg', '.jpg', ],
}

work_directory = r'F:\rawimagedb\repository\nsfv repo\3d\3d comix'
data = []

# create paiplain
NLP_pipline = NLPPipline()
NLP_pipline.operations.append(NLPTextExtendByRegexDict(replace_dictionary))
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
NLP_pipline.operations.append(NLPTokensDeleteIntegers())
NLP_pipline.operations.append(NLPTokensDeleteShort(4))
NLP_pipline.operations.append(NLPTokensToLoverCase())
NLP_pipline.operations.append(NLPTokensDeleteStopWords())
# NLP_pipline.operations.append(NLPTokensSpellChecking())
# NLP_pipline.operations.append(NLPTokensLemmatization())
# NLP_pipline.operations.append(NLPTokensPOSTag())

NLP_pipline.operations.append(NLPTokensBagOfWords())

with gr.Blocks() as gui:
    worck_directory = gr.Textbox(lines=1, label="worck directory")

    dataframe_Output = gr.Dataframe(label="json output")


    def piplineAnalise(worck_directory):
        files = get_files(worck_directory, ['*.jpg', '*.png', '*.jpeg', '*.gif', '*.bmp'])
        files_text = ''
        for file in files:
            file_name = os.path.basename(file)
            files_text += file_name + "\n"
        NLP_pipline.text = files_text
        NLP_pipline.run()
        counted_bagofwords = NLP_pipline.countedBagOfWords
        # sort
        counted_bagofwords = {k: v for k, v in
                              sorted(counted_bagofwords.items(), key=lambda item: item[1], reverse=True)}
        dataframe = pd.DataFrame(counted_bagofwords.items(), columns=['word', 'count'])

        return dataframe


    process_button = gr.Button(label="process")
    process_button.click(fn=piplineAnalise, inputs=[worck_directory], outputs=[dataframe_Output])

gui.launch()