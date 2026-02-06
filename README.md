# rasa-movies-bot

Rasa chatbot for movie suggestions and cinema ticket booking

This chatbot is designed to make movie suggestions using a movie as an example, provide information about the movies and help the user book, modify or cancel a movie screening reservation.

Motivation for choosing this specific domain and capabilities underlies in the sudden rise of streaming platforms in the past recent years in correlation to the sudden drop of visitors in movie theaters. Through this application, users get to benefit from the perk that comes with streaming platforms (movie suggestions based on what they like/have already seen) while providing easier access to booking a movie ticket to watch the movie they chose. Inspiration behind this kind of implementation was Cinobo (https://cinobo.com/en/); a movie theater that also offers streaming services for many movies and series.
The domain covers intents:

*  greet

*  goodbye

*  ask similar movies

*  book ticket(s)

*  ask movie details

*  cancel ticket

*  modify ticket count

*  bot challenge

## Scenarios

The implementation consists of a total of 9 scenarios. We will analyze 5 of these scenarios, which are considered to have important variations.

### Scenario 1 (mockup): Similar Movies

*  Action: action_find_similar_movies

*  Functionality: Finds 3 movies that are similar to the one referred from the user.

*  Demonstrates: The movies provided from TheMovieDB api.

### Scenario 2: Movie Details

*  Action: action_get_movie_details

*  Functionality: Acquire details about the plot and the rating of a movie based on its title. In addition to that, movie titled is stored in a separate .txt file (movie.txt) to use in future patches.

*  Demonstrates: static lists of data consisting of the summary and the rating of the movie.

### Scenario 3-5: Book a ticket/Modify/Cancel booking

Actions:

*  action_book_ticket : books one (or more tickets) as suggested by the user. Provides an easy booking experience for the user in order to visit the cinema.

*  action_modify_ticket_count : modifies the booking; changes ticket count based on what the user indicates. Provides the ability to modify a reservation in case of a slight change of plans (i.e. more or less people decide they want to watch the movie).

*  action_cancel_ticket : cancels booking(s) made by the particular user. Provides the ability to completely cancel the reservation in case of a mistake or the desire for a complete change of plans.

## Data sources

1.	Movies.txt
A .txt file containing a list of available movies. This works as a demo; it can either be a list of movies available to “stream”, or a list of movies that are currently playing. To make it exclusively as list of currently playing movies, only a few “tweaks” are required.
Important feature: current file is updated through the action “action_get_movie_details”. The list expands automatically each time a user asks for information about a movie. This way, the correct movie title is always extracted (since it is provided from the API), resulting in a faster completion of actions, while reducing API requests. Because of this method, each “patch” (retraining of the bot) adds more movies in its database. 

2.	Bookings.csv
A .csv file containing information about each booking. For each booking it is stored: the user id (which is a different id for each session), the movie it is intended to be watched, a randomly generated reservation number (booking id) and the number of tickets for each booking. With this implementation the user is able to modify or cancel the booking easily, while being able to book more than one movies to watch.

3.	The Movie DataBase (TMDB) API
Provides information about the movie. The capabilities utilized in the current version of the bot are: movie information (summary, rating and movie title) and the correlation of a movie with 3 others (used in action “action_find_similar_movies”).

## Challenges and solutions

*  Numbers as text:
The bot did not recognize numbers written in text (i.e. “six”) instead of an integer, in order to be aware of how many tickets to book.

Solution: a word mapping was implemented (i.e. one=1, two=2 etc) so that it can identify the right number. For instances such as “Book a ticket”, we simply included more examples in the nlu.yml, as well as other possible utterances which are suitable for bookings with more than one tickets.

*  Movie titles:
Some movie titles contain articles (“The Matrix”, “The Fantastic 4” etc) where slot is difficult to be recognized from the bot, or it fails to tell 2 movies apart (“The Matrix”, “Matrix”). Also, it faces challenges with synonyms or abbreviations of the title (“spiderman” instead of “Spider-Man”, “lotr” instead of  “Lord of The Rings”).

Solution: To deal with ambiguity, the movies.txt is a temporary but working solution, in addition to explicitly adding more references of these movies as examples in the nlu.yml. Regarding abbreviations and synonyms, we added “synonyms” in nlu.yml so that it acquires the ability to correlate 2 or more slots that appear quite different between them.

*  Confusion on actions to perform:
There were instances where the bot was asked to provide information about a movie, but decided to search for a booking or make one. This problem showed that there were not enough instances of utterances correlated with each action or that they were overlapping.
Solution: Adding more examples helped the bot better distinguish the which was the right action to perform, while carefully examining all the examples given for a possible overlap.

## Keys and credentials

TMDB: requires a valid API key obtained from the website. To obtain the key, it simply requires to create an account using your email and verify it.
To access specific capabilities (i.e. search for similar movies or obtain information about a movie, there are specific links provided in code (actions.py)).

## Example run

**User:**  hello

**Bot:** Hey! How are you?

**User:**  give me info on Deadpool

**Bot:** Found it: 'Deadpool' (Rating: 7.622/10).
Plot: The origin story of former Special Forces operative turned mercenary Wade Wilson, who, after being subjected to a rogue experiment that leaves him with accelerated healing powers, adopts the alter ego Deadpool. Armed with his new abilities and a dark, twisted sense of humor, Deadpool hunts down the man who nearly destroyed his life.

**User:**  find similar movies

**Bot:** If you liked 'Deadpool', you might enjoy: Deadpool 2, Captain America: Civil War, Doctor Strange.

**User:**  Give me info on Doctor Strange

**Bot:** Found it: 'Doctor Strange' (Rating: 7.417/10).
Plot: After his career is destroyed, a brilliant but arrogant surgeon gets a new lease on life when a sorcerer takes him under her wing and trains him to defend the world against evil.

**User:**  Book a ticket

**Bot:** I found 'Doctor Strange'. Ticket #3720 booked for 1 person(s)!

**User:**  Actually, make it 4

**Bot:** Done! Your booking for Doctor Strange is now for 4 tickets.

**User:**  Thank you!

**Bot:** Enjoy your movie!

**User:**  I want to cancel my booking

**Bot:** Booking cancelled.

**User:**  byebye

**Bot:** Enjoy your movie!

## Dialogue Policy

Since slots carry over, it was considered pointless to exclusively re-state the movie that the user wants to book. The most natural way to communicate is to assume that the last specific object (movie) referenced is the one that has to be booked or searched for similar movies.

The same assumption is also set for cancelation or modification of each booking, since it is less likely to book more than one movie in one session. Therefore, utterances such as “book it”, “cancel my reservation”, “find similar movies” etc, are considered valid for the current state of the bot. However, regarding bookings, this kind of assumptions should be handled more carefully in future updates.

Regarding re-stating the movie title, the user makes sure that the bot retrieved the right movie and booked the right number of tickets.
