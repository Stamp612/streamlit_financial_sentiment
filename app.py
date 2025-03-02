import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf

# Set page configuration
st.set_page_config(
    page_title="Financial Sentiment Analysis",
    page_icon="📊",
    layout="wide"
)

# Force NLTK to download resources and set custom path
@st.cache_resource
def download_nltk_resources():
    # Create a directory for NLTK data if it doesn't exist
    nltk_data_path = os.path.join(os.getcwd(), "nltk_data")
    if not os.path.exists(nltk_data_path):
        os.makedirs(nltk_data_path)
    
    # Add the custom path to NLTK's search paths
    nltk.data.path.append(nltk_data_path)
    
    # Download required NLTK resources with explicit download directory
    try:
        nltk.download('punkt', download_dir=nltk_data_path, quiet=True)
        nltk.download('stopwords', download_dir=nltk_data_path, quiet=True)
        st.success("NLTK resources downloaded successfully!")
    except Exception as e:
        st.error(f"Error downloading NLTK resources: {e}")
    
    # Verify resources were downloaded
    try:
        # Test if resources can be loaded
        from nltk.tokenize import word_tokenize
        word_tokenize("Test sentence")
        from nltk.corpus import stopwords
        stopwords.words('english')
        return True
    except LookupError as e:
        st.error(f"Failed to load NLTK resources: {e}")
        return False

# Ensure NLTK resources are downloaded
nltk_ready = download_nltk_resources()

# Simple tokenizer fallback in case NLTK fails
def simple_tokenize(text):
    return text.split()

# Preprocessing function
@st.cache_data
def preprocess_text(text):
    if not isinstance(text, str):
        return ''
    
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    
    # Use NLTK tokenizer if available, otherwise use simple tokenization
    try:
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
    except:
        st.warning("Using simplified tokenization (NLTK unavailable)")
        tokens = simple_tokenize(text)
        # Use a simple stopword list as fallback
        simple_stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'is', 'are', 'was', 'were'}
        tokens = [token for token in tokens if token not in simple_stopwords]
    
    return ' '.join(tokens)

# Load the DistilBERT model and tokenizer
@st.cache_resource
def load_distilbert_model():
    model_path = 'best_model/transformer_model'
    try:
        model = TFAutoModelForSequenceClassification.from_pretrained(model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        return model, tokenizer
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None

# Predict sentiment
def predict_sentiment(text, model, tokenizer):
    processed_text = preprocess_text(text)
    if not processed_text:
        return "Neutral", 0.0  # Handle empty input gracefully
    inputs = tokenizer(
        processed_text,
        truncation=True,
        padding='max_length',
        max_length=128,
        return_tensors='tf'
    )
    
    try:
        outputs = model(inputs)
        logits = outputs.logits.numpy()
        probs = tf.nn.softmax(logits, axis=1).numpy()[0]
        prediction = np.argmax(probs)
        sentiment = "Positive" if prediction == 1 else "Negative/Neutral"
        confidence = float(probs[prediction])
        return sentiment, confidence
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return "Error", 0.0

# Main function
def main():
    st.title("📊 Financial Sentiment Analysis")
    st.markdown("### Powered by DistilBERT")
    
    model, tokenizer = load_distilbert_model()
    if model is None or tokenizer is None:
        st.error("Failed to load the model. Please check 'best_model/transformer_model'.")
        st.stop()
    
    # User input
    st.subheader("Enter text for sentiment analysis")
    user_input = st.text_area("Type or paste financial text:", height=150)
    
    if st.button("Analyze Sentiment"):
        if user_input.strip():
            with st.spinner("Analyzing sentiment..."):
                sentiment, confidence = predict_sentiment(user_input, model, tokenizer)
                if sentiment == "Positive":
                    st.success(f"Sentiment: {sentiment}")
                elif sentiment == "Negative/Neutral":
                    st.warning(f"Sentiment: {sentiment}")
                else:
                    st.error("An unexpected error occurred.")
                st.info(f"Confidence: {confidence:.2%}")
                # Show preprocessed text
                with st.expander("🔍 View Preprocessed Text"):
                    st.write(preprocess_text(user_input))
        else:
            st.warning("⚠️ Please enter some text to analyze.")

if __name__ == "__main__":
    main()
