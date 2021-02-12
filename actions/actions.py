# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
#
#
# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.types import DomainDict
import webbrowser

class validateDeliveryForm(Action):

    def name(self) -> Text:
        return "user_details_form"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict
    ) -> List[EventType]:
        required_slots = ["name","number","delivery_location","restaurant_name","item_name"]

        for slot_name in required_slots:
            if tracker.slots.get(slot_name) is None:
                return[SlotSet("requested_slot",slot_name)]

        return[SlotSet("requested_slot",slot_name)]



class ActionSubmit(Action):
    def name(self) -> Text:
        return "action_submit"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text,Any],
    )  -> List[Dict[Text, Any]]:
         dispatcher.utter_message(template="utter_details_thanks",Name=tracker.get_slot("name"),Mobile_number=tracker.get_slot("number"),Delivery_location=tracker.get_slot("delivery_location"),Restaurant_name=tracker.get_slot("restaurant_name"),Item_name=tracker.get_slot("item_name"))

         return []


class ValidateDeliveryForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_user_details_form"

    def validate_number(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:

        #num=tracker.get_slot("number")
        if len(value) == 10:
            return{"number": value}
        else:
            dispatcher.utter_message(template="utter_ask_wrong_number")
            return{"number": None}
    # @staticmethod
    # def cuisine_db() -> List[Text]:
    #     """Database of supported cuisines"""
    #
    #     return ["caribbean", "chinese", "french"]
    #
    # def validate_cuisine(
    #     self,
    #     slot_value: Any,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: DomainDict,
    # ) -> Dict[Text, Any]:
    #     """Validate cuisine value."""
    #
    #     if slot_value.lower() in self.cuisine_db():
    #         # validation succeeded, set the value of the "cuisine" slot to value
    #         return {"cuisine": slot_value}
    #     else:
    #         # validation failed, set this slot to None so that the
    #         # user will be asked for the slot again
    #         return {"cuisine": None}