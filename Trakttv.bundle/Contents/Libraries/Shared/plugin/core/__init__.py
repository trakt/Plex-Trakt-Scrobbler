import os

if os.environ.get('TFP_TEST_HOST', 'false') == 'false':
    import ospathfix
    import printfix
