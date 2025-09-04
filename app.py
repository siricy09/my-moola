import streamlit as st
import os
import shutil
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import snapshot_download
import tempfile

st.set_page_config(page_title="MyMoola", layout="wide")

# Custom scrapbook-style CSS + Corner Images + Shimmer title + Sparkling page
page_bg = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600&display=swap');
/* Scrapbook background: dark, graph-paper vibe, and corner images */
[data-testid="stAppViewContainer"] {
    background-color: #0e0e0e;
    background-image:
        url("https://cdn-icons-png.flaticon.com/512/2331/2331941.png"),
        url("https://cdn-icons-png.flaticon.com/512/3135/3135706.png"),
        linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px);
    background-repeat: no-repeat, no-repeat, repeat, repeat;
    background-position: 5% 10%, 95% 90%, 0 0, 0 0;
    background-size: 150px, 150px, 20px 20px, 20px 20px;
    background-attachment: fixed;
    color: #f5f5f5;
    font-family: 'Baloo 2', cursive;
    position: relative;
    overflow: hidden;
}
/* Sparkle container */
.sparkle {
    pointer-events: none;
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    z-index: 9999;
    overflow: visible;
}
.sparkle-dot {
    position: absolute;
    width: 6px;
    height: 6px;
    background: radial-gradient(circle, #fff 60%, transparent 80%);
    border-radius: 50%;
    opacity: 0.6;
    filter: drop-shadow(0 0 3px #fff);
    animation: sparkle-flicker 3s infinite ease-in-out;
}
@keyframes sparkle-flicker {
    0%, 100% {opacity: 0.6;}
    50% {opacity: 0.1;}
}
/* Animate multiple dots with different delays and positions */
.sparkle-dot:nth-child(1) { top: 8%; left: 10%; animation-delay: 0s; }
.sparkle-dot:nth-child(2) { top: 12%; left: 25%; animation-delay: 0.4s; }
.sparkle-dot:nth-child(3) { top: 15%; left: 55%; animation-delay: 0.8s; }
.sparkle-dot:nth-child(4) { top: 20%; left: 45%; animation-delay: 1.2s; }
.sparkle-dot:nth-child(5) { top: 23%; left: 70%; animation-delay: 1.6s; }
.sparkle-dot:nth-child(6) { top: 27%; left: 30%; animation-delay: 2.0s; }
.sparkle-dot:nth-child(7) { top: 30%; left: 80%; animation-delay: 2.4s; }
.sparkle-dot:nth-child(8) { top: 33%; left: 15%; animation-delay: 2.8s; }
.sparkle-dot:nth-child(9) { top: 36%; left: 50%; animation-delay: 3.2s; }
.sparkle-dot:nth-child(10) { top: 40%; left: 65%; animation-delay: 3.6s; }
/* Shimmer animation for heading */
h1 {
    text-align: center;
    font-family: 'Baloo 2', cursive;
    font-size: 3.5rem;
    color: #ffe066;
    text-shadow: 2px 2px #ff6b6b, 4px 4px #1e1e1e;
    position: relative;
    overflow: hidden;
}
h1::before {
    content: "";
    position: absolute;
    top: 0; left: -75%;
    width: 50%;
    height: 100%;
    background: linear-gradient(
        120deg,
        rgba(255,255,255,0) 0%,
        rgba(255,255,255,0.6) 50%,
        rgba(255,255,255,0) 100%
    );
    transform: skewX(-25deg);
    animation: shimmer 2.5s infinite;
}
@keyframes shimmer {
    0% {
        left: -75%;
    }
    100% {
        left: 125%;
    }
}
/* Chat bubbles */
.chat-bubble-user {
    text-align: right;
    background: #ffe066;
    padding: 14px;
    border-radius: 18px;
    margin: 10px;
    display: inline-block;
    max-width: 70%;
    font-family: 'Baloo 2', cursive;
    color: #111;
    box-shadow: 3px 3px 0px #222;
}
.chat-bubble-bot {
    text-align: left;
    background: #7bed9f;
    padding: 14px;
    border-radius: 18px;
    margin: 10px;
    display: inline-block;
    max-width: 70%;
    font-family: 'Baloo 2', cursive;
    color: #111;
    box-shadow: 3px 3px 0px #222;
}
/* Quick buttons styling */
.quick-button {
    background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
    border: none;
    border-radius: 15px;
    padding: 12px 20px;
    color: white;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
    font-size: 1rem;
    margin: 5px;
    box-shadow: 3px 3px 0px #222;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-block;
}
.quick-button:hover {
    transform: translate(-1px, -1px);
    box-shadow: 4px 4px 0px #222;
}
/* Loading spinner */
.loading-moola {
    text-align: center;
    color: #ffe066;
    font-family: 'Baloo 2', cursive;
    font-size: 1.2rem;
    margin: 20px 0;
}
/* Status messages */
.status-success {
    background: linear-gradient(135deg, #7bed9f, #70b3ff);
    color: #111;
    padding: 12px;
    border-radius: 12px;
    margin: 10px 0;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
    box-shadow: 2px 2px 0px #222;
}
.status-info {
    background: linear-gradient(135deg, #70b3ff, #5a9cff);
    color: #111;
    padding: 12px;
    border-radius: 12px;
    margin: 10px 0;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
    box-shadow: 2px 2px 0px #222;
}
.status-warning {
    background: linear-gradient(135deg, #ffa726, #ffb74d);
    color: #111;
    padding: 12px;
    border-radius: 12px;
    margin: 10px 0;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
    box-shadow: 2px 2px 0px #222;
}
/* Chat container */
.chat-container {
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
    margin: 20px 0;
}
/* Calculator cards */
.calculator-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.result-card {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    text-align: center;
    box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    color: #fff;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
}
.needs-card {
    background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
}
.wants-card {
    background: linear-gradient(135deg, #4ecdc4, #44a08d);
}
.savings-card {
    background: linear-gradient(135deg, #45b7d1, #96c93d);
}
.input-container {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    backdrop-filter: blur(5px);
}
.calculator-title {
    color: #ffe066;
    font-family: 'Baloo 2', cursive;
    font-size: 1.8rem;
    text-align: center;
    margin-bottom: 20px;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}
</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

# Load Hugging Face Model (with error handling)
@st.cache_resource(show_spinner=False)
def load_model():
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    # Try multiple cache directory strategies
    cache_options = [
        "./model_cache",  # Original attempt
        os.path.expanduser("~/.cache/huggingface/transformers"),  # Default HF cache
        tempfile.mkdtemp(),  # Temporary directory
        None  # Let HF handle it automatically
    ]
    
    for cache_dir in cache_options:
        try:
            # Clear any existing lock files if using custom cache
            if cache_dir and cache_dir.startswith("./"):
                lock_pattern = os.path.join(cache_dir, "models--TinyLlama--TinyLlama-1.1B-Chat-v1.0", "*.lock")
                import glob
                for lock_file in glob.glob(lock_pattern):
                    try:
                        os.remove(lock_file)
                        st.info(f"Removed stale lock file: {lock_file}")
                    except:
                        pass
            
            # Attempt to load the model
            st.info(f"Trying cache directory: {cache_dir or 'default'}")
            
            if cache_dir:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name, 
                    cache_dir=cache_dir,
                    local_files_only=False,
                    force_download=False
                )
                model = AutoModelForCausalLM.from_pretrained(
                    model_name, 
                    cache_dir=cache_dir,
                    local_files_only=False,
                    force_download=False
                )
            else:
                # Use default HF cache location
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
            
            st.success(f"Model loaded successfully using cache: {cache_dir or 'default'}")
            return tokenizer, model
            
        except Exception as e:
            st.warning(f"Failed with cache {cache_dir or 'default'}: {str(e)}")
            continue
    
    # If all cache options fail, try downloading without cache
    try:
        st.info("Attempting direct download without cache...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=None)
        model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=None)
        return tokenizer, model
    except Exception as e:
        st.error(f"All loading attempts failed. Error: {str(e)}")
        st.error("Please check your internet connection and try again.")
        st.stop()

# Alternative: Load smaller model if TinyLlama fails
@st.cache_resource(show_spinner=False)
def load_fallback_model():
    """Load an even smaller model as fallback"""
    try:
        model_name = "microsoft/DialoGPT-small"  # Smaller alternative
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        return tokenizer, model
    except Exception as e:
        st.error(f"Fallback model also failed: {str(e)}")
        return None, None

# Generate Response
def generate_response(user_input, tokenizer, model):
    if not tokenizer or not model:
        return "Sorry, the model is not available. Please refresh and try again."
    
    try:
        # Create a more detailed and specific prompt for financial advice
        financial_context = """You are MyMoola, an expert financial advisor. Provide accurate, helpful financial advice in bullet point format.

IMPORTANT FORMATTING RULES:
- Use bullet points for all key information
- Keep each bullet point short (1-2 lines max)
- Provide 5-8 bullet points total
- Include specific numbers/amounts when relevant

CONTENT GUIDELINES:
- If asked about SIP, explain Systematic Investment Plan with practical steps
- If asked about stocks, provide actionable stock market advice
- Focus on Indian financial context (Rupees, Indian products)
- Give practical, actionable advice
- Use simple, clear language

FORMAT EXAMPLE:
**Topic Name**
• Point 1 with specific detail
• Point 2 with actionable step  
• Point 3 with example/number

Remember: Be concise, practical, and use bullet points always."""

        prompt = f"<|system|>\n{financial_context}\n<|user|>\n{user_input}\n<|assistant|>\n"
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        
        with st.spinner("AI is thinking..."):
            outputs = model.generate(
                **inputs,
                max_new_tokens=250,  # Increased to avoid cutoff
                do_sample=True,
                temperature=0.7,  # Slightly higher for more variety
                top_p=0.9,
                repetition_penalty=1.2,  # Higher to reduce repetition
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                early_stopping=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
        # Clean up the response further
        response = clean_response(response, user_input)
        
        return response
    
    except Exception as e:
        return f"Sorry, I encountered an error generating a response: {str(e)}"

def clean_response(response, user_input):
    """Clean and improve the AI response"""
    
    # Remove any remaining system prompts or artifacts
    response = response.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
    
    # Handle specific financial terms that might be confused
    user_lower = user_input.lower()
    
    if "sip" in user_lower and "chatbot" in response.lower():
        # If the AI confused SIP with a chatbot, provide correct SIP definition
        return """**SIP (Systematic Investment Plan)**

• **What it is**: Regular monthly investment in mutual funds (min Rs.500)
• **Key Benefit**: Rupee cost averaging - buy more units when price is low
• **How to start**: Choose fund → Set amount → Auto-debit monthly
• **Best duration**: 3+ years for optimal returns
• **Returns**: 10-12% annually (equity funds, long-term)
• **Tax benefit**: ELSS funds save tax under 80C
• **Perfect for**: Retirement, child education, wealth building
• **Pro tip**: Start with Rs.1000/month, increase 10% yearly"""

    if "stock trading" in user_lower and len(response) < 50:
        # If response is too short for stock trading, provide comprehensive answer
        return """**Stock Trading Basics for Beginners:**

• **Start with Education**: Learn fundamental & technical analysis
• **Open Accounts**: Demat & Trading account with broker
• **Start Small**: Begin with Rs.10,000-Rs.50,000
• **Choose Blue-chip**: Start with TCS, Reliance, HDFC Bank
• **Set Rules**: Never invest borrowed money, diversify sectors
• **Stop-loss**: Set limits to minimize losses
• **Investment vs Trading**: Buy & hold for years (safer) vs frequent trading (riskier)
• **Beginner Tip**: Start with SIP in index funds before individual stocks"""
    
    # Remove any references to "MyMoola app" or similar generic responses
    problematic_phrases = [
        "mymoola app", "logging in with", "chatbot designed", "available on the", 
        "app and can be accessed", "mobile number", "email address", 
        "personalized financial advice based on your", "helps you save money and invest wisely"
    ]
    
    if any(phrase in response.lower() for phrase in problematic_phrases):
        return generate_fallback_response(user_input)
    
    # Validate response relevance
    if len(response.strip()) < 20:
        return generate_fallback_response(user_input)
    
    # If response doesn't seem to address the financial question, use fallback
    financial_keywords = ["invest", "money", "fund", "saving", "budget", "loan", "financial", "rupee", "rs.", "%", "return"]
    if not any(keyword in response.lower() for keyword in financial_keywords) and len(user_input) > 10:
        return generate_fallback_response(user_input)
    
    return response

def generate_fallback_response(user_input):
    """Generate appropriate fallback responses for common financial questions"""
    user_lower = user_input.lower()
    
    fallback_responses = {
        "sip": """**SIP (Systematic Investment Plan)**

• **What it is**: Regular monthly investment in mutual funds (min Rs.500)
• **Key Benefit**: Rupee cost averaging - buy more units when price is low
• **How to start**: Choose fund → Set amount → Auto-debit monthly
• **Best duration**: 3+ years for optimal returns
• **Returns**: 10-12% annually (equity funds, long-term)
• **Tax benefit**: ELSS funds save tax under 80C
• **Perfect for**: Retirement, child education, wealth building
• **Pro tip**: Start with Rs.1000/month, increase 10% yearly""",
        
        "mutual fund": """**Mutual Funds**

• **What it is**: Pool money from many investors to buy stocks/bonds
• **Types**: Equity (stocks), Debt (bonds), Hybrid (mixed)
• **Minimum**: Start with Rs.500/month via SIP
• **Returns**: 10-12% annually (equity funds, long-term)
• **Benefits**: Professional management, instant diversification
• **Liquidity**: Redeem anytime (except ELSS - 3yr lock)
• **Best for beginners**: Large cap or index funds
• **Tax**: Long-term gains >Rs.1L taxed at 10%""",
        
        "emergency fund": """**Emergency Fund** is your financial safety net:

• **Amount**: 6-12 months of expenses
• **Where**: High-yield savings account or liquid funds
• **Use**: Medical emergencies, job loss, urgent repairs
• **Build**: Start with Rs.1000/month, automate it""",
        
        "budget": """**Budgeting Made Simple**:

• **50-30-20 Rule**: 50% needs, 30% wants, 20% savings
• **Track**: Use apps or simple Excel sheet
• **Categories**: Housing, food, transport, entertainment
• **Review**: Monthly check and adjust as needed""",
        
        "credit score": """**Credit Score** ranges from 300-850:

• **750+**: Excellent - Best loan rates
• **700-749**: Good - Most loans approved
• **650-699**: Fair - Higher interest rates
• **Below 650**: Poor - Limited options
• **Improve**: Pay on time, keep utilization <30%, don't close old cards""",
        
        "insurance": """**Insurance Basics**:

• **Term Life**: High coverage, low premium (Rs.50L for Rs.1000/month)
• **Health**: Medical expenses coverage (Rs.5-10L minimum)
• **General**: Car, home, travel insurance
• **Rule**: Life insurance = 10-15x annual income""",
        
        "tax saving": """**Tax Saving Options (80C)**:

• **ELSS Mutual Funds**: Best returns + tax saving
• **PPF**: 15-year lock-in, tax-free returns
• **EPF**: Employer contribution matching
• **Home Loan**: Principal repayment saves tax
• **Limit**: Rs.1.5L per year under 80C"""
    }
    
    # Check for multiple keywords
    for key, response in fallback_responses.items():
        if key in user_lower:
            return response
    
    # Check for related terms
    if any(term in user_lower for term in ["invest", "investment", "return"]):
        return """**Investment Options for Beginners**:

• **Best for Beginners**: SIP in diversified mutual funds
• **Safe Options**: PPF, NSC, Bank FDs
• **Market Linked**: Mutual funds, stocks, ETFs
• **Real Estate**: REITs for small amounts
• **Golden Rule**: Start early, invest regularly, stay patient!"""
    
    if any(term in user_lower for term in ["loan", "emi", "debt"]):
        return """**Loan & Debt Management**:

• **Repayment Strategy**: Pay high-interest debts first
• **EMI Rule**: Total EMIs shouldn't exceed 40% of income
• **Home Loan**: Longest tenure, lowest rates
• **Personal Loan**: Avoid unless emergency
• **Tip**: Extra payments toward principal save huge interest!"""
    
    return "I'd be happy to help with your financial question! Could you please be more specific about what you'd like to know? I can help with topics like investments, budgeting, savings, SIP, mutual funds, insurance, loans, and more."

# Clear Cache Function
def clear_model_cache():
    """Clear the model cache to resolve permission issues"""
    cache_paths = [
        "./model_cache",
        os.path.expanduser("~/.cache/huggingface/transformers")
    ]
    
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                shutil.rmtree(cache_path)
                st.success(f"Cleared cache: {cache_path}")
            except Exception as e:
                st.warning(f"Could not clear {cache_path}: {str(e)}")

# Sparkle dots
sparkle_html = """
<div class="sparkle">
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
    <div class="sparkle-dot"></div>
</div>
"""
st.markdown(sparkle_html, unsafe_allow_html=True)

# Add cache management
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Clear Cache"):
        clear_model_cache()
        st.cache_resource.clear()
        st.experimental_rerun()

# Model loading with better error handling
try:
    with st.spinner("Loading TinyLLaMA model (first time may take a minute)..."):
        tokenizer, model = load_model()
        
    if tokenizer and model:
        st.success("Model loaded and ready to chat!")
    else:
        st.warning("Primary model failed. Trying fallback...")
        with st.spinner("Loading fallback model..."):
            tokenizer, model = load_fallback_model()
            if tokenizer and model:
                st.info("Fallback model loaded successfully!")
except Exception as e:
    st.error(f"Model loading failed: {str(e)}")
    st.info("**Troubleshooting Tips:**")
    st.info("1. Try clicking 'Clear Cache' button above")
    st.info("2. Check your internet connection")
    st.info("3. Wait a few minutes and refresh the page")
    st.stop()

# Title with shimmer effect
st.markdown("<h1>MyMoola - Your Finance Buddy</h1>", unsafe_allow_html=True)

# 50/30/20 Calculator Function
def calculate_50_30_20(income, current_expenses=0):
    """Calculate 50/30/20 budget breakdown"""
    available_income = max(0, income - current_expenses)
    
    needs = available_income * 0.50
    wants = available_income * 0.30
    savings = available_income * 0.20
    
    return {
        'available_income': available_income,
        'needs': needs,
        'wants': wants,
        'savings': savings,
        'needs_percentage': 50,
        'wants_percentage': 30,
        'savings_percentage': 20
    }

# Quick Calculator Section
st.markdown("### Quick Calculator")

# Add tabs for different calculators
tab1, tab2 = st.tabs(["50/30/20 Budget Calculator", "Ask AI Questions"])

with tab1:
    st.markdown('<div class="calculator-card">', unsafe_allow_html=True)
    st.markdown('<div class="calculator-title">50/30/20 Budget Calculator</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        monthly_income = st.number_input(
            "Monthly Income (Rs.)", 
            min_value=0, 
            value=50000, 
            step=1000,
            help="Enter your total monthly income"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        current_expenses = st.number_input(
            "Current Fixed Expenses (Rs.)", 
            min_value=0, 
            value=0, 
            step=1000,
            help="Enter your current unavoidable expenses (if any)"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("Calculate Budget Breakdown", type="primary"):
        if monthly_income > 0:
            result = calculate_50_30_20(monthly_income, current_expenses)
            
            st.markdown("#### Your Budget Breakdown:")
            
            # Display results in beautiful cards
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f'''
                <div class="result-card needs-card">
                    <h3>50% NEEDS</h3>
                    <h2>Rs. {result['needs']:,.0f}</h2>
                    <p>Rent, utilities, groceries, minimum debt payments</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div class="result-card wants-card">
                    <h3>30% WANTS</h3>
                    <h2>Rs. {result['wants']:,.0f}</h2>
                    <p>Entertainment, dining out, hobbies, shopping</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'''
                <div class="result-card savings-card">
                    <h3>20% SAVINGS</h3>
                    <h2>Rs. {result['savings']:,.0f}</h2>
                    <p>Emergency fund, investments, retirement</p>
                </div>
                ''', unsafe_allow_html=True)
            
            # Additional insights
            st.markdown("#### Smart Tips:")
            tips_col1, tips_col2 = st.columns(2)
            
            with tips_col1:
                st.info(f"""
                **Automate Your Savings**
                Set up automatic transfer of Rs. {result['savings']:,.0f} to a separate savings account on payday.
                """)
            
            with tips_col2:
                st.success(f"""
                **Emergency Fund Goal**
                Build 6 months of expenses: Rs. {result['needs'] * 6:,.0f} using your 20% savings.
                """)
            
            if result['available_income'] < monthly_income:
                st.warning(f"""
                **Note:** After fixed expenses of Rs. {current_expenses:,}, you have Rs. {result['available_income']:,} available for the 50/30/20 allocation.
                """)
        else:
            st.error("Please enter a valid monthly income amount.")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    # Example questions
    st.header("Try Example Questions")
    cols = st.columns(2)
    if cols[0].button("What is the 50/30/20 rule?"):
        st.session_state.setdefault("chat_history", [])
        bot_response = generate_response("What is the 50/30/20 rule?", tokenizer, model)
        st.session_state.chat_history.append({"user": "What is the 50/30/20 rule?", "bot": bot_response})

    if cols[1].button("How do I start an emergency fund?"):
        st.session_state.setdefault("chat_history", [])
        bot_response = generate_response("How do I start an emergency fund?", tokenizer, model)
        st.session_state.chat_history.append({"user": "How do I start an emergency fund?", "bot": bot_response})

    # Additional example questions
    cols2 = st.columns(2)
    if cols2[0].button("What's a good credit score?"):
        st.session_state.setdefault("chat_history", [])
        bot_response = generate_response("What's a good credit score?", tokenizer, model)
        st.session_state.chat_history.append({"user": "What's a good credit score?", "bot": bot_response})

    if cols2[1].button("How to invest Rs.1000?"):
        st.session_state.setdefault("chat_history", [])
        bot_response = generate_response("How should I invest Rs.1000?", tokenizer, model)
        st.session_state.chat_history.append({"user": "How should I invest Rs.1000?", "bot": bot_response})

# User input
st.subheader("Ask Your Own Question")
user_input = st.text_input("Type your financial question here:", placeholder="e.g., How do I budget my salary?")
if user_input:
    st.session_state.setdefault("chat_history", [])
    bot_response = generate_response(user_input, tokenizer, model)
    st.session_state.chat_history.append({"user": user_input, "bot": bot_response})

# Display chat history
if "chat_history" in st.session_state and st.session_state.chat_history:
    st.header("Chat History")
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5 chats
        st.markdown(f"<div style='text-align: right;'><div class='chat-bubble-user'><b>You:</b> {chat['user']}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: left;'><div class='chat-bubble-bot'><b>MyMoola:</b> {chat['bot']}</div></div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
# Add footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #ffe066; font-family: "Baloo 2", cursive; margin-top: 30px;'>
    <p><b>MyMoola</b> - Making financial literacy fun and accessible!</p>
    <p style='font-size: 0.8rem; color: #ccc;'>
        <i>Disclaimer: This is for educational purposes. Always consult with a financial advisor for personalized advice.</i>
    </p>
</div>
""", unsafe_allow_html=True)