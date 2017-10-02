import praw
import config
import languages
import time
from datetime import datetime
from googletrans import Translator

command = "!translate"

r = praw.Reddit (user_agent = "Translator Bot v0.1",
                 client_id = config.client_id,
                 client_secret = config.client_secret,
                 username = config.username,
                 password = config.password)

subreddit = r.subreddit("all")
count = 0

def translate (phrase, from_language, to_language):
    # translates a phrase from one language to another
    # if from_language is None, uses Google Translate's detect language function
    # if to_language is None, translates to English
    translator = Translator()
    if from_language is None and to_language is None:
        translation = translator.translate(phrase)
    elif from_language is None:
        translation = translator.translate(phrase, dest=to_language)
    elif to_language is None:
        translation = translator.translate(phrase, src=from_language)
    else:
        translation = translator.translate(phrase, dest=to_language, src=from_language)
    return translation

def index_of(some_list, item):
    # returns the index of some item in a list
    # if item not found, then returns -1
    try:
        return some_list.index(item)
    except ValueError:
        return -1

def convert_language(language):
    # returns a tuple
    # first item in the tuple is string, second item is a bool
    # if the language is valid, the first item is set to the language code, the second item is set to true
    # if the language is invalid, the first item is set to None, the second item is set to false
    # if the language is None, the first item is just set to None, the second item is still set to true

    if language is None:
        return (None, True)
    elif (language in languages.code_to_name): #checks if language string is already a language code
        return (language, True)
    else:
        try:
            return (languages.name_to_code[language.lower()], True)
        except KeyError:
            return (None, False)

def validate_comment(comment):
    # checks if bot should reply to comment
    #   -must contain command (!translate)
    #   -parent comment must not be deleted
    #   -must not reply to self
    #   -must not have already replied
    if command not in comment.body.lower():
        return False
    if comment.parent().banned_by is not None:
        print ("Parent comment deleted for comment #" + comment.id)
    if comment.author.name == "GoogleTranslate-Bot":
        print ("Cannot reply to self for comment #" + comment.id)
        return False
    comment.refresh()
    for child in comment.replies:
        if child.author.name == "GoogleTranslate-Bot":
            print ("Already replied to comment #" + comment.id)
            return False

    return True

def process_comment(comment):
    # processes the comment and translates the specified phrase
    # returns a tuple consisting of the original phrase, the translated phrase, the original language, the new language,
    # and two bools that describe whether the specified language was valid
    # plus an that describes whether the parent submission (0), parent comment (1), or a specified phrase (2) was translated
    comment_words = comment.body.lower().split() #converts comment to list of words to remove spaces

    translate_index = index_of(comment_words, "!translate")
    from_index = index_of(comment_words, "from")
    to_index = index_of(comment_words, "to")
    
    from_language = ""
    to_language = ""
    phrase = ""

    if(from_index == -1):
        from_language = None
    else:
        # sets from_language to the string between "from" and other keywords (or end of comment)
        i = from_index + 1
        while (i != to_index and i != translate_index and i < len(comment_words)):
            from_language += comment_words[i] + " "
            i += 1
        from_language = from_language[:-1] #removes the space at the end

    if(to_index == -1):
        to_language = None
    else:
        # sets to_language to the string between "to" and other keywords (or end of comment)
        i = to_index + 1
        while (i != from_index and i != translate_index and i < len(comment_words)):
            to_language += comment_words[i] + " "
            i += 1
        to_language = to_language[:-1] #removes the space at the end

    if(translate_index + 1 == from_index or translate_index + 1 == to_index or translate_index + 1 >= len(comment_words)):
        #check whether comment parent is submission or comment
        try:
            phrase = comment.parent().body
            phrase_type = 1
        except AttributeError:
            phrase = comment.parent().selftext
            phrase_type = 0
    else:
        # sets phrase to the string between "!translate" and other keywords (or end of comment)
        i = translate_index + 1
        while (i != from_index and i != to_index and i < len(comment_words)):
            phrase += comment_words[i] + " "
            i += 1
        phrase_type = 2
        phrase = phrase[:-1] #removes the space at the end

    # convert language names to language codes
    from_language_tuple = convert_language(from_language)
    to_language_tuple = convert_language(to_language)

    translation = translate(phrase, from_language_tuple[0], to_language_tuple[0])
    return (translation, from_language_tuple[1], to_language_tuple[1], phrase_type)

def reply(comment):
    # generates reply to comment
    # translation_tuple is in the form: (translation, bool specifying validity of origin language, 
    # bool specifying validity of destination language, int specifying whether
    # original phrase is a submission (0), comment (1), or specified phrase (2))
    translation_tuple = process_comment(comment)
    reply = ""

    if(translation_tuple[3] == 0):
        phrase_type = "submission"
    elif(translation_tuple[3] == 1):
        phrase_type = "comment"
    else:
        phrase_type = "phrase"

    beginning_of_to_language_apology = "Sorry, I was "
    if(translation_tuple[1] is False): # check if original from_language was valid
        reply += "Sorry, I was unable to translate the " + phrase_type + " provided from the language you specified. \n"
        if (translation_tuple[2] is False):
            beginning_of_to_language_apology = "I was also "

    if(translation_tuple[2] is False):
        reply += beginning_of_to_language_apology + "unable to translate the " 
        reply += phrase_type + " provided to the language you specified. \n" 
    
    reply += "\n***\n"

    reply += '^(Original Text: "' + translation_tuple[0].origin + '")\n \n' # used single quotes here so I could include double quotes in string
    reply += "**Translated from " + languages.code_to_name[translation_tuple[0].src.lower()]
    reply += " to " + languages.code_to_name[translation_tuple[0].dest.lower()]
    reply += ': "' + translation_tuple[0].text + '"**\n'

    if (translation_tuple[0].pronunciation is not None): # check if pronunciation is available
        reply += '*Pronounciation: "' + translation_tuple[0].pronunciation + '"*\n'

    reply += "\n***\n"
    reply += "^(Beep, boop, I'm a bot.) ^[info](https://github.com/hmku/googletranslate-bot)"

    comment.reply(reply)
    return reply

def run_bot():
    # runs the bot
    for comment in subreddit.stream.comments():	
        timestr = str (time.localtime()[3]) + ":" + str(time.localtime()[4])
        if validate_comment(comment):
            print ("Comment #" + comment.id + " processed at " + timestr + "!")
            print ("Bot's reply to #" + comment.id + ": \n" + reply(comment) + "\n")

while count < 100: # stops trying after 100 failed attempts (~300 seconds)
    try:
        print('Starting bot at %s' % (datetime.now()))
        count = 0
        run_bot()
    except Exception as e:
        print("> %s - Connection lost. Restarting in 3 seconds... %s" % (datetime.now(), e))
        count += 1
        time.sleep(3)
        continue