from openai import OpenAI
clientAI = OpenAI()
import pymongo

url = 'mongodb://localhost:27017'
client = pymongo.MongoClient(url)
db = client['aICounseling']
screening_collection = db['screening']

def ask_question(question):
    try:
        completion = clientAI.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": question}
            ]
        )
        # Assuming the text content you want to save is within the 'content' attribute of the message
        answer = completion.choices[0].message
        content = answer.content
        return content
    except Exception as e:
        print("Error during API call:", e)
        raise
        

def askOpenAI(info):

    question = f"I am going to give you a DUI screening exam. This exam consists of a couple different sections: intake_assessment, mast, adhs, abi, tvi, si, di, vi, lof, hi, and dvpi. I want you to score each scorable section seperatly to the best of your ability as if you were a counselor and then give me overall score. Additionally, I want you to catch any red flags on the test. For instance if they said they not drink but they got a DUI. Here is the screening assessment: {info}"
    # Get the answer from OpenAI
    answer = ask_question(question)
    return answer

def update_screening_scores():
    for document in screening_collection.find():
        info = document  # Assuming the document structure directly corresponds to the expected input format for askOpenAI
        assessment_score = askOpenAI(info)
        #Update the document with the assessment score
        screening_collection.update_one({'_id': document['_id']}, {'$set': {'assessment_score': assessment_score}})
        print("updated a document")


