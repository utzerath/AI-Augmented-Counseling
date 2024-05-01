"""

This Python script is part of a Django web application related to DUI (Driving Under the Influence) Screening Assessments. Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It follows the model-view-template architectural pattern, which is particularly suited for managing complex data-driven websites.

Here’s a breakdown of what the various parts of the script do:

Imports and Initializations: The script begins by importing necessary modules from Django and other libraries. It defines a client for accessing an AI service and a class myAuthentication to manage authentication states within the application.

View Functions: These functions are the core of Django's view layer, where web requests are received and responses are sent back. Each function corresponds to a specific endpoint or feature of the application:
homepage, signup, signin, signout: Handle user authentication and the homepage rendering.

screeningTest: Manages the DUI screening test process, collecting extensive data from forms, structuring this data, and saving it to a database.
today: Handles daily entries for users, supporting text, video, audio, and other types of files.

entries: Displays all entries related to a user.

serve_file: Handles the downloading of files stored in the MongoDB GridFS.

adminDashboard: A view for admin users to manage and view data of all users.

Database Operations: The script interacts with MongoDB to store and retrieve data. It uses GridFS for managing large files like video and audio, which are linked to user entries.

OpenAI Integration: Parts of the script communicate with OpenAI to perform complex assessments on the data gathered during the screening tests. This integration allows for automated analysis and response generation based on user inputs.

Utility Functions: Includes functions like ask_question which abstracts API calls to OpenAI and askOpenAI which specifically formats and sends data related to DUI screenings for analysis.

Error Handling and Messages: Throughout the script, Django’s messaging framework is used to give feedback to the user about the success or failure of various operations.

"""


from io import BytesIO
from django.shortcuts import redirect, render
from django.urls import reverse
from .models import logIn_collection, text_entries_collection, video_entries_collection, audio_entries_collection, otherFiles_entries_collection, adminLogIn_collection, screening_collection
from django.http import HttpResponse, JsonResponse, QueryDict, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from db_connection import fs
from bson import ObjectId
from django.utils import timezone
from datetime import datetime
#import askOpenAI
from openai import OpenAI
clientAI = OpenAI()

class myAuthentication:
    is_auth = False
    username = ""
    is_admin = False


# Create your views here.
def homepage(request):
    return render(request, "userAuthentication/homepage.html")

def signup(request):
    current_date = timezone.now().date()
    current_date_datetime = datetime.combine(current_date, datetime.min.time())
    if request.method == "POST":
        #username = request.POST['username']
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        
        user_logIn = {
            'username': username,
            'fname' : fname,
            'lname' : lname,
            'email' : email,
            'password' : password
        }

        logIn_collection.insert_one(user_logIn)
        messages.sucess(request, "Your Account has been successfully created.")

        return redirect('signin')


    return render(request, "userAuthentication/signup.html", {'date': current_date_datetime})

def signin(request):
    current_date = timezone.now().date()
    current_date_datetime = datetime.combine(current_date, datetime.min.time())
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user_logIn = logIn_collection.find_one({'username': username})
        adminLogIn = adminLogIn_collection.find_one({'username' : username})
        
        if adminLogIn and adminLogIn['password'] == password:
            myAuthentication.is_auth = True
            myAuthentication.username = username
            myAuthentication.is_admin = True

            return redirect('adminDashboard')
        
        if user_logIn and user_logIn['password'] == password:
            myAuthentication.is_auth = True
            myAuthentication.username = username

            return render(request, 'userAuthentication/ScreeningTest.html', {'username': username})
        
        

        else:
            messages.error(request, "Bad Credentials")
            return render(request, "userAuthentication/signin.html")

    return render(request, "userAuthentication/signin.html", {'date': current_date_datetime})

def signout(request):
    current_date = timezone.now().date()
    current_date_datetime = datetime.combine(current_date, datetime.min.time())
    pass

def screeningTest(request):
    username = request.GET.get('username', None)

    if not myAuthentication.is_auth:
        return redirect('signin')
    
    if request.method == 'POST':
        # Extract client information
        """
        Client Info Starts Here
        """
        client_info = {
            'last_name': request.POST['last_name'],
            'first_name': request.POST['first_name'],
            'middle_name': request.POST.get('middle_name', ''),
            'dob': '-'.join([request.POST['dob_year'], request.POST['dob_month'], request.POST['dob_day']]),  # Assuming 'YYYY-MM-DD' format
            'address': request.POST['address'],
            'sex': request.POST.get('sex', None),
            'special_accommodations': request.POST.get('special_accommodations', None),
            'court_ordered': request.POST.get('court_ordered', None)
        }

        """
        Intake Assessment Starts Here
        """
        # Intake/Assessment
        # Behavioral Health Issues - checkboxes can have multiple values, so getlist is used
        behavioral_health_issues = request.POST.getlist('behavioral_health_issues')
        
        # Psychological History
        psychological_history = request.POST.getlist('psychological_history')
        psychological_other = request.POST.get('psychological_other', '')

        # Social History
        social_history = request.POST.getlist('Social_History')
        social_history_other = request.POST.get('social_history_other', '')
        
        # Educational and Vocational History
        educational_and_vocational_history = request.POST.get('Educational_and_Vocational_History')
        educational_and_vocational_history_other = request.POST.get('Educational_and_Vocational_History_Other', '')

        # Medical History
        medical_history = request.POST.getlist('medical_history')
        other_medical_conditions = request.POST.get('Other', '')
        prescribed_medications = request.POST.get('Prescribed_Medications', '')
        over_counter_medications = request.POST.get('Over_Counter_Medications', '')

        # Medication & Substance Use History
        # List all substances you expect to have in your form
        expected_substances = [
            'Alcohol', 'Antidepressants', 'Antipsychotics', 'Cocaine',
            'Hallucinogens', 'Marijuana', 'Narcotics', 'Sedatives', 'Amphetamines', 'Other'
        ]

        # Initialize an empty list to hold the substance use history data
        substance_use_history = []

        # Iterate over each expected substance to collect their respective data
        for substance in expected_substances:
            # Normalize the substance name to match the form input naming convention
            normalized_substance_name = substance.lower().replace(" ", "_")
            
            # Check if the "never used" checkbox for this substance is checked
            never_used_key = f"{normalized_substance_name}_never"
            never_used = never_used_key in request.POST
            
            # If the substance is marked as never used, we do not need to gather more info on it
            if never_used:
                substance_data = {
                    'substance': substance,
                    'never_used': True
                }
            else:
                substance_data = {
                    'substance': substance,
                    'never_used': False,
                    'last_used': request.POST.get(f"{normalized_substance_name}_last_used", ''),
                    'amount': request.POST.get(f"{normalized_substance_name}_amount", ''),
                    'frequency': request.POST.get(f"{normalized_substance_name}_frequency", '')
                }

            # Add the substance data dictionary to our list
            substance_use_history.append(substance_data)

        # Legal History
        legal_history = {
            'DUI': request.POST.get('DUI'),
            'non_DUI': request.POST.get('non_DUI'),
            'domestic_violence': request.POST.get('domestic_violence'),
            'domestic_violence_description': request.POST.get('domestic_violence_description', ''),
            'restraining_order': 'restraining_order' in request.POST,
            'restraining_order_date': request.POST.get('restraining_order_date', ''),
            'assault_conflict': request.POST.get('assault_conflict'),
            'other_legal_issues': 'other_legal_issues' in request.POST,
            'other_legal_issues_date': request.POST.get('other_legal_issues_date', '')
        }

        # Behavioral Health Treatment and Hospitalization History
        # Initialize an empty list to hold the behavioral health history data
        behavioral_health_history = []

        # You may have a predefined list of program identifiers or you can dynamically generate them based on form inputs
        expected_programs = [
            'no_program', 'prior_screening', 'education_dui', 
            'outpatient_treatment', 'inpatient_treatment',
            # ... any additional programs you have on your form
        ]

        # Iterate over each expected program to collect their respective data
        for program_id in expected_programs:
            # Collect the data for each program if the checkbox indicating participation is checked
            if program_id in request.POST:
                program_data = {
                    'program': request.POST.get(program_id, ''),
                    'agency': request.POST.get(f"{program_id}_agency", ''),
                    'purpose': request.POST.get(f"{program_id}_purpose", ''),
                    'date': request.POST.get(f"{program_id}_date", ''),
                    'assignment': request.POST.get(f"{program_id}_assignment", '')
                }
                behavioral_health_history.append(program_data)


        # Combine all intake/assessment data into a dictionary
        intake_assessment = {
            'behavioral_health_issues': behavioral_health_issues,
            'psychological_history': psychological_history,
            'psychological_other': psychological_other,
            'social_history': social_history,
            'social_history_other': social_history_other,
            'educational_and_vocational_history': educational_and_vocational_history,
            'educational_and_vocational_history_other': educational_and_vocational_history_other,
            'medical_history': medical_history,
            'other_medical_conditions': other_medical_conditions,
            'prescribed_medications': prescribed_medications,
            'over_counter_medications': over_counter_medications,
            'substance_use_history': substance_use_history,  # This would be defined above
            'legal_history': legal_history,  # This would be defined above
            'behavioral_health_history': behavioral_health_history,  # This would be defined above
        # ... include any other sections as needed ...
        }
        
        """
        Assessment Questions
        """
        mast_questions = {f"q{i}": request.POST[f"q{i}"] for i in range(25)}
        adhs_questions = {f"ADHS_q{i}": request.POST[f"ADHS_q{i}"] for i in range(1, 26)}
        abi_questions = {f"abi_q{i}": request.POST[f"abi_q{i}"] for i in range(1, 11)}
        tvi_questions = {f"tvi_q{i}": request.POST[f"tvi_q{i}"] for i in range(1, 11)}
        si_questions = {f"si_q{i}": request.POST[f"si_q{i}"] for i in range(1, 16)}
        di_questions = {f"di_q{i}": request.POST[f"di_q{i}"] for i in range(1, 12)}
        vi_questions = {f"vi_q{i}": request.POST[f"vi_q{i}"] for i in range(1, 7)}
        lof_questions = {f"lof_q{i}": request.POST[f"lof_q{i}"] for i in range(1, 13)}
        hi_questions = {f"hi_q{i}": request.POST[f"hi_q{i}"] for i in range(1, 23)}
        dvpi_questions = {f"dvpi_q{i}": request.POST[f"dvpi_q{i}"] for i in range(1, 16)}
    
        MAST_questions = {
            "q0": "Do you enjoy a drink now and then?",
            "q1": "Do you feel you are a normal drinker? (By normal, we mean you drink less than or as much as most other people)",
            "q2": "Have you ever awakened the morning after drinking and found that you could not remember a part of the evening?",
            "q3": "Does your spouse (or do your parents) ever worry or complain about your drinking?",
            "q4": "Can you stop drinking without difficulty after one or two drinks?",
            "q5": "Do you ever feel guilty about your drinking?",
            "q6": "Friends or relatives think you are a normal drinker?",
            "q7": "Are you able to stop drinking when you want to?",
            "q8": "Have you ever attended a meeting of Alcoholics Anonymous (AA)?",
            "q9": "Have you gotten into physical fights when drinking?",
            "q10": "Has drinking ever created problems between you and a near relative or close friend?",
            "q11": "Has any family member or close friend gone to anyone for help about your drinking?",
            "q12": "Have you ever lost friends because of your drinking?",
            "q13": "Have you ever gotten into trouble at work because of drinking?",
            "q14": "Have you ever lost a job because of drinking?",
            "q15": "Have you ever neglected your obligations, your family, or your work for two or more days in a row because you were drinking?",
            "q16": "Do you drink before noon fairly often?",
            "q17": "Have you ever been told you have liver trouble such as cirrhosis?",
            "q18": "After heavy drinking, have you ever had delirium tremens (D.T.s), severe shaking, heard voices, or seen things that weren’t there?",
            "q19": "Have you ever gone to anyone for help about your drinking?",
            "q20": "Have you ever been hospitalized because of drinking?",
            "q21": "Has your drinking ever resulted in your being hospitalized in a psychiatric ward?",
            "q22": "Have you ever gone to any doctor, social worker, or clergyman for help with any emotional problem in which drinking was part of the problem?",
            "q23": "Have you been arrested more than once for driving under the influence of alcohol?",
            "q24": "Have you ever been arrested, even for a few hours, because of other drunken behavior?"
        }

        ADHS_questions = {
            "ADHS_q1": "Have you had 3 or more alcohol/drug related arrests/citations?",
            "ADHS_q2": "Was your blood alcohol level .15 or above?",
            "ADHS_q3": "Do you habitually abuse or have a problem controlling alcohol or drugs?",
            "ADHS_q4": "Do you feel you have a problem with alcohol/drugs?",
            "ADHS_q5": "Have you been diagnosed with substance abuse or organic brain disease due to substance abuse?",
            "ADHS_q6": "Have you experienced any of these withdrawal symptoms: Hallucinogens",
            "ADHS_q7": "Have you experienced any of these withdrawal symptoms: Convulsive Seizures",
            "ADHS_q8": "Have you experienced any of these withdrawal symptoms: Delirium tremens",
            "ADHS_q9": "Have been medically diagnosed as having any of these complications: Alcohol liver disease",
            "ADHS_q10": "Have been medically diagnosed as having any of these complications: Alcoholic pancreatitis",
            "ADHS_q11": "Have been medically diagnosed as having any of these complications: Alcoholic cardiomyopathy",
            "ADHS_q12": "Have you had two alcohol/drug related arrests/citations?",
            "ADHS_q13": "Have you ever lost time from work or school due to alcohol or drug use?",
            "ADHS_q14": "Have you had any problems with family, friends or peers due to your alcohol/drug use?",
            "ADHS_q15": "Have you had 3 or more alcohol/drug related arrests/citations?",
            "ADHS_q16": "Have you ever gone to a DUI class, Alcohol/Drug class, medical facility, or treatment center because of your alcohol/drug use?",
            "ADHS_q17": "Have you ever had any memory loss after alcohol/drug use?",
            "ADHS_q18": "Have you ever passed out (become unconscious) after drinking/drug use?",
            "ADHS_q19": "Have you experienced any of these after alcohol/drug use: Shakes or malaise relieved by drinking/using",
            "ADHS_q20": "Have you experienced any of these after alcohol/drug use: Irritability",
            "ADHS_q21": "Have you experienced any of these after alcohol/drug use: Nausea",
            "ADHS_q22": "Have you experienced any of these after alcohol/drug use: Anxiety",
            "ADHS_q23": "Have you used alcohol/drugs to cope with or escape from problems/stress?",
            "ADHS_q24": "Have you experienced an increase of use, a change of tolerance (e.g. BAC ≥ .18) or change in pattern of use?",
            "ADHS_q25": "Have you ever had dramatic personality changes after alcohol/drug use?"
        }

        ABI_questions = {
            "abi_q1": "Have you attended class or a program for anger or destructive behavior?",
            "abi_q2": "Have you been cited, arrested or charged for threatening someone, property damage, assault or other aggressive acts?",
            "abi_q3": "Do your feelings build up so that you feel like exploding?",
            "abi_q4": "Do you get mad easily or have an explosive temper?",
            "abi_q5": "Do people tell you to calm down?",
            "abi_q6": "Do you sometimes feel so angry you could lose control?",
            "abi_q7": "Do you hit, kick, punch, destroy or throw things when you are very upset?",
            "abi_q8": "Has your anger ever caused problems for your family, friends and/or partner?",
            "abi_q9": "Do you get into arguments or fights even when you don't want to?",
            "abi_q10": "Have you lost time at work or school or lost friends because of your temper?",
        }

        TVI_questions = {
            "tvi_q1": "1. Have you experienced or witnessed a life threatening or terrifying event? Explain.",
            "tvi_q2": "1. Have you experienced or witnessed a life threatening or terrifying event?",
            "tvi_q3": "2. Have you witnessed or experienced physical, emotional or sexual abuse? Who?",
            "tvi_q4": "2. Have you witnessed or experienced physical, emotional or sexual abuse? When?",
            "tvi_q5": "2. Have you witnessed or experienced physical, emotional or sexual abuse? How many times?",
            "tvi_q6": "2. Have you witnessed or experienced physical, emotional or sexual abuse?",
            "tvi_q7": "3. Have you been, or witnessed kidnapping, beating, shooting, stabbing, threatening or any other form of victimization? Who?",
            "tvi_q8": "3. Have you been, or witnessed kidnapping, beating, shooting, stabbing, threatening or any other form of victimization? When?",
            "tvi_q9": "3. Have you been, or witnessed kidnapping, beating, shooting, stabbing, threatening or any other form of victimization? How many times?",
            "tvi_q10": "3. Have you been, or witnessed kidnapping, beating, shooting, stabbing, threatening or any other form of victimization?",
            "tvi_q11": "4. Have you witnessed or experienced months of ongoing intense emotional distress? Explain.",
            "tvi_q12": "4. Have you witnessed or experienced months of ongoing intense emotional distress?",
            "tvi_q13": "5. Have you received medical, psychiatric, psychological or counseling treatment for any items 1 through 4? If yes, explain",
            "tvi_q14": "5. Have you received medical, psychiatric, psychological or counseling treatment for any items 1 through 4? What treatment did you receive?",
            "tvi_q15": "5. Have you received medical, psychiatric, psychological or counseling treatment for any items 1 through 4? Are you satisfied with the treatment result? Explain"

        }

        SI_questions = {
            "si_q1": "1. Has life become very painful or unbearable?",
            "si_q2": "2. Do you feel overwhelming pain, distress or depression?",
            "si_q3": "3. Do you feel that life is not worth living?",
            "si_q4": "4. Have you thought of hurting yourself or killing yourself? How many times?",
            "si_q5": "4. Have you thought of hurting yourself or killing yourself? When?",
            "si_q6": "4. Have you thought of hurting yourself or killing yourself?",
            "si_q7": "5. Have you ever made any plans to hurt or kill yourself? How many times?",
            "si_q8": "5. Have you ever made any plans to hurt or kill yourself? When?",
            "si_q9": "5. Have you ever made any plans to hurt or kill yourself?",
            "si_q10": "6. Have you ever attempted to hurt or kill yourself? When?",
            "si_q11": "6. Have you ever attempted to hurt or kill yourself? How?",
            "si_q12": "6. Have you ever attempted to hurt or kill yourself?",
            "si_q13": "7. Do you want to hurt or kill yourself now?",
            "si_q14": "8. Do you have a plan about how to hurt or kill yourself?",
            "si_q15": "9. [Additional information for yes answers if any]",
            # Continue with additional questions if they exist, based on the naming convention used in your form
        }

        DI_questions = {
            "di_q1": "1. Do you feel undeserving or worthless?",
            "di_q2": "2. [The second question's text]",
            "di_q3": "3. [The third question's text]",
            "di_q4": "4. Do you feel hopeless about your future?",
            "di_q5": "5. Has your sleep been restless lately?",
            "di_q6": "6. Have you enjoyed yourself lately?",
            "di_q7": "7. Do you feel your life is a failure lately?",
            "di_q8": "8. Do you feel you just can't get going?",
            "di_q9": "9. Are you often unhappy?",
            "di_q10": "10. Are you very angry with yourself?",
            "di_q11": "[The additional explanation's prompt for yes answers]"
        }

        VI_questions = {
            "vi_q1": "The conflict that brought me to this screening involved which of the following, to the other person: No Injury",
            "vi_q2": "The conflict that brought me to this screening involved which of the following, to the other person: A minor injury with complete recovery in a few days",
            "vi_q3": "The conflict that brought me to this screening involved which of the following, to the other person: Injury with complete recovery in a few weeks",
            "vi_q4": "The conflict that brought me to this screening involved which of the following, to the other person: Injury with complete recovery in a few months",
            "vi_q5": "The conflict that brought me to this screening involved which of the following, to the other person: Disabling Injury",
            "vi_q6": "The conflict that brought me to this screening involved which of the following, to the other person: Death"
        }

        LOF_questions = {
            "lof_q1": "Arguing (without threats)",
            "lof_q2": "Property damage or yelling (without threats)",
            "lof_q3": "Physical contact or threat of contact (push, hold, slaps, restrain, block movement)",
            "lof_q4": "Physical force or threat of force (hit, punch, kick, bite, etc)",
            "lof_q5": "Weapon display or threat of weapon use (club, knife, gun, etc)",
            "lof_q6": "Weapon use, choking or forced sex",
            "lof_q7": "Arguing (without threats) - Other person's actions",
            "lof_q8": "Property damage or yelling (without threats) - Other person's actions",
            "lof_q9": "Physical contact or threat of contact (push, hold, slaps, restrain, block movement) - Other person's actions",
            "lof_q10" :"Physical force or threat of force (hit, punch, kick, bite, etc)",
            "lof_q11" : "Weapon display or threat of weapon use (club, knife, gun, etc)",
            "lof_q12" : " Weapon use, choking or forced sex"
        }

        HI_questions = {
            "hi_q1": "Was there a time when you were often in fights? When?",
            "hi_q2": "Was there a time when you were often in fights? Why?",
            "hi_q3": "Was there a time when you were often in fights?",
            "hi_q4": "Do you feel you must control others or be in charge? When?",
            "hi_q5": "Do you feel you must control others or be in charge? How?",
            "hi_q6": "Do you feel you must control others or be in charge?",
            "hi_q7": "Do you like to carry a weapon for protection or to feel powerful?",
            "hi_q8": "Do you feel so hurt that you have the right to hurt someone? Who?",
            "hi_q9": "Do you feel so hurt that you have the right to hurt someone?",
            "hi_q10": "Are you going to pursue, follow or stalk someone? Who?",
            "hi_q11": "Are you going to pursue, follow or stalk someone?",
            "hi_q12": "Are you angry enough to hit or harm someone? Who?",
            "hi_q13": "Are you angry enough to hit or harm someone?",
            "hi_q14": "Are you seeking revenge with someone? Who?",
            "hi_q15": "Are you seeking revenge with someone?",
            "hi_q16": "Are you going to confront someone verbally? Who?",
            "hi_q17": "Are you going to confront someone verbally?",
            "hi_q18": "Are you going to confront someone with force or a weapon? Who?",
            "hi_q19": "Are you going to confront someone with force or a weapon?",
            "hi_q20": "Are you going to harm someone? Who?",
            "hi_q21": "Are you going to harm someone? ",
            "hi_q22": "Are you going to harm someone? Explain."


        }

        DVPI_questions = {
            "dvpi_q1": "Have you been cited, arrested, or charged for threatening someone, property damage, assault, or other aggressive acts? How many times?",
            "dvpi_q2": "Have you been cited, arrested, or charged for threatening someone, property damage, assault, or other aggressive acts?",
            "dvpi_q3": "Have you attended or been referred to a domestic violence offender treatment program, including today? How many times?",
            "dvpi_q4": "Have you attended or been referred to a domestic violence offender treatment program, including today?",
            "dvpi_q5": "Have you ever been so angry that you threatened, restrained, hit, shoved or kicked your partner or a family member?",
            "dvpi_q6": "Do your conflicts usually follow a pattern of tension building, followed by a blow up and then a peaceful time?",
            "dvpi_q7": "Have you ever stalked anyone? How many times?",
            "dvpi_q8": "Have you ever stalked anyone?",
            "dvpi_q9": "Do you become jealous easily? Why?",
            "dvpi_q10": "Do you become jealous easily?",
            "dvpi_q11": "Do you control others for their own good or to protect them?",
            "dvpi_q12": "Do you feel you could lose control and abuse or assault your partner or family member?",
            "dvpi_q13": "Do you use anger, intimidation or threats to control your partner or family member? How many times?",
            "dvpi_q14": "Do you use anger, intimidation or threats to control your partner or family member?",
            "dvpi_q15": "Do you ever feel calm and composed when you are angry or during conflicts?",

        }



        # Combine all data into a single dictionary to store in MongoDB
        assessment_data = {
            'intake_assessment': intake_assessment,

            'mast_questions': MAST_questions,
            'adhs_questions': ADHS_questions,
            'abi_questions': ABI_questions,
            'tvi_questions': TVI_questions,
            'si_questions': SI_questions,
            'di_questions': DI_questions,
            'vi_questions': VI_questions,
            'lof_questions': LOF_questions,
            'hi_questions': HI_questions,
            'dvpi_questions': DVPI_questions,

            'mast_answers': mast_questions,
            'adhs_answers': adhs_questions,
            'abi_answers': abi_questions,
            'tvi_answers': tvi_questions,
            'si_answers': si_questions,
            'di_answers': di_questions,
            'vi_answers': vi_questions,
            'lof_answers': lof_questions,
            'hi_answers': hi_questions,
            'dvpi_answers': dvpi_questions,
        }

        assessment_score = askOpenAI(assessment_data)
        assessment = {
            "client_info" : client_info,
            "assessment_data" : assessment_data,
            "assessment_score" : assessment_score
        }
        # Insert into MongoDB
        insert_result = screening_collection.insert_one(assessment)
        

        if insert_result.inserted_id:
            messages.success(request, "Screening data saved successfully.")
        else:
            messages.error(request, "Failed to save screening data.")
            return render(request, 'screeningTest.html')
            

    return render(request, 'userAuthentication/screeningTest.html', {'username': username})


    
def today(request):

    current_date = timezone.now().date() 
    current_date_datetime = datetime.combine(current_date, datetime.now().time())
    username = request.GET.get('username', None)
    
    if not myAuthentication.is_auth:
        return redirect('signin')

    if request.method == 'POST':
        username = request.POST.get('username', None)
        text_entry = request.POST.get('text_entry', None)
        video_file = request.FILES.get('video', None)
        audio_file = request.FILES.get('audio', None)
        other_file = request.FILES.get('other_file', None)
        goToEntries = request.POST.get('goToEntries', None)
        if goToEntries:
            return render(request, 'userAuthentication/entries.html')

        if audio_file:
            audio_id = fs.put(audio_file, filename = audio_file.name, content_type = audio_file.content_type)
            

            audio_entry = {
                'username': username,
                'date' : current_date_datetime,
                'audio_id': audio_id
                # Add other relevant fields if needed
            }
            audio_entries_collection.insert_one(audio_entry)

        if other_file:
            otherFile_id = fs.put(other_file, filename = other_file.name, content_type = other_file.content_type)
            
            otherFile_entry = {
                'username': username,
                'date' : current_date_datetime,
                'otherFile_id': otherFile_id
                # Add other relevant fields if needed
            }
            otherFiles_entries_collection.insert_one(otherFile_entry)
        
        if video_file:
            # Get the GridFS instance and open an upload stream for the video
              # Assuming 'db' is your MongoDB database connection
            video_id = fs.put(video_file, filename=video_file.name, content_type=video_file.content_type)

            # Add the video entry to your collection
            video_entry = {
                'username': username,
                'date' : current_date_datetime,
                'video_id': video_id
                # Add other relevant fields if needed
            }
            video_entries_collection.insert_one(video_entry)

        if text_entry:
            text_journal_entry = {
                'username': username,
                'date' : current_date_datetime,
                'text_entry': text_entry
            }
            text_entries_collection.insert_one(text_journal_entry)

        return redirect(reverse('entries') + f'?username={username}')

    return render(request, 'userAuthentication/today.html', {'username': username})

def entries(request):
    current_date = timezone.now().date()
    username = request.GET.get('username', None)
    
    if not (myAuthentication.is_auth and myAuthentication.username == username ):
        return redirect('signin')
    
    # Query your database to retrieve the entries for the logged-in user
    # Convert the cursor objects to lists so you can iterate over them in the template
    textEntries = list(text_entries_collection.find({'username': username}))
    videoEntries = list(video_entries_collection.find({'username': username}))
    audioEntries = list(audio_entries_collection.find({'username': username}))
    otherEntries = list(otherFiles_entries_collection.find({'username': username}))

    file_id = []

    for entry in videoEntries:
        file_id.append(entry['video_id'])
        
    for entry in audioEntries:
        file_id.append(entry['audio_id'])
    
    for entry in otherEntries:
        file_id.append(entry['otherFile_id'])

    return render(request, 'userAuthentication/entries.html', {
        'username': username, 
        'textEntries': textEntries, 
        'videoEntries': videoEntries,
        'audioEntries': audioEntries,
        'otherEntries': otherEntries,
        'fileEntries': file_id  # this remains unchanged
    })

def serve_file(request, file_id):
    # Retrieve the video file from GridFS by its ObjectI
    print("Hello")
    file_id = ObjectId(f'{file_id}')
    file = fs.get(file_id)

    if file:
        # Set the response headers for serving a video
        response = HttpResponse(file.read(), content_type=file.content_type)
        response['Content-Disposition'] = f'attachment; filename="file.filename"'
        return response
    
    # Handle the case when the video is not found
    return HttpResponse('Video not found', status=404)

def adminDashboard(request, selected_username = None):
    username = request.GET.get('username', None)
    if not (myAuthentication.is_auth and myAuthentication.is_admin):
        return redirect('signin')
    current_date = timezone.now().date()

    users = logIn_collection.find()
    user_journals = []
    textEntries = []
    videoEntries = []
    audioEntries = []
    otherEntries = []


    if selected_username:
        textEntries = list(text_entries_collection.find({'username': selected_username}))
        videoEntries = list(video_entries_collection.find({'username': selected_username}))
        audioEntries = list(audio_entries_collection.find({'username': selected_username}))
        otherEntries = list(otherFiles_entries_collection.find({'username': selected_username}))

        

    
    return render(request, 'userAuthentication/adminDashboard.html', {
        'users': users,
        'selected_user': selected_username,
        'textEntries': textEntries, 
        'videoEntries': videoEntries,
        'audioEntries': audioEntries,
        'otherEntries': otherEntries,
        'user_journals': user_journals
    })

def generic(request):
    return render(request, 'userAuthentication/generic.html')


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


