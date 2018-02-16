from __future__ import absolute_import
import json
import pytz
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime

from corehq import toggles
from corehq.apps.domain.decorators import api_auth, check_domain_migration, two_factor_exempt
from dimagi.utils.web import json_response
from dimagi.utils.logging import notify_exception

from corehq.motech.repeaters.views import AddCaseRepeaterView
from custom.enikshay.integrations.ninetyninedots.exceptions import NinetyNineDotsException
from custom.enikshay.integrations.ninetyninedots.utils import (
    AdherenceCaseFactory,
    PatientDetailsUpdater,
    update_adherence_confidence_level,
    update_default_confidence_level,
)
import six


class RegisterPatientRepeaterView(AddCaseRepeaterView):
    urlname = 'register_99dots_patient'
    page_title = "Register 99DOTS Patients"
    page_name = "Register 99DOTS Patients"


class UpdatePatientRepeaterView(AddCaseRepeaterView):
    urlname = 'update_99dots_patient'
    page_title = "Update 99DOTS Patients"
    page_name = "Update 99DOTS Patients"


class UpdateAdherenceRepeaterView(AddCaseRepeaterView):
    urlname = 'update_99dots_adherence'
    page_title = "Update 99DOTS Adherence"
    page_name = "Update 99DOTS Adherence"


class UpdateTreatmentOutcomeRepeaterView(AddCaseRepeaterView):
    urlname = 'update_99dots_treatment_outcome'
    page_title = "Update 99DOTS Treatment Outcome"
    page_name = "Update 99DOTS Treatment Outcome"


class UnenrollPatientRepeaterView(AddCaseRepeaterView):
    urlname = 'unenroll_99dots_patient'
    page_title = "Unenroll 99DOTS Patients"
    page_name = "Unenroll 99DOTS Patients"


@toggles.NINETYNINE_DOTS.required_decorator()
@api_auth
@two_factor_exempt
@require_POST
@csrf_exempt
@check_domain_migration
def update_patient_adherence(request, domain):
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return json_response({"error": "Malformed JSON"}, status_code=400)

    beneficiary_id = request_json.get('beneficiary_id')
    adherence_values = request_json.get('adherences')
    factory = AdherenceCaseFactory(domain, beneficiary_id)

    try:
        validate_beneficiary_id(beneficiary_id)
        validate_adherence_values(adherence_values)
        factory.create_adherence_cases(adherence_values)
    except NinetyNineDotsException as e:
        return json_response({"error": six.text_type(e)}, status_code=400)

    try:
        factory.update_episode_adherence_properties()
    except NinetyNineDotsException as e:
        notify_exception(
            request,
            message=("An error occurred updating the episode case after receiving a 99DOTS"
                     "adherence case for beneficiary {}. {}").format(beneficiary_id, e))
    return json_response({"success": "Patient adherences updated."})


@toggles.NINETYNINE_DOTS.required_decorator()
@api_auth
@two_factor_exempt
@require_POST
@csrf_exempt
@check_domain_migration
def update_patient_details(request, domain):
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return json_response({"error": "Malformed JSON"}, status_code=400)

    try:
        PatientDetailsUpdater(domain, request_json).update_cases()
    except NinetyNineDotsException as e:
        return json_response({"error": six.text_type(e)}, status_code=400)

    return json_response({"success": "Patient details updated."})


@toggles.NINETYNINE_DOTS.required_decorator()
@api_auth
@two_factor_exempt
@require_POST
@csrf_exempt
@check_domain_migration
def update_adherence_confidence(request, domain):
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return json_response({"error": "Malformed JSON"}, status_code=400)
    beneficiary_id = request_json.get('beneficiary_id')
    start_date = request_json.get('start_date')
    end_date = request_json.get('end_date')
    confidence_level = request_json.get('confidence_level')

    try:
        validate_beneficiary_id(beneficiary_id)
        validate_dates(start_date, end_date)
        validate_confidence_level(confidence_level)
        update_adherence_confidence_level(
            domain=domain,
            person_id=beneficiary_id,
            start_date=parse_datetime(start_date),
            end_date=parse_datetime(end_date),
            new_confidence=confidence_level
        )
    except NinetyNineDotsException as e:
        return json_response({"error": e.message}, status_code=400)

    return json_response({"success": "Patient adherences updated."})


@toggles.NINETYNINE_DOTS.required_decorator()
@api_auth
@two_factor_exempt
@require_POST
@csrf_exempt
@check_domain_migration
def update_default_confidence(request, domain):
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return json_response({"error": "Malformed JSON"}, status_code=400)

    beneficiary_id = request_json.get('beneficiary_id')
    confidence_level = request_json.get('confidence_level')

    try:
        validate_beneficiary_id(beneficiary_id)
        validate_confidence_level(confidence_level)
        update_default_confidence_level(domain, beneficiary_id, confidence_level)
    except NinetyNineDotsException as e:
        return json_response({"error": e.message}, status_code=400)

    return json_response({"success": "Default Confidence Updated"})


def validate_beneficiary_id(beneficiary_id):
    if beneficiary_id is None:
        raise NinetyNineDotsException("Beneficiary ID is null")
    if not isinstance(beneficiary_id, six.string_types):
        raise NinetyNineDotsException("Beneficiary ID should be a string")


def validate_dates(start_date, end_date):
    if start_date is None:
        raise NinetyNineDotsException("start_date is null")
    if end_date is None:
        raise NinetyNineDotsException("end_date is null")
    try:
        parse_datetime(start_date).astimezone(pytz.UTC)
        parse_datetime(end_date).astimezone(pytz.UTC)
    except:
        raise NinetyNineDotsException("Malformed Date")


def validate_adherence_values(adherence_values):
    if adherence_values is None or not isinstance(adherence_values, list):
        raise NinetyNineDotsException("Adherences invalid")


def validate_confidence_level(confidence_level):
    valid_confidence_levels = ['low', 'medium', 'high']
    if confidence_level not in valid_confidence_levels:
        raise NinetyNineDotsException(
            message="New confidence level invalid. Should be one of {}".format(
                valid_confidence_levels
            )
        )
