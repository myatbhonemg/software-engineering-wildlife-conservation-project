**#Log-in Accounts**
System admin
email: Admin@komodohun.com
password: password 

**#All the accounts below's password is "1".**
studen1@email.com
teacher1@email.com
sadmin1@email.com #school admin
principal1@email.com
cadmin1@email.com #Community admin
public1@email.com

# 5005CMD-Software-Engineering-Assessment

How User Registration Works: 

Komodo Hub uses a two-step registration system to ensure only verified users can access the platform. Users cannot create their own accounts - they must be registered by authorized administrators first.

The Two-Step Process
Step 1: Admin Registers the User
Who can register users:

School Admin → Can register Students and Teachers
Community Admin → Can register Community Members

What the admin does:

Admin logs into their dashboard
Goes to "Register Member" page
Fills out the new user's information
Clicks "Register"

What happens in the backend:

System checks if the email already exists in database
If email is NEW:
Create new user account

Important: At this step, User who was registered can register themselves.

Step 2: User Register
What the user does:

User goes to register account page.
Type in information including email.
Click Request Access Code button

Then, System check whether the user's email has been registered by admins or not. 
If registered, system will send the email that include access code.
User use the access code and finalise the registeration process.

Then, go to login page and go on to their dashboards.
