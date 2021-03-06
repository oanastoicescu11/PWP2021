import json
import datetime

from werkzeug.datastructures import Headers
from tapi.constants import *
from flask import request, Response


# MasonBuilder was given during the exercises. Here with no modifications.
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


# Helper for creating person with metadata
def person_to_api_person(person):
    # convert a Person db item to a corresponding PersonItem API schema JSON presentation
    p = CalorieBuilder({
        'id': person.id,
    })
    return p


def meal_to_api_meal(meal):
    # convert a Meal db item to a corresponding MealItem API schema JSON presentation
    m = CalorieBuilder({
        'id': meal.id,
        'name': meal.name,
        'description': meal.description,
        'servings': meal.servings
    })
    return m


def mealrecord_to_api_mealrecord(mealrecord):
    # convert a MealRecord db item to a corresponding MealRecordItem API schema JSON presentation
    m = CalorieBuilder({
        'person_id': mealrecord.person_id,
        'meal_id': mealrecord.meal_id,
        'amount': mealrecord.amount,
        'timestamp': mealrecord.timestamp
    })
    return m


def mealportion_to_api_mealportion(mealportion):
    # convert a MealRecord db item to a corresponding MealRecordItem API schema JSON presentation
    m = CalorieBuilder({
        'portion_id': mealportion.portion_id,
        'meal_id': mealportion.meal_id,
        'weight_per_serving': mealportion.weight_per_serving
    })
    return m


def portion_to_api_portion(portion):
    # convert a Portion db item to a corresponding PortionItem API schema JSON presentation
    p = CalorieBuilder({
        'id': portion.id,
        'name': portion.name,
        'calories': portion.calories,
        'density': portion.density,
        'alcohol': portion.alcohol,
        'carbohydrate': portion.carbohydrate,
        'protein': portion.protein,
        'fat': portion.fat

    })
    return p


def myconverter(o):
    # converter for datetime object to json representation
    if isinstance(o, datetime.datetime):
        return o.__str__()


def make_mealportion_handle(meal, portion):
    return "{}-{}".format(meal, portion)


def make_mealrecord_handle(person, meal, timestamp):
    # parse parameters to make unique handle
    handle = person + '-' + meal + '-' + \
             datetime.datetime.strftime(timestamp, '%Y-%m-%d %H:%M:%S.%f').replace(" ", "_")
    return handle


class CalorieBuilder(MasonBuilder):
    """ CalorieBuilder is a neat utility class for building the MASON response """
    def add_control_profile(self):
        # profile is IANA defined control, outside of calorie namespace
        self.add_control(
            "profile",
            # TODO: entity specific url
            href=URL_PROFILE
        )

    def add_control_collection(self, href):
        # collection is IANA defined control, outside of calorie namespace
        self.add_control(
            "collection",
            href=href
        )

    def add_control_self(self, href):
        # self is IANA defined control, outside of calorie namespace
        self.add_control(
            "self",
            href=href
        )

    def add_control_delete(self, href):
        # delete is calmeta specific control, within calorie namespace
        self.add_control(
            NS + ':delete',
            method="DELETE",
            href=href
        )


def add_calorie_namespace(resp):
    resp.add_namespace(NS, URL_LINK_RELATIONS)


def add_mason_response_header(headers=None):
    # helper for adding mason content type for a header
    if headers is None:
        headers = Headers()
    headers.add('Content-Type', MASON)
    return headers


# create_error_response was given in the exercise
def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


def error_404():
    return create_error_response(
        404, "Not found!", "Entity not found with given handle.")


def error_415():
    return create_error_response(
        415, "Invalid Content-Type", "Request content type must be JSON")


def error_409():
    return create_error_response(
        409, "Already exists!", "Entity with given handle already exists.")


def error_400():
    return create_error_response(
        400, "Invalid JSON", "Request JSON does not follow the jsonschema.")
