#!/usr/bin/env python
# coding: utf-8

# In[3]:


from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup as bs
from openai import OpenAI
import json
from rapidfuzz import fuzz

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
                response_format={ "type": "json_object" }
            )
            return response

        # Prepare the prompt
        prompt1 = """Output all the product information below in json fomat:\n
            <productinfo>
            {productinfo:{'product_image': First product image url,
             'name': Name of the product, 
             'brand': Product brand,
             'category': Assign one of the value Hair, Skincare, Fragnances, Bath & Body, Makeup or Other,
             'original_price': Original price without any currency symbol in integer,
             'offer_price': Offer price without any currency symbol in integer,
             'size_in_number': Size amount in integer without the unit,
             'size_unit': Size unit such as gm, ml etc.,
             'description': Only text, exlude images, rephrase if longer than 100 words to reduce it to 100 words,
             'ingredients': [List of ingredients],
             'how_to_use': Bullet points of how to use,
             'rating': Return only rating value in float format, exclude number of rating and reviews,
             'best_before': Return best before time period of use since manufacture}
             }
             </productinfo>"""
        
        prompt = prompt1 + doc1

        # Get the response from OpenAI
        ai_response = generate_response(prompt=prompt, model=GPT_MODEL)
        ai_response1 = json.loads(ai_response.choices[0].message.content)
            
#         # Extract brand and name from AI response
#         brand = ai_response1.get('productinfo').get('brand', '').lower()
#         name = ai_response1.get('productinfo').get('name', '').lower()

#         # Load the CSV file
#         df = pd.read_csv('Skincare_final.csv')
        
#         def calculate_similarity(row):
#             brand_similarity = fuzz.ratio(brand, row['Brand'].lower())
#             name_similarity = fuzz.ratio(name, row['Name'].lower())
#             return (brand_similarity + name_similarity) / 2  # Average similarity

#                 # Apply similarity calculation
#         df['similarity'] = df.apply(calculate_similarity, axis=1)
        
        
#         if not df.empty:
#             # Return the best match
#             best_match = df.sort_values(by='similarity', ascending=False).reset_index(drop=True)[0]
#             ai_response1['matched_product'] = best_match
#         else:
#             ai_response1['matched_product'] = None

        # Extract the content
        return jsonify(ai_response1), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()

