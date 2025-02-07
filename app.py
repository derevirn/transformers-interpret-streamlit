import asyncio
import gc
import logging
import os

import pandas as pd
#import psutil
import streamlit as st
from PIL import Image
from streamlit import components
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from transformers_interpret import SequenceClassificationExplainer

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)


#def print_memory_usage():
#    logging.info(f"RAM memory % used: {psutil.virtual_memory()[2]}")


@st.cache(allow_output_mutation=True, suppress_st_warning=True, max_entries=1)
def load_model(model_name):
    return (
        AutoModelForSequenceClassification.from_pretrained(model_name),
        AutoTokenizer.from_pretrained('bert-base-uncased'),
    )


def main():

    st.title("COVID-19 Fake News Detection")

    image = Image.open("./images/tight@1920x_transparent.png")
    st.sidebar.image(image, use_column_width=True)
    st.sidebar.markdown(
        "Check out the package on [Github](https://github.com/cdpierse/transformers-interpret)"
    )
    st.info(
        "Due to limited resources only low memory models are available. Run this [app locally](https://github.com/cdpierse/transformers-interpret-streamlit) to run the full selection of available models. "
    )

    # uncomment the options below to test out the app with a variety of classification models.
    models = {
        './model/checkpoint-3000': 'Fake News'
    }
    model_name = st.sidebar.selectbox(
        "Choose a classification model", list(models.keys())
    )
    model, tokenizer = load_model(model_name)
    if model_name.startswith("textattack/"):
        model.config.id2label = {0: "NEGATIVE (0) ", 1: "POSITIVE (1)"}
    model.eval()
    cls_explainer = SequenceClassificationExplainer(model=model, tokenizer=tokenizer)
    if cls_explainer.accepts_position_ids:
        emb_type_name = st.sidebar.selectbox(
            "Choose embedding type for attribution.", ["word", "position"]
        )
        if emb_type_name == "word":
            emb_type_num = 0
        if emb_type_name == "position":
            emb_type_num = 1
    else:
        emb_type_num = 0

    explanation_classes = ["predicted"] + list(model.config.label2id.keys())
    explanation_class_choice = st.sidebar.selectbox(
        "Explanation class: The class you would like to explain output with respect to.",
        explanation_classes,
    )
    my_expander = st.expander(
        "Click here for description of models and their tasks"
    )
    with my_expander:
        st.json(models)

    # st.info("Max char limit of 350 (memory management)")
    text = st.text_area(
        "Enter text to be interpreted",
        "I like you, I love you",
        height=400,
        max_chars=850,
    )

    if st.button("Interpret Text"):
       # print_memory_usage()

        st.text("Output")
        with st.spinner("Interpreting your text (This may take some time)"):
            if explanation_class_choice != "predicted":
                word_attributions = cls_explainer(
                    text,
                    class_name=explanation_class_choice,
                    embedding_type=emb_type_num,
                    internal_batch_size=2,
                )
            else:
                word_attributions = cls_explainer(
                    text, embedding_type=emb_type_num, internal_batch_size=2
                )

        if word_attributions:
            word_attributions_expander = st.expander(
                "Click here for raw word attributions"
            )
            with word_attributions_expander:
                st.json(word_attributions)
            components.v1.html(
                cls_explainer.visualize()._repr_html_(), scrolling=True, height=350
            )


if __name__ == "__main__":
    main()
