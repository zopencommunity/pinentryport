#!/usr/bin/env python

import pexpect
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Locate the pinentry-tty executable
pintty = next((os.path.realpath(os.path.join(root, file))
               for root, _, files in os.walk('.')
               for file in files if file == "pinentry-tty"), None)

# Constants
INITIAL_HANDSHAKE = "OK Pleased to meet you"
BYE_COMMAND = "BYE"
CLOSING_CONNECTION = "OK closing connection"
TIMEOUT_ERROR = "Timeout waiting for: {expected}"
UNEXPECTED_EOF = "Unexpected end of file."

def log_output(enable_log, message):
    if enable_log:
        logging.info(message)

def send_command(child, command):
    child.sendline(command)

def expect_response(child, expected, timeout):
    try:
        child.expect(expected, timeout=timeout)
        return True
    except pexpect.TIMEOUT:
        logging.error(TIMEOUT_ERROR.format(expected=expected))
        return False
    except pexpect.EOF:
        logging.error(UNEXPECTED_EOF)
        return False

def test_pinentry_with_pty(commands, expected_responses, timeout=30, enable_log=False):
    """
    Test pinentry-tty with given commands and expected responses.

    Args:
        commands (list): List of commands to send.
        expected_responses (list): List of lists of expected responses for each command.
                                   Each command can have multiple expected responses.
        timeout (int): Timeout in seconds for expecting responses.

    Returns:
        bool: True if all commands received their expected responses; False otherwise.
    """
    try:
        # Start the pinentry-tty process
        child = pexpect.spawn(pintty, timeout=timeout)
        all_output = ""

        # Wait for the initial handshake
        if not expect_response(child, INITIAL_HANDSHAKE, timeout):
            return False

        log_output(enable_log, child.before.decode('utf-8') + child.after.decode('utf-8'))

        # Process each command
        for i, command in enumerate(commands):
            send_command(child, command)
            for expected in expected_responses[i]:
                if not expect_response(child, expected, 5):
                    return False
                log_output(enable_log, child.before.decode('utf-8') + child.after.decode('utf-8'))

        # Terminate the session cleanly
        send_command(child, BYE_COMMAND)
        if not expect_response(child, CLOSING_CONNECTION, timeout):
            return False

        log_output(enable_log, all_output)
        return True

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return False

TEST_CASES = [
    {
        "name": "Basic PIN test",
        "commands": [
            "SETPROMPT Enter your PIN",
            "SETTITLE PIN WINDOW",
            "GETPIN",
            "1234"
        ],
        "expected_responses": [
            ["OK"],
            ["OK"],
            ["PIN WINDOW", "Enter your PIN:"],
            ["D 1234", "OK"]
        ]
    },
    {
        "name": "Invalid Command",
        "commands": ["INVALIDCOMMAND"],
        "expected_responses": [["ERR"]]
    },
    {
        "name": "Timeout Simulation",
        "commands": [
            "SETDESC Operation with timeout",
            "SETTIMEOUT 3",
            "GETPIN"
        ],
        "expected_responses": [
            ["OK"],
            ["OK"],
            ["Operation with timeout", "PIN:", "ERR"]
        ]
    },
    {
        "name": "Correct PIN Repeat",
        "commands": [
            "SETPROMPT PIN",
            "SETTITLE PIN WINDOW",
            "SETREPEAT Re-Enter PIN",
            "GETPIN",
            "12345",
            "12345"
        ],
        "expected_responses": [
            ["OK"],
            ["OK"],
            ["OK"],
            ["PIN WINDOW", "PIN"],
            ["Re-Enter PIN"],
            ["PIN_REPEATED", "12345", "OK"]
        ]
    },
    {
        "name": "Incorrect PIN Repeat",
        "commands": [
            "SETPROMPT PIN",
            "SETTITLE PIN WINDOW",
            "SETREPEAT Re-Enter PIN",
            "SETREPEATERROR PIN MISMATCH",
            "GETPIN",
            "12345",
            "67890",
            "12345",
            "12345"
        ],
        "expected_responses": [
            ["OK"],
            ["OK"],
            ["OK"],
            ["OK"],
            ["PIN WINDOW", "PIN"],
            ["Re-Enter PIN"],
            ["PIN MISMATCH", "PIN:"],
            ["Re-Enter PIN"],
            ["PIN_REPEATED", "12345", "OK"]
        ]
    }
]

def run_tests():
    passed_count = 0
    failed_count = 0
    total_tests = len(TEST_CASES)

    for test in TEST_CASES:
        logging.info(f"Running test: {test['name']}")
        try:
            result = test_pinentry_with_pty(test["commands"], test["expected_responses"])
            if result:
                logging.info(f"Test passed: {test['name']}")
                passed_count += 1
            else:
                logging.info(f"Test failed: {test['name']}")
                failed_count += 1
        except Exception as e:
            logging.error(f"Test failed with error: {test['name']}. Error: {str(e)}")
            failed_count += 1

    # Display Summary
    logging.info("\nTest Summary:")
    print(f"Total tests: {total_tests}")
    print(f"Passed:      {passed_count}")
    print(f"Failed:      {failed_count}")

# Run all the tests
run_tests()
