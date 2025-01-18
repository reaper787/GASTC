import firebase_admin
import json
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from waitress import serve
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.googlesearch import GoogleSearch
from phi.tools.yfinance import YFinanceTools

_=load_dotenv(find_dotenv())
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY')
)

model = "gpt-4o-mini"
temperature = 0.7
max_tokens = 1500

cred = credentials.Certificate(json.loads(os.environ.get('FIRESTORE_CONFIG')))
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__, static_folder="Static", template_folder='Templates')

CORS(app)

def getResponse(messages):
    completion = client.chat.completions.create(
        model = model,
        temperature = temperature,
        max_tokens= max_tokens,
        messages = messages

    )
    return completion.choices[0].message.content

@app.route('/prompt', methods=['POST'])
def handle_login():
    data = request.json
    company_name = data.get('companyName')

    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400

    print(f"Company name received: {company_name}")

    doc_ref = db.collection('businessInfo').document(company_name)
    doc = doc_ref.get()

    if doc.exists:
        doc_dict = doc.to_dict()
        visits = doc_dict.get('visits', 0)

        # Convert visits to integer and handle None/invalid values
        try:
            visits = int(visits)
        except (ValueError, TypeError):
            visits = 0

        # Always increment visits
        doc_ref.update({
            "visits": visits + 1
        })

        # Generate prompt for first-time users
        if visits == 0:
            # Extract all the values
            industry = doc_dict.get('industry')
            startup_cost = doc_dict.get('startupCost')
            product_list = doc_dict.get('productList')
            product_details = doc_dict.get('productDetails')
            product_prices = doc_dict.get('productPrices')
            cost_make = doc_dict.get('costToMake')
            sell_price = doc_dict.get('sellPrice')
            product_description = doc_dict.get('productDescription')
            help_needed = doc_dict.get('helpNeeded')
            why_buy = doc_dict.get('whyBuy')
            self_description = doc_dict.get('selfDescription')
            target_audience = doc_dict.get('targetAudience')

            # Construct the prompt with the variables
            prompt = f"""create a start up template and plan using the following details. Perenthesis mean that it was inputed from a form submitted by the buisness owner.
            My business is in the ({industry}) industry. 
            It will cost ({startup_cost}) to start this business. 
            My company name is ({company_name}). 
            Here are some details about my product/s with the prices and how much it costs me to make: cost to make my best product:({cost_make}) and i'm selling it for this much: ({sell_price}), some details about my products: ({product_details}) cost to make all my products: ({product_prices})
            The central theme around all of my product/s is/are: ({product_description})
            I need help on this: ({help_needed}). 
            This is why people should buy my product/s: ({why_buy})
            I am selling my product/s to these type of people: ({target_audience})
            Make sure it is easy for a/n ({self_description}) to understand. 

            Give me tips using information from reliable sources from people with experience in the area. 
            Exclude information from reddit, Quora and other sources where random people are writing. 
            Use very reliable sources to give the information. 
            Do not state that you found it from these resources in the template. 
            Make sure to give key ideas such as marketing and expert techniques for the best result. 
            In the template, add a final section called Tips. Give information that should be helpful to their company. Make the tips specifically for MY company. 
            Make it easy and convenient for me to read.
            If my company has any issues that make it hard for success, analyze and give me a better way to do it. 
            Problems like selling cost and profit makes it harder for people to choose because it's expensive. 
            Try to find a problem in the company and make it better. 
            Analyze what's on the market and state all of the competitors in the area and try to make MY company better. 
            Include at the very end a market research analysis.
            Try to customize the template in marketing based on my product. If I have cars as my product, use different marketing ideas that will help increase sales toward cars. 
            Tell me a reliable and efficient way in marketing to get more sales. I want this marketing strategy to be efficient and effective based on only MY company and the information I GAVE you.
            Don't restate any information I told you
            Add when I will break even to pay off how much money I used to start the company.
            Try to add any financial advice from Alex Hormozi, Warren Buffet, Reid Hoffman, Mark Cuban and other successful entrepreneurs.
            Do not say it is from any of those entrepreneurs
            Conduct research on all similar products to mine. Try to perfect my price based on other prices.
            Make sure to advise all of my products. Don't advise only one.
            THIS IS THE MOST IMPORTANT PART. MAKE SURE TO ANSWER MY QUESTION AND CONCERNS AND AT THE VERY END, GIVE A TO-DO LIST IF YOU THINK IT IS NECESSARY
            MAKE SURE EVERY TINY LITTLE PART OF THE PROMPT IS RELIABLE INFORMATION THAT HAS BEEN TESTED.
            SHARE DETAILS ABOUT THE EXPECTED GROWTH AND HOW MANY EMPLOYEES THAT ARE EXPECTED TO HIRE AND IN ABOUT HOW LONg WILL I BREAK EVEN BASED ON THIS PROMPT AND DETAILS ABOUT COMPETITORS IN SIMMILAR FEILDS
            AND DONT REPEAT INFORMATION.
            """

            messages = [
                {"role": "user", "content": prompt},
            ]

            buisness_plan = getResponse(messages)

            doc_ref.update({
                "prompt": prompt,
                "buisnessPlan": buisness_plan,
            })

        return jsonify({'message': f"Company name {company_name} exists", 'data': doc_dict}), 200

    else:
        print('Company doesn\'t exist')
        return jsonify({'error': 'Company doesn\'t Exists'}), 404
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login_form():
    return render_template('Login.html')

@app.route('/signup')
def signup():
    return render_template('Signup.html')

@app.route('/plan')
def plan():
    return render_template('plan.html')

@app.route('/market', methods=['GET', 'POST'])
def market():
    '''
    doc_ref = db.collection('businessInfo').document(company_name)
    doc = doc_ref.get()
    doc_dict = doc.to_dict()

    industry = doc_dict.get('industry')

    ## Create Agents (from GITHUB) https://github.com/deepcharts/projects/blob/main/stock_sentiment_agents.ipynb

    # Sentiment Agent
    sentiment_agent = Agent(
        name="Sentiment Agent",
        role="Search and interpret news articles.",
        model=OpenAIChat(id="gpt-4o"),
        tools=[GoogleSearch()],
        instructions=[
            "Find relevant news articles for each company and analyze the sentiment.",
            "Provide sentiment scores from 1 (negative) to 10 (positive) with reasoning and sources."
            "Cite your sources. Be specific and provide links."
        ],
        show_tool_calls=True,
        markdown=True,
    )

    # Finance Agent
    finance_agent = Agent(
        name="Finance Agent",
        role="Get financial data and interpret trends.",
        model=OpenAIChat(id="gpt-4o"),
        tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
        instructions=[
            "Retrieve stock prices, analyst recommendations, and key financial data.",
            "Focus on trends and present the data in tables with key insights."
        ],
        show_tool_calls=True,
        markdown=True,
    )

    # Analyst Agent
    analyst_agent = Agent(
        name="Analyst Agent",
        role="Ensure thoroughness and draw conclusions.",
        model=OpenAIChat(id="gpt-4o"),
        instructions=[
            "Check outputs for accuracy and completeness.",
            "Synthesize data to provide a final sentiment score (1-10) with justification."
        ],
        show_tool_calls=True,
        markdown=True,
    )

    # Team of Agents
    agent_team = Agent(
        model=OpenAIChat(id="gpt-4o"),
        team=[sentiment_agent, finance_agent, analyst_agent],
        instructions=[
            "Combine the expertise of all agents to provide a cohesive, well-supported response.",
            "Always include references and dates for all data points and sources.",
            "Present all data in structured tables for clarity.",
            "Explain the methodology used to arrive at the sentiment scores."
        ],
        show_tool_calls=True,
        markdown=True,
    )

    ## Run Agent Team
    # Final Prompt
    response = agent_team.run(
        f"Analyze the sentiment for the top companies in this industry: {industry} today. \n\n"
        "1. **Sentiment Analysis**: Search for relevant news articles and interpret th–e sentiment for each company. Provide sentiment scores on a scale of 1 to 10, explain your reasoning, and cite your sources.\n\n"
        "2. **Financial Data**: Analyze stock price movements, analyst recommendations, and any notable financial data. Highlight key trends or events, and present the data in tables.\n\n"
        "3. **Consolidated Analysis**: Combine the insights from sentiment analysis and financial data to assign a final sentiment score (1-10) for each company. Justify the scores and provide a summary of the most important findings.\n\n"
        "Ensure your response is accurate, comprehensive, and includes references to sources with publication dates.",
        stream=True
    )
    '''
    return render_template('market.html')




if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
