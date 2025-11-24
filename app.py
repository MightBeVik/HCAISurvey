from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

CSV_FILE = 'survey_results.csv'
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbzVBavg2aqnQYLRR3ZR696LPKNhgNqqsZC5jE4ykbAyfusH35j6SAtxAj9S3BeASxdlkw/exec"


# Define 10 survey questions
QUESTIONS = [
    {"id": 1, "type": "options", "question": "Have you ever been to Therapy or used Mental Health Applications?", "name": "Therapy Experience",
     "options": [
         {"text": "Yes"},
         {"text": "No"}
     ]},
    {"id": 2, "type": "card", "question": "Data Handling", "name": "Data Handling",
     "options": [
         {"text": "Local", "image": "Ondevice.png", "title": "On-Device", "description": "All processing and storage of user data occurs locally on your device, ensuring maximum privacy and rapid response times."},
         {"text": "On-Cloud", "image": "Cloudbase.png", "title": "Cloud-Based", "description": "User data is securely managed and processed on remote servers, offering seamless access, synchronization across devices, and powerful computational resources."}
     ]},
    {"id": 3, "type": "card", "question": "Human Oversight", "name": "Human Oversight",
     "options": [
         {"text": "None", "image": "None.png", "title": "Autonomous", "description": "The system operates fully autonomously, driven entirely by algorithms and machine learning models without manual intervention."},
         {"text": "Other User Support", "image": "Other user support.png", "title": "Peer Support", "description": "We foster a community where fellow users can provide guidance, troubleshoot issues, and share expertise and solutions."},
         {"text": "Professional Oversight", "image": "Professional oversight.png", "title": "Professional Oversight", "description": "Dedicated, expert teams regularly monitor, review, and refine system performance, ensuring accuracy, safety, and continuous improvement."}
     ]},
    {"id": 4, "type": "card", "question": "Content Style", "name": "Content Style",
     "options": [
         {"text": "Text-Based", "image": "Teect-based.png", "title": "Text-Based", "description": "All interactions and information delivery are conducted through clear, concise, and structured written communication."},
         {"text": "Voice Interface", "image": "Voice interface.png", "title": "Voice Interface", "description": "We prioritize natural language processing, allowing users to interact with the system entirely through spoken commands and audio feedback."},
         {"text": "Gamified Experience", "image": "Gamified.png", "title": "Gamified Experience", "description": "We integrate playful challenges, rewards, and progress tracking into the user journey to drive engagement and motivation."}
     ]},
    {"id": 5, "type": "card", "question": "Effectiveness", "name": "Effectiveness",
     "options": [
         {"text": "No Evidence", "image": "No Evidence.png", "title": "No Evidence", "description": "Claims are currently based on internal expectations and future goals, pending external validation and testing."},
         {"text": "User Testimonials", "image": "User testimonial.png", "title": "User Testimonials", "description": "Our success is validated by direct feedback and documented experiences from our community of users."},
         {"text": "Professional Studies", "image": "Professional research.png", "title": "Professional Studies", "description": "Our methods are rigorously backed by peer-reviewed studies and independent, scientifically sound investigations."}
     ]},
    {"id": 6, "type": "card", "question": "Crisis Handling", "name": "Crisis Handling",
     "options": [
         {"text": "None", "image": "None.png", "title": "Standard Support", "description": "Standard operating procedures apply for all issues; we do not offer specialized, time-critical response mechanisms."},
         {"text": "Resource Sharing Only", "image": "Resource sharing.png", "title": "Resource Sharing", "description": "We provide a curated library of links, documents, and external contacts for users to self-serve during critical times."},
         {"text": "24/7 Emergency Response", "image": "Professional oversight.png", "title": "24/7 Emergency Response", "description": "A dedicated, round-the-clock team is available to immediately address and resolve urgent, high-priority issues."}
     ]},
    {"id": 7, "type": "card", "question": "Cost", "name": "Cost",
     "options": [
         {"text": "Free", "image": "Free.png", "title": "Free", "description": "Access to the product's features without any charge."},
         {"text": "Subscription-Based", "image": "5 dollors.png", "title": "Subscription", "description": "Access provided through a recurring monthly or annual payment."},
         {"text": "One-Time Purchase", "image": "15 dollars.png", "title": "One-Time Payment", "description": "Access provided through a single, non-recurring purchase."}
     ]},
    {"id": 8, "type": "card", "question": "Privacy", "name": "Privacy",
     "options": [
         {"text": "Legal Policy Only", "image": "Legal Policy.png", "title": "Legal Policy Only", "description": "Our commitment is defined solely by the terms and conditions outlined in our official privacy policy."},
         {"text": "See Your Data", "image": "See your Data.png", "title": "View Your Data", "description": "We offer transparent tools that allow you to easily view and understand all the information we have collected about your usage."},
         {"text": "Download Your Data", "image": "See your Data.png", "title": "Export Your Data", "description": "Users have the fundamental right to export and retrieve a copy of all their personal data in a usable format at any time."}
     ]},
    {"id": 9, "type": "card", "question": "Response Type", "name": "Response Type",
     "options": [
         {"text": "Same for Everyone", "image": "Same for everyone.png", "title": "Standardized", "description": "The system provides a consistent, standardized set of responses regardless of the individual user or their history."},
         {"text": "Learns from User", "image": "Learn from you.png", "title": "Personalized", "description": "Responses and content are dynamically personalized and adapted based on your past interactions, preferences, and behavior."},
         {"text": "Expert-Designed", "image": "Expert design.png", "title": "Expert-Curated", "description": "All core responses are curated and reviewed by specialists in the field to ensure maximum accuracy and authoritative quality."}
     ]},
    {"id": 10, "type": "ranking", "question": "Rank your selections from most important to least important", "name": "Ranking"}
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
        for q in QUESTIONS[1:9]:
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
    return redirect(url_for('thank_you'))

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    init_csv()
    app.run(debug=True)
