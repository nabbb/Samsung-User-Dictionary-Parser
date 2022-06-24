import binascii
import logging
import struct
import os
import time
import pandas as pd

"""
Samsung User Dictionary Parser 

@Author: Nabila Agni
@Date: 14/06/2022
@Credit: Ruud Schramp
@Version: 1.0
"""


# Global variables
max_depth = False


# setup of the activity logger & creating a folder for the output files
def setup_activity_logger():
    print("\nEnter name that you want to give to the folder (+ path) for the output files: "
          "\nExample: case_number_samsung_s21")
    print('NOTE: do not use forbidden characters (:*?"<>\|) for the folder name')

    while True:
        folder_name = input(">Folder name (+path): ")
        try:
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
                logfile = folder_name + "//" + time.strftime("%Y_%m_%d-%H_%M_%S_%p ") + "testlog.log"
                break
            else:
                print("\nFolder already exists. Please insert another name for the folder.")
        except OSError as f:
            print("\nUnable to create the folder because of invalid characters or because it is not possible to create "
                  "a folder on this location. Please try again.")
            print('NOTE: do not use forbidden characters (:*?"<>\|) for the folder name')

    logging.basicConfig(level="DEBUG", filename=logfile, filemode="w",
                        format="%(asctime)s :: %(funcName)s :: %(lineno)d :: %(message)s")
    logging.info("Created a logfile. Location: " + logfile)
    logging.info("Name (+ path) of the folder in which the output files will be stored, inserted by the user: "
                 + folder_name)

    return folder_name


# user input for the names (+paths) of the necessary input files
def file_locations():
    print("\nEnter the path to and the filename of the dynamic.lm file you want to use:\nExample: /home/tmp/dynamic.lm")

    while True:
        dynamic_file = input(">Filename (+path): ")
        if dynamic_file.endswith(".lm"):
            try:
                with open(dynamic_file, "r") as file:
                    break
            except OSError as f:
                print("\nThe path and/or file does not exist. Please enter an existing path to an existing file: "
                      "\nExample: /home/tmp/dynamic.lm")
                logging.error("The user entered a non-existing file/filepath: " + dynamic_file)
        else:
            print("\nThe file should be a .lm file. Please insert a correct filename.")
            logging.error("The user inserted no file extension or another file extension than .lm: " + dynamic_file)

    logging.info("Dynamic language model filename (+ path), inserted by the user: " + dynamic_file)

    print("\nEnter the path to and the filename of the XLSX Word list file you want to use: "
          "\nExample: /home/tmp/20220511_word_list_ufed.xlsx")

    while True:
        excel_file = input(">Filename (+path): ")
        if excel_file.endswith(".xlsx"):
            try:
                with open(excel_file, "r") as file:
                    break
            except OSError as f:
                print("\nThe path and/or file does not exist. Please enter an existing path to an existing file: "
                      "\nExample: /home/tmp/20220511_word_list_ufed.xlsx")
                logging.error("The user entered a non-existing file/filepath: " + excel_file)
        else:
            print("\nThe file should be a .xlsx file. Please insert a correct filename.")
            logging.error("The user inserted no file extension or another file extension than .xlsx: " + excel_file)

    logging.info("UFED Report filename (+ path), inserted by the user: " + excel_file)

    print("\nEnter the path to and the filename of the text message you want to import (in txt format): "
          "\nExample: /home/tmp/message1.txt")

    while True:
        text_message = input("Filename (+path): ")
        if text_message.endswith(".txt"):
            try:
                with open(text_message, "r") as file:
                    break
            except OSError as f:
                print("\nThe path and/or file does not exist. Please enter an existing path to an existing file: "
                      "\nExample: /home/tmp/message1.txt")
                logging.error("The user entered a non-existing file/filepath: " + text_message)
        else:
            print("\nThe file should be a .txt file. Please insert a correct filename.")
            logging.error("The user inserted no file extension or another file extension than .txt: " + text_message)

    logging.info("Message filename (+ path), inserted by the user: " + text_message)

    return dynamic_file, excel_file, text_message


# make lists of the xlsx file which include the words, frequencies en index numbers
def create_word_list(excel_file):
    read_file = pd.read_excel(excel_file, header=1, usecols=["#", "Word", "Frequency"])
    ufed_list = read_file.to_dict("index")
    ufed_index_word = {}
    ufed_word_freq = {}

    for i in list(ufed_list):
        dictionary = ufed_list.get(i)
        dict_indexes, dict_word, dict_freq = dictionary["#"], dictionary["Word"], dictionary["Frequency"]

        if "(" and ")" in str(dict_indexes):
            ufed_list.pop(i)
        else:
            ufed_index_word[dict_indexes - 1] = dict_word
            ufed_word_freq[dict_word] = dict_indexes, dict_freq

    if len(ufed_list) == 0:
        print("\nUnable to extract information from the UFED report export file. Please restart the program and try again.")
        logging.error("Unable to extract information from the UFED report export file")
        logging.info("The program has been stopped.")
        exit()

    logging.info("Created two dictionaries from the UFED report export file")
    return ufed_index_word, ufed_word_freq


# start parsing the dynamic.lm file. uses other functions
def parse_file(dynamic_file, ufed_index_word, folder_name):
    with open(dynamic_file, "rb") as inputfile:
        index = seek_begin(inputfile)
        inputfile.seek(index)
        depth = "root"
        word_pred_file = folder_name + "//" + time.strftime("%Y_%m_%d-%H_%M_%S_%p ") + "result_predict.txt"
        logging.info("Created a file to write the word predictions to. Location: " + word_pred_file)
        logging.info("Making the Trie, converting the index numbers to words and writing the to output file...")

        parse_node(word_pred_file, inputfile, depth, ufed_index_word)
        logging.info("Finished making the Trie and writing the Trie paths to the output file.")


# find the offset of the first element in the Trie to be able to create the Trie
def seek_begin(dynamic_file):
    end = "06646d6170"
    convert = dynamic_file.read()
    hex_str = (str(binascii.hexlify(convert))[2:-1])
    logging.info("Converting language model file to hex with binascii.hexlify...")

    if len(hex_str) == 0:
        print("\nUnable to extract information from the language model file. Please restart the program and try again.")
        logging.error("The language model file " + dynamic_file.name
                     + " does not contain the right data to use with this program.  ")
        logging.info("The program has been stopped.")
        exit()

    logging.info("Looking for beginning of the Trie...")
    index = hex_str.find(end) + 18
    logging.info("Trie starts at offset: " + hex(int(index / 2)))

    return int(index / 2)


# read the content of dynamic.lm file 2 bytes (little endian notation) at a time from the found offset
def read_short(dynamic_file):
    short = dynamic_file.read(2)
    return struct.unpack("<H", short)[0]


# create a Trie from the content of the dynamic.lm file and write it to output file 'word_predict.txt'
def parse_node(word_pred_file, dynamic_file, depth, ufed_index_word):
    global max_depth
    with open(word_pred_file, "a", encoding="utf-8") as f:
        while True:
            number = read_short(dynamic_file)
            if number == 0:
                if max_depth:
                    max_depth = False
                    f.write(str(depth) + "\n")
                return

            max_depth = True
            frequency = read_short(dynamic_file)
            zeros = read_short(dynamic_file)
            word = ufed_index_word.get(number)
            if word is None:
                word = number
            parse_node(word_pred_file, dynamic_file, depth + " -> " + str(word) + "(" + str(frequency) + ")",
                       ufed_index_word)


# compare the words from the input message to the words from the UFED dictionary
def message_check(folder_name, ufed_word_freq, text_message):
    msg_list = []
    existingWords = 0
    with open(text_message, "r") as f:
        msg_rate_file = folder_name + "//" + time.strftime("%Y_%m_%d-%H_%M_%S_%p ") + "result_message.txt"
        msg_output = open(msg_rate_file, "a", encoding="utf-8")
        output_file = msg_output.name
        logging.info("Created a file to write the matching words between the message and UFED report export file to. "
                     "Location: " + msg_rate_file)

        for line in f.readlines():
            for word in line.split():
                msg_list.append(word)

        logging.info("Adding matching words to the output file...")
        for word in msg_list:
            wordExist = ufed_word_freq.get(word)

            if wordExist is None:
                existingWords = existingWords
            else:
                existingWords = existingWords + 1
                index = str(ufed_word_freq.get(word)[0])
                freq = str(ufed_word_freq.get(word)[1])
                msg_output.write(index + " " + word + "(" + freq + ")" + "\n")
        msg_output.close()

    if len(msg_list) == 0:
        print("\nThe file that should contain the text message is empty. Unable to compare words if there are none.")
        logging.warning("The file that should contain the text message is empty.")
        with open(output_file, "a") as f:
            f.write("This file was empty. Unable to compare words if there are none.")
            logging.info("Wrote a line in the empty text file.")
            logging.info("Finished.")
        pass
    else:
        logging.info("Defining the rate of the matching words...")
        matchingWordsRate = existingWords / len(msg_list) * 100
        define_result(output_file, matchingWordsRate)


# determine reliability percentage (existing words / max amount of words * 100)
def define_result(output_file, matchingWordsRate):
    with open(output_file, "r+") as f:
        intWordRate = round(matchingWordsRate, 1)
        logging.info("The matching words rate = " + str(intWordRate) + "%")
        if os.path.getsize(output_file) > 1:
            data = f.read()
            f.seek(0, 0)
            logging.info("Writing the matching words rate to the output file.")
            f.write(str(intWordRate) + "% of the words in the message match with the words from the "
                                       "UFED report export file.\n\n" + data)


if __name__ == "__main__":
    folder_name = setup_activity_logger()
    dynamic_file, excel_file, text_message = file_locations()
    ufed_index_word, ufed_word_freq = create_word_list(excel_file)
    parse_file(dynamic_file, ufed_index_word, folder_name)
    message_check(folder_name, ufed_word_freq, text_message)
    print("\n\n------------------------------------------------------------------------------------------------------")
    print("Finished! You can find the output files in the following folder:", folder_name)
    logging.info("Finished.")
