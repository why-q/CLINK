import logging

def setup_logging(tag="main"):
    if tag == "main":
        logging.basicConfig(filename='./clink.log', 
                        filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    elif tag == "test":
        logging.basicConfig(filename='./tests.log', 
                        filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    else: 
        print("Invalid tag")