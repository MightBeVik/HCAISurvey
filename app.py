from flask import Flask, render_template, request, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import csv
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

CSV_FILE = 'survey_results.csv'
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbz7pvaiuOx7-U-mz3OpoXhllOYTB0iJJljkXVLbtgMnR6bIjQF1ViILJSbqXCrB1w2iNA/exec"

QUESTIONS = [
    {"id": 1, "type": "options", "question": "What is your age?", "name": "Age",
     "options": [
         {"text": "Under 18"},
         {"text": "18-24"},
         {"text": "25-34"},
         {"text": "35-44"},
         {"text": "45-54"},
         {"text": "55-64"},
         {"text": "65+"}
     ]},
    {"id": 2, "type": "options", "question": "Have you ever been to Therapy or used Mental Health Applications?", "name": "Therapy Experience",
     "options": [
         {"text": "Yes"},
         {"text": "No"}
     ]},
    {"id": 3, "type": "card", "question": "Data Handling", "name": "Data Handling", "description": "How would you prefer your data to be stored and processed?",
     "options": [
         {"text": "Local", "image": "Ondevice.png", "title": "On-Device", "description": "Keeps your data on your device."},
         {"text": "On-Cloud", "image": "Cloudbase.png", "title": "Cloud-Based", "description": "Stores and processes your data in the cloud."}
     ]},
    {"id": 4, "type": "card", "question": "Human Oversight", "name": "Human Oversight", "description": "How much human involvement would you want in the system's decisions?",
     "options": [
         {"text": "None", "image": "None.png", "title": "Autonomous", "description": "Runs fully without human involvement."},
         {"text": "Other User Support", "image": "Other user support.png", "title": "Peer Support", "description": "Lets other users help you."},
         {"text": "Professional Oversight", "image": "Professional oversight.png", "title": "Professional Oversight", "description": "Experts monitor and review the system."}
     ]},
    {"id": 5, "type": "card", "question": "Content Style", "name": "Content Style", "description": "How would you prefer the system to communicate with you?",
     "options": [
         {"text": "Text-Based", "image": "Teect-based.png", "title": "Text-Based", "description": "Uses written messages to communicate."},
         {"text": "Voice Interface", "image": "Voice interface.png", "title": "Voice Interface", "description": "Lets you speak and hear responses."},
         {"text": "Gamified Experience", "image": "Gamified.png", "title": "Gamified Experience", "description": "Adds rewards and challenges for engagement."}
     ]},
    {"id": 6, "type": "card", "question": "Effectiveness", "name": "Effectiveness", "description": "What level of evidence would you expect behind the system's results?",
     "options": [
         {"text": "No Evidence", "image": "No Evidence.png", "title": "No Evidence", "description": "Not yet supported by external evidence."},
         {"text": "User Testimonials", "image": "User testimonial.png", "title": "User Testimonials", "description": "Validated through user experiences."},
         {"text": "Professional Studies", "image": "Professional research.png", "title": "Professional Studies", "description": "Backed by scientific research."}
     ]},
    {"id": 7, "type": "card", "question": "Crisis Handling", "name": "Crisis Handling", "description": "How should the system respond during urgent or high-stress situations?",
     "options": [
         {"text": "None", "image": "None.png", "title": "Standard Support", "description": "No special support for urgent issues."},
         {"text": "Resource Sharing Only", "image": "Resource sharing.png", "title": "Resource Sharing", "description": "Provides links and resources for crises."},
         {"text": "24/7 Emergency Response", "image": "Professional oversight.png", "title": "24/7 Emergency Response", "description": "Offers 24/7 urgent-issue support."}
     ]},
    {"id": 8, "type": "card", "question": "Cost", "name": "Cost", "description": "How would you prefer to pay for access to the system?",
     "options": [
         {"text": "Free", "image": "Free.png", "title": "Free", "description": "Free access to the product."},
         {"text": "Subscription-Based", "image": "5 dollors.png", "title": "Subscription", "description": "Requires a recurring payment."},
         {"text": "One-Time Purchase", "image": "15 dollars.png", "title": "One-Time Payment", "description": "One-time payment for full access."}
     ]},
    {"id": 9, "type": "card", "question": "Privacy", "name": "Privacy", "description": "What level of control would you like over your personal data?",
     "options": [
         {"text": "Legal Policy Only", "image": "Legal Policy.png", "title": "Legal Policy Only", "description": "Follows our official privacy policy."},
         {"text": "See Your Data", "image": "See your Data.png", "title": "View Your Data", "description": "Lets you view all your data."},
         {"text": "Download Your Data", "image": "Export_your_data.png", "title": "Export Your Data", "description": "Lets you download your data."}
     ]},
    {"id": 10, "type": "card", "question": "Response Type", "name": "Response Type", "description": "How personalized should the system's responses be?",
     "options": [
         {"text": "Same for Everyone", "image": "Same for everyone.png", "title": "Standardized", "description": "Same responses for all users."},
         {"text": "Learns from User", "image": "Learn from you.png", "title": "Personalized", "description": "Learns and adapts to you."},
         {"text": "Expert-Designed", "image": "Expert design.png", "title": "Expert-Curated", "description": "Responses created by experts."}
     ]},
    {"id": 11, "type": "ranking", "question": "Rank your selections from most important to least important", "name": "Ranking"}
]

def init_csv():
    """Initialize CSV file with headers if it doesn't exist"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = ['Timestamp'] + [q['name'] for q in QUESTIONS]
            writer.writerow(headers)

@app.route('/')
def index():
    # Check if user already completed survey
#    if request.cookies.get('survey_completed'):
#        return render_template('already_completed.html')
    
    session.clear()
    session['answers'] = {}
    return render_template('start.html')

@app.route('/survey/<int:question_num>', methods=['GET', 'POST'])
def survey(question_num):
    if question_num < 1 or question_num > len(QUESTIONS):
        return redirect(url_for('index'))
    
    if 'answers' not in session:
        session['answers'] = {}
    
    if request.method == 'POST':
        # Save the answer
        question = QUESTIONS[question_num - 1]
        
        # Handle ranking question differently
        if question.get('type') == 'ranking':
            answer = request.form.get('ranking_order')
            session['answers'][question['name']] = answer
        else:
            answer = request.form.get(question['name'])
            session['answers'][question['name']] = answer
        
        session.modified = True
        
        # Handle navigation
        if 'next' in request.form and question_num < len(QUESTIONS):
            return redirect(url_for('survey', question_num=question_num + 1))
        elif 'previous' in request.form and question_num > 1:
            return redirect(url_for('survey', question_num=question_num - 1))
        elif 'submit' in request.form and question_num == len(QUESTIONS):
            return redirect(url_for('submit_survey'))
    
    question = QUESTIONS[question_num - 1]
    progress = (question_num / len(QUESTIONS)) * 100
    saved_answer = session['answers'].get(question['name'], '')
    
    # For ranking question, gather all selected options
    selected_items = []
    if question.get('type') == 'ranking':
        for q in QUESTIONS[2:10]:
            answer_text = session['answers'].get(q['name'], '')
            if answer_text:
                for opt in q['options']:
                    if opt['text'] == answer_text:
                        selected_items.append({
                            'text': opt['text'],
                            'title': opt.get('title', opt['text']),
                            'image': opt.get('image', ''),
                            'description': opt.get('description', '')
                        })
                        break
    
    return render_template('survey.html', 
                         question=question, 
                         question_num=question_num,
                         total_questions=len(QUESTIONS),
                         progress=progress,
                         saved_answer=saved_answer,
                         selected_items=selected_items)

@app.route('/submit', methods=['GET'])
@limiter.limit("3 per hour")
def submit_survey():
    if 'answers' not in session:
        return redirect(url_for('index'))
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    answers = session['answers']
    
    # Write to CSV (local backup)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        row = [timestamp] + [answers.get(q['name'], '') for q in QUESTIONS]
        writer.writerow(row)
    
    # Send to Google Sheets
    try:
        responses = {'Timestamp': timestamp}
        responses.update(answers)
        requests.post(GOOGLE_SHEETS_URL, json=responses, timeout=5)
    except Exception as e:
        print(f"Error sending to Google Sheets: {e}")
    
    session.clear()
    
    # Set cookie to mark survey as completed
    response = redirect(url_for('thank_you'))
    #response.set_cookie('survey_completed', 'true', max_age=365*24*60*60)  # 1 year
    return response

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    init_csv()
    app.run(debug=True)
