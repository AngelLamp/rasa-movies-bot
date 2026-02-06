# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import os
import csv
import random
import json
import requests
import difflib
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


db = "bookings.csv"
api_key = "your_api_key" 


def save_movie_to_lookup(movie_title):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_directory) 
    file_path = os.path.join(project_root, "data", "movies.txt")
    
    if not os.path.exists(os.path.dirname(file_path)):
        file_path = "data/movies.txt"
    
    existing_movies = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            existing_movies = [line.strip().lower() for line in f.readlines()]
    
    if movie_title.lower() not in existing_movies:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{movie_title}")
        print(f"Verified and added '{movie_title}' to movies.txt")


class ActionGetMovieDetails(Action):
    def name(self) -> Text:
        return "action_get_movie_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        movie_query = next(tracker.get_latest_entity_values("movie_name"), None)

        if not movie_query:
            movie_query = tracker.get_slot('movie_name')

        if not movie_query:
            dispatcher.utter_message(text="Which movie are you asking about?")
            return []

        base_url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": api_key, "query": movie_query}

        try:
            response = requests.get(base_url, params=params)
            data = response.json()

            if response.status_code == 200 and not data['results']:
                print(f"Direct search failed for '{movie_query}'. Trying fuzzy match...")
            
            try:
                with open("movies.txt", "r") as f:
                    known_movies = [line.strip() for line in f.readlines()]
                
                matches = difflib.get_close_matches(movie_query, known_movies, n=1, cutoff=0.6)
                
                if matches:
                    suggestion = matches[0]
                    dispatcher.utter_message(text=f"I couldn't find '{movie_query}', but I found '{suggestion}'. Checking that...")
                    
                    params['query'] = suggestion
                    response = requests.get(base_url, params=params)
                    data = response.json()
            except FileNotFoundError:
                print("movies.txt not found. Skipping fuzzy match.")

            if response.status_code == 200 and data['results']:
                movie_data = data['results'][0]
                official_title = movie_data['title']
                overview = movie_data['overview']
                rating = movie_data['vote_average']

                save_movie_to_lookup(official_title)

                dispatcher.utter_message(
                    text=f"Found it: '{official_title}' (Rating: {rating}/10).\nPlot: {overview}"
                )
                return [SlotSet("movie_name", official_title)]
            
            else:
                dispatcher.utter_message(text=f"I couldn't find details for '{movie_query}'.")
                return []

        except Exception as e:
            print(f"Error: {e}")
            dispatcher.utter_message(text="I'm having trouble connecting to the movie database.")
            return []

class ActionFindSimilarMovies(Action):
    def name(self) -> Text:
        return "action_find_similar_movies"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        movie_query = tracker.get_slot('movie_name')
        if not movie_query:
            dispatcher.utter_message(text="I need to know which movie you liked first. Try 'find movies like Batman'.")
            return []

        search_url = "https://api.themoviedb.org/3/search/movie"
        try:
            search_res = requests.get(search_url, params={"api_key": api_key, "query": movie_query})
            search_data = search_res.json()
            
            if not search_data['results']:
                dispatcher.utter_message(text=f"I couldn't find '{movie_query}'.")
                return []
            
            movie_id = search_data['results'][0]['id']
            official_title = search_data['results'][0]['title']

            sim_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
            sim_res = requests.get(sim_url, params={"api_key": api_key})
            sim_data = sim_res.json()

            if sim_data['results']:
                titles = [m['title'] for m in sim_data['results'][:3]]
                titles_str = ", ".join(titles)
                dispatcher.utter_message(text=f"If you liked '{official_title}', you might enjoy: {titles_str}.")
            else:
                dispatcher.utter_message(text=f"I don't have any recommendations based on '{official_title}'.")

        except Exception as e:
            print(f"Error: {e}")
            dispatcher.utter_message(text="Sorry, I couldn't get recommendations right now.")
        return []

class ActionBookTicket(Action):

    def name(self) -> Text:
        return "action_book_ticket"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_id = tracker.sender_id
        ticket_count_str = next(tracker.get_latest_entity_values("ticket_count"), "1")

        word_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
        if ticket_count_str.lower() in word_map:
            ticket_count_str = word_map[ticket_count_str.lower()]
        
        new_movie_entity = next(tracker.get_latest_entity_values("movie_name"), None)
        slot_movie = tracker.get_slot('movie_name')

        movie_query = None

        if new_movie_entity:
            movie_query = new_movie_entity
        elif slot_movie:
            movie_query = slot_movie
        else:
            dispatcher.utter_message(text="Which movie do you want to book tickets for?")
            return []

        base_url = "https://api.themoviedb.org/3/search/movie"
        
        params = {
            "api_key": api_key,
            "query": movie_query
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if response.status_code == 200 and data['results']:
                official_title = data['results'][0]['title']
                booking_id = random.randint(1000, 9999)
                
                updated_rows = []
                if os.path.exists(db):
                    with open(db, "r", encoding="utf-8") as file:
                        reader = csv.reader(file)
                        header = next(reader, None)
                        if header: updated_rows.append(header)
                        for row in reader:
                            if row[0] != user_id:
                                updated_rows.append(row)
                else:
                    updated_rows.append(["user_id", "movie_title", "booking_id", "seats"])
                
                updated_rows.append([user_id, official_title, booking_id, ticket_count_str])

                with open(db, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerows(updated_rows)
                
                dispatcher.utter_message(
                    text=f"I found '{official_title}'. Ticket #{booking_id} booked for {ticket_count_str} person(s)!"
                )
                return [SlotSet("movie_name", official_title)]
            else:
                dispatcher.utter_message(text=f"I couldn't find '{movie_query}'. Maybe try another movie?")
                
        except Exception as e:
            print(f"Error: {e}")
            dispatcher.utter_message(text="System error connecting to movie database.")
        return []

class ActionModifyTicketCount(Action):

    def name(self) -> Text:
        return "action_modify_ticket_count"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_id = tracker.sender_id
        new_count_str = next(tracker.get_latest_entity_values("ticket_count"), None)

        if not new_count_str:
            dispatcher.utter_message(text="How many tickets do you want?")
            return []


        word_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}        
        
        try:
            if new_count_str.lower() in word_map:
                new_count_int = word_map[new_count_str.lower()]
            else:
                new_count_int = int(new_count_str)
        except ValueError:
            dispatcher.utter_message(text=f"I didn't understand the number '{new_count_str}'.")
            return []

        updated_rows = []
        found_booking = False
        movie_title = ""

        if not os.path.exists(db):
            dispatcher.utter_message(text="No bookings found.")
            return []
        
        with open(db, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header: updated_rows.append(header)
            
            for row in reader:
                if row[0] == user_id:
                    row[3] = str(new_count_int)
                    found_booking = True
                    movie_title = row[1]
                updated_rows.append(row)

        if found_booking:
            with open(db, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(updated_rows)

            dispatcher.utter_message(
                text=f"Done! Your booking for {movie_title} is now for {new_count_int} tickets."
            )
        else:
            dispatcher.utter_message(text="I couldn't find a booking to modify.")
        return []
    
class ActionCancelTicket(Action):

    def name(self) -> Text:
        return "action_cancel_ticket"
    
    def run(self, dispatcher, tracker, domain):
        user_id = tracker.sender_id
        updated_rows = []
        found = False
        
        if not os.path.exists(db):
             dispatcher.utter_message(text="No bookings to cancel.")
             return []

        with open(db, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            if header: updated_rows.append(header)
            for row in reader:
                if row[0] == user_id:
                    found = True
                else:
                    updated_rows.append(row)
        
        if found:
            with open(db, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(updated_rows)
            dispatcher.utter_message(text="Booking cancelled.")
        else:
            dispatcher.utter_message(text="No booking found for you.")
        return []