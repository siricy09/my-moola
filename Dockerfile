FROM python:3.11-slim

WORKDIR /app

COPY app.py requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Pre-cache TinyLlama model weights
RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
tokenizer = AutoTokenizer.from_pretrained('TinyLlama/TinyLlama-1.1B-Chat-v1.0', cache_dir='/app/model_cache'); \
model = AutoModelForCausalLM.from_pretrained('TinyLlama/TinyLlama-1.1B-Chat-v1.0', cache_dir='/app/model_cache')"

EXPOSE 7860

CMD [ "streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true" ]
