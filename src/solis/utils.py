import logging

def setup_logging(debug=False):
    '''
    Configures logging
    '''
    log = logging.getLogger(__name__).parent
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(process)d - %(message)s')
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    streamh = logging.StreamHandler()
    streamh.setFormatter(formatter)
    log.addHandler(streamh)
