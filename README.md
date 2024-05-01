# ResearchDevelopmentProject-AICounseling
Learn more about this Research and Development Project (Artificial Intelligence Augmented Counseling) at https://research.gcu.edu/rdp/cse

# About Our Team
![image](https://github.com/utzerath/AI-Augmented-Counseling/assets/97542190/9a3aa1e7-065f-4040-a13c-eca2c3494e35)

### My part in this team:
Build a website with Front and Backend Capabilites in order to optimze healthcare

### Purpose
This website optmizes counseling in two different ways. 

First, users can automatically upload their journal entries so that the counselor can see how their patient is doing before they have an in-person session. This will mean that they spend less time catching up, allowing the counselor to focus on the heart of the session.

Secondly, users can take a DUI screening assessment. After one receives a DUI, court-ordered counseling is often the outcome. Judges use this DUI screening assessment in court. This assessment is also given to the counselor, who is able to evaluate this assessment and devise a counseling plan. By scoring and evaluating this assessment automatically, we will eliminate human error in scoring (misinterpretations, miscalculations, ambiguous answers/questions, subjective answers). In addition, the counselor will automatically use this evaluation generated by OpenAI.

### What I used to develop this website:
Django

### Website Capabilities

Login + Singup Features

Authentication and Authorization Techniques

Users can take DUI Screening Assement with automatic AI scoring and evaluation

Admin Dashboard- Can we users journal entries

Users can upload Journal entries

All data is stored in a database

### Sensym Webstie- HTML Pages
HomePage

Singin

Singup

screeningTest.html (more about this in navigating and using sensym)

adminDashboard

entries

today

### Back End
-MongoDB

Whats in our DB?

##### adminLogIn

-username

-fname

-lname

-email

-password

##### entries (journal entries a user upload or write)

-username

-date

-foreign key to file (we need this in order to retrieve journal entries)

##### files 

These are binary files that the package gridFS uploads (we use these for video and audio journal entries)

##### logIn

-username

-fname

-lname

-email

-password

##### screening

-Client Info

-Assessment_Data

-Assessment_Score (Automatically Evaluated by ChatGPT)
