import streamlit as st
import pandas as pd
import numpy as np
import re
import nltk
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf

# Set page configuration
st.set_page_config(
    page_title="Financial Sentiment Analysis",
    page_icon="📊",
    layout="wide"
)

# Setup NLTK for Streamlit Cloud
@st.cache_resource
def setup_nltk_cloud():
    # This is the key fix for Streamlit Cloud - download directly without checking
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
        return True
    except Exception as e:
        st.error(f"Failed to download NLTK resources: {str(e)}")
        return False

# Initialize NLTK resources
nltk_ready = setup_nltk_cloud()

# Simple preprocessing without NLTK
def basic_preprocess(text):
    if not isinstance(text, str):
        return ''
    
    # Basic text cleaning
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Simple tokenization and stop word removal
    tokens = text.split()
    
    # Basic English stopwords list
    basic_stopwords = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
                      "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
                      'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 
                      'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 
                      'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 
                      'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was',
                      'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 
                      'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 
                      'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 
                      'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                      'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 
                      'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'}
    
    tokens = [token for token in tokens if token not in basic_stopwords]
    return ' '.join(tokens)

# Preprocessing function with fallback
@st.cache_data
def preprocess_text(text):
    if not nltk_ready:
        return basic_preprocess(text)
        
    try:
        # Import these here to avoid errors if NLTK download failed
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        
        if not isinstance(text, str):
            return ''
        
        # Basic text cleaning
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # NLTK tokenization and stopword removal
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
        return ' '.join(tokens)
    except Exception as e:
        st.warning(f"NLTK processing failed: {str(e)}. Using basic processing instead.")
        return basic_preprocess(text)

# Load the DistilBERT model and tokenizer
@st.cache_resource
def load_distilbert_model():
    try:
        model_path = 'best_model/transformer_model'
        model = TFAutoModelForSequenceClassification.from_pretrained(model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        return model, tokenizer
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None, None

# Predict sentiment
def predict_sentiment(text, model, tokenizer):
    processed_text = preprocess_text(text)
    if not processed_text:
        return "Unknown", 0.0
        
    inputs = tokenizer(
        processed_text,
        truncation=True,
        padding='max_length',
        max_length=128,
        return_tensors='tf'
    )
    outputs = model(inputs)
    logits = outputs.logits.numpy()
    probs = tf.nn.softmax(logits, axis=1).numpy()[0]
    prediction = np.argmax(probs)
    sentiment = "Positive" if prediction == 1 else "Negative/Neutral"
    confidence = float(probs[prediction])
    return sentiment, confidence

# Main function
def main():
    st.title("📊 Financial Sentiment Analysis")
    st.markdown("### Powered by DistilBERT")
    
    # Load the model
    model, tokenizer = load_distilbert_model()
    if model is None or tokenizer is None:
        st.error("Failed to load the model. Please check model files in 'best_model/transformer_model'.")
        st.stop()
    
    # User input
    st.subheader("Enter text for sentiment analysis")
    user_input = st.text_area("Type or paste financial text:", height=150)
    
    if st.button("Analyze Sentiment"):
        if user_input:
            with st.spinner("Analyzing sentiment..."):
                sentiment, confidence = predict_sentiment(user_input, model, tokenizer)
                
                # Display results
                if sentiment == "Positive":
                    st.success(f"Sentiment: {sentiment}")
                else:
                    st.error(f"Sentiment: {sentiment}")
                st.info(f"Confidence: {confidence:.2%}")
                
                # Display processing method used
                if nltk_ready:
                    method = "NLTK"
                else:
                    method = "basic (fallback)"
                    
                with st.expander(f"View Preprocessed Text ({method})"):
                    st.write(preprocess_text(user_input))
        else:
            st.warning("Please enter some text to analyze.")

if __name__ == "__main__":
    main()
