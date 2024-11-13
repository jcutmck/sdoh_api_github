from flask import Blueprint, request, jsonify, current_app, session
from utils.extensions import cache
import requests
from functools import wraps
from datetime import datetime
import pytz

submit_bp = Blueprint('submit', __name__)

# Define the decorator here, before the routes
def require_validation(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get("Session-ID")
        validate_token = request.headers.get("Validation-Token")

        if not session_id or not validate_token:
            return jsonify({"error": "Missing session ID or validation token"}), 401

        stored_token = cache.get(f"{session_id}_validation_token")
        if not stored_token or stored_token != validate_token:
            return jsonify({"error": "Invalid or expired verification token"}), 401

        return f(*args, **kwargs)
    return decorated_function


@submit_bp.route('/api/submit', methods=['POST', 'OPTIONS'])
def submit():
    if request.method == 'OPTIONS':
        # Handle preflight CORS requests
        return '', 204  # No Content for preflight requests

    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"error": "Unsupported Media Type"}), 415


    current_app.logger.info("!!START of FSCOMMIT-SUBMIT ROUTE!!")
    data = request.json
    current_app.logger.info(data)
    session_id = request.headers.get('Session-ID')
    validation_data = cache.get(session_id)
    current_app.logger.info(f"FSCOMMIT -Session ID: {session_id}")
    current_app.logger.info(f"FSCOMMIT -Session data set: {session.get('{session_id}_validation_data')}")

    # Get current date and time in EST/EDT timezone
    est_timezone = pytz.timezone('America/New_York') 
    current_datetime = datetime.now(est_timezone)

    # Format the date and time
    date_str = current_datetime.strftime('%Y-%m-%d')
    time_str = current_datetime.strftime('%H:%M')

    current_app.logger.info(f"Date: {date_str}, Time: {time_str}")

    fname = validation_data.get('FNM')
    lname = validation_data.get('LNM')
    dtbrt = validation_data.get('DOB')
    rsltdt = date_str
    rslttm = time_str
    mrn = cache.get(f"{session_id}_mrn")
    fin = cache.get(f"{session_id}_fin")
    participate = data.get('participation')
    nonparticipant = "I choose not to answer"

    if (participate == "I choose not to participate"):
        hous_sec = nonparticipant
        hous_con = nonparticipant
        food_sec = nonparticipant
        food_acc = nonparticipant
        heal_acc = nonparticipant
        util_sec = nonparticipant
        care_acc = nonparticipant
        occu_acc = nonparticipant
        educ_sec = nonparticipant
        fina_sec = nonparticipant
        phys_sec = nonparticipant
        emot_sec = nonparticipant
        safe_sec = nonparticipant
        well_sec = nonparticipant
        legal_sec = nonparticipant
        refuge_sec = nonparticipant
        military_stat = nonparticipant
        help_req = "no"
        sdohConsentProgram = "I do not agree"
        sdohConsentHelp = "I do not agree"
        hous_con_str = nonparticipant
    elif (participate == "I choose to participate"):
        hous_sec = data.get('housingSecurity')
        # Capture the housingCondition values as a list
        hous_con = data.get('housingCondition', [])
        food_sec = data.get('foodSecurity')
        food_acc = data.get('foodAccess')
        heal_acc = data.get('healthcareAccess')
        util_sec = data.get('utilitySecurity')
        care_acc = data.get('childcareAccess')
        occu_acc = data.get('occupationAccess')
        educ_sec = data.get('educationAccess')
        fina_sec = data.get('financialSecurity')
        phys_sec = data.get('physicalSecurity')
        emot_sec = data.get('emotionalSecurity')
        safe_sec = data.get('safetySecurity')
        well_sec = data.get('wellbeingSecurity')
        legal_sec = data.get('legalStatus')
        refuge_sec = data.get('refugeSecurity')
        military_stat = data.get('militaryService')
        help_req = data.get('requestHelp')
        sdohConsentProgram = data.get('sdohConsentProgram')
        sdohConsentHelp = data.get('sdohConsentHelp')
        hous_con_str = "\n".join(hous_con)

    #nonprod form = 5848665
    #prod form = 5780073
    formstack= 'https://www.formstack.com/api/v2/form/5848665/submission.json'

    # Conditional logic to set domain data - Only set if relevant values are not empty
    # Financial Domain
 #   if all(value != '' for value in [occu_acc, educ_sec, fina_sec]):

    # All positive frequency answers
    pos_true_answers = {"Sometimes true", "Often true"}

    # All positive frequency answers
    pos_freq_answers = {"Sometimes", "Fairly often", "Frequently"}

    if (fina_sec in pos_freq_answers):
        domain_financial = "POSITIVE"
    else:
        domain_financial = "negative" 

    # Childcare Domain
    #  if care_acc != '':
    if (care_acc == "Yes"):
        domain_childcare = "POSITIVE"
    else:
        domain_childcare = "negative"

    # Food Domain
   # if food_sec != '':
    if any(answer in pos_true_answers for answer in [food_acc, food_sec]):
        domain_food = "POSITIVE"
    else:
        domain_food = "negative"

    # Check if any concerning condition is selected in housing condition list
    housing_conditions = ["Bug infestation", "Mold", "Lead paint or pipes", "Inadequate heat",
        "Oven or stove not working", "No or not working smoke detectors", "Water leaks"]

    has_concerning_condition = any(condition in hous_con for condition in housing_conditions)

    # Housing domain
    #if all(value != '' for value in [hous_sec, hous_con]):
    if hous_sec == "Yes" or has_concerning_condition:
        domain_housing = "POSITIVE"
    else:
        domain_housing = "negative"

    # Safety Domain
    #if all(value != '' for value in [phys_sec, emot_sec, safe_sec, well_sec]):
    #if any(answer in pos_freq_answers for answer in [phys_sec, emot_sec, safe_sec, well_sec]):
        #domain_safety = "POSITIVE"
    #else:
        #domain_safety = "negative" 

    # Transport Domain
    #if food_sec != '':
    if (heal_acc == "Yes"):
        domain_transport = "POSITIVE"
    else:
        domain_transport = "negative"

    # Utility Domain
    #if food_sec != '':
    if (util_sec in ("Yes", "Already shut off")):
        domain_utility = "POSITIVE"
    else:
        domain_utility = "negative"

    # Personal Safety Score Calculator
    # Map scores to answers
    answer_scores = {
        "Never": 1,
        "Rarely": 2,
        "Sometimes": 3,
        "Fairly often": 4,
        "Frequently": 5,
        "I choose not to answer": 0
    }

    # User entered values list
    answers = [phys_sec, emot_sec, safe_sec, well_sec]
    # Calculate total score
    # Default to 0 if answer is not found
    safety_score = sum(answer_scores.get(answer, 0) for answer in answers)
    current_app.logger.info(f"DOB: {dtbrt}")


    # Safety Domain
    #if all(value != '' for value in [phys_sec, emot_sec, safe_sec, well_sec]):
    if safety_score > 10:
        domain_safety = "POSITIVE"
    else:
        domain_safety = "negative"


    # Employment Domain
    if (occu_acc == "No"):
        domain_employment = "POSITIVE"
    else:
        domain_employment = "negative"

    # Education Domain
    if (educ_sec == "No"):
        domain_education = "POSITIVE"
    else:
        domain_education = "negative"

    # Additional Factors Domain
    if (legal_sec == "Yes" or refuge_sec == "Yes" or military_stat in ("Veteran/Honorably discharged", "Veteran/Dishonorably discharged")):
        domain_add_factors = "POSITIVE"
    else:
        domain_add_factors = "negative"

    # Send the data to the mock external system
    #responses = requests.post(f'http://{external_system_ip}/verify', json=data)


    # Construct payload for Formstack submission
    #non-prod:
    payload = {
        "field_169568839": {
          "first": fname,
          "last": lname,
        },
        "field_169568836": rsltdt,
        "field_169568837": rslttm,
        "field_169568834": mrn,      
        "field_169568835": fin,
        "field_169568840": dtbrt,
        "field_169568841": hous_sec,
        "field_169568842": hous_con_str, #hous_con,
        "field_169568843": food_sec,
        "field_169568844": food_acc,
        "field_169568845": heal_acc,
        "field_169568846": util_sec,
        "field_169568847": care_acc,
        "field_169568848": occu_acc,
        "field_169568849": educ_sec,
        "field_169568850": fina_sec,
        "field_169568851": phys_sec,
        "field_169568852": emot_sec,
        "field_169568853": safe_sec,
        "field_169568854": well_sec,
        "field_174042542": legal_sec,
        "field_174042555": refuge_sec,
        "field_174042557": military_stat,
        "field_169568855": help_req,
        "field_172501608": sdohConsentProgram,
        "field_171471885": sdohConsentHelp,
        "field_173550269": domain_financial,
        "field_173549876": domain_childcare,
        "field_173549893": domain_food,
        "field_173549892": domain_housing,
        "field_173549880": domain_safety,
        "field_173549879": domain_transport,
        "field_173550241": domain_utility,
        "field_174042914": domain_employment,
        "field_174042915": domain_education,
        "field_174042910": domain_add_factors,
        "field_173550244": safety_score,
        # Add more fields as needed
    }

#production:
#    payload = {
#	"field_166238501": {
#          "first": fname,
#          "last": lname,
#        },
#     	 "field_166238471": mrn,
#        "field_166238472": fin,
#        "field_166238529": dtbrt,
#        "field_166238573": hous_sec,
#        "field_166239604": hous_con_str, #hous_con,
#        "field_166239670": food_sec,
#        "field_166239685": food_acc,
#        "field_166239714": heal_acc,
#        "field_166239734": util_sec,
#        "field_166239744": care_acc,
#        "field_166239752": occu_acc,
#        "field_166239754": educ_sec,
#        "field_166239758": fina_sec,
#        "field_166239858": phys_sec,
#        "field_166239860": emot_sec,
#        "field_166239867": safe_sec,
#        "field_166239871": well_sec,
#        "field_166239912": help_req,
        # Add more fields as needed
#    }





# Retrieve the bearer token from a secure location
    bearer_token = "ccf1c3dd965d78588833343192c19514"  # Replace with actual token retrieval

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }

    # Send the data to FormStack
    response = requests.post(formstack, json=payload, headers=headers)


    # Check if the request was successful
    if response.status_code in {200,201}:
        # Assuming the Formstack API responds with JSON containing submission information
        response_data = response.json()
        return jsonify(response_data), 200  # Return the response from Formstack
    else:
        return jsonify({"error": "Failed to submit data to Formstack"}), response.status_code

# Additional test route for debugging purposes
#@submit_bp.route('/submit/test', methods=['GET'])
#def test_submit():
#    return "Submit endpoint is reachable!"
# Protected API route using decorator

@submit_bp.route('/api/protected-route', methods=['POST'])
@require_validation
def protected_route():
    # This route can only be accessed with a valid session ID and validation token
    return jsonify({"message": "Access granted to protected submission route"}), 200
