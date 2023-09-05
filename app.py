import json
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import logging
import requests
import openai
from flask import Flask, Response, request, jsonify, send_from_directory
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from azure.core.credentials import AzureKeyCredential
import app

load_dotenv()

app = Flask(__name__, static_folder="static")
app.debug = True
# Static Files
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('favicon.ico')

@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory("static/assets", path)


# ACS Integration Settings
AZURE_SEARCH_SERVICE = os.environ.get("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX")
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")
AZURE_SEARCH_USE_SEMANTIC_SEARCH =os.environ.get("AZURE_SEARCH_USE_SEMANTIC_SEARCH", "false")
AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG =os.environ.get("AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG", "default")
AZURE_SEARCH_TOP_K = os.environ.get("AZURE_SEARCH_TOP_K", 5)
AZURE_SEARCH_ENABLE_IN_DOMAIN =os.environ.get("AZURE_SEARCH_ENABLE_IN_DOMAIN", "true")
AZURE_SEARCH_CONTENT_COLUMNS =os.environ.get("AZURE_SEARCH_CONTENT_COLUMNS")
AZURE_SEARCH_FILENAME_COLUMN =os.environ.get("AZURE_SEARCH_FILENAME_COLUMN")
AZURE_SEARCH_TITLE_COLUMN =os.environ.get("AZURE_SEARCH_TITLE_COLUMN")
AZURE_SEARCH_URL_COLUMN = os.environ.get("AZURE_SEARCH_URL_COLUMN")

# AOAI Integration Settings
AZURE_OPENAI_RESOURCE = os.environ.get("AZURE_OPENAI_RESOURCE")
AZURE_OPENAI_MODEL = os.environ.get("AZURE_OPENAI_MODEL")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_TEMPERATURE = os.environ.get("AZURE_OPENAI_TEMPERATURE", 0)
AZURE_OPENAI_TOP_P = os.environ.get("AZURE_OPENAI_TOP_P", 1.0)
AZURE_OPENAI_MAX_TOKENS =os.environ.get("AZURE_OPENAI_MAX_TOKENS", 1000)
AZURE_OPENAI_STOP_SEQUENCE =os.environ.get("AZURE_OPENAI_STOP_SEQUENCE")
AZURE_OPENAI_SYSTEM_MESSAGE = os.environ.get("AZURE_OPENAI_SYSTEM_MESSAGE", "You are an AI assistant that helps people find information.")
AZURE_OPENAI_PREVIEW_API_VERSION =os.environ.get("AZURE_OPENAI_PREVIEW_API_VERSION", "2023-06-01-preview")
AZURE_OPENAI_STREAM =os.environ.get("AZURE_OPENAI_STREAM", "true")
AZURE_OPENAI_MODEL_NAME =os.environ.get("AZURE_OPENAI_MODEL_NAME", "gpt-35-turbo") # Name of the model, e.g. 'gpt-35-turbo' or 'gpt-4'

#ALS Integration Settings
AZURE_LANGUAGE_ENDPOINT = os.environ.get("AZURE_LANGUAGE_ENDPOINT")
AZURE_LANGUAGE_KEY = os.environ.get("AZURE_LANGUAGE_KEY")

SHOULD_STREAM = True if AZURE_OPENAI_STREAM.lower() == "true" else False

messages = [
        {
            "role": "system",
            "content": AZURE_OPENAI_SYSTEM_MESSAGE
        }
    ]

def is_chat_model():
    if 'gpt-4' in AZURE_OPENAI_MODEL_NAME.lower() or AZURE_OPENAI_MODEL_NAME.lower() in ['gpt-35-turbo-4k', 'gpt-35-turbo-16k']:
        return True
    return False

def should_use_data():
    if AZURE_SEARCH_SERVICE and AZURE_SEARCH_INDEX and AZURE_SEARCH_KEY:
        return True
    return False

def should_use_data_elastic(request):
    request_messages = request.json["messages"]
    length=len(request_messages)
    question=request_messages[length-1]['content']
    es = Elasticsearch('http://localhost:9200')
    inputtext = question
    resp = es.search(index="kxgenaiindex",size=1, query={"multi_match" : {
            "query" : "{}".format(inputtext),
            "fields": ["attachmenttext1"]
        }})
    output = ""
    #print("Got %d Hits:" % resp['hits']['total']['value'])
    for hit in resp['hits']['hits']:
        #print("%(id)s %(attachmenttext1)s: %(documentid)s" % hit["_source"])
        output = "%(attachmenttext1)s" % hit["_source"]
        #print("%(id)s %(attachmenttext1)s" % hit["_source"])
    if output=="":
        return False
    else:
        return True

def prepare_body_headers_with_data(request):
    request_messages = request.json["messages"]

    body = {
        "messages": request_messages,
        "temperature": float(AZURE_OPENAI_TEMPERATURE),
        "max_tokens": int(AZURE_OPENAI_MAX_TOKENS),
        "top_p": float(AZURE_OPENAI_TOP_P),
        "stop": AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        "stream": SHOULD_STREAM,
        "dataSources": [
            {
                "type": "AzureCognitiveSearch",
                "parameters": {
                    "endpoint": f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
                    "key": AZURE_SEARCH_KEY,
                    "indexName": AZURE_SEARCH_INDEX,
                    "fieldsMapping": {
                        "contentField": AZURE_SEARCH_CONTENT_COLUMNS.split("|") if AZURE_SEARCH_CONTENT_COLUMNS else [],
                        "titleField": AZURE_SEARCH_TITLE_COLUMN if AZURE_SEARCH_TITLE_COLUMN else None,
                        "urlField": AZURE_SEARCH_URL_COLUMN if AZURE_SEARCH_URL_COLUMN else None,
                        "filepathField": AZURE_SEARCH_FILENAME_COLUMN if AZURE_SEARCH_FILENAME_COLUMN else None
                    },
                    "inScope": True if AZURE_SEARCH_ENABLE_IN_DOMAIN.lower() == "true" else False,
                    "topNDocuments": AZURE_SEARCH_TOP_K,
                    "queryType": "semantic" if AZURE_SEARCH_USE_SEMANTIC_SEARCH.lower() == "true" else "simple",
                    "semanticConfiguration": AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG if AZURE_SEARCH_USE_SEMANTIC_SEARCH.lower() == "true" and AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG else "",
                    "roleInformation": AZURE_OPENAI_SYSTEM_MESSAGE
                }
            }
        ]
    }

    chatgpt_url = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/openai/deployments/{AZURE_OPENAI_MODEL}"
    if is_chat_model():
        chatgpt_url += "/chat/completions?api-version=2023-03-15-preview"
    else:
        chatgpt_url += "/completions?api-version=2023-03-15-preview"

    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_OPENAI_KEY,
        'chatgpt_url': chatgpt_url,
        'chatgpt_key': AZURE_OPENAI_KEY,
        "x-ms-useragent": "GitHubSampleWebApp/PublicAPI/1.0.0"
    }

    return body, headers


def stream_with_data(body, headers, endpoint):
    s = requests.Session()
    response = {
        "id": "",
        "model": "",
        "created": 0,
        "object": "",
        "choices": [{
            "messages": []
        }]
    }
    try:
        with s.post(endpoint, json=body, headers=headers, stream=True) as r:
            for line in r.iter_lines(chunk_size=10):
                if line:
                    lineJson = json.loads(line.lstrip(b'data:').decode('utf-8'))
                    if 'error' in lineJson:
                        yield json.dumps(lineJson).replace("\n", "\\n") + "\n"
                    response["id"] = lineJson["id"]
                    response["model"] = lineJson["model"]
                    response["created"] = lineJson["created"]
                    response["object"] = lineJson["object"]

                    role = lineJson["choices"][0]["messages"][0]["delta"].get("role")
                    if role == "tool":
                        response["choices"][0]["messages"].append(lineJson["choices"][0]["messages"][0]["delta"])
                    elif role == "assistant": 
                        response["choices"][0]["messages"].append({
                            "role": "assistant",
                            "content": ""
                        })
                    else:
                        deltaText = lineJson["choices"][0]["messages"][0]["delta"]["content"]
                        if deltaText != "[DONE]":
                            response["choices"][0]["messages"][1]["content"] += deltaText

                    yield json.dumps(response).replace("\n", "\\n") + "\n"
    except Exception as e:
        yield json.dumps({"error": str(e)}).replace("\n", "\\n") + "\n"

def stream_without_data(response):
    responseText = ""
    for line in response:
        deltaText = line["choices"][0]["delta"].get('content')
        if deltaText and deltaText != "[DONE]":
            responseText += deltaText

        response_obj = {
            "id": line["id"],
            "model": line["model"],
            "created": line["created"],
            "object": line["object"],
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": responseText
                }]
            }]
        }
        yield json.dumps(response_obj).replace("\n", "\\n") + "\n"


def conversation_with_data(request):
    body, headers = prepare_body_headers_with_data(request)
    endpoint = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/openai/deployments/{AZURE_OPENAI_MODEL}/extensions/chat/completions?api-version={AZURE_OPENAI_PREVIEW_API_VERSION}"
    
    if not SHOULD_STREAM:
        r = requests.post(endpoint, headers=headers, json=body)
        status_code = r.status_code
        r = r.json()

        return Response(json.dumps(r).replace("\n", "\\n"), status=status_code)
    else:
        if request.method == "POST":
            return Response(stream_with_data(body, headers, endpoint), mimetype='text/event-stream')
        else:
            return Response(None, mimetype='text/event-stream')
                

def data_from_elastic(test):
    es = Elasticsearch('http://localhost:9200')
    inputtext = test
    resp = es.search(index="kxgenaiindex",size=1, query={"multi_match" : {
            "query" : "{}".format(inputtext),
            "fields": ["attachmenttext1"]
        }})
    output = ""
    #print("Got %d Hits:" % resp['hits']['total']['value'])
    for hit in resp['hits']['hits']:
        #print("%(id)s %(attachmenttext1)s: %(documentid)s" % hit["_source"])
        output = "%(attachmenttext1)s" % hit["_source"]
        #print("%(id)s %(attachmenttext1)s" % hit["_source"])
    return output

def stream_with_data_elastic(response,question):
    responseText=data_from_elastic(question)
    for line in response:
        response_obj = {
            "id": line["id"],
            "model": line["model"],
            "created": line["created"],
            "object": line["object"],
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": responseText
                }]
            }]
        }
        yield json.dumps(response_obj).replace("\n", "\\n") + "\n"


def stream_without_data_elastic(response):
    responseText = ""
    for line in response:
        deltaText = line["choices"][0]["delta"].get('content')
        if deltaText and deltaText != "[DONE]":
            responseText += deltaText

        response_obj = {
            "id": line["id"],
            "model": line["model"],
            "created": line["created"],
            "object": line["object"],
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": responseText
                }]
            }]
        }
        yield json.dumps(response_obj).replace("\n", "\\n") + "\n"

def summarize_data(request):
    openai.api_type = "azure"
    openai.api_base = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/"
    openai.api_version = "2022-12-01"
    openai.api_key = AZURE_OPENAI_KEY
    response = openai.Completion.create(
        engine="gpt35_1",
        prompt="Provide a summary of the text below that captures its main idea. \n\n"+request,
        temperature=0,
        max_tokens=250,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
    print(response)
    response_obj = {
            "id": response.id,
            "object": response.object,
            "created": response.created,
            "model": response.model,
            "content": response.choices[0].text}
    print(response_obj)
    return jsonify(response_obj), 200


def conversation_without_data(request):
    openai.api_type = "azure"
    openai.api_base = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/"
    openai.api_version = "2023-03-15-preview"
    openai.api_key = AZURE_OPENAI_KEY
    request_messages = request.json["messages"]

    for message in request_messages:
        messages.append({
            "role": message["role"] ,
            "content": message["content"]
        })

    response = openai.ChatCompletion.create(
        engine=AZURE_OPENAI_MODEL,
        messages = messages,
        temperature=float(AZURE_OPENAI_TEMPERATURE),
        max_tokens=int(AZURE_OPENAI_MAX_TOKENS),
        top_p=float(AZURE_OPENAI_TOP_P),
        stop=AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        stream=SHOULD_STREAM
    )

    if not SHOULD_STREAM:
        response_obj = {
            "id": response,
            "model": response.model,
            "created": response.created,
            "object": response.object,
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": response.choices[0].message.content
                }]
            }]
        }
        return jsonify(response_obj), 200
    else:
        if request.method == "POST":
            return Response(stream_without_data(response), mimetype='text/event-stream')
        else:
            return Response(None, mimetype='text/event-stream')

def conversation_without_data_elastic(request):
    openai.api_type = "azure"
    openai.api_base = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/"
    openai.api_version = "2023-03-15-preview"
    openai.api_key = AZURE_OPENAI_KEY

    request_messages = request.json["messages"]
    messages = [
        {
            "role": "system",
            "content": AZURE_OPENAI_SYSTEM_MESSAGE
        }
    ]

    for message in request_messages:
        messages.append({
            "role": message["role"] ,
            "content": message["content"]
        })
    print(messages)
    response = openai.ChatCompletion.create(
        engine=AZURE_OPENAI_MODEL,
        messages = messages,
        temperature=float(AZURE_OPENAI_TEMPERATURE),
        max_tokens=int(AZURE_OPENAI_MAX_TOKENS),
        top_p=float(AZURE_OPENAI_TOP_P),
        stop=AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        stream=SHOULD_STREAM
    )
    if not SHOULD_STREAM:
        response_obj = {
            "id": response,
            "model": response.model,
            "created": response.created,
            "object": response.object,
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": response.choices[0].message.content
                }]
            }]
        }

        return jsonify(response_obj), 200
    else:
        if request.method == "POST":
            return Response(stream_without_data_elastic(response), mimetype='text/event-stream')
        else:
            return Response(None, mimetype='text/event-stream')
        
def conversation_with_data_elastic(request):
    openai.api_type = "azure"
    openai.api_base = f"https://{AZURE_OPENAI_RESOURCE}.openai.azure.com/"
    openai.api_version = "2023-03-15-preview"
    openai.api_key = AZURE_OPENAI_KEY
    request_messages = request.json["messages"]
    length=len(request_messages)
    question=request_messages[length-1]['content']
 
    for message in request_messages:
        messages.append({
            "role": message["role"] ,
            "content": message["content"]
        })
    print(messages)
    response = openai.ChatCompletion.create(
        engine=AZURE_OPENAI_MODEL,
        messages = messages,
        temperature=float(AZURE_OPENAI_TEMPERATURE),
        max_tokens=int(AZURE_OPENAI_MAX_TOKENS),
        top_p=float(AZURE_OPENAI_TOP_P),
        stop=AZURE_OPENAI_STOP_SEQUENCE.split("|") if AZURE_OPENAI_STOP_SEQUENCE else None,
        stream=SHOULD_STREAM
    )
    if not SHOULD_STREAM:
        response_obj = {
            "id": response,
            "model": response.model,
            "created": response.created,
            "object": response.object,
            "choices": [{
                "messages": [{
                    "role": "assistant",
                    "content": response.choices[0].message.content
                }]
            }]
        }
        return jsonify(response_obj), 200
    else:
        if request.method == "POST":
            return Response(stream_with_data_elastic(response,question), mimetype='text/event-stream')
        else:
            return Response(None, mimetype='text/event-stream')
                

@app.route("/conversation1", methods=["GET", "POST"])
def conversation():
    try:
        use_data = should_use_data()
        if use_data:
            return conversation_with_data(request)
        else:
            return conversation_without_data(request)
    except Exception as e:
        logging.exception("Exception in /conversation1")
        return jsonify({"error": str(e)}), 500
    
@app.route("/conversationwithelastic", methods=["GET", "POST"])
def conversationwithelastic():
    try:
        use_data = should_use_data_elastic(request)
        if use_data:
            return conversation_with_data_elastic(request)
        else:
            return conversation_without_data_elastic(request)
    except Exception as e:
        logging.exception("Exception in /conversation")
        return jsonify({"error": str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        print ("inside summari api")                                        
        # print(request.json["text"])
        result = summarize_data(request.json["text"])
        return result
    except Exception as e:
        logging.exception("Exception in /conversation1")
        return jsonify({"error": str(e)}), 500 


@app.route("/langsummarize", methods=["GET","POST"])
def sample_abstractive_summarization():
   try:
    # [START abstractive_summary]
    import os
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.textanalytics import TextAnalyticsClient

    endpoint = AZURE_LANGUAGE_ENDPOINT
    key = AZURE_LANGUAGE_KEY
    print("request",request.data.decode("utf-8"))
    text_analytics_client = TextAnalyticsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    # document = [
    #     "At Microsoft, we have been on a quest to advance AI beyond existing techniques, by taking a more holistic, "
    #     "human-centric approach to learning and understanding. As Chief Technology Officer of Azure AI Cognitive "
    #     "Services, I have been working with a team of amazing scientists and engineers to turn this quest into a "
    #     "reality. In my role, I enjoy a unique perspective in viewing the relationship among three attributes of "
    #     "human cognition: monolingual text (X), audio or visual sensory signals, (Y) and multilingual (Z). At the "
    #     "intersection of all three, there's magic-what we call XYZ-code as illustrated in Figure 1-a joint "
    #     "representation to create more powerful AI that can speak, hear, see, and understand humans better. "
    #     "We believe XYZ-code will enable us to fulfill our long-term vision: cross-domain transfer learning, "
    #     "spanning modalities and languages. The goal is to have pretrained models that can jointly learn "
    #     "representations to support a broad range of downstream AI tasks, much in the way humans do today. "
    #     "Over the past five years, we have achieved human performance on benchmarks in conversational speech "
    #     "recognition, machine translation, conversational question answering, machine reading comprehension, "
    #     "and image captioning. These five breakthroughs provided us with strong signals toward our more ambitious "
    #     "aspiration to produce a leap in AI capabilities, achieving multisensory and multilingual learning that "
    #     "is closer in line with how humans learn and understand. I believe the joint XYZ-code is a foundational "
    #     "component of this aspiration, if grounded with external knowledge sources in the downstream AI tasks."
    # ]
    document = [request.data.decode("utf-8")]
    # document = [
    #     "Format: PDF  Page Start: 1  1/10  The shape of consumer spending    Potent forces are shaping today\u2019s spending decisions\u2014particularly the more discretionary ones\u2014  sending mixed signals worldwide    Splurge or save? In recent months, consumers worldwide likely feel caught between two minds. As global  anxiety around the pandemic wanes, many are eager to spend on sorely missed experiences like travel,  Article 5 minute read \u00b7 08 August 2022    Stephen Rogers  United States    Leon Pieters  Netherlands    Anthony Waelter  United States  Page End: 1  Page Start: 2  2/10  restaurants, and entertainment. But built-up pandemic demand is hitting hurdles in the form of spiking  inflation and persistent headlines warning of a potential global recession.    Which way consumers are leaning\u2014spend on much-deserved joy or save for potentially more challenging  times\u2014can depend on where you look across the world.    For example, spending intentions are beginning to paint a picture of dwindling consumer confidence in  the United States and the United Kingdom. Considering their upcoming monthly budgets, the share of  wallet consumers plan to allocate toward more discretionary categories has been slipping since  September 2021 (figure 1). Planned pullbacks are more substantial among Americans, even hitting less  discretionary categories like clothing and personal care. In both countries, housing (including utilities)  and transportation remain the only categories grabbing a larger share of consumers\u2019 wallets lately.  Page End: 2  Page Start: 3  3/10  The rising cost of living is a likely driver of shifting spending intentions. Inflation has been high in the  United States and the United Kingdom, hitting roughly 9% between May and June.  1  Page End: 3  Page Start: 4  4/10  Consumer confidence appears a bit stronger in some countries, such as Japan, where inflation remains  relatively low. Compared to last September, Japanese consumers in June planned to allocate a slightly  larger share of their monthly budgets toward categories like recreation and entertainment, restaurants,  and leisure travel (figure 1). Over the same nine-month period, the Bank of Japan's Consumer Spending  Index for Real Services jumped 10 points, from 88 to 98.    The trends suggest that built-up pandemic demand is still winning the battle over saving in some  countries. In Japan, the absence of spiking inflation is important to consider. At face value, it makes sense  that consumers would feel more comfortable spending freely in a more price-stable environment\u2014but the  drivers behind spending are still murky. Consumers may still be reacting to global inflation more broadly,  diverting more cash towards discretionary categories now with the expectation that prices could rise in  the near future.    But there are also countries with high inflation, where spending intentions haven't changed much. In  Germany, for example, inflation hit 8% in May\u2014roughly on par with the United States and the United  Kingdom. Discretionary spending intentions, however, have yet to show signs of budging (figure 1).    Globally, consumers appear to respond differently to strong inflation and the bleak economic outlook.  Financial sentiment and key differences at the country level could offer some insight as to why.    Consumers\u2019 \ufb01nancial footing    Even across the world's largest economies, consumers\u2019 capacity to absorb financial pressures like inflation  and recession likely varies.    Financial sentiment among Americans, for example, has been flashing warning signals for over a year. In  May 2021, the national Personal Savings Rate stood near record highs. At that time, only 33% of  Americans expressed concern about their level of savings (figure 2).  2    3    4    5  Page End: 4  Page Start: 5  5/10  Page End: 5  Page Start: 6  6/10  But rising inflation quickly exposed a shaky financial footing. As rates climbed, in tandem with sunsetting  pandemic relief programs, savings concerns followed suit. Nearly two-thirds (61%) of Americans now  express concerns about their savings\u2014with the Personal Savings Rate sitting at only 5%. Savings concern  among consumers in the United Kingdom is following a similar trend.    More recently, concerns about credit card debt are rising among Americans (48%). And some trends,  such as the number of lower-income Americans struggling to make upcoming payments, have been  steadily increasing since the pandemic\u2019s early days.    In stark contrast, financial sentiment in Germany appears considerably stronger. Only 32% of German  consumers express savings concern\u2014a figure that\u2019s remained steady for nearly two years. Additionally,  fewer consumers in Germany cite concerns around credit card debt (32%). But compared to the United  States, credit card use is generally less prevalent in Germany.    Local environment    Beyond financial well-being, key differences at the country level could also be influencing consumers\u2019  intention to splurge or save:    Nature of inflation: Reactions to inflation are likely being driven by the nature of inflation itself. In  Germany, where spending intentions remain relatively steady, inflation is exclusively driven by higher  energy prices, including natural gas and heating oil, as well as food prices. Prices, however, have  remained stable (or even fallen) in a few categories outside of energy and food\u2014including passenger  transportation services, telecom services, and electronics. In contrast, inflation in the United States  has generally been universal. Throughout the pandemic, expansive fiscal policies drove a consumer  spending boom on goods that helped nurture inflation. As a result, nearly all categories in the United  States Consumer Price index have increased over the past year.  6    7    8    9    10    11  Page End: 6  Page Start: 7  7/10  Hot housing: Housing represents the most significant consumer spending category by far. In the  United States, where spending intentions for discretionary categories weakened the most, median  home prices have increased 33% in the past two years. Housing prices have increased in the United  Kingdom (20%) and Germany (17%) since 2020\u2014but the jumps haven't been as strong.    Social safety nets: Socialized programs are also an important factor to consider. Over the next  month, German consumers only plan to allocate 6% of their monthly budget to health care and  education. Americans plan to spend closer to 10%. Additionally, recent drops in the cost of some  passenger transportation services in Germany are driven by government subsidies. Programs like  socialized health care and education are likely important lifelines for consumers who use these services  \u2014particularly during economic downturns.    The shape of consumer industry    Pandemic-influenced consumer patterns rendered many historic demand models obsolete.    Persisting inflation; rising interest rates; ongoing supply-chain disruption; and slowing economic growth  \u2014these new pressures will continue to shape already altered consumer demand and preferences.    Complicating factors will be that demand and preferences will evolve unevenly and at different rates  across the globe. Understanding consumers\u2019 financial well-being may become key to regional and local  market trends.    For example, income bifurcation has shaped consumer spending in the United States for quite some time.  In turn, it has shaped strategies and business models. For example, revenue growth among price-based  and premier retailers outpaced more balanced retailers for years. Airlines have been busy segmenting  their cabins to create a broader mix of high- and lower-priced fares.  12    13    14  Page End: 7  Page Start: 8  8/10  Just as the pandemic challenged conventional wisdom, consumer companies should expect the  confluence of economic pressures to challenge the typical recession playbook equally. Consumer  companies will likely want to include consumer financial well-being and increasingly granular consumer  behavioral data in their models to remain agile and ahead of a dynamically evolving environment.    1. Haver Analytics. View in Article    2. Ibid. View in Article    3. Bank of Japan, Consumption Activity Index (CAI). The CAI is compiled by using a variety of sales and supply-side statistics  on goods and services as its source statistics and is provided as a measure for capturing short-term consumption activity on  both monthly and quarterly bases. The CAI traces movements of consumption in the household side of the economy. View  in Article    4. Haver Analytics. View in Article    5. Bureau of Economic Analysis. View in Article    6. Deloitte, \u201cGlobal State of the Consumer Tracker,\u201d accessed August 1, 2022. View in Article    7. Ibid. View in Article    8. Ibid. View in Article    9. NPR, \u201cAlong with the US, Europe is hit with extraordinarily high inflation numbers,\u201d podcast, June 1, 2022. View in Article    10. Destatis.de, \u201cPrice trends of selected goods and services,\u201d accessed August 1, 2022. View in Article  \uf067 Endnotes  Page End: 8  Page Start: 9  9/10  11. US Bureau of Labor Statistics, \u201cTED: The Economics Daily,\u201d July 18, 2022. View in Article    12. FRED, \u201cMedian Sales Price of Houses Sold for the United States,\u201d July 26, 2022. View in Article    13. Destatis.de, \u201cResidential property price indices,\u201d accessed August 1, 2022. View in Article    14. Stephen Rogers and Anthony Waelter, The pursuit of happiness ... if you can afford it, Deloitte Insights, February 10, 2022.  View in Article    The authors would like to thank Marcello Gasdia and Dinesh T for their significant contributions to this article.    Cover image by: Natalie Pfaff    Stephen Rogers  Managing Director  stephenrogers@deloitte.com  \uf067 Acknowledgments    Consumer    Deloitte Consumer leaders work with global brands to create winning strategies for the near future  in the Automotive; Consumer Products; Retail; and Transportation, Hospitality & Services sectors.    Our mission is to use our proprietary data and judgement to help you get closer to your consumers.  Page End: 9  Page Start: 10  +1 475 277 9018    \u00a9 2022. See Terms of Use for more information.    Deloitte refers to one or more of Deloitte Touche Tohmatsu Limited, a UK private company limited by guarantee (\"DTTL\"), its network of member \ufb01rms,  and their related entities. DTTL and each of its member \ufb01rms are legally separate and independent entities. DTTL (also referred to as \"Deloitte Global\")  does not provide services to clients. In the United States, Deloitte refers to one or more of the US member \ufb01rms of DTTL, their related entities that  operate using the \"Deloitte\" name in the United States and their respective a\ufb03liates. Certain services may not be available to attest clients under the  rules and regulations of public accounting. Please see www.deloitte.com/about to learn more about our global network of member \ufb01rms.  Page End: 10 "
    # ]
    print("document:", document[0])
    poller = text_analytics_client.begin_abstract_summary(document,sentence_count=8)
    abstractive_summary_results = poller.result()
    abstract=''
    for result in abstractive_summary_results:
        if result.kind == "AbstractiveSummarization":
            print("Summaries abstracted:")
            [print(f"{summary.text}\n") for summary in result.summaries]
            for restext in result.summaries:
                abstract+= restext.text
            print("abstract",abstract)       
        elif result.is_error is True:
            print("...Is an error with code '{}' and message '{}'".format(
                result.error.code, result.error.message
            ))
    return abstract
   except Exception as e:
        logging.exception("Exception in /langsummarize")
        return jsonify({"error": str(e)}), 500  
    # [END abstractive_summary]


if __name__ == "__main__":
    app.run()
