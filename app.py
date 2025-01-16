#!/usr/bin/env python
# coding: utf-8

# In[3]:


from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup as bs
from openai import OpenAI

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        # Get input data from the request
        data = request.get_json()
        url = data.get('url')
        api_key = data.get('api_key')

        if not url or not api_key:
            return jsonify({"error": "Missing URL or API key"}), 400

        # Fetch the webpage
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch the webpage"}), 500

        content = response.text
        soup = bs(content, "html.parser")

        # Remove unnecessary tags
        for tag in soup(["script", "style", "noscript", "footer", "header", "aside", "nav"]):
            tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, (str,)) and text.startswith("<!--")):
            comment.extract()

        # Prepare the processed HTML
        doc1 = str(soup)

        # OpenAI client initialization
        client = OpenAI(api_key=api_key)
        
        # GPT model configuration
        GPT_MODEL = 'gpt-4o-mini'

        # Generate response function
        def generate_response(prompt, model):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format="json_object"
            )
            return response

        # Prepare the prompt
        prompt1 = """Output all the product information below in json fomat:\n
            <productinfo>
            {'product_image': First product image url,
             'name': Name of the product, 
             'brand': Product brand,
             'category': Assign one of the value Hair, Skincare, Fragnances, Bath & Body, Makeup or Other,
             'original price': Original price without any currency symbol,
             'offer price': Offer price without any currency symbol,
             'size in number': Size amount without the unit,
             'size unit': Size unit such as gm, ml etc.,
             'description': Only text, exlude images, rephrase if longer than 100 words to reduce it to 100 words,
             'ingredients': [List of ingredients],
             'how to use': Bullet points of how to use,
             'rating': Return only rating value, exclude number of rating and reviews,
             'Best before': Return best before time period of use since manufacture}
             </productinfo>"""
        
        prompt = prompt1 + doc1

        # Get the response from OpenAI
        ai_response = generate_response(prompt=prompt, model=GPT_MODEL)

        # Extract the content
        return jsonify(ai_response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()

