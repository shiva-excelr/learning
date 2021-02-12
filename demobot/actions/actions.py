# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


#This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import json
import requests
import traceback
import datetime
import random
from string import Template

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(template="utter_how_to_help")
        dispatcher.utter_message(template="utter_how_to_help_buttons")

        dispatcher.utter_message(template="utter_how_to_help_custom")
        dispatcher.utter_message(template="utter_how_to_help_custom_1")

        return []

class CustomBot105AskGreetName(Action):

    def name(self) -> Text:
        return "action_s_105_ask_greet_name"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List:
         #dispatcher.utter_template("utter_ask_greet_name", tracker)
        print("- action_s_105_ask_greet_name -->", tracker.latest_message)

        if tracker.sender_id is None:
            dispatcher.utter_message("Where did you come from, I never seen you...")
            return []

        last_template_event, last_event_custom_info, merged_custom = find_last_template_and_data(tracker.events)
        print("sender_id",tracker.sender_id)
        handle_greet_call(dispatcher, domain, tracker)

        #handle_all_other_cases(dispatcher, domain, tracker, last_template_event, last_event_custom_info, merged_custom)

        return []

def find_last_template_and_data(events):
  last_events = find_last_events(events, 3)
  if len(last_events) > 0:
    for e in reversed(last_events):
      last_event = e
      last_event_data = last_event["data"]
      if last_event_data["custom"] is not None and len(last_event_data["custom"]) > 0:
        merged_custom = {}
        if isinstance(last_event_data["custom"], str):
          last_event_data["custom"]["blocks"] = json.loads(last_event_data["custom"]["blocks"])
        #print("last_event_data['custom']-->",last_event_data["custom"]["blocks"])
        for c in last_event_data["custom"]["blocks"]:
            #print("c",c)
            merged_custom.update(c)
        if 'template_id' in merged_custom and "slot_name" in merged_custom:
          # if previous step all complete then don't send any merged_custom object back
          if merged_custom.get("template_id", "") == "utter_mark_steps_complete":
            merged_custom = {}
          #TODO: if the same template is repeating from last 2 conseqcutive runs.. just clear it out for now...!
          return e, last_event_data["custom"], merged_custom
  return None, None, None


def find_last_events(events, how_many=1):
  if events is not None and len(events) > 0:
    only_user_events = []
    for e in events:
      if e["event"] == "bot":
        only_user_events.append(e)
    if len(only_user_events) > 0:
      return only_user_events[how_many * -1:]

  return []

def handle_greet_call(dispatcher: object, domain: object, tracker: object) -> object:
    last_template_event, last_event_custom_info, merged_custom = find_last_template_and_data(tracker.events)
    print("[action_s_105_ask_greet_name] last_template_event ->", last_template_event)
    if last_event_custom_info is not None:
        # save the name to the template id
        # check the slot exist before
        event_slot_key = merged_custom.get("slot_name", None)
        if event_slot_key == "customerName":
            return handle_name_slot(dispatcher, domain, tracker, last_template_event, last_event_custom_info,
                                    merged_custom)
        elif merged_custom.get("template_id", "") == "how_to_help":
            dispatcher.utter_message(template="utter_how_to_help_next")
    else:
        return handle_name_slot(dispatcher, domain, tracker, last_template_event, last_event_custom_info, merged_custom)

    return []


def handle_name_slot(dispatcher, domain, tracker, last_template_event, last_event_custom_info, merged_custom):
    print("last_template_event ->", last_template_event)
    just_got_slot = False
    validation_result = True
    slot_value = ""

    if last_event_custom_info is not None:
        print("SLOT KEY-->", merged_custom.get("slot_name", None))
        # save the name to the template id
        # check the slot exist before
        event_slot_key = merged_custom.get("slot_name", None)
        # find_custom_info_by_key(last_event_custom_info, "slot_name")
        # if event_slot_key is not None and ai_bots_cache_dao.slot_exist(tracker.sender_id, event_slot_key):
        # just_got_slot = True
        if event_slot_key is not None:
            current_time = datetime.datetime.now()
            slot_value = tracker.latest_message.get("text", "")
            #validation_result = action_validators.run_validations(custom_dict=merged_custom, txt=slot_value)
            questions = [{'id': '0', 'question': 'what is my name'}]
            context = tracker.latest_message["text"]
            if (ask_bert_105(questions, context).get("0")):
                slot_value=ask_bert_105(questions, context).get("0")

                #validation_result = action_validators.run_validations(custom_dict=merged_custom, txt=slot_value)



    print("last_template_event ->", last_template_event, " just_got_slot ->", just_got_slot)

    print("slot_value",slot_value)
    if slot_value != "":
        user_name=True
    else:
        user_name = False
    # print("user_name -->>", user_name)
    if user_name:
        # get utter_ask_greet_name_01 from domain and pick one random one and present that
        # Did I great already? if so, let me not say that again...
        # if find_last_template_id_exists(events=tracker.events, template_id="greet_name_01") is False:
        if just_got_slot is False:
            random_domain_entry_text = build_message_by_template(domain, "utter_how_to_help")
        else:
            random_domain_entry_text = build_message_by_template(domain, "utter_how_to_help_01")
        dispatcher.utter_message(random_domain_entry_text)
        dispatcher.utter_message(template="utter_how_to_help_next")
        dispatcher.utter_message(template="utter_how_to_help_custom")
    else:
        if validation_result is True:
            print("-->")
            dispatcher.utter_message(template="utter_ask_greet_name")
            dispatcher.utter_message(template="utter_ask_name")
            dispatcher.utter_message(template="utter_ask_name_custom")
        else:
            dispatcher.utter_message(template="utter_re_ask_name")
            dispatcher.utter_message(template="utter_ask_name_custom")

    return []


def ask_bert_105(questions, context):
    try:
        responseObj = requests.post(
        "https://dl-server-api.skil.ai/v0/deep-learning/qa-generic-model/find-answers-based-on-context",
        data=json.dumps({'context': context, 'questions': questions}, indent = 2) )
        #print("x json-->", responseObj.text)
        x = json.loads(responseObj.text)
        if x.get("results", None) is not None and len(x.get("results")) > 0:
            return x.get("results")
        else:
            return {}
    except Exception as e:
        traceback.print_exc()
        print('Exception at bert', e)

def build_message_by_template(domain, template_name):
  all_domain_entries = domain.get("responses").get(template_name)
  random_domain_entry_text = random.choice(all_domain_entries).get("text")
  #random_domain_entry_text = Template(random_domain_entry_text).safe_substitute(dict_obj)
  return random_domain_entry_text
